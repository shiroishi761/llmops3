"""実験関連のDTO"""
from dataclasses import dataclass
from typing import Optional, Dict, Any, List


@dataclass
class ExperimentConfigDto:
    """実験設定のDTO"""
    experiment_name: str
    prompt_name: str
    dataset_name: str
    llm_endpoint: str
    description: Optional[str] = None
    

@dataclass  
class ExperimentResultDto:
    """実験結果のDTO"""
    experiment_id: str
    status: str
    summary: 'ExperimentSummaryDto'
    errors: List['ErrorDto']
    result_file_path: str
    

@dataclass
class ExperimentSummaryDto:
    """実験サマリーのDTO"""
    total_documents: int
    successful_count: int
    failed_count: int
    overall_accuracy: float
    field_accuracies: Dict[str, float]
    field_scores: Optional[Dict[str, Dict[str, float]]] = None
    execution_time_ms: Optional[int] = None
    

@dataclass
class ErrorDto:
    """エラー情報のDTO"""
    document_id: str
    error_message: str
    error_type: str