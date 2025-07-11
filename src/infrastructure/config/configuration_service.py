"""設定管理サービス"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from dotenv import load_dotenv


class ConfigurationService:
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
        
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        config = {}
        
        # YAMLファイルを読み込み
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
                
        return config
    
    def get_field_weight(self, field_name: str) -> float:
        """
        フィールドの重みを取得
        
        Args:
            field_name: フィールド名
            
        Returns:
            フィールドの重み
        """
        field_weights = self.config.get("field_weights", {})
        
        # 直接フィールド名で取得
        if field_name in field_weights:
            return float(field_weights[field_name])
        
        # デフォルト重み
        return float(field_weights.get("default_weight", 1.0))
    
    def get_field_weights_dict(self) -> Dict[str, float]:
        """
        すべてのフィールド重みを辞書形式で取得
        
        Returns:
            フィールド名と重みの辞書
        """
        field_weights = self.config.get("field_weights", {})
        weights_dict = {}
        
        # すべてのフィールドを処理
        for field_name, weight in field_weights.items():
            if field_name == "items" and isinstance(weight, dict):
                # itemsが辞書の場合、各サブフィールドを展開
                for sub_field, sub_weight in weight.items():
                    weights_dict[f"items.{sub_field}"] = float(sub_weight)
            elif field_name != "default_weight":
                weights_dict[field_name] = float(weight)
                    
        return weights_dict
    
    def get_default_weight(self) -> float:
        """デフォルトの重みを取得"""
        field_weights = self.config.get("field_weights", {})
        return float(field_weights.get("default_weight", 1.0))
    
    def get_items_field_weights(self) -> Dict[str, float]:
        """
        items内のフィールド重みを辞書形式で取得
        
        Returns:
            フィールド名と重みの辞書（items.プレフィックスなし）
        """
        field_weights = self.config.get("field_weights", {})
        items_weights = {}
        
        # itemsフィールドが辞書の場合、その内容を取得
        if "items" in field_weights and isinstance(field_weights["items"], dict):
            for field_name, weight in field_weights["items"].items():
                items_weights[field_name] = float(weight)
        else:
            # 後方互換性のため、items.で始まるフィールドも探す
            for field_name, weight in field_weights.items():
                if field_name.startswith("items.") and field_name != "items.default_weight":
                    # items.プレフィックスを除去
                    items_field_name = field_name[6:]  # "items."の長さは6
                    items_weights[items_field_name] = float(weight)
                    
        return items_weights
    
    def get_items_field_weight(self, field_name: str) -> float:
        """
        items内の特定フィールドの重みを取得
        
        Args:
            field_name: フィールド名（items.プレフィックスなし）
            
        Returns:
            フィールドの重み
        """
        field_weights = self.config.get("field_weights", {})
        
        # items.プレフィックスを付けて検索
        items_field_key = f"items.{field_name}"
        if items_field_key in field_weights:
            return float(field_weights[items_field_key])
        
        # デフォルト重み
        return float(field_weights.get("default_weight", 1.0))
    
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