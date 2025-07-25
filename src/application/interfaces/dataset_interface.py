"""データセットサービスのインターフェース"""
from typing import List, Dict, Any, Protocol


class DatasetInterface(Protocol):
    """データセット管理のインターフェース"""
    
    def get_dataset(self, dataset_name: str) -> List[Dict[str, Any]]:
        """
        データセットを取得
        
        Args:
            dataset_name: データセット名
            
        Returns:
            データセットドキュメントのリスト
            
        Raises:
            FileNotFoundError: データセットファイルが見つからない場合
            RuntimeError: ファイル読み込みに失敗した場合
        """
        ...
    
    def list_available_datasets(self) -> List[str]:
        """
        利用可能なデータセット名の一覧を取得
        
        Returns:
            データセット名のリスト（拡張子なし）
        """
        ...
    
    def dataset_exists(self, dataset_name: str) -> bool:
        """
        データセットファイルが存在するかチェック
        
        Args:
            dataset_name: データセット名
            
        Returns:
            存在するかどうか
        """
        ...