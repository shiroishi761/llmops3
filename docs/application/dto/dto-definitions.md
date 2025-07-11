# DTO（Data Transfer Object）定義

## 概要
アプリケーション層で使用されるデータ転送オブジェクトの定義。層間のデータ受け渡しに使用する。

## 基本原則
1. **不変性**: DTOは作成後に変更されない
2. **シンプル**: ビジネスロジックを含まない
3. **シリアライズ可能**: JSON等への変換が可能
4. **検証**: 基本的な型検証のみ

## 共通DTO

### ErrorDto
```
{
  code: str
  message: str
  details: Optional[Dict[str, Any]]
  timestamp: datetime
}
```

### PaginationDto
```
{
  page: int
  page_size: int
  total_items: int
  total_pages: int
}
```

### DateRangeDto
```
{
  start_date: date
  end_date: date
}
```

## 実験関連DTO

### ExperimentConfigDto
```
{
  experiment_name: str
  prompt_name: str
  dataset_name: str
  llm_endpoint: str
  metadata: Optional[Dict[str, Any]]
  parallel_execution: Optional[int] = 5
  retry_count: Optional[int] = 5
  timeout_seconds: Optional[int] = 120
}
```

### ExperimentResultDto
```
{
  experiment_id: str
  name: str
  status: str  # "pending" | "running" | "completed" | "failed"
  created_at: datetime
  executed_at: Optional[datetime]
  summary: Optional[ExperimentSummaryDto]
  errors: List[ErrorDto]
  result_file_path: Optional[str]
}
```

### ExperimentSummaryDto
```
{
  total_documents: int
  successful_count: int
  failed_count: int
  overall_accuracy: float
  field_accuracies: Dict[str, float]
  total_execution_time_ms: int
  average_execution_time_ms: float
}
```

### DocumentResultDto
```
{
  document_id: str
  status: str  # "success" | "failed"
  accuracy: Optional[AccuracyMetricDto]  # 成功時のみ
  execution_time_ms: int
  retry_count: int
  error: Optional[ErrorDto]  # 失敗時のみ
}
```

### AccuracyMetricDto
```
{
  overall_score: float  # 0.0-1.0
  field_scores: Dict[str, float]
  weighted_score: float
}
```

## 抽出関連DTO

### ExtractRequestDto
```
{
  endpoint: str
  ocr_content: str
  document_id: str
  company_name: str
  customers: Dict[str, int]  # {customer_name: customer_id}
  account_items: List[str]
  request_id: Optional[str]
  trace_id: Optional[str]
}
```

### ExtractResponseDto
```
{
  status: str  # "success" | "error"
  data: Optional[ExtractedDataDto]
  error: Optional[ErrorDto]
  metadata: ResponseMetadataDto
}
```

### ExtractedDataDto
```
{
  # 文書基本情報
  doc_transaction: str
  doc_title: str
  doc_type: str  # "quotation" | "invoice" | "receipt" | "unknown"
  doc_number: str
  doc_date: str  # yyyy-mm-dd
  
  # 取引先情報
  destination: str
  destination_customer_id: int
  issuer: str
  issuer_phone_number: str
  issuer_zip: str
  issuer_customer_id: int
  issuer_address: str
  
  # 金額情報
  t_number: str
  sub_total: str
  tax_price: int
  total_price: int
  tax_type: str  # "external" | "internal"
  
  # 工事情報
  construction_name: str
  construction_site: str
  construction_period: str
  payment_terms: str
  expiration_date: str
  
  # 明細項目
  items: List[LineItemDto]
}
```

### LineItemDto
```
{
  name: str
  quantity: float
  price: float
  sub_total: float
  unit: str
  spec: str
  note: str
  account_item: str
  items: Optional[List[LineItemDto]]  # 階層構造
}
```

### ResponseMetadataDto
```
{
  execution_time_ms: int
  llm_model: str
  prompt_version: str
  endpoint_used: str
  retry_count: int
  trace_url: Optional[str]
}
```

## 比較関連DTO

### ComparisonCriteriaDto
```
{
  primary_metric: str  # "accuracy" | "speed" | "success_rate"
  secondary_metrics: List[str]
  weights: Dict[str, float]
  minimum_thresholds: Optional[Dict[str, float]]
}
```

### ComparisonResultDto
```
{
  comparison_id: str
  compared_at: datetime
  criteria: ComparisonCriteriaDto
  experiments: List[ExperimentComparisonDto]
  best_experiment: ExperimentSummaryDto
  analysis: AnalysisDto
}
```

### ExperimentComparisonDto
```
{
  experiment_id: str
  name: str
  rank: int
  overall_score: float
  metrics: Dict[str, MetricDto]
  strengths: List[str]
  weaknesses: List[str]
}
```

### MetricDto
```
{
  name: str
  value: float
  unit: str
  normalized_value: float  # 0.0-1.0
}
```

### AnalysisDto
```
{
  summary: str
  recommendations: List[str]
  trends: List[TrendDto]
  insights: List[str]
}
```

### TrendDto
```
{
  metric_name: str
  direction: str  # "improving" | "declining" | "stable"
  change_rate: float
  period: DateRangeDto
}
```

## 検証関連DTO

### ValidationResultDto
```
{
  is_valid: bool
  errors: List[ValidationErrorDto]
  warnings: List[str]
}
```

### ValidationErrorDto
```
{
  field: str
  message: str
  value: Any
}
```

## 変換規則

### ドメインモデル → DTO
```python
# 例: Experiment → ExperimentResultDto
def to_dto(experiment: Experiment) -> ExperimentResultDto:
    return ExperimentResultDto(
        experiment_id=experiment.id,
        name=experiment.name,
        status=experiment.status.value,
        # ... その他のフィールド
    )
```

### DTO → ドメインモデル
```python
# 例: ExtractedDataDto → ExtractionResult
def to_domain(dto: ExtractedDataDto) -> ExtractionResult:
    return ExtractionResult(
        document_type=DocumentType(dto.doc_type),
        # ... その他のフィールド
    )
```

## 実装時の注意点

### バリデーション
- 型の一致確認
- 必須フィールドの存在確認
- 値の範囲確認

### シリアライゼーション
- 日付型の文字列変換
- Enumの値変換
- ネストした構造の処理

### パフォーマンス
- 大量データ時のメモリ効率
- 遅延読み込みの検討