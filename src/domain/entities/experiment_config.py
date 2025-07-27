"""実験設定エンティティ"""
from typing import List, Optional, Union, Dict
from pydantic import BaseModel

class PromptConfig(BaseModel):
    """プロンプト設定"""
    llm_name: str  # LLMサービス名
    prompt_name: str  # プロンプトテンプレート名

class ExperimentConfig(BaseModel):
    """実験設定"""
    experiment_name: str
    dataset_name: str
    llm_endpoint: str
    description: Optional[str] = None
    
    # プロンプト設定
    prompts: Optional[List[PromptConfig]] = None
    
    def is_multi_prompt(self) -> bool:
        """複数プロンプト形式かどうか"""
        return self.prompts is not None
    
    def get_prompt_names(self) -> List[str]:
        """使用するプロンプト名のリストを取得"""
        if self.prompts:
            return [p.prompt_name for p in self.prompts]
        return []
    
    def get_prompt_configs(self) -> List[PromptConfig]:
        """プロンプト設定のリストを取得"""
        return self.prompts or []