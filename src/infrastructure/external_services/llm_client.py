"""LLMエンドポイントへのHTTPクライアント"""
import time
import os
import httpx
from typing import Dict, Any, List, Optional
from ...domain.exceptions import ExternalServiceError

class LLMClient:
    """LLMエンドポイントへのHTTPクライアント"""
    
    def __init__(self):
        """
        LLMクライアントを初期化
        """
        # Dockerコンテナ間の通信では、サービス名を使用
        self.base_url = os.getenv("API_BASE_URL", "http://app:8000")
        self.timeout = 300.0  # 5分のタイムアウト
        
    def extract(
        self,
        llm_endpoint: str,
        prompt: str = None,
        prompt_template: str = None,
        input_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        LLMエンドポイントを呼び出してデータを抽出
        
        Args:
            llm_endpoint: 使用するLLMエンドポイント（例: "llm/gemini/1.5-flash"）
            prompt: 完成したプロンプト文字列（後方互換性のため）
            prompt_template: プロンプトテンプレート
            input_data: 入力データ
            
        Returns:
            抽出結果を含む辞書
            
        Raises:
            ExternalServiceError: API呼び出しエラー
        """
        try:
            start_time = time.time()
            
            # HTTPリクエスト用のペイロード作成
            if prompt:
                # 後方互換性: 完成したプロンプトを使用
                payload = {
                    "prompt": prompt
                }
            else:
                # 新方式: テンプレートとデータを分離
                payload = {
                    "prompt_template": prompt_template,
                    "input_data": input_data or {}
                }
            
            # エンドポイントURLを構築
            url = f"{self.base_url}/{llm_endpoint}"
            
            # HTTPリクエストを送信
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                extraction_time_ms = int((time.time() - start_time) * 1000)
                
                # レスポンス形式を統一
                extracted_data = result.get("data", {})
                
                # エージェントエンドポイントの場合、余分なネストを解消
                if isinstance(extracted_data, dict) and "data" in extracted_data:
                    # 実際のデータは data.data に入っている場合
                    actual_data = extracted_data.get("data", {})
                    extracted_data = actual_data
                
                return {
                    "extracted_data": extracted_data,
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
        prompt: str = None,
        prompt_template: str = None,
        input_data: Dict[str, Any] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        非同期でLLMエンドポイントを呼び出してデータを抽出
        
        Args:
            llm_endpoint: 使用するLLMエンドポイント（例: "llm/gemini/1.5-flash"）
            prompt: 完成したプロンプト文字列（後方互換性のため）
            prompt_template: プロンプトテンプレート
            input_data: 入力データ
            config: 実験設定（プロンプト情報など）
            
        Returns:
            抽出結果を含む辞書
            
        Raises:
            ExternalServiceError: API呼び出しエラー
        """
        try:
            start_time = time.time()
            
            # HTTPリクエスト用のペイロード作成
            if prompt:
                # 後方互換性: 完成したプロンプトを使用
                payload = {
                    "prompt": prompt
                }
            else:
                # 新方式: 入力データと設定を送信
                payload = {
                    "input_data": input_data or {}
                }
                
                # 実験設定がある場合は追加
                if config:
                    payload["config"] = config
                
                # テンプレートがある場合は追加（後方互換性）
                if prompt_template:
                    payload["prompt_template"] = prompt_template
            
            # エンドポイントURLを構築
            url = f"{self.base_url}/{llm_endpoint}"
            
            # 非同期 HTTPリクエストを送信
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                extraction_time_ms = int((time.time() - start_time) * 1000)
                
                # レスポンス形式を統一
                extracted_data = result.get("data", {})
                
                # エージェントエンドポイントの場合、余分なネストを解消
                if isinstance(extracted_data, dict) and "data" in extracted_data:
                    # 実際のデータは data.data に入っている場合
                    actual_data = extracted_data.get("data", {})
                    extracted_data = actual_data
                
                return {
                    "extracted_data": extracted_data,
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
