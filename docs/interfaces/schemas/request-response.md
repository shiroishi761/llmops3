# リクエスト・レスポンススキーマ定義

## 概要
APIのリクエストとレスポンスのスキーマ定義。Pydanticモデルとして実装され、自動バリデーションとOpenAPI仕様生成に使用される。

## 共通スキーマ

### ErrorResponse
```python
class ErrorResponse(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

### MetadataResponse
```python
class MetadataResponse(BaseModel):
    execution_time_ms: int
    endpoint_used: str
    model_version: Optional[str] = None
    trace_id: Optional[str] = None
```

## メインエンドポイントスキーマ

### MainRequest
```python
class MainRequest(BaseModel):
    endpoint: str = Field(..., description="処理エンドポイント名")
    ocr_content: str = Field(..., description="OCR結果（Markdown形式）")
    document_id: str = Field(..., description="文書ID")
    company_name: str = Field(..., description="自社名")
    customers: Dict[str, int] = Field(..., description="顧客マスタ")
    account_items: List[str] = Field(..., description="勘定科目リスト")
    
    class Config:
        schema_extra = {
            "example": {
                "endpoint": "extract_v1",
                "ocr_content": "# 請求書\n\n...",
                "document_id": "doc_001",
                "company_name": "株式会社Example",
                "customers": {"顧客A": 101, "顧客B": 102},
                "account_items": ["外注費", "材料費", "経費"]
            }
        }
```

### ExtractedDataResponse
```python
class LineItemResponse(BaseModel):
    name: str
    quantity: float
    price: float
    sub_total: float
    unit: str = ""
    spec: str = ""
    note: str = ""
    account_item: str = ""
    items: Optional[List['LineItemResponse']] = []

class ExtractedDataResponse(BaseModel):
    # 文書基本情報
    doc_transaction: str
    doc_title: str
    doc_type: Literal["quotation", "invoice", "receipt", "unknown"]
    doc_number: str
    doc_date: str = Field(..., regex="^\d{4}-\d{2}-\d{2}$")
    
    # 取引先情報
    destination: str
    destination_customer_id: int
    issuer: str
    issuer_phone_number: str = ""
    issuer_zip: str = ""
    issuer_customer_id: int
    issuer_address: str = ""
    
    # 金額情報
    t_number: str = ""
    sub_total: str
    tax_price: int
    total_price: int
    tax_type: Literal["external", "internal"]
    
    # 工事情報
    construction_name: str = ""
    construction_site: str = ""
    construction_period: str = ""
    payment_terms: str = ""
    expiration_date: str = ""
    
    # 明細項目
    items: List[LineItemResponse]
```

### MainResponse
```python
class MainResponse(BaseModel):
    status: Literal["success", "error"]
    data: Optional[ExtractedDataResponse] = None
    error: Optional[ErrorResponse] = None
    metadata: Optional[MetadataResponse] = None
```

## 実験関連スキーマ

### ExperimentRunRequest
```python
class ExperimentRunRequest(BaseModel):
    config_path: str = Field(..., description="YML設定ファイルパス")
    
    @validator('config_path')
    def validate_config_path(cls, v):
        if not v.endswith('.yml') and not v.endswith('.yaml'):
            raise ValueError('Config file must be YAML')
        return v
```

### ExperimentStatusResponse
```python
class ExperimentProgress(BaseModel):
    processed: int
    total: int
    percentage: float

class ExperimentSummary(BaseModel):
    total_documents: int
    successful_count: int
    failed_count: int
    overall_accuracy: float
    field_accuracies: Dict[str, float]
    execution_time_ms: int

class ExperimentStatusResponse(BaseModel):
    id: str
    name: str
    status: Literal["pending", "running", "completed", "failed"]
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: Optional[ExperimentProgress] = None
    summary: Optional[ExperimentSummary] = None
    error: Optional[ErrorResponse] = None
```

### ExperimentCompareRequest
```python
class ExperimentCompareRequest(BaseModel):
    experiment_ids: List[str] = Field(..., min_items=2)
    metric: Literal["accuracy", "speed", "success_rate"] = "accuracy"
    include_details: bool = False
```

### ExperimentCompareResponse
```python
class ExperimentMetrics(BaseModel):
    accuracy: float
    speed_ms: float
    success_rate: float

class ExperimentComparison(BaseModel):
    experiment_id: str
    name: str
    rank: int
    metrics: ExperimentMetrics
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None

class ExperimentCompareResponse(BaseModel):
    comparisons: List[ExperimentComparison]
    best_experiment_id: str
    analysis: Optional[str] = None
```

## ヘルスチェックスキーマ

### HealthCheckResponse
```python
class ServiceHealth(BaseModel):
    status: Literal["ok", "error"]
    message: Optional[str] = None
    latency_ms: Optional[int] = None

class HealthCheckResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    uptime_seconds: int
    checks: Dict[str, ServiceHealth]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

## バリデーション詳細

### カスタムバリデーター

#### 顧客マスタ検証
```python
@validator('customers')
def validate_customers(cls, v):
    if not v:
        raise ValueError('Customers must not be empty')
    if any(not isinstance(customer_id, int) for customer_id in v.values()):
        raise ValueError('All customer IDs must be integers')
    return v
```

#### OCRコンテンツ検証
```python
@validator('ocr_content')
def validate_ocr_content(cls, v):
    if len(v.strip()) < 10:
        raise ValueError('OCR content too short')
    if len(v) > 1_000_000:  # 1MB制限
        raise ValueError('OCR content too large')
    return v
```

#### 日付形式検証
```python
@validator('doc_date')
def validate_date_format(cls, v):
    try:
        datetime.strptime(v, '%Y-%m-%d')
    except ValueError:
        raise ValueError('Date must be in YYYY-MM-DD format')
    return v
```

## スキーマ変換

### DTO → スキーマ
```python
def dto_to_response(dto: ExtractedDataDto) -> ExtractedDataResponse:
    return ExtractedDataResponse(
        doc_transaction=dto.doc_transaction,
        doc_title=dto.doc_title,
        # ... 他のフィールド
        items=[
            LineItemResponse(**item.dict())
            for item in dto.items
        ]
    )
```

### スキーマ → DTO
```python
def request_to_dto(request: MainRequest) -> ExtractRequestDto:
    return ExtractRequestDto(
        endpoint=request.endpoint,
        ocr_content=request.ocr_content,
        document_id=request.document_id,
        company_name=request.company_name,
        customers=request.customers,
        account_items=request.account_items
    )
```

## OpenAPI仕様拡張

### タグ定義
```python
tags_metadata = [
    {
        "name": "extraction",
        "description": "文書データ抽出API",
    },
    {
        "name": "experiments",
        "description": "実験管理API",
    },
    {
        "name": "health",
        "description": "ヘルスチェックAPI",
    }
]
```

### レスポンス例
```python
responses = {
    400: {
        "description": "Bad Request",
        "content": {
            "application/json": {
                "example": {
                    "status": "error",
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "Invalid endpoint name"
                    }
                }
            }
        }
    }
}
```

## 実装時の注意点

### パフォーマンス
- 大きなリクエストボディの制限
- ネストが深い構造の検証コスト
- バリデーションの最適化

### セキュリティ
- インジェクション対策
- 機密情報のマスキング
- 入力サイズの制限

### 互換性
- スキーマバージョニング
- 後方互換性の維持
- 非推奨フィールドの管理