"""プロンプトサービスのインターフェース"""
from typing import List, Protocol


class PromptInterface(Protocol):
    """プロンプト管理のインターフェース"""
    
    def get_prompt(self, prompt_name: str) -> str:
        """
        プロンプトを取得
        
        Args:
            prompt_name: プロンプト名
            
        Returns:
            プロンプトテンプレート
            
        Raises:
            FileNotFoundError: プロンプトファイルが見つからない場合
        """
        ...
    
    def list_available_prompts(self) -> List[str]:
        """
        利用可能なプロンプト名の一覧を取得
        
        Returns:
            プロンプト名のリスト（拡張子なし）
        """
        ...
    
    def prompt_exists(self, prompt_name: str) -> bool:
        """
        プロンプトファイルが存在するかチェック
        
        Args:
            prompt_name: プロンプト名
            
        Returns:
            存在するかどうか
        """
        ...