"""LLMエンドポイントルーター"""
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from ...application.services.configuration_service import ConfigurationService
from ...infrastructure.external_services.gemini_service import GeminiService
from ...application.services.prompt_service import PromptService

router = APIRouter(prefix="/llm", tags=["LLM Extraction"])

# サービスの初期化
config_service = ConfigurationService("config/config.yml")
gemini_service = GeminiService(config_service)
prompt_service = PromptService()


class ExtractionRequest(BaseModel):
    """抽出リクエスト（旧形式: prompt_name）"""
    prompt_name: str
    input_data: Dict[str, Any]


class DirectExtractionRequest(BaseModel):
    """抽出リクエスト（新形式: 直接prompt）"""
    prompt: str
    input_data: Dict[str, Any]


class SimpleExtractionRequest(BaseModel):
    """抽出リクエスト（最新形式: プロンプトのみ）"""
    prompt: str


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
        # プロンプトテンプレートを取得
        prompt_template = prompt_service.get_prompt(request.prompt_name)
        
        # プロンプトを構築
        prompt = prompt_template.format(**request.input_data)
        
        # LLMで抽出
        start_time = time.time()
        
        result = gemini_service.extract(
            prompt,
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
async def gemini_15_simple(request: SimpleExtractionRequest):
    """
    Gemini 1.5 Flash (Simple)
    - Model: gemini-1.5-flash
    - Temperature: 0
    - Max Tokens: 8192
    """
    try:
        # LLMで抽出
        start_time = time.time()
        
        result = gemini_service.extract(
            request.prompt,
            model_name="gemini-1.5-flash",
            temperature=0,
            max_tokens=8192
        )
        
        extraction_time_ms = int((time.time() - start_time) * 1000)
        
        return ExtractionResponse(
            success=True,
            data=result["data"],
            extraction_time_ms=extraction_time_ms,
            endpoint="llm/gemini/1.5-flash",
            model_settings={
                "model": "gemini-1.5-flash",
                "temperature": 0,
                "max_tokens": 8192
            },
            thinking_process=result.get("thinking_process")
        )
        
    except Exception as e:
        return ExtractionResponse(
            success=False,
            data={},
            error=str(e),
            endpoint="llm/gemini/1.5-flash",
            model_settings={
                "model": "gemini-1.5-flash",
                "temperature": 0,
                "max_tokens": 8192
            }
        )


@router.post("/gemini/2.0-flash-thinking", response_model=ExtractionResponse)
async def gemini_20_thinking(request: ExtractionRequest):
    """
    Gemini 2.0 Flash Thinking (Experimental)
    - Model: gemini-2.0-flash-thinking-exp
    - Temperature: 0.1
    - Max Tokens: 32768
    - Thinking Budget: 8192 tokens
    """
    try:
        # プロンプトテンプレートを取得
        prompt_template = prompt_service.get_prompt(request.prompt_name)
        
        # プロンプトを構築
        prompt = prompt_template.format(**request.input_data)
        
        # LLMで抽出（推論モード）
        start_time = time.time()
        
        result = gemini_service.extract(
            prompt,
            model_name="gemini-2.0-flash-thinking-exp",
            temperature=0,
            max_tokens=32768,
            thinking_budget=8192  # 8192トークンの推論
        )
        
        extraction_time_ms = int((time.time() - start_time) * 1000)
        
        response_data = {
            "success": True,
            "data": result["data"],
            "extraction_time_ms": extraction_time_ms,
            "endpoint": "llm/gemini/2.0-thinking",
            "model_settings": {
                "model": "gemini-2.0-flash-thinking-exp",
                "temperature": 0,
                "max_tokens": 32768,
                "thinking_budget": 8192
            }
        }
        
        # 推論プロセスが含まれている場合は追加
        if "thinking_process" in result:
            response_data["thinking_process"] = result["thinking_process"]
        
        return ExtractionResponse(**response_data)
        
    except Exception as e:
        return ExtractionResponse(
            success=False,
            data={},
            error=str(e),
            endpoint="llm/gemini/2.0-thinking",
            model_settings={
                "model": "gemini-2.0-flash-thinking-exp",
                "temperature": 0,
                "max_tokens": 32768,
                "thinking_budget": 8192
            }
        )


@router.post("/gemini/2.5-flash-thinking", response_model=ExtractionResponse)
async def gemini_25_thinking(request: ExtractionRequest):
    """
    Gemini 2.5 Flash Thinking (Latest)
    - Model: gemini-2.5-flash-thinking-001
    - Temperature: 0.1
    - Max Tokens: 32768
    - Thinking Budget: 16384 tokens (より深い推論)
    """
    try:
        # プロンプトテンプレートを取得
        prompt_template = prompt_service.get_prompt(request.prompt_name)
        
        # プロンプトを構築
        prompt = prompt_template.format(**request.input_data)
        
        # LLMで抽出（最新の推論モード）
        start_time = time.time()
        
        result = gemini_service.extract(
            prompt,
            model_name="gemini-2.5-flash-thinking-001",
            temperature=0,
            max_tokens=32768,
            thinking_budget=24576  # 24576トークンの推論
        )
        
        extraction_time_ms = int((time.time() - start_time) * 1000)
        
        response_data = {
            "success": True,
            "data": result["data"],
            "extraction_time_ms": extraction_time_ms,
            "endpoint": "llm/gemini/2.5-thinking",
            "model_settings": {
                "model": "gemini-2.5-flash-thinking-001",
                "temperature": 0,
                "max_tokens": 32768,
                "thinking_budget": 24576
            }
        }
        
        # 推論プロセスが含まれている場合は追加
        if "thinking_process" in result:
            response_data["thinking_process"] = result["thinking_process"]
        
        return ExtractionResponse(**response_data)
        
    except Exception as e:
        return ExtractionResponse(
            success=False,
            data={},
            error=str(e),
            endpoint="llm/gemini/2.5-thinking",
            model_settings={
                "model": "gemini-2.5-flash-thinking-001",
                "temperature": 0,
                "max_tokens": 32768,
                "thinking_budget": 24576
            }
        )


@router.post("/gemini/2.0-flash-thinking-simple", response_model=ExtractionResponse)
async def gemini_20_thinking_simple(request: SimpleExtractionRequest):
    """
    Gemini 2.0 Flash Thinking (Simple)
    - Model: gemini-2.0-flash-thinking-exp-1219
    - Temperature: 0
    - Max Tokens: 8192
    """
    try:
        # LLMで抽出（推論モード）
        start_time = time.time()
        
        result = gemini_service.extract(
            request.prompt,
            model_name="gemini-2.0-flash-thinking-exp-1219",
            temperature=0,
            max_tokens=8192
        )
        
        extraction_time_ms = int((time.time() - start_time) * 1000)
        
        response_data = {
            "success": True,
            "data": result["data"],
            "extraction_time_ms": extraction_time_ms,
            "endpoint": "llm/gemini/2.0-flash-thinking",
            "model_settings": {
                "model": "gemini-2.0-flash-thinking-exp-1219",
                "temperature": 0,
                "max_tokens": 8192
            }
        }
        
        # 推論プロセスが含まれている場合は追加
        if "thinking_process" in result:
            response_data["thinking_process"] = result["thinking_process"]
        
        return ExtractionResponse(**response_data)
        
    except Exception as e:
        return ExtractionResponse(
            success=False,
            data={},
            error=str(e),
            endpoint="llm/gemini/2.0-flash-thinking",
            model_settings={
                "model": "gemini-2.0-flash-thinking-exp-1219",
                "temperature": 0,
                "max_tokens": 8192
            }
        )


@router.post("/gemini/2.5-flash-thinking-simple", response_model=ExtractionResponse)
async def gemini_25_thinking_simple(request: SimpleExtractionRequest):
    """
    Gemini 2.5 Flash Thinking (Simple)
    - Model: gemini-2.5-flash-thinking-exp-1206
    - Temperature: 0
    - Max Tokens: 8192
    """
    try:
        # LLMで抽出（最新の推論モード）
        start_time = time.time()
        
        result = gemini_service.extract(
            request.prompt,
            model_name="gemini-2.5-flash-thinking-exp-1206",
            temperature=0,
            max_tokens=8192
        )
        
        extraction_time_ms = int((time.time() - start_time) * 1000)
        
        response_data = {
            "success": True,
            "data": result["data"],
            "extraction_time_ms": extraction_time_ms,
            "endpoint": "llm/gemini/2.5-flash-thinking",
            "model_settings": {
                "model": "gemini-2.5-flash-thinking-exp-1206",
                "temperature": 0,
                "max_tokens": 8192
            }
        }
        
        # 推論プロセスが含まれている場合は追加
        if "thinking_process" in result:
            response_data["thinking_process"] = result["thinking_process"]
        
        return ExtractionResponse(**response_data)
        
    except Exception as e:
        return ExtractionResponse(
            success=False,
            data={},
            error=str(e),
            endpoint="llm/gemini/2.5-flash-thinking",
            model_settings={
                "model": "gemini-2.5-flash-thinking-exp-1206",
                "temperature": 0,
                "max_tokens": 8192
            }
        )