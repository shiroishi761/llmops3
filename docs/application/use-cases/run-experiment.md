# 実験実行ユースケース

## 概要
オフライン精度検証実験を実行するユースケース。YMLファイルの設定に基づいて実験を実行し、結果を保存する。

## RunExperimentUseCase

### 責務
- 実験設定の読み込みと検証
- 外部サービスとの連携調整
- 実験の実行制御
- 結果の永続化

### 依存関係
- Domain層: Experiment, ExperimentManagementService, AccuracyEvaluationService
- Infrastructure層: LangfuseService, GeminiService, FileService

### 主要メソッド

#### execute
```
execute(experiment_config_path: str) -> ExperimentResultDto
```
YMLファイルから実験設定を読み込み、実験を実行する。

**処理フロー**:
1. YMLファイルの読み込みと検証
2. 実験エンティティの作成
3. Langfuseからプロンプトとデータセットを取得
4. 各ドキュメントの処理（並列実行）
5. 結果の集約と保存

#### execute_from_config
```
execute_from_config(config: ExperimentConfigDto) -> ExperimentResultDto
```
設定DTOから直接実験を実行する。

### 処理の詳細

#### 1. 設定の検証
```
- 必須フィールドの存在確認
- プロンプト名の有効性
- データセット名の有効性
- エンドポイントの有効性
```

#### 2. リソースの取得
```
- Langfuseからプロンプトテンプレートを取得
- Langfuseからデータセットを取得
- データセット内の各アイテムを検証
```

#### 3. ドキュメント処理
```
for each document in dataset:
  - プロンプトに変数を埋め込み
  - LLMエンドポイントを呼び出し
  - レスポンスをパース
  - 精度を評価
  - 結果を記録
```

#### 4. 並列実行制御
```
- ThreadPoolまたはAsyncIOで並列化
- 同時実行数の制限（デフォルト: 5）
- エラー時のリトライ（最大5回）
- タイムアウト処理
```

#### 5. 結果の保存
```
- Langfuseに実行トレースを保存
- ローカルファイルシステムにJSON保存
- 実験サマリーの更新
```

### エラーハンドリング

#### 設定エラー
- InvalidConfigurationError: YML形式不正
- ResourceNotFoundError: プロンプト/データセット不在

#### 実行時エラー
- LLMServiceError: API呼び出し失敗
- ParsingError: レスポンスパース失敗
- TimeoutError: タイムアウト

#### リトライポリシー
```
retry_delays = [1, 2, 4, 8, 16]  # 秒
max_retries = 5

retryable_errors = [
  TimeoutError,
  TemporaryLLMError,
  NetworkError
]
```

### 入出力DTO

#### ExperimentConfigDto
```
{
  experiment_name: str
  prompt_name: str
  dataset_name: str
  llm_endpoint: str
  metadata: Optional[Dict[str, Any]]
  parallel_execution: Optional[int]
  retry_count: Optional[int]
}
```

#### ExperimentResultDto
```
{
  experiment_id: str
  status: str
  summary: ExperimentSummaryDto
  errors: List[ErrorDto]
  result_file_path: str
}
```

#### ExperimentSummaryDto
```
{
  total_documents: int
  successful_count: int
  failed_count: int
  overall_accuracy: float
  field_accuracies: Dict[str, float]
  execution_time_ms: int
}
```

### 協調するユースケース
- `CompareExperimentsUseCase`: 実験結果の比較
- `ExportResultsUseCase`: 結果のエクスポート

## 実装時の注意点

### トランザクション管理
- 各ドキュメント処理は独立したトランザクション
- 実験全体の状態更新は別トランザクション

### パフォーマンス最適化
- バッチ処理での効率化
- メモリ使用量の監視
- 大規模データセット対応

### 監視とログ
- 進捗状況のリアルタイム更新
- エラーの詳細ログ
- パフォーマンスメトリクス