"""フィールド評価結果関連のDTO"""
from dataclasses import dataclass
from typing import Optional, Any, List, Dict


@dataclass(frozen=True)
class FieldEvaluationResultDto:
    """フィールド評価結果のDTO"""
    field_name: str
    expected_value: Optional[Any]
    actual_value: Optional[Any]
    is_correct: bool
    score: float
    weight: float
    display_name: str 
    item_index: Optional[int] = None
    details: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class DocumentEvaluationResultDto:
    """ドキュメント評価結果のDTO"""
    document_id: str
    is_successful: bool
    overall_accuracy: float
    total_score: float
    max_possible_score: float
    field_results: List[FieldEvaluationResultDto]
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None