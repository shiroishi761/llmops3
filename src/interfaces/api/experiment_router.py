"""実験実行用APIルーター"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from ...application.use_cases.run_experiment import RunExperimentUseCase
from ...application.dto.experiment_dto import ExperimentResultDto

router = APIRouter(prefix="/api/experiments", tags=["experiments"])


class RunExperimentRequest(BaseModel):
    """実験実行リクエスト"""
    experiment_name: str
    dataset_override: Optional[str] = None  # データセットを上書きする場合
    prompt_override: Optional[str] = None   # プロンプトを上書きする場合


class RunExperimentResponse(BaseModel):
    """実験実行レスポンス"""
    experiment_id: str
    status: str
    summary: Dict[str, Any]
    result_file_path: str


@router.post("/run", response_model=RunExperimentResponse)
async def run_experiment(request: RunExperimentRequest):
    """指定された実験を実行"""
    try:
        use_case = RunExperimentUseCase()
        
        # experiments.ymlから実験を実行
        result = use_case.execute(
            "experiments/experiments.yml",
            request.experiment_name
        )
        
        return RunExperimentResponse(
            experiment_id=result.experiment_id,
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


@router.get("/list")
async def list_experiments():
    """利用可能な実験一覧を取得"""
    import yaml
    from pathlib import Path
    
    try:
        experiments_path = Path("experiments/experiments.yml")
        if not experiments_path.exists():
            return {"experiments": []}
            
        with open(experiments_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            
        if "experiments" not in config:
            return {"experiments": []}
            
        experiments = []
        for exp in config["experiments"]:
            experiments.append({
                "name": exp.get("experiment_name"),
                "prompt_name": exp.get("prompt_name"),
                "dataset_name": exp.get("dataset_name"),
                "llm_endpoint": exp.get("llm_endpoint"),
                "description": exp.get("description", "")
            })
            
        return {"experiments": experiments}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"実験一覧取得エラー: {str(e)}")


@router.post("/compare")
async def compare_experiments(experiment_names: List[str]):
    """複数の実験を実行して結果を比較"""
    try:
        results = []
        use_case = RunExperimentUseCase()
        
        for exp_name in experiment_names:
            result = use_case.execute(
                "experiments/experiments.yml",
                exp_name
            )
            results.append({
                "experiment_name": exp_name,
                "experiment_id": result.experiment_id,
                "overall_accuracy": result.summary.overall_accuracy,
                "field_accuracies": result.summary.field_accuracies,
                "total_documents": result.summary.total_documents,
                "successful_count": result.summary.successful_count,
                "failed_count": result.summary.failed_count
            })
            
        return {
            "comparison": results,
            "best_experiment": max(results, key=lambda x: x["overall_accuracy"])["experiment_name"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"実験比較エラー: {str(e)}")