# Langfuseサービス実装

## 概要
Langfuseとの連携を実装するインフラストラクチャ層のサービス。プロンプト管理、データセット取得、トレーシングを担当。

## LangfuseService

### 責務
- Langfuse APIとの通信
- プロンプトテンプレートの取得
- データセットの取得
- 実行トレースの記録
- エラーハンドリングとリトライ

### 依存関係
- 外部: Langfuse Python SDK
- Domain層: 各種リポジトリインターフェース実装のため

### 主要メソッド

#### initialize
```
initialize(api_key: str, base_url: Optional[str]) -> None
```
Langfuseクライアントを初期化する。

#### get_prompt
```
get_prompt(prompt_name: str, version: Optional[str]) -> PromptTemplate
```
プロンプトテンプレートを取得する。

**処理**:
1. Langfuse APIを呼び出し
2. プロンプトデータを取得
3. キャッシュに保存
4. PromptTemplateオブジェクトとして返却

#### get_dataset
```
get_dataset(dataset_name: str) -> Dataset
```
データセットを取得する。

**処理**:
1. データセット情報を取得
2. 全アイテムを取得
3. Datasetオブジェクトとして返却

#### get_dataset_items
```
get_dataset_items(
    dataset_name: str,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> List[DatasetItem]
```
データセットアイテムをページネーションで取得。

#### create_trace
```
create_trace(
    name: str,
    metadata: Dict[str, Any]
) -> Trace
```
新しいトレースを作成する。

#### log_generation
```
log_generation(
    trace_id: str,
    input_data: Dict[str, Any],
    output_data: Dict[str, Any],
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    latency_ms: int
) -> None
```
LLM生成結果をトレースに記録する。

### データ構造

#### PromptTemplate
```
{
    name: str
    version: str
    template: str
    variables: List[str]
    metadata: Dict[str, Any]
    created_at: datetime
}
```

#### Dataset
```
{
    name: str
    description: str
    metadata: Dict[str, Any]
    items_count: int
}
```

#### DatasetItem
```
{
    id: str
    input: Dict[str, Any]
    expected_output: Dict[str, Any]
    metadata: Optional[Dict[str, Any]]
}
```

#### Trace
```
{
    id: str
    name: str
    metadata: Dict[str, Any]
    created_at: datetime
}
```

### エラーハンドリング

#### リトライ戦略
```python
retry_config = {
    "max_attempts": 3,
    "backoff_factor": 2,
    "retryable_errors": [
        ConnectionError,
        TimeoutError,
        HTTPError(status_code=503)
    ]
}
```

#### エラータイプ
- `LangfuseConnectionError`: 接続エラー
- `LangfuseNotFoundError`: リソース不在
- `LangfuseRateLimitError`: レート制限
- `LangfuseAuthError`: 認証エラー

### キャッシュ戦略

#### プロンプトキャッシュ
```
- TTL: 1時間
- キー: prompt_name + version
- 無効化: 手動または期限切れ
```

#### データセットキャッシュ
```
- TTL: 10分（開発時）
- TTL: 1時間（本番）
- キー: dataset_name
```

### 設定

#### 環境変数
```
LANGFUSE_API_KEY: APIキー
LANGFUSE_BASE_URL: ベースURL（オプション）
LANGFUSE_TIMEOUT: タイムアウト秒数（デフォルト: 30）
LANGFUSE_CACHE_ENABLED: キャッシュ有効化（デフォルト: true）
```

#### 設定例
```python
config = {
    "api_key": os.getenv("LANGFUSE_API_KEY"),
    "base_url": "https://cloud.langfuse.com",
    "timeout": 30,
    "cache": {
        "enabled": True,
        "prompt_ttl": 3600,
        "dataset_ttl": 600
    }
}
```

## LangfuseExperimentRepository

### 責務
実験結果をLangfuseに保存するリポジトリ実装。

### 実装メソッド

#### save
```
save(experiment: Experiment) -> None
```
実験結果をLangfuseのトレースとして保存。

#### find_by_id
```
find_by_id(experiment_id: str) -> Optional[Experiment]
```
Langfuseから実験データを復元。

### トレース構造
```
Trace: experiment_run
├── Generation: document_1_extraction
│   ├── input: OCRコンテンツ
│   ├── output: 抽出結果
│   └── metrics: 精度スコア
├── Generation: document_2_extraction
└── Summary: experiment_summary
    ├── overall_accuracy
    └── execution_time
```

## 実装時の注意点

### パフォーマンス
- バッチ処理での効率的なAPI呼び出し
- 適切なページネーション
- 並列処理時のレート制限対応

### セキュリティ
- APIキーの安全な管理
- 機密データのマスキング
- HTTPS通信の強制

### 監視
- API呼び出し回数の追跡
- エラー率の監視
- レスポンスタイムの記録

### テスト
- モックサーバーの使用
- 統合テストの実装
- エラーケースのテスト