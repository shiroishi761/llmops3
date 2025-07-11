# APIエンドポイント仕様

## 概要
FastAPIで実装するHTTP APIのエンドポイント仕様。インターフェース層として、外部からのリクエストを受け付け、アプリケーション層のユースケースを呼び出す。

## メインエンドポイント

### POST /api/main
統一されたエントリーポイント。`endpoint`フィールドで処理を振り分ける。

#### リクエスト
```typescript
{
  endpoint: string        // 実行するエンドポイント名
  ocr_content: string    // OCR結果（Markdown形式）
  document_id: string    // 文書ID
  company_name: string   // 自社名
  customers: {           // 顧客マスタ
    [name: string]: number
  }
  account_items: string[] // 勘定科目リスト
}
```

#### レスポンス
```typescript
// 成功時
{
  status: "success"
  data: ExtractedData    // 抽出結果
  metadata?: {
    execution_time_ms: number
    endpoint_used: string
  }
}

// エラー時
{
  status: "error"
  error: {
    code: string
    message: string
    details?: any
  }
}
```

#### エンドポイント一覧
- `extract_v1`: 標準抽出
- `extract_v2_experimental`: 実験的な改良版
- `extract_with_cot`: Chain of Thought版
- その他、動的に追加可能

## 実験・管理用エンドポイント

### POST /api/experiments/run
実験を実行する（YML設定ファイルベース）。

#### リクエスト
```typescript
{
  config_path: string    // YML設定ファイルのパス
}
```

#### レスポンス
```typescript
{
  experiment_id: string
  status: "started" | "queued"
  estimated_time_seconds: number
}
```

### GET /api/experiments/{experiment_id}
実験の状態を取得する。

#### レスポンス
```typescript
{
  id: string
  name: string
  status: "pending" | "running" | "completed" | "failed"
  progress?: {
    processed: number
    total: number
  }
  summary?: ExperimentSummary
}
```

### GET /api/experiments/compare
実験結果を比較する。

#### クエリパラメータ
- `ids`: カンマ区切りの実験ID
- `metric`: 比較基準（accuracy, speed, success_rate）

#### レスポンス
```typescript
{
  comparisons: [{
    experiment_id: string
    rank: number
    metrics: {
      accuracy: number
      speed_ms: number
      success_rate: number
    }
  }]
  best_experiment_id: string
}
```

## ヘルスチェック

### GET /api/health
システムの健全性を確認する。

#### レスポンス
```typescript
{
  status: "healthy" | "degraded" | "unhealthy"
  version: string
  checks: {
    langfuse: "ok" | "error"
    gemini: "ok" | "error"
    storage: "ok" | "error"
  }
}
```

## エラーハンドリング

### HTTPステータスコード
- `200`: 成功
- `400`: 不正なリクエスト
- `401`: 認証エラー（将来実装）
- `404`: リソース不在
- `429`: レート制限
- `500`: サーバーエラー
- `503`: サービス利用不可

### エラーコード
```typescript
enum ErrorCode {
  // 400系
  INVALID_REQUEST = "INVALID_REQUEST"
  MISSING_FIELD = "MISSING_FIELD"
  UNKNOWN_ENDPOINT = "UNKNOWN_ENDPOINT"
  
  // 500系
  INTERNAL_ERROR = "INTERNAL_ERROR"
  LLM_ERROR = "LLM_ERROR"
  STORAGE_ERROR = "STORAGE_ERROR"
}
```

## 実装詳細

### ルーターの構成
```python
from fastapi import APIRouter, Depends
from interfaces.schemas import MainRequest, MainResponse

router = APIRouter(prefix="/api")

@router.post("/main")
async def main_endpoint(
    request: MainRequest,
    use_case: ExtractDocumentUseCase = Depends(get_extract_use_case)
) -> MainResponse:
    # エンドポイントに基づいて処理を振り分け
    return await use_case.execute(request)
```

### 依存性注入
```python
def get_extract_use_case() -> ExtractDocumentUseCase:
    # 各サービスを注入
    config = ConfigurationService()
    gemini = GeminiService(config)
    langfuse = LangfuseService(config)
    
    return ExtractDocumentUseCase(gemini, langfuse)
```

### ミドルウェア

#### CORSミドルウェア
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番では制限
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
```

#### ロギングミドルウェア
```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    logger.info(f"{request.method} {request.url.path} - {duration:.3f}s")
    return response
```

#### レート制限（将来実装）
```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/main")
@limiter.limit("100/minute")
async def main_endpoint(...):
    pass
```

## セキュリティ

### 認証（将来実装）
- APIキー認証
- JWT トークン
- OAuth2

### 入力検証
- Pydanticによる自動検証
- SQLインジェクション対策
- XSS対策

### 監査ログ
- すべてのAPIコールを記録
- 機密情報のマスキング
- 長期保存

## パフォーマンス

### 非同期処理
- FastAPIの非同期サポート活用
- 並行処理の最適化

### キャッシング
- プロンプトのキャッシュ
- 静的データのキャッシュ

### 最適化
- データベースクエリの最適化
- N+1問題の回避

## モニタリング

### メトリクス
- リクエスト数
- レスポンスタイム
- エラー率
- 同時接続数

### アラート
- エラー率上昇
- レスポンス遅延
- リソース枯渇

## API仕様書

### OpenAPI (Swagger)
- 自動生成: `/docs`
- ReDoc: `/redoc`

### 使用例
```bash
# 文書抽出
curl -X POST http://localhost:8000/api/main \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint": "extract_v1",
    "ocr_content": "...",
    "document_id": "doc_001",
    "company_name": "株式会社Example",
    "customers": {"顧客A": 101},
    "account_items": ["外注費", "材料費"]
  }'
```