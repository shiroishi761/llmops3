"""手動依存性注入コンテナ"""
from src.application.use_cases.run_experiment import RunExperimentUseCase
from src.domain.services.accuracy_evaluator import AccuracyEvaluator
from src.domain.services.external_llm_service import ExternalLLMService
from src.domain.services.config_provider import ConfigProvider
from src.domain.repositories.experiment_repository import ExperimentRepository

from src.infrastructure.config.configuration_service import ConfigurationService
from src.infrastructure.external_services.langfuse_service import LangfuseService
from src.infrastructure.external_services.llm_client import LLMClient
from src.infrastructure.repositories.file_experiment_repository import FileExperimentRepository
from src.infrastructure.services.integrated_llm_service import IntegratedLLMService
from src.infrastructure.report.html_report_generator import HTMLReportGenerator
from src.domain.services.accuracy_evaluation_service import AccuracyEvaluationService
from src.domain.services.items_matching_service import ItemsMatchingService
from src.domain.services.field_score_calculator import FieldScoreCalculatorFactory


class DIContainer:
    """手動依存性注入コンテナ"""
    
    def __init__(self):
        self._config_provider = None
        self._experiment_repository = None
        self._external_llm_service = None
        self._accuracy_evaluator = None
        self._items_matching_service = None
        self._field_score_calculator_factory = None
    
    @property
    def config_provider(self) -> ConfigProvider:
        """設定プロバイダーを取得"""
        if self._config_provider is None:
            self._config_provider = ConfigurationService()
        return self._config_provider
    
    @property 
    def experiment_repository(self) -> ExperimentRepository:
        """実験リポジトリを取得"""
        if self._experiment_repository is None:
            self._experiment_repository = FileExperimentRepository()
        return self._experiment_repository
    
    @property
    def external_llm_service(self) -> ExternalLLMService:
        """外部LLMサービスを取得"""
        if self._external_llm_service is None:
            config = self.config_provider
            langfuse_service = LangfuseService(config)
            llm_client = LLMClient()
            self._external_llm_service = IntegratedLLMService(langfuse_service, llm_client)
        return self._external_llm_service
    
    @property
    def items_matching_service(self) -> ItemsMatchingService:
        """明細マッチングサービスを取得"""
        if self._items_matching_service is None:
            # 純粋なLLMマッチングサービスとして作成
            self._items_matching_service = ItemsMatchingService()
        return self._items_matching_service
    
    @property
    def field_score_calculator_factory(self) -> FieldScoreCalculatorFactory:
        """フィールドスコア計算ファクトリを取得"""
        if self._field_score_calculator_factory is None:
            self._field_score_calculator_factory = FieldScoreCalculatorFactory(
                items_matching_service=self.items_matching_service
            )
        return self._field_score_calculator_factory
    
    @property
    def accuracy_evaluator(self) -> AccuracyEvaluator:
        """精度評価サービスを取得"""
        if self._accuracy_evaluator is None:
            self._accuracy_evaluator = AccuracyEvaluationService()
            # ファクトリを設定されたものに差し替え
            self._accuracy_evaluator.calculator_factory = self.field_score_calculator_factory
        return self._accuracy_evaluator
    
    def create_run_experiment_use_case(self) -> RunExperimentUseCase:
        """RunExperimentUseCaseを作成"""
        return RunExperimentUseCase(
            experiment_repository=self.experiment_repository,
            external_llm_service=self.external_llm_service,
            accuracy_evaluator=self.accuracy_evaluator,
            config_provider=self.config_provider
        )
    
