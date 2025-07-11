"""ItemsMatchingServiceのユニットテスト"""

import pytest
from src.domain.services.items_matching_service import ItemsMatchingService


class TestItemsMatchingService:
    """ItemsMatchingServiceのテスト"""
    
    @pytest.fixture
    def service(self):
        return ItemsMatchingService()
    
    def test_exact_match(self, service):
        """完全一致のテスト"""
        expected = [
            {"name": "商品A", "quantity": 1, "price": 1000, "sub_total": 1000}
        ]
        actual = [
            {"name": "商品A", "quantity": 1, "price": 1000, "sub_total": 1000}
        ]
        
        accuracy, matches = service.calculate_items_accuracy(expected, actual)
        
        assert accuracy == 1.0
        assert len(matches) == 1
        assert matches[0].match_score == 1.0
    
    def test_partial_match(self, service):
        """部分一致のテスト"""
        expected = [
            {"name": "商品A", "quantity": 1, "price": 1000},
            {"name": "商品B", "quantity": 2, "price": 2000}
        ]
        actual = [
            {"name": "商品A", "quantity": 1, "price": 1000},  # 完全一致
            {"name": "商品C", "quantity": 3, "price": 3000}   # 不一致
        ]
        
        accuracy, matches = service.calculate_items_accuracy(expected, actual)
        
        assert 0.4 < accuracy < 0.6  # 約50%の精度
        assert len(matches) == 2
        assert matches[0].match_score == 1.0  # 商品Aは完全一致
        assert matches[1].match_score < 0.5   # 商品Bは不一致
    
    def test_name_partial_match(self, service):
        """品目名の部分一致テスト"""
        expected = [{"name": "モータ"}]
        actual = [{"name": "ホンプモータユニット"}]
        
        accuracy, matches = service.calculate_items_accuracy(expected, actual)
        
        # "モータ"が"ホンプモータユニット"に含まれるので部分一致
        assert matches[0].match_score > 0
        assert matches[0].field_matches.get("name", False) is True
    
    def test_empty_values_handling(self, service):
        """空値の処理テスト"""
        expected = [{"name": "商品A", "note": ""}]
        actual = [{"name": "商品A", "note": None}]
        
        accuracy, matches = service.calculate_items_accuracy(expected, actual)
        
        # 空文字列とNoneは同じとして扱われる
        assert matches[0].match_score > 0.8
    
    def test_different_order(self, service):
        """異なる順序のアイテムマッチング"""
        expected = [
            {"name": "商品A", "quantity": 1},
            {"name": "商品B", "quantity": 2},
            {"name": "商品C", "quantity": 3}
        ]
        actual = [
            {"name": "商品C", "quantity": 3},  # 順序が異なる
            {"name": "商品A", "quantity": 1},
            {"name": "商品B", "quantity": 2}
        ]
        
        accuracy, matches = service.calculate_items_accuracy(expected, actual)
        
        # 順序が異なっても全て一致すれば100%
        assert accuracy == 1.0
    
    def test_extra_items_in_actual(self, service):
        """実際の値に余分なアイテムがある場合"""
        expected = [
            {"name": "商品A", "quantity": 1}
        ]
        actual = [
            {"name": "商品A", "quantity": 1},
            {"name": "商品B", "quantity": 2},
            {"name": "商品C", "quantity": 3}
        ]
        
        accuracy, matches = service.calculate_items_accuracy(expected, actual)
        
        # 期待値の商品Aは見つかるので、その分は100%
        assert accuracy == 1.0
        assert len(matches) == 1
    
    def test_missing_items_in_actual(self, service):
        """実際の値に不足がある場合"""
        expected = [
            {"name": "商品A", "quantity": 1},
            {"name": "商品B", "quantity": 2},
            {"name": "商品C", "quantity": 3}
        ]
        actual = [
            {"name": "商品A", "quantity": 1}
        ]
        
        accuracy, matches = service.calculate_items_accuracy(expected, actual)
        
        # 3つ中1つしか見つからないので精度は低い
        assert accuracy < 0.5
        assert matches[0].match_score == 1.0  # 商品Aは一致
        assert matches[1].match_score == 0.0  # 商品Bは見つからない
        assert matches[2].match_score == 0.0  # 商品Cは見つからない
    
    def test_create_items_metric(self, service):
        """メトリクス生成のテスト"""
        expected = [{"name": "商品A", "price": 1000}]
        actual = [{"name": "商品A", "price": 1000}]
        
        metric_dict = service.create_items_metric(expected, actual, base_weight=5.0)
        
        assert metric_dict["field_name"] == "items"
        assert metric_dict["weight"] == 5.0
        assert metric_dict["is_correct"] is True  # 80%以上
        assert metric_dict["items_accuracy"] == 1.0
        assert len(metric_dict["items_matches"]) == 1