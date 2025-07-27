"""設定サービスのインターフェース"""
from typing import Dict, Any, Optional, Protocol, List
from ...domain.models.prompt_config import PromptConfig

class ConfigurationInterface(Protocol):
    """設定管理のインターフェース"""
    
    def get_field_weights_dict(self) -> Dict[str, float]:
        """
        すべてのフィールド重みを辞書形式で取得
        
        Returns:
            フィールド名と重みの辞書
        """
        ...
    
    def get_default_weight(self) -> float:
        """
        デフォルトの重みを取得
        
        Returns:
            デフォルト重み
        """
        ...
    
    def load_experiment_config(self, config_path: str, experiment_name: Optional[str] = None) -> Dict[str, Any]:
        """
        実験設定を読み込み
        
        Args:
            config_path: 実験設定ファイルのパス
            experiment_name: 実験名（指定した場合はその実験のみ取得）
            
        Returns:
            実験設定の辞書
            
        Raises:
            FileNotFoundError: 設定ファイルが見つからない場合
            ValueError: 指定された実験名が見つからない場合
        """
        ...
    
    def get_prompt_config(self, experiment_config: Dict[str, Any]) -> List[PromptConfig]:
        """
        実験設定からプロンプト設定を取得
        
        Args:
            experiment_config: 実験設定の辞書
            
        Returns:
            PromptConfigのリスト
        """
        ...
    
    @property
    def gemini_api_key(self) -> str:
        """
        Gemini APIキーを取得
        
        Returns:
            APIキー
        """
        ...
