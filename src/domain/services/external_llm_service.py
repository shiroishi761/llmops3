"""外部LLMサービスの抽象インターフェース"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any

from src.domain.exceptions import PromptNotFoundError, DatasetNotFoundError, ExtractionFailedError


class ExternalLLMService(ABC):
    """外部LLMサービスの抽象インターフェース
    
    プロンプト管理、データセット管理、文書抽出を統合したインターフェース
    """
    
    @abstractmethod
    async def get_prompt(self, prompt_name: str) -> str:
        """
        プロンプトテンプレートを取得
        
        Args:
            prompt_name: プロンプト名
            
        Returns:
            プロンプトテンプレート文字列
            
        Raises:
            PromptNotFoundError: プロンプトが見つからない場合
        """
        pass
    
    @abstractmethod
    async def get_dataset(self, dataset_name: str) -> List[Dict[str, Any]]:
        """
        データセットを取得
        
        Args:
            dataset_name: データセット名
            
        Returns:
            データセットアイテムのリスト
            
        Raises:
            DatasetNotFoundError: データセットが見つからない場合
        """
        pass
    
    @abstractmethod
    async def extract_document(
        self,
        llm_endpoint: str,
        prompt_name: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        文書から情報を抽出
        
        Args:
            llm_endpoint: 使用するLLMエンドポイント
            prompt_name: プロンプト名（トレーシング用）
            input_data: 入力データ
            
        Returns:
            抽出結果辞書（extracted_data, extraction_time_msを含む）
            
        Raises:
            ExtractionFailedError: 抽出に失敗した場合
        """
        pass
    
    @abstractmethod
    async def flush(self) -> None:
        """
        バッファのフラッシュ（ログやトレースデータの送信）
        """
        pass