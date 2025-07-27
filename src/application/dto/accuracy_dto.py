"""精度評価関連のDTO"""
from dataclasses import dataclass
from typing import List, Any

@dataclass
class FieldEvaluationDto:
    """フィールド評価結果のDTO"""
    field_name: str
    expected_value: Any
    actual_value: Any
    is_correct: bool
    score: float
    weight: float
    item_index: int = None
    
    def to_domain_model(self):
        """DTOからドメインモデルに変換"""
        from ...domain.models.field_result import FieldEvaluationResult
        return FieldEvaluationResult(
            field_name=self.field_name,
            expected_value=self.expected_value,
            actual_value=self.actual_value,
            is_correct=self.is_correct,
            score=self.score,
            weight=self.weight,
            item_index=self.item_index
        )

@dataclass
class DocumentEvaluationDto:
    """ドキュメント評価結果のDTO"""
    document_id: str
    field_results: List[FieldEvaluationDto]
    extraction_time_ms: int = 0
    error: str = None
    
    def to_domain_model(self):
        """DTOからドメインモデルに変換"""
        from ...domain.models.extraction_result import DocumentEvaluationResult
        domain_field_results = [dto.to_domain_model() for dto in self.field_results]
        return DocumentEvaluationResult(
            document_id=self.document_id,
            field_results=domain_field_results,
            extraction_time_ms=self.extraction_time_ms,
            error=self.error
        )
