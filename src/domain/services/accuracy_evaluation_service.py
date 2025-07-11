"""精度評価サービス"""
from typing import Dict, List, Any, Optional, Union

from ..models.field_result import FieldEvaluationResult
from .field_score_calculator import FieldScoreCalculatorFactory


class AccuracyEvaluationService:
    """精度評価を行うドメインサービス"""
    
    def __init__(self, config_service=None):
        self.config_service = config_service
        self.calculator_factory = FieldScoreCalculatorFactory()
    
    def evaluate_extraction(
        self,
        expected: Dict[str, Any],
        actual: Dict[str, Any],
        field_weights: Dict[str, float],
        default_weight: float = 1.0
    ) -> List[FieldEvaluationResult]:
        """
        抽出結果の精度を評価
        
        Args:
            expected: 期待される抽出データ
            actual: 実際の抽出データ
            field_weights: フィールドごとの重み
            default_weight: デフォルトの重み
            
        Returns:
            各フィールドの精度結果のリスト
        """
        results = []
        
        # すべての期待されるフィールドを評価
        all_fields = set(expected.keys()) | set(actual.keys())
        
        for field_name in all_fields:
            # itemsフィールドは特別に処理
            if field_name == 'items':
                expected_items = expected.get(field_name, [])
                actual_items = actual.get(field_name, [])
                
                # itemsフィールドのサブフィールドを個別に評価
                items_results = self._evaluate_items_fields(
                    expected_items, actual_items, field_weights, default_weight
                )
                results.extend(items_results)
            else:
                expected_value = expected.get(field_name)
                actual_value = actual.get(field_name)
                
                # フィールドの重みを取得
                weight = field_weights.get(field_name, default_weight)
                
                # 適切なCalculatorを取得して評価
                calculator = self.calculator_factory.get_calculator(field_name)
                field_results = calculator.calculate(
                    field_name, expected_value, actual_value, weight
                )
                results.extend(field_results)
            
        return results
    
    def _evaluate_items_fields(
        self,
        expected_items: List[Dict[str, Any]],
        actual_items: List[Dict[str, Any]],
        field_weights: Dict[str, float],
        default_weight: float
    ) -> List[FieldEvaluationResult]:
        """itemsのサブフィールドを個別に評価"""
        results = []
        
        # ItemsCalculatorを使用
        calculator = self.calculator_factory.get_calculator('items')
        
        # items全体を評価（各サブフィールドとアイテムインデックスを考慮）
        items_results = calculator.calculate(
            'items', expected_items, actual_items, 
            field_weights, default_weight
        )
        results.extend(items_results)
        
        return results
    
