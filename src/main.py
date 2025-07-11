"""FastAPIメインアプリケーション"""
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional

from .infrastructure.config.configuration_service import ConfigurationService
from .infrastructure.external_services.langfuse_service import LangfuseService
from .infrastructure.external_services.gemini_service import GeminiService
from .interfaces.api.experiment_router import router as experiment_router

app = FastAPI(
    title="LLMOps精度検証プラットフォーム",
    description="複数のLLMエンドポイントで文書抽出精度を検証するAPI",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# サービスの初期化
config_service = ConfigurationService()
langfuse_service = LangfuseService(config_service)
gemini_service = GeminiService(config_service)

# ルーターを登録
app.include_router(experiment_router)


class ExtractionRequest(BaseModel):
    """抽出リクエスト"""
    prompt_name: str
    input_data: Dict[str, Any]
    
    
class ExtractionResponse(BaseModel):
    """抽出レスポンス"""
    success: bool
    data: Dict[str, Any]
    extraction_time_ms: Optional[int] = None
    error: Optional[str] = None
    endpoint: str
    model_settings: Dict[str, Any]
    thinking_process: Optional[str] = None


@app.get("/")
async def root():
    """ヘルスチェック"""
    return {"status": "healthy", "service": "LLMOps Accuracy Platform"}




@app.post("/llm/gemini/1.5-flash", response_model=ExtractionResponse)
async def gemini_15(request: ExtractionRequest):
    """
    Gemini 1.5 Flash
    - Model: gemini-1.5-flash
    - Temperature: 0.1
    - Max Tokens: 8192
    """
    try:
        # プロンプトテンプレートを取得
        prompt_template = langfuse_service.get_prompt(request.prompt_name)
        
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


@app.post("/llm/gemini/2.0-flash-thinking", response_model=ExtractionResponse)
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
        prompt_template = langfuse_service.get_prompt(request.prompt_name)
        
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


@app.post("/llm/gemini/2.5-flash-thinking", response_model=ExtractionResponse)
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
        prompt_template = langfuse_service.get_prompt(request.prompt_name)
        
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


