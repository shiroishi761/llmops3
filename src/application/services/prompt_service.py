"""ローカルプロンプト管理サービス"""
from pathlib import Path
from typing import Dict, Optional
import os


class PromptService:
    """ローカルファイルベースのプロンプト管理サービス"""
    
    def __init__(self, prompts_dir: Optional[str] = None):
        """
        初期化
        
        Args:
            prompts_dir: プロンプトディレクトリのパス（デフォルト: プロジェクトルート/prompts）
        """
        if prompts_dir:
            self.prompts_dir = Path(prompts_dir)
        else:
            # プロジェクトルートからpromptsディレクトリを設定
            project_root = Path(__file__).parent.parent.parent.parent
            self.prompts_dir = project_root / "prompts"
        
        # キャッシュ
        self._prompt_cache: Dict[str, str] = {}
    
    def get_prompt(self, prompt_name: str) -> str:
        """
        プロンプトテンプレートを取得
        
        Args:
            prompt_name: プロンプトファイル名（拡張子なし）
            
        Returns:
            プロンプトテンプレート文字列
            
        Raises:
            FileNotFoundError: プロンプトファイルが見つからない場合
            RuntimeError: ファイル読み込みに失敗した場合
        """
        # キャッシュから取得を試行
        if prompt_name in self._prompt_cache:
            return self._prompt_cache[prompt_name]
        
        # ファイルパスを構築
        prompt_file = self.prompts_dir / f"{prompt_name}.txt"
        
        if not prompt_file.exists():
            raise FileNotFoundError(
                f"プロンプトファイルが見つかりません: {prompt_file}\n"
                f"次のコマンドでLangfuseから同期してください: "
                f"python -m src.cli_prompts sync {prompt_name}"
            )
        
        try:
            # ファイルを読み込み
            with open(prompt_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
            
            # キャッシュに保存
            self._prompt_cache[prompt_name] = content
            
            return content
            
        except Exception as e:
            raise RuntimeError(f"プロンプトファイルの読み込みに失敗しました: {prompt_file}, {str(e)}")
    
    def list_available_prompts(self) -> list[str]:
        """
        利用可能なプロンプト名の一覧を取得
        
        Returns:
            プロンプト名のリスト（拡張子なし）
        """
        if not self.prompts_dir.exists():
            return []
        
        prompt_files = list(self.prompts_dir.glob("*.txt"))
        return [f.stem for f in prompt_files]
    
    def reload_cache(self) -> None:
        """プロンプトキャッシュをクリア（ファイル変更時に使用）"""
        self._prompt_cache.clear()
    
    def get_prompt_path(self, prompt_name: str) -> Path:
        """
        プロンプトファイルのパスを取得
        
        Args:
            prompt_name: プロンプト名
            
        Returns:
            プロンプトファイルのPath
        """
        return self.prompts_dir / f"{prompt_name}.txt"
    
    def prompt_exists(self, prompt_name: str) -> bool:
        """
        プロンプトファイルが存在するかチェック
        
        Args:
            prompt_name: プロンプト名
            
        Returns:
            存在するかどうか
        """
        return self.get_prompt_path(prompt_name).exists()