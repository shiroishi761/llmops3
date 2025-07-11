"""実験実行ユースケース"""
import uuid
import yaml
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..dto.experiment_dto import (
    ExperimentConfigDto,
    ExperimentResultDto,
    ExperimentSummaryDto,
    ErrorDto
)
from ...domain.models.experiment import Experiment, ExperimentStatus
from ...domain.models.extraction_result import DocumentEvaluationResult
from ...domain.services.accuracy_evaluation_service import AccuracyEvaluationService
from ...infrastructure.config.configuration_service import ConfigurationService
from ...infrastructure.external_services.langfuse_service import LangfuseService
from ...infrastructure.external_services.gemini_service import GeminiService
from ...infrastructure.external_services.llm_client import LLMClient
from ...infrastructure.repositories.file_experiment_repository import FileExperimentRepository
from ...infrastructure.llm.llm_matching_service import LLMMatchingService


class RunExperimentUseCase:
    """実験を実行するユースケース"""
    
    def __init__(
        self,
        config_service: Optional[ConfigurationService] = None,
        langfuse_service: Optional[LangfuseService] = None,
        gemini_service: Optional[GeminiService] = None,
        experiment_repository: Optional[FileExperimentRepository] = None,
        accuracy_service: Optional[AccuracyEvaluationService] = None,
        llm_client: Optional[LLMClient] = None
    ):
        """
        初期化
        
        Args:
            config_service: 設定サービス
            langfuse_service: Langfuseサービス
            gemini_service: Geminiサービス
            experiment_repository: 実験リポジトリ
            accuracy_service: 精度評価サービス
            llm_client: LLMクライアント
        """
        self.config_service = config_service or ConfigurationService()
        self.langfuse_service = langfuse_service or LangfuseService(self.config_service)
        self.gemini_service = gemini_service or GeminiService(self.config_service)
        self.experiment_repository = experiment_repository or FileExperimentRepository()
        self.llm_client = llm_client or LLMClient()
        
        # 精度評価サービス
        self.accuracy_service = accuracy_service or AccuracyEvaluationService(
            self.config_service
        )
        
    def execute(self, experiment_config_path: str, experiment_name: Optional[str] = None) -> ExperimentResultDto:
        """
        実験設定ファイルから実験を実行
        
        Args:
            experiment_config_path: 実験設定ファイルのパス
            experiment_name: 実験名（指定した場合はその実験のみ実行）
            
        Returns:
            実験結果DTO
        """
        # 設定ファイルを読み込み
        config = self._load_experiment_config(experiment_config_path, experiment_name)
        
        # DTOに変換
        config_dto = ExperimentConfigDto(
            experiment_name=config["experiment_name"],
            prompt_name=config["prompt_name"],
            dataset_name=config["dataset_name"],
            llm_endpoint=config["llm_endpoint"],
            description=config.get("description")
        )
        
        # 実験を実行
        return self.execute_from_config(config_dto)
    
    def execute_from_config(self, config: ExperimentConfigDto) -> ExperimentResultDto:
        """
        設定DTOから実験を実行
        
        Args:
            config: 実験設定DTO
            
        Returns:
            実験結果DTO
        """
        # 実験エンティティを作成
        experiment = Experiment(
            id=str(uuid.uuid4()),
            name=config.experiment_name,
            prompt_name=config.prompt_name,
            dataset_name=config.dataset_name,
            llm_endpoint=config.llm_endpoint,
            description=config.description
        )
        
        # 実験を開始
        experiment.mark_as_running()
        print(f"実験を開始します: {config.experiment_name}")
        
        errors: List[ErrorDto] = []
        
        try:
            # プロンプトを取得
            print(f"プロンプトを取得中: {config.prompt_name}")
            prompt_template = self.langfuse_service.get_prompt(config.prompt_name)
            
            # データセットを取得
            print(f"データセットを取得中: {config.dataset_name}")
            dataset_items = self.langfuse_service.get_dataset(config.dataset_name)
            print(f"データセット内のアイテム数: {len(dataset_items)}")
            
            # フィールド重みを取得
            field_weights = self.config_service.get_field_weights_dict()
            default_weight = self.config_service.get_default_weight()
            
            # 各ドキュメントを処理
            for i, item in enumerate(dataset_items):
                print(f"処理中 ({i+1}/{len(dataset_items)}): {item['id']}")
                
                try:
                    # ドキュメント処理
                    result = self._process_document(
                        item,
                        prompt_template,
                        config.prompt_name,
                        config.llm_endpoint,
                        field_weights,
                        default_weight
                    )
                    experiment.add_result(result)
                    
                    if result.is_success():
                        print(f"  ✓ 成功 (精度: {result.calculate_accuracy():.2%})")
                    else:
                        print(f"  ✗ 失敗: {result.error}")
                        errors.append(ErrorDto(
                            document_id=item['id'],
                            error_message=result.error or "Unknown error",
                            error_type="extraction_error"
                        ))
                        
                except Exception as e:
                    print(f"  ✗ エラー: {str(e)}")
                    errors.append(ErrorDto(
                        document_id=item['id'],
                        error_message=str(e),
                        error_type="processing_error"
                    ))
            
            # 実験を完了
            experiment.mark_as_completed()
            print("実験が完了しました")
            
        except Exception as e:
            # 実験を失敗として記録
            experiment.mark_as_failed(str(e))
            print(f"実験が失敗しました: {str(e)}")
            raise
            
        finally:
            # Langfuseのバッファをフラッシュ
            self.langfuse_service.flush()
            
        # 結果を保存
        result_path = self.experiment_repository.save(experiment)
        print(f"結果を保存しました: {result_path}")
        
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
    
    def _load_experiment_config(self, config_path: str, experiment_name: Optional[str] = None) -> Dict[str, Any]:
        """実験設定ファイルを読み込み"""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"実験設定ファイルが見つかりません: {config_path}")
            
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            
        # experiment_nameが指定されている場合は、その実験を探す
        if experiment_name:
            if "experiments" in config:
                # 複数実験形式
                for exp in config["experiments"]:
                    if exp.get("experiment_name") == experiment_name:
                        return exp
                raise ValueError(f"実験名が見つかりません: {experiment_name}")
            elif config.get("experiment_name") == experiment_name:
                # 単一実験形式（後方互換性のため）
                return config
            else:
                raise ValueError(f"実験名が見つかりません: {experiment_name}")
        else:
            # experiment_nameが指定されていない場合は従来の形式を想定
            if "experiments" in config:
                raise ValueError("実験名を指定してください (--name オプション)")
            
        # 必須フィールドを検証
        required_fields = ["experiment_name", "prompt_name", "dataset_name", "llm_endpoint"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"必須フィールドがありません: {field}")
                
        return config
    
    def _process_document(
        self,
        item: Dict[str, Any],
        prompt_template: str,
        prompt_name: str,
        llm_endpoint: str,
        field_weights: Dict[str, float],
        default_weight: float
    ) -> DocumentEvaluationResult:
        """単一のドキュメントを処理"""
        document_id = item["id"]
        input_data = item["input"]
        expected_data = item["expected_output"]
        
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
            extraction_response = self.llm_client.extract(
                llm_endpoint=llm_endpoint,
                prompt_name=prompt_name,
                input_data=input_data
            )
            extraction_time_ms = extraction_response.get("extraction_time_ms", int((time.time() - start_time) * 1000))
            
            extracted_data = extraction_response.get("extracted_data", {})
            
            # 精度を評価
            field_results = self.accuracy_service.evaluate_extraction(
                expected_data,
                extracted_data,
                field_weights,
                default_weight
            )
            
            # 結果を作成
            return DocumentEvaluationResult(
                document_id=document_id,
                expected_data=expected_data,
                extracted_data=extracted_data,
                field_results=field_results,
                extraction_time_ms=extraction_time_ms
            )
            
        except Exception as e:
            # エラー時の結果
            return DocumentEvaluationResult(
                document_id=document_id,
                expected_data=expected_data,
                extracted_data={},
                field_results=[],
                error=str(e)
            )
