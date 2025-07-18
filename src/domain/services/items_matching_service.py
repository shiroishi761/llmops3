"""明細項目のマッチングサービス"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ItemMatch:
    """アイテムマッチング結果"""
    expected_item: Dict[str, Any]
    matched_item: Optional[Dict[str, Any]]
    match_score: float
    match_reason: Optional[str] = None


class ItemsMatchingService:
    """明細項目の高度なマッチングを行うサービス"""
    
    def __init__(self, llm_matching_service=None):
        self.llm_matching_service = llm_matching_service
    
    async def match_items(
        self,
        expected_items: List[Dict[str, Any]],
        actual_items: List[Dict[str, Any]]
    ) -> List['ItemMatch']:
        """
        期待されるアイテムと実際のアイテムをマッチング
        
        Returns:
            マッチング結果のリスト
        """
        if not expected_items:
            return []
        
        if not actual_items:
            return [ItemMatch(item, None, 0.0) for item in expected_items]
        
        return await self._match_with_llm(expected_items, actual_items)
    
    
    async def _match_with_llm(
        self,
        expected_items: List[Dict[str, Any]],
        actual_items: List[Dict[str, Any]]
    ) -> List[ItemMatch]:
        """LLMを使用したマッチング"""

        if not self.llm_matching_service:
            raise ValueError("LLMマッチングサービスが設定されていません")
        
        llm_matches = await self.llm_matching_service.match_items(expected_items, actual_items)
        
        matches = []
        for exp_idx, act_idx, confidence in llm_matches:
            expected_item = expected_items[exp_idx]
            
            if act_idx >= 0 and act_idx < len(actual_items):
                actual_item = actual_items[act_idx]
                
                matches.append(ItemMatch(
                    expected_item=expected_item,
                    matched_item=actual_item,
                    match_score=confidence,
                    match_reason=f"LLM信頼度: {confidence:.2f}"
                ))
            else:
                matches.append(ItemMatch(
                    expected_item=expected_item,
                    matched_item=None,
                    match_score=0.0,
                    match_reason="対応する項目なし"
                ))
        
        return matches
    
    
    
