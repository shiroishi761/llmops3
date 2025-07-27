"""明細項目マッチングサービスのインターフェース"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, List

class ItemsMatchingInterface(ABC):
    """明細項目マッチングサービスのインターフェース"""
    
    @abstractmethod
    def process_matched_items(
        self,
        expected_data: Dict[str, Any],
        extracted_data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        itemsフィールドのマッチング処理を実行し、再配置されたデータを返す
        
        Args:
            expected_data: 期待データ（元データ）
            extracted_data: 抽出データ（元データ）
            
        Returns:
            Tuple[Dict[str, Any], Dict[str, Any]]: 
                - 再配置された期待データ
                - 再配置された抽出データ
        """
        pass
    
    @abstractmethod
    def match_and_reorder_items(
        self,
        expected_items: List[Dict[str, Any]],
        extracted_items: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        itemsリストのマッチングと再配置を実行
        
        Args:
            expected_items: 期待するitemsリスト
            extracted_items: 抽出されたitemsリスト
            
        Returns:
            Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]: 
                - マッチング済みの期待items
                - マッチング済みの抽出items
        """
        pass
