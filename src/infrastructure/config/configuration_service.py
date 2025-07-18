"""設定管理サービス"""
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import yaml
from dotenv import load_dotenv

from src.domain.services.config_provider import ConfigProvider
from src.domain.exceptions import ConfigurationError


class ConfigurationService(ConfigProvider):
    """設定を管理するサービス"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初期化
        
        Args:
            config_path: 設定ファイルのパス（指定しない場合はデフォルト）
        """
        # .envファイルを読み込み
        load_dotenv()
        
        # 設定ファイルのパス
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = Path("config/config.yml")
            
        # 設定を読み込み
        self.config = self._load_config()
        
        # フィールド重みを初期化時に解析
        self._field_weights, self._default_weight = self._parse_field_weights()
        
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        config = {}
        
        # YAMLファイルを読み込み
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
                
        return config
    
    def _parse_field_weights(self) -> Tuple[Dict[str, float], float]:
        """
        フィールド重みを解析し、統一形式で返す
        
        Returns:
            (全フィールド重み辞書, デフォルト重み)
        """
        field_weights_config = self.config.get("field_weights", {})
        
        # デフォルト重みを取得
        default_weight = float(field_weights_config.get("default_weight", 1.0))
        
        # 全フィールド重み辞書
        all_weights = {}
        
        for field_name, weight in field_weights_config.items():
            if field_name == "default_weight":
                continue
            elif field_name == "items" and isinstance(weight, dict):
                # itemsが辞書の場合、各サブフィールドを展開
                for sub_field, sub_weight in weight.items():
                    full_field_name = f"items.{sub_field}"
                    all_weights[full_field_name] = float(sub_weight)
            else:
                # 通常のフィールドまたはitems.プレフィックス付きフィールド
                all_weights[field_name] = float(weight)
        
        return all_weights, default_weight
    
    
    def get_field_weights_dict(self) -> Dict[str, float]:
        """
        すべてのフィールド重みを辞書形式で取得
        
        Returns:
            フィールド名と重みの辞書
        """
        return self._field_weights.copy()  # 防御的コピー
    
    def get_default_weight(self) -> float:
        """デフォルトの重みを取得"""
        return self._default_weight
    
    
    
    @property
    def gemini_api_key(self) -> str:
        """Gemini APIキーを取得"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        return api_key
    
    @property
    def langfuse_public_key(self) -> str:
        """Langfuse公開キーを取得"""
        key = os.getenv("LANGFUSE_PUBLIC_KEY")
        if not key:
            raise ValueError("LANGFUSE_PUBLIC_KEY environment variable is not set")
        return key
    
    @property
    def langfuse_secret_key(self) -> str:
        """Langfuseシークレットキーを取得"""
        key = os.getenv("LANGFUSE_SECRET_KEY")
        if not key:
            raise ValueError("LANGFUSE_SECRET_KEY environment variable is not set")
        return key
    
    @property
    def langfuse_host(self) -> str:
        """LangfuseホストURLを取得"""
        return os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")