"""精度評価サービス"""
from typing import Dict, List, Any

from src.domain.models.field_result import FieldEvaluationResult
from src.domain.services.field_score_calculator import FieldScoreCalculatorFactory
from src.application.dto.field_evaluation_dto import FieldEvaluationResultDto
from src.domain.services.accuracy_evaluator import AccuracyEvaluator


class AccuracyEvaluationService(AccuracyEvaluator):
    """精度評価を行うドメインサービス"""
    
    def __init__(self):
        self.calculator_factory = FieldScoreCalculatorFactory()
    
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
        """
        domain_results = []
        
        # すべての期待されるフィールドを評価
        all_fields = set(expected.keys()) | set(actual.keys())
        
        for field_name in all_fields:
            # itemsフィールドは特別に処理
            if field_name == 'items':
                expected_items = expected.get(field_name, [])
                actual_items = actual.get(field_name, [])
                
                # itemsフィールドのサブフィールドを個別に評価
                items_results = self._evaluate_items_fields_unified(
                    expected_items, actual_items, field_weights, default_weight
                )
                domain_results.extend(items_results)
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
                domain_results.extend(field_results)
            
        # ドメインオブジェクトをDTOに変換
        return [self._to_dto(result) for result in domain_results]
    
    def _evaluate_items_fields_unified(
        self,
        expected_items: List[Dict[str, Any]],
        actual_items: List[Dict[str, Any]],
        field_weights: Dict[str, float],
        default_weight: float
    ) -> List[FieldEvaluationResult]:
        """itemsのサブフィールドを統一的に評価"""
        results = []
        
        # 各アイテムを順序で比較
        max_items = max(len(expected_items), len(actual_items))
        
        for item_index in range(max_items):
            expected_item = expected_items[item_index] if item_index < len(expected_items) else {}
            actual_item = actual_items[item_index] if item_index < len(actual_items) else {}
            
            # 各サブフィールドを評価（expected_itemとactual_itemのキーを動的に収集）
            all_sub_fields = set(expected_item.keys()) | set(actual_item.keys())
            
            # field_weightsからitems.で始まるフィールドも追加
            items_fields_from_weights = {
                field_name.replace('items.', '') 
                for field_name in field_weights.keys() 
                if field_name.startswith('items.')
            }
            all_sub_fields.update(items_fields_from_weights)
            
            for sub_field in all_sub_fields:
                field_key = f'items.{sub_field}'
                weight = field_weights.get(field_key, default_weight)
                
                expected_value = expected_item.get(sub_field)
                actual_value = actual_item.get(sub_field)
                
                # 適切なCalculatorを取得して評価
                calculator = self.calculator_factory.get_calculator(field_key)
                result = calculator.calculate_score(
                    field_key, expected_value, actual_value, weight, item_index
                )
                results.append(result)
        
        return results
    
    def _to_dto(self, domain_result: FieldEvaluationResult) -> FieldEvaluationResultDto:
        """ドメインオブジェクトをDTOに変換"""
        return FieldEvaluationResultDto(
            field_name=domain_result.field_name,
            expected_value=domain_result.expected_value,
            actual_value=domain_result.actual_value,
            is_correct=domain_result.is_correct,
            score=domain_result.score,
            weight=domain_result.weight,
            display_name=domain_result.get_display_name(),
            item_index=domain_result.item_index,
            details=domain_result.details
        )
    
