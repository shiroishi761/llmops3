"""ItemsMatchingServiceのユニットテスト"""

import pytest
from src.domain.services.items_matching_service import ItemsMatchingService


class MockLLMMatchingService:
    """LLMマッチングサービスのモック"""
    
    def match_items(self, expected_items, actual_items):
        """完全一致のケースを模擬"""
        matches = []
        for i, expected in enumerate(expected_items):
            # 簡単なname比較による模擬マッチング
            best_match_idx = -1
            best_confidence = 0.0
            
            for j, actual in enumerate(actual_items):
                if expected.get("name") == actual.get("name"):
                    best_match_idx = j
                    best_confidence = 1.0
                    break
            
            matches.append((i, best_match_idx, best_confidence))
        
        return matches


class TestItemsMatchingService:
    """ItemsMatchingServiceのテスト"""
    
    @pytest.fixture
    def service(self):
        return ItemsMatchingService(llm_matching_service=MockLLMMatchingService())
    
    def test_llm_service_required(self):
        """LLMサービスが必須であることのテスト"""
        service = ItemsMatchingService()  # LLMサービスなし
        
        with pytest.raises(ValueError, match="LLMマッチングサービスが設定されていません"):
            service.match_items([{"name": "商品A"}], [{"name": "商品A"}])
    
    def test_exact_match(self, service):
        """完全一致のテスト"""
        expected = [
            {"name": "商品A", "quantity": 1, "price": 1000, "sub_total": 1000}
        ]
        actual = [
            {"name": "商品A", "quantity": 1, "price": 1000, "sub_total": 1000}
        ]
        
        matches = service.match_items(expected, actual)
        
        assert len(matches) == 1
        assert matches[0].match_score == 1.0
        assert matches[0].expected_item == expected[0]
        assert matches[0].matched_item == actual[0]
        assert "LLM信頼度: 1.00" in matches[0].match_reason
    
    def test_no_match(self, service):
        """マッチしない場合のテスト"""
        expected = [{"name": "商品A"}]
        actual = [{"name": "商品B"}]
        
        matches = service.match_items(expected, actual)
        
        assert len(matches) == 1
        assert matches[0].match_score == 0.0
        assert matches[0].expected_item == expected[0]
        assert matches[0].matched_item is None
        assert matches[0].match_reason == "対応する項目なし"
    
    def test_empty_expected_items(self, service):
        """期待値が空の場合のテスト"""
        expected = []
        actual = [{"name": "商品A"}]
        
        matches = service.match_items(expected, actual)
        
        assert len(matches) == 0
    
    def test_empty_actual_items(self, service):
        """実際の値が空の場合のテスト"""
        expected = [{"name": "商品A"}]
        actual = []
        
        matches = service.match_items(expected, actual)
        
        assert len(matches) == 1
        assert matches[0].match_score == 0.0
        assert matches[0].matched_item is None