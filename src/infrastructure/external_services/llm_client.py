"""LLMエンドポイントへのHTTPクライアント"""
import time
import os
import httpx
from typing import Dict, Any
from ...domain.exceptions import ExternalServiceError


class LLMClient:
    """LLMエンドポイントへのHTTPクライアント"""
    
    def __init__(self):
        """
        LLMクライアントを初期化
        """
        self.base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        self.timeout = 300.0  # 5分のタイムアウト
        
    def extract(
        self,
        llm_endpoint: str,
        prompt: str
    ) -> Dict[str, Any]:
        """
        LLMエンドポイントを呼び出してデータを抽出
        
        Args:
            llm_endpoint: 使用するLLMエンドポイント（例: "llm/gemini/1.5-flash"）
            prompt: 実行するプロンプト文字列（入力データが既に埋め込み済み）
            
        Returns:
            抽出結果を含む辞書
            
        Raises:
            ExternalServiceError: API呼び出しエラー
        """
        try:
            start_time = time.time()
            
            # HTTPリクエスト用のペイロード作成
            payload = {
                "prompt": prompt
            }
            
            # エンドポイントURLを構築（-simpleサフィックスを追加）
            simple_endpoint = f"{llm_endpoint}-simple"
            url = f"{self.base_url}/{simple_endpoint}"
            
            # HTTPリクエストを送信
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                extraction_time_ms = int((time.time() - start_time) * 1000)
                
                # レスポンス形式を統一
                return {
                    "extracted_data": result.get("data", {}),
                    "extraction_time_ms": result.get("extraction_time_ms", extraction_time_ms),
                    "thinking_process": result.get("thinking_process"),
                    "model_settings": result.get("model_settings", {}),
                    "endpoint": llm_endpoint
                }
            
        except httpx.HTTPStatusError as e:
            raise ExternalServiceError(
                f"HTTP error calling {llm_endpoint}: {e.response.status_code} - {e.response.text}"
            )
        except httpx.RequestError as e:
            raise ExternalServiceError(
                f"Request error calling {llm_endpoint}: {str(e)}"
            )
        except Exception as e:
            raise ExternalServiceError(
                f"LLM extraction failed: {str(e)}"
            )
    
    
    async def extract_async(
        self,
        llm_endpoint: str,
        prompt: str
    ) -> Dict[str, Any]:
        """
        非同期でLLMエンドポイントを呼び出してデータを抽出
        
        Args:
            llm_endpoint: 使用するLLMエンドポイント（例: "llm/gemini/1.5-flash"）
            prompt: 実行するプロンプト文字列（入力データが既に埋め込み済み）
            
        Returns:
            抽出結果を含む辞書
            
        Raises:
            ExternalServiceError: API呼び出しエラー
        """
        try:
            start_time = time.time()
            
            # HTTPリクエスト用のペイロード作成
            payload = {
                "prompt": prompt
            }
            
            # エンドポイントURLを構築（-simpleサフィックスを追加）
            simple_endpoint = f"{llm_endpoint}-simple"
            url = f"{self.base_url}/{simple_endpoint}"
            
            # 非同期HTTPリクエストを送信
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                extraction_time_ms = int((time.time() - start_time) * 1000)
                
                # レスポンス形式を統一
                return {
                    "extracted_data": result.get("data", {}),
                    "extraction_time_ms": result.get("extraction_time_ms", extraction_time_ms),
                    "thinking_process": result.get("thinking_process"),
                    "model_settings": result.get("model_settings", {}),
                    "endpoint": llm_endpoint
                }
            
        except httpx.HTTPStatusError as e:
            raise ExternalServiceError(
                f"HTTP error calling {llm_endpoint}: {e.response.status_code} - {e.response.text}"
            )
        except httpx.RequestError as e:
            raise ExternalServiceError(
                f"Request error calling {llm_endpoint}: {str(e)}"
            )
        except Exception as e:
            raise ExternalServiceError(
                f"LLM extraction failed: {str(e)}"
            )

