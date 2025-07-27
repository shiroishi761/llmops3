"""フィールドスコア計算のStrategyパターン"""
from abc import ABC, abstractmethod
from typing import Any, Optional
import re
from datetime import datetime
from ...application.dto.accuracy_dto import FieldEvaluationDto

class FieldScoreCalculator(ABC):
    """フィールドスコア計算の基底クラス"""
    
    @abstractmethod
    def calculate(self, field_name: str, expected: Any, actual: Any, weight: float, item_index: Optional[int] = None) -> FieldEvaluationDto:
        """
        フィールドスコアを計算
        
        Args:
            field_name: フィールド名
            expected: 期待値
            actual: 実際の値
            weight: 重み
            item_index: アイテムインデックス（オプション）
            
        Returns:
            FieldEvaluationDto: 計算結果DTO
        """
        pass

class SimpleFieldCalculator(FieldScoreCalculator):
    """単純な文字列比較による計算"""
    
    def calculate(self, field_name: str, expected: Any, actual: Any, weight: float, item_index: Optional[int] = None) -> FieldEvaluationDto:
        """文字列として比較し、完全一致で正解"""
        is_correct = self._is_match(expected, actual)
        score = 1.0 if is_correct else 0.0  # スコアは0〜1の範囲
        
        return FieldEvaluationDto(
            field_name=field_name,
            expected_value=expected,
            actual_value=actual,
            is_correct=is_correct,
            score=score,
            weight=weight,
            item_index=item_index
        )
    
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
    
    def calculate(self, field_name: str, expected: Any, actual: Any, weight: float, item_index: Optional[int] = None) -> FieldEvaluationDto:
        """金額として比較"""
        is_correct = self._is_amount_match(expected, actual)
        score = 1.0 if is_correct else 0.0  # スコアは0〜1の範囲
        
        return FieldEvaluationDto(
            field_name=field_name,
            expected_value=expected,
            actual_value=actual,
            is_correct=is_correct,
            score=score,
            weight=weight,
            item_index=item_index
        )
    
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
    
    def calculate(self, field_name: str, expected: Any, actual: Any, weight: float, item_index: Optional[int] = None) -> FieldEvaluationDto:
        """日付として比較"""
        is_correct = self._is_date_match(expected, actual)
        score = 1.0 if is_correct else 0.0  # スコアは0〜1の範囲
        
        return FieldEvaluationDto(
            field_name=field_name,
            expected_value=expected,
            actual_value=actual,
            is_correct=is_correct,
            score=score,
            weight=weight,
            item_index=item_index
        )
    
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

class FieldScoreCalculatorFactory:
    """フィールドに応じて適切なCalculatorを選択するFactory"""
    
    def __init__(self, items_matching_service=None):
        self.items_matching_service = items_matching_service
        self._calculators = {
            'simple': SimpleFieldCalculator(),
            'amount': AmountFieldCalculator(),
            'date': DateFieldCalculator()
        }
        
        # フィールド名とCalculatorのマッピング
        self._field_mappings = {
            'total_price': 'amount',
            'tax_price': 'amount',
            'sub_total': 'amount',
            'doc_date': 'date',
            'expiration_date': 'date'
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
