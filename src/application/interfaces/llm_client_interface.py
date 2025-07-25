"""LLMクライアントのインターフェース"""
from typing import Dict, Any, Protocol


class LLMClientInterface(Protocol):
    """LLMクライアントのインターフェース"""
    
    def extract(
        self,
        llm_endpoint: str,
        prompt: str
    ) -> Dict[str, Any]:
        """
        LLMエンドポイントを呼び出してデータを抽出
        
        Args:
            llm_endpoint: 使用するLLMエンドポイント
            prompt: 実行するプロンプト文字列（入力データが既に埋め込み済み）
            
        Returns:
            抽出結果を含む辞書
            
        Raises:
            ExternalServiceError: API呼び出しエラー
        """
        ...
    
    async def extract_async(
        self,
        llm_endpoint: str,
        prompt: str
    ) -> Dict[str, Any]:
        """
        非同期でLLMエンドポイントを呼び出してデータを抽出
        
        Args:
            llm_endpoint: 使用するLLMエンドポイント
            prompt: 実行するプロンプト文字列（入力データが既に埋め込み済み）
            
        Returns:
            抽出結果を含む辞書
            
        Raises:
            ExternalServiceError: API呼び出しエラー
        """
        ...