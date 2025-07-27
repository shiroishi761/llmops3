"""プロンプト設定モデル"""
from pydantic import BaseModel

class PromptConfig(BaseModel):
    """プロンプト設定"""
    llm_name: str  # LLMサービス名
    prompt_name: str  # プロンプトテンプレート名