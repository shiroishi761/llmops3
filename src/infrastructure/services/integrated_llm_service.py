"""統合LLMサービス実装"""
import time
from typing import Dict, List, Any

from src.domain.services.external_llm_service import ExternalLLMService
from src.domain.exceptions import PromptNotFoundError, DatasetNotFoundError, ExtractionFailedError
from src.infrastructure.external_services.langfuse_service import LangfuseService
from src.infrastructure.external_services.llm_client import LLMClient


class IntegratedLLMService(ExternalLLMService):
    """Langfuse + LLMClient統合サービス"""
    
    def __init__(self, langfuse_service: LangfuseService, llm_client: LLMClient):
        self.langfuse_service = langfuse_service
        self.llm_client = llm_client
    
    async def get_prompt(self, prompt_name: str) -> str:
        """プロンプトテンプレートを取得"""
        try:
            return self.langfuse_service.get_prompt(prompt_name)
        except Exception as e:
            raise PromptNotFoundError(f"プロンプト '{prompt_name}' が見つかりません: {str(e)}")
    
    async def get_dataset(self, dataset_name: str) -> List[Dict[str, Any]]:
        """データセットを取得"""
        try:
            return self.langfuse_service.get_dataset(dataset_name)
        except Exception as e:
            raise DatasetNotFoundError(f"データセット '{dataset_name}' が見つかりません: {str(e)}")
    
    async def extract_document(
        self,
        llm_endpoint: str,
        prompt_name: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """文書から情報を抽出"""
        try:
            start_time = time.time()
            response = self.llm_client.extract(
                llm_endpoint=llm_endpoint,
                prompt_name=prompt_name,
                input_data=input_data
            )
            extraction_time_ms = response.get("extraction_time_ms", int((time.time() - start_time) * 1000))
            
            return {
                "extracted_data": response.get("extracted_data", {}),
                "extraction_time_ms": extraction_time_ms
            }
        except Exception as e:
            raise ExtractionFailedError(f"文書抽出に失敗しました: {str(e)}")
    
    async def flush(self) -> None:
        """バッファのフラッシュ"""
        self.langfuse_service.flush()