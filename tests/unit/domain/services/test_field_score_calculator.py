"""FieldScoreCalculatorのテスト"""
import pytest
from datetime import datetime
from src.domain.services.field_score_calculator import (
    SimpleFieldCalculator,
    AmountFieldCalculator,
    DateFieldCalculator,
    ItemsFieldCalculator,
    FieldScoreCalculatorFactory
)
from src.domain.models.field_result import FieldResult


class TestSimpleFieldCalculator:
    """SimpleFieldCalculatorのテストクラス"""
    
    def setup_method(self):
        self.calculator = SimpleFieldCalculator()
    
    def test_exact_match(self):
        """完全一致の場合"""
        result = self.calculator.calculate_score("test_field", "value", "value", 2.0)
        
        assert result.is_correct is True
        assert result.score == 2.0
    
    def test_mismatch(self):
        """不一致の場合"""
        result = self.calculator.calculate_score("test_field", "expected", "actual", 2.0)
        
        assert result.is_correct is False
        assert result.score == 0.0
    
    def test_whitespace_handling(self):
        """前後の空白を無視"""
        result = self.calculator.calculate_score("test_field", "  value  ", "value", 2.0)
        
        assert result.is_correct is True
        assert result.score == 2.0
    
    def test_case_insensitive(self):
        """大文字小文字を区別しない"""
        result = self.calculator.calculate_score("test_field", "VALUE", "value", 2.0)
        
        assert result.is_correct is True
        assert result.score == 2.0
    
    def test_null_values(self):
        """null値の処理"""
        # 両方null
        result1 = self.calculator.calculate_score("test_field", None, None, 2.0)
        assert result1.is_correct is True
        
        # 片方null
        result2 = self.calculator.calculate_score("test_field", None, "value", 2.0)
        assert result2.is_correct is False
        
        result3 = self.calculator.calculate_score("test_field", "value", None, 2.0)
        assert result3.is_correct is False


class TestAmountFieldCalculator:
    """AmountFieldCalculatorのテストクラス"""
    
    def setup_method(self):
        self.calculator = AmountFieldCalculator()
    
    def test_exact_number_match(self):
        """正確な数値の一致"""
        result = self.calculator.calculate_score("total_price", 1000, 1000, 3.0)
        
        assert result.is_correct is True
        assert result.score == 3.0
    
    def test_comma_removal(self):
        """カンマ除去"""
        result = self.calculator.calculate_score("total_price", "1,000", "1000", 3.0)
        
        assert result.is_correct is True
        assert result.score == 3.0
    
    def test_currency_symbol_removal(self):
        """通貨記号の除去"""
        result = self.calculator.calculate_score("total_price", "¥1000", "1000", 3.0)
        
        assert result.is_correct is True
        assert result.score == 3.0
    
    def test_decimal_handling(self):
        """小数点の処理"""
        result = self.calculator.calculate_score("total_price", "1000.00", "1000", 3.0)
        
        assert result.is_correct is True
        assert result.score == 3.0
    
    def test_amount_mismatch(self):
        """金額の不一致"""
        result = self.calculator.calculate_score("total_price", 1000, 2000, 3.0)
        
        assert result.is_correct is False
        assert result.score == 0.0
    
    def test_invalid_amount(self):
        """不正な金額（数値に変換できない）"""
        result = self.calculator.calculate_score("total_price", "abc", "abc", 3.0)
        
        assert result.is_correct is True  # 文字列比較にフォールバック
        assert result.score == 3.0


class TestDateFieldCalculator:
    """DateFieldCalculatorのテストクラス"""
    
    def setup_method(self):
        self.calculator = DateFieldCalculator()
    
    def test_same_format_match(self):
        """同じフォーマットでの一致"""
        result = self.calculator.calculate_score("doc_date", "2024-01-01", "2024-01-01", 1.5)
        
        assert result.is_correct is True
        assert result.score == 1.5
    
    def test_different_format_match(self):
        """異なるフォーマットでの一致"""
        result = self.calculator.calculate_score("doc_date", "2024-01-01", "2024/01/01", 1.5)
        
        assert result.is_correct is True
        assert result.score == 1.5
    
    def test_japanese_format(self):
        """日本語フォーマットの処理"""
        result = self.calculator.calculate_score("doc_date", "2024年1月1日", "2024-01-01", 1.5)
        
        assert result.is_correct is True
        assert result.score == 1.5
    
    def test_date_mismatch(self):
        """日付の不一致"""
        result = self.calculator.calculate_score("doc_date", "2024-01-01", "2024-01-02", 1.5)
        
        assert result.is_correct is False
        assert result.score == 0.0
    
    def test_invalid_date(self):
        """不正な日付"""
        result = self.calculator.calculate_score("doc_date", "invalid", "invalid", 1.5)
        
        assert result.is_correct is True  # 文字列比較にフォールバック
        assert result.score == 1.5


class TestItemsFieldCalculator:
    """ItemsFieldCalculatorのテストクラス"""
    
    def setup_method(self):
        self.calculator = ItemsFieldCalculator()
    
    def test_exact_match_without_service(self):
        """サービスなしでの完全一致"""
        items = [{"name": "item1", "price": 100}]
        result = self.calculator.calculate_score("items", items, items, 2.0)
        
        assert result.is_correct is True
        assert result.score == 2.0
    
    def test_mismatch_without_service(self):
        """サービスなしでの不一致"""
        items1 = [{"name": "item1", "price": 100}]
        items2 = [{"name": "item2", "price": 200}]
        result = self.calculator.calculate_score("items", items1, items2, 2.0)
        
        assert result.is_correct is False
        assert result.score == 0.0


class TestFieldScoreCalculatorFactory:
    """FieldScoreCalculatorFactoryのテストクラス"""
    
    def setup_method(self):
        self.factory = FieldScoreCalculatorFactory()
    
    def test_get_simple_calculator(self):
        """単純フィールドのCalculator取得"""
        calculator = self.factory.get_calculator("unknown_field")
        
        assert isinstance(calculator, SimpleFieldCalculator)
    
    def test_get_amount_calculator(self):
        """金額フィールドのCalculator取得"""
        calculator = self.factory.get_calculator("total_price")
        
        assert isinstance(calculator, AmountFieldCalculator)
    
    def test_get_date_calculator(self):
        """日付フィールドのCalculator取得"""
        calculator = self.factory.get_calculator("doc_date")
        
        assert isinstance(calculator, DateFieldCalculator)
    
    def test_get_items_calculator(self):
        """明細フィールドのCalculator取得"""
        calculator = self.factory.get_calculator("items")
        
        assert isinstance(calculator, ItemsFieldCalculator)
    
    def test_add_field_mapping(self):
        """フィールドマッピングの追加"""
        self.factory.add_field_mapping("custom_amount", "amount")
        calculator = self.factory.get_calculator("custom_amount")
        
        assert isinstance(calculator, AmountFieldCalculator)
    
    def test_add_invalid_mapping(self):
        """無効なマッピングの追加"""
        with pytest.raises(ValueError, match="Unknown calculator type"):
            self.factory.add_field_mapping("custom_field", "invalid_type")