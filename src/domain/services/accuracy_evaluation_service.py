"""精度評価サービス"""
from typing import Dict, List, Any, Optional, Union

from ...application.dto.accuracy_dto import FieldEvaluationDto
from .field_score_calculator import FieldScoreCalculatorFactory
class AccuracyEvaluationService:
    """精度評価を行うドメインサービス"""
    
    def __init__(self):
        self.calculator_factory = FieldScoreCalculatorFactory()
    
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
                field_result = calculator.calculate(
                    field_name, expected_value, actual_value, weight
                )
                # Calculatorは既にDTOを返すので、そのまま使用
                results.append(field_result)
            
        return results
    
    def _evaluate_items_fields(
        self,
        expected_items: List[Dict[str, Any]],
        actual_items: List[Dict[str, Any]],
        field_weights: Dict[str, float],
        default_weight: float
    ) -> List[FieldEvaluationDto]:
        """itemsのサブフィールドを個別に評価（事前にマッチング済み前提）"""
        results = []
        
        # 実際のデータからサブフィールドを動的に取得
        all_sub_fields = set()
        for item in expected_items:
            all_sub_fields |= set(item.keys())
        for item in actual_items:
            all_sub_fields |= set(item.keys())
        
        # マッチング済みのアイテムペアを評価
        from itertools import zip_longest
        
        for item_index, (expected_item, actual_item) in enumerate(zip_longest(expected_items, actual_items, fillvalue={})):
            # 各サブフィールドを個別に評価
            for sub_field in all_sub_fields:
                field_key = f'items.{sub_field}'
                weight = field_weights.get(field_key, default_weight)
                
                expected_value = expected_item.get(sub_field)
                actual_value = actual_item.get(sub_field)
                
                # 適切なCalculatorで評価
                if sub_field in ['price', 'sub_total']:
                    calculator = self.calculator_factory.get_calculator('amount')
                elif sub_field == 'quantity':
                    calculator = self.calculator_factory.get_calculator('amount')  # 数量も金額計算ロジックを使用
                else:
                    calculator = self.calculator_factory.get_calculator('simple')
                
                result = calculator.calculate(
                    field_key, expected_value, actual_value, weight, item_index
                )
                results.append(result)
        
        return results
