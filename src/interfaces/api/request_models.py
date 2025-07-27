"""APIリクエストモデル"""
from pydantic import BaseModel
from typing import Dict, Any, Optional, Union

class SimpleExtractionRequest(BaseModel):
    """抽出リクエスト（後方互換性: プロンプトのみ）"""
    prompt: str

class TemplateExtractionRequest(BaseModel):
    """テンプレートベースの抽出リクエスト"""
    prompt_template: str
    input_data: Dict[str, Any]

class UniversalExtractionRequest(BaseModel):
    """統合抽出リクエスト（両方の形式をサポート）"""
    prompt: Optional[str] = None
    prompt_template: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    
    def is_template_mode(self) -> bool:
        """テンプレートモードかどうか"""
        return self.prompt_template is not None
    
    def get_prompt(self) -> str:
        """最終的なプロンプトを取得"""
        if self.prompt:
            return self.prompt
        elif self.prompt_template and self.input_data:
            # テンプレートに変数を注入
            prompt = self.prompt_template
            for key, value in self.input_data.items():
                placeholder = f"{{{key}}}"
                if isinstance(value, str):
                    prompt = prompt.replace(placeholder, value)
            return prompt
        else:
            raise ValueError("プロンプトまたはテンプレート＋データが必要です")