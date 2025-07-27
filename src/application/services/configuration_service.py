"""設定管理サービス"""
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from ...domain.models.prompt_config import PromptConfig
import yaml
from dotenv import load_dotenv

class ConfigurationService:
    """設定を管理するサービス"""

    def __init__(self, field_weights_config_path: str):
        """
        初期化

        Args:
            field_weights_config_path: フィールド重み設定ファイルのパス（必須）
        """
        if not field_weights_config_path:
            raise ValueError("設定ファイルのパスが指定されていません")

        # .envファイルを読み込み
        load_dotenv()

        # フィールド重み設定を読み込み
        self.field_weights_config = self._load_field_weights_config(field_weights_config_path)

        # API keys from environment
        self._gemini_api_key = os.getenv("GEMINI_API_KEY", "")

    def _load_yaml_file(self, file_path: Path, required: bool = False) -> Dict[str, Any]:
        """
        YAMLファイルを読み込む汎用メソッド

        Args:
            file_path: 読み込むファイルのパス
            required: ファイルの存在が必須かどうか

        Returns:
            読み込んだ設定の辞書

        Raises:
            FileNotFoundError: required=Trueでファイルが見つからない場合
        """
        if not file_path.exists():
            if required:
                raise FileNotFoundError(f"設定ファイルが見つかりません: {file_path}")
            return {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
                return config
        except yaml.YAMLError as e:
            raise ValueError(f"YAML解析エラー ({file_path}): {str(e)}")
        except Exception as e:
            raise RuntimeError(f"ファイル読み込みエラー ({file_path}): {str(e)}")

    def _load_field_weights_config(self, config_path: str) -> Dict[str, Any]:
        """フィールド重み設定ファイルを読み込み"""
        return self._load_yaml_file(Path(config_path), required=False)

    def get_field_weights_dict(self) -> Dict[str, float]:
        """
        すべてのフィールド重みを辞書形式で取得

        Returns:
            フィールド名と重みの辞書
        """
        field_weights = self.field_weights_config.get("field_weights", {})
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
        field_weights = self.field_weights_config.get("field_weights", {})
        return float(field_weights.get("default_weight", 1.0))

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
            ValueError: 指定された実験名が見つからない場合、またはYAML解析エラー
            RuntimeError: ファイル読み込みエラー
        """
        # 統一された読み込みメソッドを使用
        experiments_config = self._load_yaml_file(Path(config_path), required=True)

        # experiment_nameが指定されている場合は、その実験を探す
        if experiment_name:
            if "experiments" in experiments_config:
                # 複数実験形式
                for experiment_config in experiments_config["experiments"]:
                    if experiment_config.get("experiment_name") == experiment_name:
                        return self._validate_experiment_config(experiment_config)
                raise ValueError(f"実験名が見つかりません: {experiment_name}")
            elif experiments_config.get("experiment_name") == experiment_name:
                # 単一実験形式（後方互換性のため）
                return self._validate_experiment_config(experiments_config)
            else:
                raise ValueError(f"実験名が見つかりません: {experiment_name}")
        else:
            # experiment_nameが指定されていない場合は従来の形式を想定
            if "experiments" in experiments_config:
                raise ValueError("実験名を指定してください (--name オプション)")

        return self._validate_experiment_config(experiments_config)

    def _validate_experiment_config(self, experiment_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        実験設定の必須フィールドを検証

        Args:
            experiment_config: 実験設定の辞書

        Returns:
            検証済みの実験設定

        Raises:
            ValueError: 必須フィールドが不足している場合
        """
        required_fields = ["experiment_name", "dataset_name", "llm_endpoint"]
        for field in required_fields:
            if field not in experiment_config:
                raise ValueError(f"必須フィールドがありません: {field}")

        # プロンプト設定の検証（promptsが必要）
        if not experiment_config.get("prompts"):
            raise ValueError("プロンプト設定（prompts）が必要です")

        return experiment_config

    def get_prompt_config(self, experiment_config: Dict[str, Any]) -> List[PromptConfig]:
        """
        実験設定からプロンプト設定を取得

        Args:
            experiment_config: 実験設定の辞書

        Returns:
            PromptConfigのリスト
        """
        prompts = experiment_config.get("prompts")
        if not prompts:
            raise ValueError("プロンプト設定（prompts）が必要です")

        # PromptConfigオブジェクトのリストを作成
        prompt_configs = []
        for p in prompts:
            prompt_configs.append(PromptConfig(
                llm_name=p.get("llm_name"),
                prompt_name=p.get("prompt_name")
            ))
        
        return prompt_configs

    @property
    def gemini_api_key(self) -> str:
        """Gemini APIキーを取得"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        return api_key
