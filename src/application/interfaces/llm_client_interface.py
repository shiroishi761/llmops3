"""LLMクライアントのインターフェース"""
from typing import Dict, Any, Protocol, Optional

class LLMClientInterface(Protocol):
    """LLMクライアントのインターフェース"""
    
    def extract(
        self,
        llm_endpoint: str,
        prompt: Optional[str] = None,
        prompt_template: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        LLMエンドポイントを呼び出してデータを抽出
        
        Args:
            llm_endpoint: 使用するLLMエンドポイント
            prompt: 完成したプロンプト文字列（後方互換性）
            prompt_template: プロンプトテンプレート
            input_data: 入力データ
            
        Returns:
            抽出結果を含む辞書
            
        Raises:
            ExternalServiceError: API呼び出しエラー
        """
        ...
    
    async def extract_async(
        self,
        llm_endpoint: str,
        prompt: Optional[str] = None,
        prompt_template: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        非同期でLLMエンドポイントを呼び出してデータを抽出
        
        Args:
            llm_endpoint: 使用するLLMエンドポイント
            prompt: 完成したプロンプト文字列（後方互換性）
            prompt_template: プロンプトテンプレート
            input_data: 入力データ
            
        Returns:
            抽出結果を含む辞書
            
        Raises:
            ExternalServiceError: API呼び出しエラー
        """
        ...
