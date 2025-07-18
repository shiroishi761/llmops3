"""実験実行ユースケース"""
import uuid
import yaml
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.application.dto.experiment_dto import (
    ExperimentConfigDto,
    ExperimentResultDto,
    ExperimentSummaryDto,
    ErrorDto
)
from src.application.dto.field_evaluation_dto import (
    FieldEvaluationResultDto,
    DocumentEvaluationResultDto
)
from src.domain.models.experiment import Experiment, ExperimentStatus
from src.domain.services.accuracy_evaluator import AccuracyEvaluator
from src.domain.services.external_llm_service import ExternalLLMService
from src.domain.services.config_provider import ConfigProvider
from src.domain.repositories.experiment_repository import ExperimentRepository


logger = logging.getLogger(__name__)


class RunExperimentUseCase:
    """実験を実行するユースケース"""
    
    def __init__(
        self,
        experiment_repository: ExperimentRepository,
        external_llm_service: ExternalLLMService,
        accuracy_evaluator: AccuracyEvaluator,
        config_provider: ConfigProvider
    ):
        """
        初期化
        
        Args:
            experiment_repository: 実験リポジトリ
            external_llm_service: 外部LLMサービス
            accuracy_evaluator: 精度評価サービス
            config_provider: 設定プロバイダー
        """
        self.experiment_repository = experiment_repository
        self.external_llm_service = external_llm_service
        self.accuracy_evaluator = accuracy_evaluator
        self.config_provider = config_provider
        
    async def execute_from_config_path(self, experiment_config_path: str, experiment_name: Optional[str] = None) -> ExperimentResultDto:
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
        
        return await self.execute_from_config(config_dto)
    
    async def execute_from_config(self, config: ExperimentConfigDto) -> ExperimentResultDto:
        """
        設定DTOから実験を実行
        
        Args:
            config: 実験設定DTO
            
        Returns:
            実験結果DTO
        """
        experiment = Experiment(
            id=str(uuid.uuid4()),
            name=config.experiment_name,
            prompt_name=config.prompt_name,
            dataset_name=config.dataset_name,
            llm_endpoint=config.llm_endpoint,
            description=config.description
        )
        
        experiment.mark_as_running()
        logger.info(f"実験を開始します: {config.experiment_name}")
        
        errors: List[ErrorDto] = []
        
        try:
            logger.info(f"プロンプトを取得中: {config.prompt_name}")
            prompt_template = await self.external_llm_service.get_prompt(config.prompt_name)
            
            logger.info(f"データセットを取得中: {config.dataset_name}")
            dataset_items = await self.external_llm_service.get_dataset(config.dataset_name)
            logger.info(f"データセット内のアイテム数: {len(dataset_items)}")
            
            field_weights = self.config_provider.get_field_weights_dict()
            default_weight = self.config_provider.get_default_weight()
            
            for i, item in enumerate(dataset_items):
                logger.info(f"処理中 ({i+1}/{len(dataset_items)}): {item['id']}")
                
                try:
                    result_dto = await self._process_document(
                        item,
                        prompt_template,
                        config.prompt_name,
                        config.llm_endpoint,
                        field_weights,
                        default_weight
                    )
                    
                    experiment.add_result_from_dto(result_dto)
                    
                    if result_dto.is_successful:
                        logger.info(f"  ✓ 成功 (精度: {result_dto.overall_accuracy:.2%})")
                    else:
                        logger.warning(f"  ✗ 失敗: {result_dto.error_message}")
                        errors.append(ErrorDto(
                            document_id=item['id'],
                            error_message=result_dto.error_message or "Unknown error",
                            error_type="extraction_error"
                        ))
                        
                except Exception as e:
                    logger.error(f"  ✗ エラー: {str(e)}")
                    errors.append(ErrorDto(
                        document_id=item['id'],
                        error_message=str(e),
                        error_type="processing_error"
                    ))
            
            experiment.mark_as_completed()
            logger.info("実験が完了しました")
            
        except Exception as e:
            experiment.mark_as_failed(str(e))
            logger.error(f"実験が失敗しました: {str(e)}")
            raise
            
        finally:
            await self.external_llm_service.flush()
            
        result_path = self.experiment_repository.save(experiment)
        logger.info(f"結果を保存しました: {result_path}")
        
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
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"実験設定ファイルが見つかりません: {config_path}")
            
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            
        if experiment_name:
            if "experiments" in config:
                for exp in config["experiments"]:
                    if exp.get("experiment_name") == experiment_name:
                        return exp
                raise ValueError(f"実験名が見つかりません: {experiment_name}")
            elif config.get("experiment_name") == experiment_name:
                return config
            else:
                raise ValueError(f"実験名が見つかりません: {experiment_name}")
        else:
            if "experiments" in config:
                raise ValueError("実験名を指定してください (--name オプション)")
            
        required_fields = ["experiment_name", "prompt_name", "dataset_name", "llm_endpoint"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"必須フィールドがありません: {field}")
                
        return config
    
    async def _process_document(
        self,
        item: Dict[str, Any],
        prompt_template: str,
        prompt_name: str,
        llm_endpoint: str,
        field_weights: Dict[str, float],
        default_weight: float
    ) -> DocumentEvaluationResultDto:
        document_id = item["id"]
        input_data = item["input"]
        expected_data = item["expected_output"]
        
        try:
            prompt = prompt_template
            for key, value in input_data.items():
                placeholder = f"{{{key}}}"
                if isinstance(value, str):
                    prompt = prompt.replace(placeholder, value)
                else:
                    # 画像データなど、文字列でない場合はそのまま使用
                    prompt = prompt.replace(placeholder, str(value))
            
            extraction_response = await self.external_llm_service.extract_document(
                llm_endpoint=llm_endpoint,
                prompt_name=prompt_name,
                input_data=input_data
            )
            extraction_time_ms = extraction_response.get("extraction_time_ms")
            extracted_data = extraction_response.get("extracted_data", {})
            
            field_results_dto = await self.accuracy_evaluator.evaluate_extraction(
                expected_data,
                extracted_data,
                field_weights,
                default_weight
            )
            
            total_score = sum(result.score for result in field_results_dto)
            max_possible_score = sum(result.weight for result in field_results_dto)
            overall_accuracy = total_score / max_possible_score if max_possible_score > 0 else 0.0
            
            return DocumentEvaluationResultDto(
                document_id=document_id,
                is_successful=True,
                overall_accuracy=overall_accuracy,
                total_score=total_score,
                max_possible_score=max_possible_score,
                field_results=field_results_dto,
                execution_time_ms=extraction_time_ms
            )
            
        except Exception as e:
            return DocumentEvaluationResultDto(
                document_id=document_id,
                is_successful=False,
                overall_accuracy=0.0,
                total_score=0.0,
                max_possible_score=0.0,
                field_results=[],
                error_message=str(e)
            )
    
