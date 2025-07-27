"""実験設定ローダー"""
import yaml
from typing import Dict, Any, List
from pathlib import Path
from ...domain.entities.experiment_config import ExperimentConfig, PromptConfig

def load_experiment_config(file_path: str) -> ExperimentConfig:
    """実験設定ファイルを読み込み"""
    path = Path(file_path)
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    # promptsがある場合、PromptConfigオブジェクトに変換
    if 'prompts' in data and isinstance(data['prompts'], list):
        prompt_configs = []
        for item in data['prompts']:
            if isinstance(item, dict):
                prompt_configs.append(PromptConfig(**item))
        data['prompts'] = prompt_configs
    
    return ExperimentConfig(**data)

def is_simple_format(config: ExperimentConfig) -> bool:
    """シンプルな形式（単一プロンプト）かどうか"""
    return False  # もうシンプル形式はサポートしない

def get_prompt_configuration(config: ExperimentConfig) -> Dict[str, Any]:
    """プロンプト設定情報を取得"""
    return {
        "type": "multi_prompt",
        "prompts": [
            {
                "llm_name": prompt.llm_name,
                "prompt_name": prompt.prompt_name
            }
            for prompt in config.prompts
        ] if config.prompts else []
    }