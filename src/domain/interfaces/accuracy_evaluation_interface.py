"""精度評価サービスのインターフェース"""
from typing import Dict, List, Any, Protocol

from ...application.dto.accuracy_dto import FieldEvaluationDto


class AccuracyEvaluationInterface(Protocol):
    """精度評価のインターフェース"""
    
    def evaluate_extraction(
        self,
        expected: Dict[str, Any],
        actual: Dict[str, Any],
        field_weights: Dict[str, float],
        default_weight: float = 1.0
    ) -> List[FieldEvaluationDto]:
        """
        抽出結果の精度を評価
        
        Args:
            expected: 期待される抽出データ
            actual: 実際の抽出データ
            field_weights: フィールドごとの重み
            default_weight: デフォルトの重み
            
        Returns:
            各フィールドの精度結果のDTOリスト
        """
        ...