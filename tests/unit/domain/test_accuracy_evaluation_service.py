"""AccuracyEvaluationServiceのテスト"""
import pytest
from src.domain.services.accuracy_evaluation_service import AccuracyEvaluationService


class TestAccuracyEvaluationService:
    def setup_method(self):
        self.service = AccuracyEvaluationService()
        self.field_weights = {
            "total_price": 3.0,
            "customer_id": 2.0,
            "items": 2.5
        }
    
    def test_evaluate_extraction_exact_match(self):
        """完全一致の評価テスト"""
        expected = {
            "total_price": "10000",
            "customer_id": "C12345",
            "invoice_number": "INV-001"
        }
        actual = expected.copy()
        
        metrics = self.service.evaluate_extraction(
            expected, actual, self.field_weights, default_weight=1.0
        )
        
        assert len(metrics) == 3
        assert all(metric.is_correct() for metric in metrics)
        
        # 重みの確認
        total_price_metric = next(m for m in metrics if m.field_name == "total_price")
        assert total_price_metric.weight == 3.0
        
        invoice_metric = next(m for m in metrics if m.field_name == "invoice_number")
        assert invoice_metric.weight == 1.0  # デフォルト重み
    
    def test_evaluate_extraction_with_errors(self):
        """エラーがある場合の評価テスト"""
        expected = {
            "total_price": "10000",
            "customer_id": "C12345"
        }
        actual = {
            "total_price": "10000",
            "customer_id": "C54321"  # 不一致
        }
        
        metrics = self.service.evaluate_extraction(
            expected, actual, self.field_weights
        )
        
        assert len(metrics) == 2
        
        total_price_metric = next(m for m in metrics if m.field_name == "total_price")
        customer_metric = next(m for m in metrics if m.field_name == "customer_id")
        
        assert total_price_metric.is_correct() is True
        assert customer_metric.is_correct() is False
    
    def test_evaluate_missing_fields(self):
        """欠損フィールドの評価テスト"""
        expected = {
            "total_price": "10000",
            "customer_id": "C12345"
        }
        actual = {
            "total_price": "10000"
            # customer_idが欠損
        }
        
        metrics = self.service.evaluate_extraction(
            expected, actual, self.field_weights
        )
        
        customer_metric = next(m for m in metrics if m.field_name == "customer_id")
        assert customer_metric.expected_value == "C12345"
        assert customer_metric.actual_value is None
        assert customer_metric.is_correct() is False
    
    def test_evaluate_extra_fields(self):
        """余分なフィールドがある場合のテスト"""
        expected = {
            "total_price": "10000"
        }
        actual = {
            "total_price": "10000",
            "extra_field": "extra_value"  # 余分なフィールド
        }
        
        metrics = self.service.evaluate_extraction(
            expected, actual, self.field_weights
        )
        
        # 余分なフィールドも評価対象になる
        assert len(metrics) == 2
        
        extra_metric = next(m for m in metrics if m.field_name == "extra_field")
        assert extra_metric.expected_value is None
        assert extra_metric.actual_value == "extra_value"
        assert extra_metric.is_correct() is False
    
    def test_normalize_value_with_list(self):
        """リスト値の正規化テスト"""
        expected = {
            "items": [{"name": "商品A", "price": "1000"}]
        }
        actual = {
            "items": [{"price": "1000", "name": "商品A"}]  # 順序が異なる
        }
        
        metrics = self.service.evaluate_extraction(
            expected, actual, self.field_weights
        )
        
        items_metric = next(m for m in metrics if m.field_name == "items")
        assert items_metric.is_correct() is True  # JSONに変換されて比較される
    
    def test_normalize_value_with_dict(self):
        """辞書値の正規化テスト"""
        expected = {
            "address": {"city": "東京", "zip": "100-0001"}
        }
        actual = {
            "address": {"zip": "100-0001", "city": "東京"}  # キーの順序が異なる
        }
        
        metrics = self.service.evaluate_extraction(
            expected, actual, {}
        )
        
        address_metric = next(m for m in metrics if m.field_name == "address")
        assert address_metric.is_correct() is True