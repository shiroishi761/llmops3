"""FastAPIメインアプリケーション"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .experiment_router import router as experiment_router
from .llm_router import router as llm_router

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

# ルーターを登録
app.include_router(experiment_router)
app.include_router(llm_router)

@app.get("/")
async def root():
    """ヘルスチェック"""
    return {"status": "healthy", "service": "LLMOps Accuracy Platform"}
