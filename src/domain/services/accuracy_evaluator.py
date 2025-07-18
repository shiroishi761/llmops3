"""精度評価サービスの抽象インターフェース"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any

from src.application.dto.field_evaluation_dto import FieldEvaluationResultDto
from src.domain.exceptions import AccuracyEvaluationError


class AccuracyEvaluator(ABC):
    """精度評価サービスの抽象インターフェース"""
    
    @abstractmethod
    async def evaluate_extraction(
        self,
        expected: Dict[str, Any],
        actual: Dict[str, Any],
        field_weights: Dict[str, float],
        default_weight: float = 1.0
    ) -> List[FieldEvaluationResultDto]:
        """
        抽出結果の精度を評価
        
        Args:
            expected: 期待される抽出データ
            actual: 実際の抽出データ
            field_weights: フィールドごとの重み
            default_weight: デフォルトの重み
            
        Returns:
            各フィールドの精度結果DTOのリスト
            
        Raises:
            AccuracyEvaluationError: 評価に失敗した場合
        """
        pass