"""LLMエンドポイントルーター"""
import time
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from ...application.services.configuration_service import ConfigurationService
from ...infrastructure.external_services.gemini_service import GeminiService
from ...application.services.prompt_service import PromptService

router = APIRouter(prefix="/llm", tags=["LLM Extraction"])

# サービスの初期化
config_service = ConfigurationService("config/config.yml")
prompt_service = PromptService()

class ExtractionRequest(BaseModel):
    """データ抽出リクエスト（統一形式）"""
    input_data: Dict[str, Any]
    config: Optional[Dict[str, Any]] = None  # 実験設定（プロンプト情報など）

class ExtractionResponse(BaseModel):
    """抽出レスポンス"""
    success: bool
    data: Dict[str, Any]
    extraction_time_ms: Optional[int] = None
    error: Optional[str] = None
    endpoint: str
    model_settings: Dict[str, Any]
    thinking_process: Optional[str] = None

@router.post("/gemini/1.5-flash", response_model=ExtractionResponse)
async def gemini_15(request: ExtractionRequest):
    """
    Gemini 1.5 Flash
    - Model: gemini-1.5-flash
    - Temperature: 0.1
    - Max Tokens: 8192
    """
    try:
        # GeminiServiceをインスタンス化
        gemini_service = GeminiService(
            config_service, 
            name="extraction_service",
            prompt_service=prompt_service
        )
        
        # 実験設定からプロンプト名を取得
        prompt_name = None
        if request.config and "prompts" in request.config:
            for prompt in request.config["prompts"]:
                if prompt.get("llm_name") == "extraction_service":
                    prompt_name = prompt.get("prompt_name")
                    break
        
        # プロンプト名が見つからない場合はデフォルト
        if not prompt_name:
            prompt_name = "invoice_extraction_prompt_v1"
        
        # プロンプト名と入力データを渡して抽出
        start_time = time.time()
        
        result = gemini_service.extract(
            prompt_name=prompt_name,
            input_data=request.input_data,
            model_name="gemini-1.5-flash",
            temperature=0,
            max_tokens=8192
        )
        
        extraction_time_ms = int((time.time() - start_time) * 1000)
        
        return ExtractionResponse(
            success=True,
            data=result["data"],
            extraction_time_ms=extraction_time_ms,
            endpoint="llm/gemini/1.5",
            model_settings={
                "model": "gemini-1.5-flash",
                "temperature": 0,
                "max_tokens": 8192
            }
        )
        
    except Exception as e:
        return ExtractionResponse(
            success=False,
            data={},
            error=str(e),
            endpoint="llm/gemini/1.5",
            model_settings={
                "model": "gemini-1.5-flash",
                "temperature": 0,
                "max_tokens": 8192
            }
        )

@router.post("/gemini/1.5-flash-simple", response_model=ExtractionResponse)
async def gemini_15_simple(request: ExtractionRequest):
    """
    Gemini 1.5 Flash (Simple)
    - Model: gemini-1.5-flash
    - Direct prompt input or template with data
    """
    try:
        # GeminiServiceをインスタンス化
        gemini_service = GeminiService(
            config_service, 
            name="gemini_15_flash_simple",
            prompt_service=prompt_service
        )
        
        # 実験設定からプロンプト名を取得
        prompt_name = None
        if request.config and "prompts" in request.config:
            for prompt in request.config["prompts"]:
                if prompt.get("llm_name") == "extraction_service":
                    prompt_name = prompt.get("prompt_name")
                    break
        
        # プロンプト名が見つからない場合はデフォルト
        if not prompt_name:
            prompt_name = "invoice_extraction_prompt_v1"
        
        # プロンプト名と入力データを渡して抽出
        start_time = time.time()
        
        result = gemini_service.extract(
            prompt_name=prompt_name,
            input_data=request.input_data,
            model_name="gemini-1.5-flash",
            temperature=0,
            max_tokens=8192
        )
        
        extraction_time_ms = int((time.time() - start_time) * 1000)
        
        return ExtractionResponse(
            success=True,
            data=result["data"],
            extraction_time_ms=extraction_time_ms,
            endpoint="llm/gemini/1.5-flash-simple",
            model_settings={
                "model": "gemini-1.5-flash",
                "temperature": 0,
                "max_tokens": 8192
            }
        )
        
    except Exception as e:
        return ExtractionResponse(
            success=False,
            data={},
            error=str(e),
            endpoint="llm/gemini/1.5-flash-simple",
            model_settings={
                "model": "gemini-1.5-flash",
                "temperature": 0,
                "max_tokens": 8192
            }
        )

@router.post("/agent/invoice-with-validation", response_model=ExtractionResponse)
async def agent_invoice_validation(request: ExtractionRequest):
    """
    請求書抽出＋ReAct検証エージェント
    - シンプルなReActパターン: 抽出 → 評価・修正
    """
    try:
        start_time = time.time()
        
        # 入力データからOCR内容を取得
        input_data = request.input_data
        ocr_content = input_data.get("ocr_content", "")
        
        logging.info(f"エージェント処理開始: OCR内容の長さ={len(ocr_content)}")
        
        # 実験設定からプロンプト名を取得
        extraction_prompt_name = None
        validation_prompt_name = None
        
        if request.config and "prompts" in request.config:
            for prompt in request.config["prompts"]:
                if prompt.get("llm_name") == "extraction_service":
                    extraction_prompt_name = prompt.get("prompt_name")
                elif prompt.get("llm_name") == "validation_service":
                    validation_prompt_name = prompt.get("prompt_name")
        
        # プロンプト名が見つからない場合はデフォルト
        if not extraction_prompt_name:
            extraction_prompt_name = "invoice_extraction_prompt_v1"
        if not validation_prompt_name:
            validation_prompt_name = "react_evaluation_prompt"
        
        # Step 1: 抽出用GeminiService
        extraction_service = GeminiService(
            config_service,
            name="extraction_agent",
            prompt_service=prompt_service
        )
        
        # プロンプト名で抽出
        extracted_data = extraction_service.extract(
            prompt_name=extraction_prompt_name,
            input_data=input_data,
            model_name="gemini-2.0-flash-exp",
            temperature=0,
            max_tokens=8192
        )
        
        logging.info(f"抽出結果のキー: {list(extracted_data.keys()) if isinstance(extracted_data, dict) else 'Not a dict'}")
        logging.info(f"抽出結果の一部: {str(extracted_data)[:200]}")
        
        # Step 2: ReAct評価用GeminiService
        react_service = GeminiService(
            config_service,
            name="react_agent",
            prompt_service=prompt_service
        )
        
        # ReActエージェントを実行（Gemini 2.0 Proを使用）
        react_result = react_service.extract(
            prompt_name=validation_prompt_name,
            input_data={
                "ocr_content": ocr_content,
                "extracted_data": str(extracted_data)
            },
            model_name="gemini-2.0-flash-exp",
            temperature=0,
            max_tokens=8192
        )
        
        logging.info(f"ReAct結果のキー: {list(react_result.keys()) if isinstance(react_result, dict) else 'Not a dict'}")
        logging.info(f"ReAct結果の一部: {str(react_result)[:200]}")
        
        # 結果の処理
        # 最初の抽出結果からデータを取得
        if isinstance(extracted_data, dict):
            if "data" in extracted_data:
                initial_data = extracted_data["data"]["data"] if isinstance(extracted_data["data"], dict) and "data" in extracted_data["data"] else extracted_data["data"]
            else:
                initial_data = extracted_data
        else:
            initial_data = extracted_data
        
        final_data = initial_data
        react_info = None
        
        logging.info(f"初期データのキー: {list(initial_data.keys()) if isinstance(initial_data, dict) else 'Not a dict'}")
        logging.info(f"初期データの一部: {str(initial_data)[:200]}")
        
        # 最終データを保存
        if not initial_data:
            logging.error("初期データが空です")
        
        if isinstance(react_result, dict):
            # ReAct結果からデータを取得
            if "data" in react_result:
                react_data = react_result["data"]["data"] if isinstance(react_result["data"], dict) and "data" in react_result["data"] else react_result["data"]
            else:
                react_data = react_result
            
            # ReAct結果から最終データを取得
            if react_data.get("needs_correction", False) and "corrected_data" in react_data:
                final_data = react_data["corrected_data"]
            
            # ReActの思考プロセスを保存
            react_info = {
                "thought": react_data.get("thought", ""),
                "action": react_data.get("action", ""),
                "needs_correction": react_data.get("needs_correction", False)
            }
        
        extraction_time_ms = int((time.time() - start_time) * 1000)
        
        response_data = {
            "success": True,
            "data": final_data,
            "extraction_time_ms": extraction_time_ms,
            "endpoint": "llm/agent/invoice-with-validation",
            "model_settings": {
                "agent_type": "multi_prompt_workflow",
                "workflow_steps": ["extraction", "react_evaluation"],
                "models_used": {
                    "extraction": "gemini-2.0-flash-exp",
                    "react_evaluation": "gemini-2.0-flash-exp"
                },
                "react_process": react_info
            }
        }
        
        return ExtractionResponse(**response_data)
        
    except Exception as e:
        import traceback
        logging.error(f"エージェント処理エラー: {str(e)}")
        logging.error(traceback.format_exc())
        
        return ExtractionResponse(
            success=False,
            data={},
            error=str(e),
            endpoint="llm/agent/invoice-with-validation",
            model_settings={
                "agent_type": "multi_prompt_workflow",
                "error_step": "unknown"
            }
        )
