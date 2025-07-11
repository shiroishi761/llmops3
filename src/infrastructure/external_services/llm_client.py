"""LLMエンドポイントへのHTTPクライアント"""
import os
import time
from typing import Dict, Any, Optional
import httpx
from ...domain.exceptions import ExternalServiceError


class LLMClient:
    """LLMエンドポイントへのHTTPクライアント"""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        LLMクライアントを初期化
        
        Args:
            base_url: APIのベースURL（デフォルト: http://localhost:8000）
        """
        self.base_url = base_url or os.getenv("API_BASE_URL", "http://localhost:8000")
        self.timeout = 600  # 10分のタイムアウト（大きなドキュメント処理用）
        
    def extract(
        self,
        llm_endpoint: str,
        prompt_name: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        LLMエンドポイントを呼び出してデータを抽出
        
        Args:
            llm_endpoint: 使用するLLMエンドポイント（例: "llm/gemini/1.5-flash"）
            prompt_name: Langfuseのプロンプト名
            input_data: プロンプトに渡す入力データ
            
        Returns:
            抽出結果を含む辞書
            
        Raises:
            ExternalServiceError: API呼び出しエラー
        """
        url = f"{self.base_url}/{llm_endpoint}"
        
        payload = {
            "prompt_name": prompt_name,
            "input_data": input_data
        }
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                
                if not result.get("success"):
                    raise ExternalServiceError(
                        f"LLM extraction failed: {result.get('error', 'Unknown error')}"
                    )
                
                return {
                    "extracted_data": result.get("data", {}),
                    "extraction_time_ms": result.get("extraction_time_ms"),
                    "thinking_process": result.get("thinking_process"),
                    "model_settings": result.get("model_settings", {}),
                    "endpoint": llm_endpoint
                }
                
        except httpx.TimeoutException as e:
            raise ExternalServiceError(
                f"LLM request timeout after {self.timeout}s: {str(e)}"
            )
        except httpx.HTTPStatusError as e:
            raise ExternalServiceError(
                f"LLM HTTP error {e.response.status_code}: {e.response.text}"
            )
        except Exception as e:
            raise ExternalServiceError(
                f"LLM request failed: {str(e)}"
            )
    
    async def extract_async(
        self,
        llm_endpoint: str,
        prompt_name: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        非同期でLLMエンドポイントを呼び出してデータを抽出
        
        Args:
            llm_endpoint: 使用するLLMエンドポイント（例: "llm/gemini/1.5-flash"）
            prompt_name: Langfuseのプロンプト名
            input_data: プロンプトに渡す入力データ
            
        Returns:
            抽出結果を含む辞書
            
        Raises:
            ExternalServiceError: API呼び出しエラー
        """
        url = f"{self.base_url}/{llm_endpoint}"
        
        payload = {
            "prompt_name": prompt_name,
            "input_data": input_data
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                
                if not result.get("success"):
                    raise ExternalServiceError(
                        f"LLM extraction failed: {result.get('error', 'Unknown error')}"
                    )
                
                return {
                    "extracted_data": result.get("data", {}),
                    "extraction_time_ms": result.get("extraction_time_ms"),
                    "thinking_process": result.get("thinking_process"),
                    "model_settings": result.get("model_settings", {}),
                    "endpoint": llm_endpoint
                }
                
        except httpx.TimeoutException as e:
            raise ExternalServiceError(
                f"LLM request timeout after {self.timeout}s: {str(e)}"
            )
        except httpx.HTTPStatusError as e:
            raise ExternalServiceError(
                f"LLM HTTP error {e.response.status_code}: {e.response.text}"
            )
        except Exception as e:
            raise ExternalServiceError(
                f"LLM request failed: {str(e)}"
            )