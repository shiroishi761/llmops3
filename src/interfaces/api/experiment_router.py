"""実験実行用APIルーター"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from ...application.use_cases.run_experiment import RunExperimentUseCase
from ...application.services.configuration_service import ConfigurationService
from ...application.services.prompt_service import PromptService
from ...application.services.dataset_service import DatasetService
from ...infrastructure.external_services.llm_client import LLMClient
from ...infrastructure.repositories.file_experiment_repository import FileExperimentRepository
from ...domain.services.accuracy_evaluation_service import AccuracyEvaluationService
from ...domain.services.items_matching_service import ItemsMatchingService
from ...infrastructure.external_services.gemini_service import GeminiService

router = APIRouter(prefix="/api/experiments", tags=["experiments"])

class RunExperimentRequest(BaseModel):
    """実験実行リクエスト"""
    experiment_name: str

class RunExperimentResponse(BaseModel):
    """実験実行レスポンス"""
    experiment_name: str
    status: str
    summary: Dict[str, Any]
    result_file_path: str

@router.post("/run", 
response_model=RunExperimentResponse)
async def run_experiment(request: RunExperimentRequest):
    """指定された実験を実行"""
    try:
        # 依存関係を直接注入
        config_service = ConfigurationService(field_weights_config_path="config/config.yml")
        prompt_service = PromptService()
        dataset_service = DatasetService()
        llm_client = LLMClient()
        experiment_repository = FileExperimentRepository()
        accuracy_service = AccuracyEvaluationService()
        gemini_service = GeminiService(config_service)
        items_matching_service = ItemsMatchingService(gemini_service)
        
        use_case = RunExperimentUseCase(
            config_service=config_service,
            prompt_service=prompt_service,
            dataset_service=dataset_service,
            llm_client=llm_client,
            experiment_repository=experiment_repository,
            accuracy_service=accuracy_service,
            items_matching_service=items_matching_service
        )
        
        # experiments.ymlから実験を実行
        result = await use_case.execute(
            "experiments/experiments.yml",
            request.experiment_name
        )
        
        return RunExperimentResponse(
            experiment_name=request.experiment_name,
            status=result.status,
            summary={
                "total_documents": result.summary.total_documents,
                "successful_count": result.summary.successful_count,
                "failed_count": result.summary.failed_count,
                "overall_accuracy": result.summary.overall_accuracy,
                "field_accuracies": result.summary.field_accuracies
            },
            result_file_path=result.result_file_path
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"実験実行エラー: {str(e)}")
