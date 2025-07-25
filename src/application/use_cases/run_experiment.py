"""実験実行ユースケース"""
import uuid
import time
import logging
import asyncio
from typing import Dict, Any, List, Optional

from ..dto.experiment_dto import (
    ExperimentResultDto,
    ExperimentSummaryDto,
    ErrorDto
)
from ...domain.models.experiment import Experiment
from ..dto.accuracy_dto import FieldEvaluationDto, DocumentEvaluationDto
from ..interfaces import (
    ConfigurationInterface,
    PromptInterface,
    DatasetInterface,
    LLMClientInterface
)
from ...domain.interfaces import AccuracyEvaluationInterface
from ...domain.interfaces.items_matching_interface import ItemsMatchingInterface
from ...domain.repositories.experiment_repository import ExperimentRepository


class RunExperimentUseCase:
    """実験を実行するユースケース"""
    
    def __init__(
        self,
        config_service: ConfigurationInterface,
        prompt_service: PromptInterface,
        dataset_service: DatasetInterface,
        llm_client: LLMClientInterface,
        experiment_repository: ExperimentRepository,
        accuracy_service: AccuracyEvaluationInterface,
        items_matching_service: ItemsMatchingInterface,
    ):
        """
        初期化
        
        Args:
            config_service: 設定サービス（必須）
            prompt_service: プロンプトサービス（必須）
            dataset_service: データセットサービス（必須）
            llm_client: LLMクライアント（必須）
            experiment_repository: 実験リポジトリ（必須）
            accuracy_service: 精度評価サービス（必須）
            items_matching_service: アイテムマッチングサービス（必須）
        """
        self.config_service = config_service
        self.prompt_service = prompt_service
        self.dataset_service = dataset_service
        self.llm_client = llm_client
        self.experiment_repository = experiment_repository
        self.accuracy_service = accuracy_service
        self.items_matching_service = items_matching_service
        
    async def execute(self, experiment_config_path: str, experiment_name: Optional[str] = None) -> ExperimentResultDto:
        """
        実験設定ファイルから実験を実行
        
        Args:
            experiment_config_path: 実験設定ファイルのパス
            experiment_name: 実験名（指定した場合はその実験のみ実行）
            
        Returns:
            実験結果DTO
        """
        # 設定ファイルを読み込み
        experiment_config = self.config_service.load_experiment_config(experiment_config_path, experiment_name)
        # 実験エンティティを作成
        experiment = Experiment(
            id=str(uuid.uuid4()),
            name=experiment_config["experiment_name"],
            prompt_name=experiment_config["prompt_name"],
            dataset_name=experiment_config["dataset_name"],
            llm_endpoint=experiment_config["llm_endpoint"],
            description=experiment_config.get("description")
        )
        
        # 実験を開始
        experiment.mark_as_running()
        logging.info(f"実験を開始します: {experiment_config['experiment_name']}")
        
        errors: List[ErrorDto] = []
        
        try:
            # プロンプトを取得
            logging.info(f"プロンプトを取得中: {experiment_config['prompt_name']}")
            prompt_template = self.prompt_service.get_prompt(experiment_config["prompt_name"])
            
            # データセットを取得
            logging.info(f"データセットを取得中: {experiment_config['dataset_name']}")
            documents = self.dataset_service.get_dataset(experiment_config["dataset_name"])
            logging.info(f"ローカルデータセットを使用します")
            logging.info(f"データセット内のドキュメント数: {len(documents)}")
            
            # フィールド重みを取得
            field_weights = self.config_service.get_field_weights_dict()
            default_weight = self.config_service.get_default_weight()
            
            # 各ドキュメントを処理
            for i, document in enumerate(documents):
                logging.info(f"処理中 ({i+1}/{len(documents)}): {document['id']}")
                
                try:
                    # ドキュメント処理
                    result = await self._process_document(
                        document,
                        prompt_template,
                        experiment_config["llm_endpoint"],
                        field_weights,
                        default_weight
                    )
                    experiment.add_result(result)
                    
                    if not result.error:
                        # DTOから精度を計算
                        if result.field_results:
                            total_score = sum(fr.score for fr in result.field_results)
                            total_weight = sum(fr.weight for fr in result.field_results)
                            accuracy = total_score / total_weight if total_weight > 0 else 0.0
                            logging.info(f"  ✓ 成功 (精度: {accuracy:.2%})")
                        else:
                            logging.info(f"  ✓ 成功")
                    else:
                        logging.error(f"  ✗ 失敗: {result.error}")
                        errors.append(ErrorDto(
                            document_id=document['id'],
                            error_message=result.error or "Unknown error",
                            error_type="extraction_error"
                        ))
                        
                except Exception as e:
                    logging.error(f"  ✗ エラー: {str(e)}")
                    errors.append(ErrorDto(
                        document_id=document['id'],
                        error_message=str(e),
                        error_type="processing_error"
                    ))
            
            # 実験を完了
            experiment.mark_as_completed()
            logging.info("実験が完了しました")
            
        except Exception as e:
            # 実験を失敗として記録
            experiment.mark_as_failed(str(e))
            logging.error(f"実験が失敗しました: {str(e)}")
            raise
            
        finally:
            pass
            
        # 結果を保存（DTOに変換）
        experiment_dto = experiment.to_dto()
        result_path = self.experiment_repository.save(experiment_dto)
        logging.info(f"結果を保存しました: {result_path}")
        
        # 結果DTOを作成
        summary = experiment.get_summary()
        return ExperimentResultDto(
            experiment_id=experiment.id,
            status=experiment.status.value,
            summary=ExperimentSummaryDto(
                total_documents=summary["total_documents"],
                successful_count=summary["successful_count"],
                failed_count=summary["failed_count"],
                overall_accuracy=summary["overall_accuracy"],
                field_accuracies=summary["field_accuracies"],
                field_scores=summary.get("field_scores"),
                execution_time_ms=summary["execution_time_ms"]
            ),
            errors=errors,
            result_file_path=str(result_path)
        )
    
    
    async def _process_document(
        self,
        document: Dict[str, Any],
        prompt_template: str,
        llm_endpoint: str,
        field_weights: Dict[str, float],
        default_weight: float
    ) -> DocumentEvaluationDto:
        """単一のドキュメントを処理"""
        document_id = document["id"]
        input_data = document["input"]
        expected_data = document["expected_output"]
        
        try:
            # プロンプトに変数を埋め込み
            # input_dataの各キーを対応する変数に置換
            prompt = prompt_template
            for key, value in input_data.items():
                placeholder = f"{{{key}}}"
                if isinstance(value, str):
                    prompt = prompt.replace(placeholder, value)
                else:
                    # 画像データなど、文字列でない場合はそのまま使用
                    prompt = prompt.replace(placeholder, str(value))
            
            # LLMエンドポイント経由で抽出
            start_time = time.time()
            extraction_response = await self.llm_client.extract_async(
                llm_endpoint=llm_endpoint,
                prompt=prompt
            )
            extraction_time_ms = extraction_response.get("extraction_time_ms", int((time.time() - start_time) * 1000))
            
            extracted_data = extraction_response.get("extracted_data", {})
            
            # itemsフィールドのマッチング処理をサービスに委譲
            expected_data, extracted_data = self.items_matching_service.process_matched_items(
                expected_data, extracted_data
            )
            
            # 精度を評価
            field_results_dto = self.accuracy_service.evaluate_extraction(
                expected_data,
                extracted_data,
                field_weights,
                default_weight
            )
            
            # DTOで結果を作成
            return DocumentEvaluationDto(
                document_id=document_id,
                expected_data=expected_data,
                extracted_data=extracted_data,
                field_results=field_results_dto,
                extraction_time_ms=extraction_time_ms
            )
            
        except Exception as e:
            # エラー時の結果
            return DocumentEvaluationDto(
                document_id=document_id,
                expected_data=expected_data,
                extracted_data={},
                field_results=[],
                error=str(e)
            )
