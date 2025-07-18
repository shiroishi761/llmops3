"""設定プロバイダーの抽象インターフェース"""
from abc import ABC, abstractmethod
from typing import Dict

from src.domain.exceptions import ConfigurationError


class ConfigProvider(ABC):
    """設定プロバイダーの抽象インターフェース"""
    
    @abstractmethod
    def get_field_weights_dict(self) -> Dict[str, float]:
        """
        すべてのフィールド重みを辞書形式で取得
        
        Returns:
            フィールド名と重みの辞書
            
        Raises:
            ConfigurationError: 設定の読み込みに失敗した場合
        """
        pass
    
    @abstractmethod
    def get_default_weight(self) -> float:
        """
        デフォルトの重みを取得
        
        Returns:
            デフォルト重み
            
        Raises:
            ConfigurationError: 設定の読み込みに失敗した場合
        """
        pass