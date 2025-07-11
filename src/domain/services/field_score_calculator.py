"""フィールドスコア計算のStrategyパターン"""
from abc import ABC, abstractmethod
from typing import Any, Optional, List, Dict
import re
from datetime import datetime
from ..models.field_result import FieldEvaluationResult


class FieldScoreCalculator(ABC):
    """フィールドスコア計算の基底クラス"""
    
    @abstractmethod
    def calculate_score(self, field_name: str, expected: Any, actual: Any, weight: float, item_index: Optional[int] = None) -> FieldEvaluationResult:
        """
        フィールドスコアを計算
        
        Args:
            field_name: フィールド名
            expected: 期待値
            actual: 実際の値
            weight: 重み
            
        Returns:
            FieldEvaluationResult: 計算結果
        """
        pass
    
    def calculate(self, field_name: str, expected: Any, actual: Any, weight: float) -> List[FieldEvaluationResult]:
        """
        フィールドを評価してリストで返す（デフォルト実装）
        
        Args:
            field_name: フィールド名
            expected: 期待値
            actual: 実際の値
            weight: 重み
            
        Returns:
            List[FieldEvaluationResult]: 計算結果のリスト
        """
        result = self.calculate_score(field_name, expected, actual, weight)
        return [result]


class SimpleFieldCalculator(FieldScoreCalculator):
    """単純な文字列比較による計算"""
    
    def calculate_score(self, field_name: str, expected: Any, actual: Any, weight: float, item_index: Optional[int] = None) -> FieldEvaluationResult:
        """文字列として比較し、完全一致で正解"""
        is_correct = self._is_match(expected, actual)
        
        if is_correct:
            return FieldEvaluationResult.create_correct(field_name, expected, actual, weight, item_index)
        else:
            return FieldEvaluationResult.create_incorrect(field_name, expected, actual, weight, item_index)
    
    def calculate(self, field_name: str, expected: Any, actual: Any, weight: float) -> List[FieldEvaluationResult]:
        """単一フィールドを評価してリストで返す"""
        result = self.calculate_score(field_name, expected, actual, weight)
        return [result]
    
    def _is_match(self, expected: Any, actual: Any) -> bool:
        """値が一致するかを判定"""
        if expected is None and actual is None:
            return True
        if expected is None or actual is None:
            return False
        
        # 文字列として比較（前後空白除去、大文字小文字区別なし）
        expected_str = str(expected).strip().lower()
        actual_str = str(actual).strip().lower()
        
        return expected_str == actual_str


class AmountFieldCalculator(FieldScoreCalculator):
    """金額フィールド専用の計算"""
    
    def calculate_score(self, field_name: str, expected: Any, actual: Any, weight: float, item_index: Optional[int] = None) -> FieldEvaluationResult:
        """金額として比較"""
        is_correct = self._is_amount_match(expected, actual)
        
        if is_correct:
            return FieldEvaluationResult.create_correct(field_name, expected, actual, weight, item_index)
        else:
            return FieldEvaluationResult.create_incorrect(field_name, expected, actual, weight, item_index)
    
    def calculate(self, field_name: str, expected: Any, actual: Any, weight: float) -> List[FieldEvaluationResult]:
        """単一フィールドを評価してリストで返す"""
        result = self.calculate_score(field_name, expected, actual, weight)
        return [result]
    
    def _is_amount_match(self, expected: Any, actual: Any) -> bool:
        """金額として比較"""
        if expected is None and actual is None:
            return True
        if expected is None or actual is None:
            return False
        
        try:
            expected_amount = self._parse_amount(expected)
            actual_amount = self._parse_amount(actual)
            
            # 小数点以下の誤差を考慮
            return abs(expected_amount - actual_amount) < 0.01
        except (ValueError, TypeError):
            # 数値に変換できない場合は文字列比較
            return str(expected).strip() == str(actual).strip()
    
    def _parse_amount(self, value: Any) -> float:
        """金額を数値に変換"""
        if isinstance(value, (int, float)):
            return float(value)
        
        # 文字列の場合、カンマと通貨記号を除去
        value_str = str(value).strip()
        value_str = re.sub(r'[,¥$€£]', '', value_str)
        
        return float(value_str)


class DateFieldCalculator(FieldScoreCalculator):
    """日付フィールド専用の計算"""
    
    DATE_FORMATS = [
        '%Y-%m-%d',
        '%Y/%m/%d',
        '%Y年%m月%d日',
        '%m/%d/%Y',
        '%d/%m/%Y'
    ]
    
    def calculate_score(self, field_name: str, expected: Any, actual: Any, weight: float, item_index: Optional[int] = None) -> FieldEvaluationResult:
        """日付として比較"""
        is_correct = self._is_date_match(expected, actual)
        
        if is_correct:
            return FieldEvaluationResult.create_correct(field_name, expected, actual, weight, item_index)
        else:
            return FieldEvaluationResult.create_incorrect(field_name, expected, actual, weight, item_index)
    
    def calculate(self, field_name: str, expected: Any, actual: Any, weight: float) -> List[FieldEvaluationResult]:
        """単一フィールドを評価してリストで返す"""
        result = self.calculate_score(field_name, expected, actual, weight)
        return [result]
    
    def _is_date_match(self, expected: Any, actual: Any) -> bool:
        """日付として比較"""
        if expected is None and actual is None:
            return True
        if expected is None or actual is None:
            return False
        
        try:
            expected_date = self._parse_date(expected)
            actual_date = self._parse_date(actual)
            
            return expected_date == actual_date
        except (ValueError, TypeError):
            # 日付に変換できない場合は文字列比較
            return str(expected).strip() == str(actual).strip()
    
    def _parse_date(self, value: Any) -> datetime:
        """日付を標準形式に変換"""
        if isinstance(value, datetime):
            return value.replace(hour=0, minute=0, second=0, microsecond=0)
        
        value_str = str(value).strip()
        
        for fmt in self.DATE_FORMATS:
            try:
                return datetime.strptime(value_str, fmt)
            except ValueError:
                continue
        
        raise ValueError(f"日付形式を解析できません: {value_str}")


class ItemsFieldCalculator(FieldScoreCalculator):
    """明細項目フィールド専用の計算"""
    
    def __init__(self, items_matching_service=None):
        self.items_matching_service = items_matching_service
    
    def calculate_score(self, field_name: str, expected: Any, actual: Any, weight: float, item_index: Optional[int] = None) -> FieldEvaluationResult:
        """明細項目として比較"""
        if not self.items_matching_service:
            # サービスが利用できない場合は単純比較
            is_correct = expected == actual
            details = None
        else:
            # 複雑なマッチングを実行
            expected_items = expected if isinstance(expected, list) else []
            actual_items = actual if isinstance(actual, list) else []
            
            accuracy, matches = self.items_matching_service.calculate_items_accuracy(
                expected_items, actual_items
            )
            
            # 80%以上で正解とする
            is_correct = accuracy >= 0.8
            details = {
                "items_accuracy": accuracy,
                "items_matches": [
                    {
                        "expected": match.expected_item,
                        "matched": match.matched_item,
                        "score": match.match_score,
                        "field_matches": match.field_matches
                    }
                    for match in matches
                ]
            }
        
        if is_correct:
            return FieldEvaluationResult.create_correct(field_name, expected, actual, weight, item_index, details)
        else:
            return FieldEvaluationResult.create_incorrect(field_name, expected, actual, weight, item_index, details)
    
    def calculate(self, field_name: str, expected_items: List[Dict], actual_items: List[Dict], 
                  field_weights: Dict[str, float], default_weight: float) -> List[FieldEvaluationResult]:
        """明細項目を評価してフィールド結果のリストを返す"""
        results = []
        
        # シンプルなアプローチ: 各アイテムを順序で比較
        max_items = max(len(expected_items), len(actual_items))
        
        for item_index in range(max_items):
            expected_item = expected_items[item_index] if item_index < len(expected_items) else {}
            actual_item = actual_items[item_index] if item_index < len(actual_items) else {}
            
            # 各サブフィールドを評価
            sub_fields = ['name', 'quantity', 'price', 'sub_total', 'unit', 'spec', 'note', 'account_item']
            
            for sub_field in sub_fields:
                field_key = f'items.{sub_field}'
                weight = field_weights.get(field_key, default_weight)
                
                expected_value = expected_item.get(sub_field)
                actual_value = actual_item.get(sub_field)
                
                # 適切なCalculatorで評価
                if sub_field in ['price', 'sub_total']:
                    calculator = AmountFieldCalculator()
                else:
                    calculator = SimpleFieldCalculator()
                
                result = calculator.calculate_score(
                    field_key, expected_value, actual_value, weight, item_index
                )
                results.append(result)
        
        return results


class FieldScoreCalculatorFactory:
    """フィールドに応じて適切なCalculatorを選択するFactory"""
    
    def __init__(self, items_matching_service=None):
        self.items_matching_service = items_matching_service
        self._calculators = {
            'simple': SimpleFieldCalculator(),
            'amount': AmountFieldCalculator(),
            'date': DateFieldCalculator(),
            'items': ItemsFieldCalculator(items_matching_service)
        }
        
        # フィールド名とCalculatorのマッピング
        self._field_mappings = {
            'total_price': 'amount',
            'tax_price': 'amount',
            'sub_total': 'amount',
            'doc_date': 'date',
            'expiration_date': 'date',
            'items': 'items'
        }
    
    def get_calculator(self, field_name: str) -> FieldScoreCalculator:
        """フィールド名に応じて適切なCalculatorを返す"""
        calculator_type = self._field_mappings.get(field_name, 'simple')
        return self._calculators[calculator_type]
    
    def add_field_mapping(self, field_name: str, calculator_type: str):
        """フィールドマッピングを追加"""
        if calculator_type not in self._calculators:
            raise ValueError(f"Unknown calculator type: {calculator_type}")
        self._field_mappings[field_name] = calculator_type