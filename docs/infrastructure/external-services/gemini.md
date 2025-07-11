# Gemini APIサービス実装

## 概要
Google Gemini APIとの連携を実装するインフラストラクチャ層のサービス。LLMを使用した文書データ抽出を担当。

## GeminiService

### 責務
- Gemini APIとの通信
- プロンプトの構築と送信
- レスポンスの解析
- エラーハンドリングとリトライ
- 使用量の追跡

### 依存関係
- 外部: Google Generative AI SDK
- Domain層: なし（純粋な技術的実装）

### 主要メソッド

#### initialize
```
initialize(api_key: str, model_name: str = "gemini-pro") -> None
```
Geminiクライアントを初期化する。

#### extract
```
extract(
    prompt: str,
    temperature: float = 0.1,
    max_tokens: Optional[int] = None,
    response_mime_type: str = "application/json"
) -> ExtractResponse
```
プロンプトを送信し、構造化データを抽出する。

**処理**:
1. プロンプトの検証
2. API呼び出し
3. レスポンスの解析
4. JSONのパースと検証
5. 結果の返却

#### extract_with_retry
```
extract_with_retry(
    prompt: str,
    max_retries: int = 5,
    **kwargs
) -> ExtractResponse
```
リトライ機能付きの抽出実行。

### データ構造

#### ExtractResponse
```
{
    content: str  # JSON文字列
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: int
    finish_reason: str
}
```

#### GeminiConfig
```
{
    model: str  # "gemini-pro" | "gemini-pro-vision"
    temperature: float  # 0.0-1.0
    top_p: float
    top_k: int
    max_output_tokens: int
    safety_settings: List[SafetySetting]
    response_mime_type: str
}
```

### プロンプト構築

#### システムプロンプト
```python
SYSTEM_PROMPT = """
あなたは建設業向けの文書から情報を抽出する専門家です。
OCR結果から請求書、見積書、領収書の情報を正確に抽出してください。

重要な注意事項：
1. 数値は正確に抽出してください
2. 日付は yyyy-mm-dd 形式に変換してください
3. 不明な項目は空文字列 "" を設定してください
4. 階層構造の明細は適切にネストしてください
"""
```

#### レスポンス形式指定
```python
response_schema = {
    "type": "object",
    "properties": {
        # ExtractedDataスキーマと同じ
    },
    "required": [...]
}
```

### エラーハンドリング

#### エラータイプ
- `GeminiAPIError`: API呼び出しエラー
- `GeminiRateLimitError`: レート制限
- `GeminiInvalidResponseError`: 不正なレスポンス
- `GeminiTimeoutError`: タイムアウト

#### リトライ戦略
```python
retry_delays = [1, 2, 4, 8, 16]  # 秒
retryable_errors = [
    GeminiRateLimitError,
    GeminiTimeoutError,
    ConnectionError
]
```

### レスポンス解析

#### JSON抽出
```python
def parse_response(response: GenerateContentResponse) -> Dict:
    # candidates[0].content.parts[0].textからJSON抽出
    text = response.candidates[0].content.parts[0].text
    
    # JSONのクリーニング（コードブロック除去等）
    cleaned_text = clean_json_response(text)
    
    # パースと検証
    data = json.loads(cleaned_text)
    validate_schema(data)
    
    return data
```

#### デフォルト値の適用
```python
def apply_defaults(data: Dict) -> Dict:
    # 文字列フィールド: null → ""
    # 数値フィールド: null → 0
    # 配列フィールド: null → []
    return apply_default_values(data, schema)
```

### 使用量追跡

#### メトリクス
```
- API呼び出し回数
- トークン使用量（入力/出力）
- 平均レスポンス時間
- エラー率
```

#### ログ形式
```json
{
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_123",
    "model": "gemini-pro",
    "prompt_tokens": 1500,
    "completion_tokens": 800,
    "latency_ms": 2500,
    "status": "success"
}
```

### 設定

#### 環境変数
```
GEMINI_API_KEY: APIキー
GEMINI_MODEL: モデル名（デフォルト: gemini-pro）
GEMINI_TEMPERATURE: 温度（デフォルト: 0.1）
GEMINI_MAX_TOKENS: 最大トークン数
GEMINI_TIMEOUT: タイムアウト秒数（デフォルト: 30）
```

#### エンドポイント別設定
```python
endpoint_configs = {
    "extract_v1": {
        "model": "gemini-pro",
        "temperature": 0.1,
        "max_tokens": 2000
    },
    "extract_v2_experimental": {
        "model": "gemini-pro",
        "temperature": 0.2,
        "max_tokens": 3000
    },
    "extract_with_cot": {
        "model": "gemini-pro",
        "temperature": 0.3,
        "max_tokens": 4000
    }
}
```

## 実装時の注意点

### パフォーマンス最適化
- プロンプトの最適化（トークン削減）
- バッチ処理の検討
- レスポンスキャッシュ

### セキュリティ
- APIキーの暗号化保存
- 個人情報のマスキング
- アクセスログの記録

### 品質管理
- レスポンスの検証強化
- 異常値の検出
- 抽出精度のモニタリング

### コスト管理
- トークン使用量の監視
- 不要なAPI呼び出しの削減
- 効率的なプロンプト設計

### テスト
- モックレスポンスの準備
- エッジケースのテスト
- レート制限のシミュレーション

## 拡張性

### 新モデル対応
```python
model_registry = {
    "gemini-pro": GeminiProHandler,
    "gemini-pro-vision": GeminiProVisionHandler,
    "gemini-ultra": GeminiUltraHandler  # 将来対応
}
```

### カスタムハンドラー
```python
class CustomExtractionHandler:
    def pre_process(self, prompt: str) -> str:
        # プロンプトの前処理
        pass
    
    def post_process(self, response: Dict) -> Dict:
        # レスポンスの後処理
        pass
```