# 設定管理

## 概要
アプリケーションの設定を管理するインフラストラクチャ層のコンポーネント。環境変数、設定ファイル、フィールド重みなどを統一的に管理する。

## ConfigurationService

### 責務
- 設定の読み込みと検証
- 環境別設定の管理
- 動的な設定更新
- デフォルト値の提供

### 設定階層
```
1. 環境変数（最優先）
2. 設定ファイル（config.yml）
3. デフォルト値（コード内定義）
```

## 設定ファイル構造

### config.yml（最小構成）
```yaml
# フィールド重み設定
field_weights:
  amount:
    weight: 3.0
    fields:
      - total_price
      - tax_price
      - sub_total
  
  line_items:
    weight: 2.5
    fields:
      - items
  
  customer:
    weight: 2.0
    fields:
      - destination_customer_id
      - issuer_customer_id
  
  default_weight: 1.0
```


## フィールド重み設定

フィールド重み設定は`config.yml`の`field_weights`セクションに統合されました。

## 環境変数

### 必須環境変数
```bash
# API Keys
GEMINI_API_KEY=your-gemini-api-key
LANGFUSE_API_KEY=your-langfuse-api-key
```

### オプション環境変数
```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Gemini Configuration
GEMINI_MODEL=gemini-pro
GEMINI_TEMPERATURE=0.1
GEMINI_MAX_TOKENS=2000

# Langfuse Configuration
LANGFUSE_BASE_URL=https://cloud.langfuse.com
LANGFUSE_CACHE_ENABLED=true

# Storage Configuration
STORAGE_TYPE=file
STORAGE_BASE_PATH=/data/llmops

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## ConfigurationService実装

### 初期化
```python
class ConfigurationService:
    def __init__(self):
        self.config = self._load_config()
```

### 設定読み込み
```python
def _load_config(self) -> Dict:
    # 1. デフォルト設定
    config = self._get_defaults()
    
    # 2. 設定ファイル
    yaml_config = self._read_yaml("config.yml")
    config = deep_merge(config, yaml_config)
    
    # 3. 環境変数で上書き
    config = self._apply_env_vars(config)
    
    # 4. 検証
    self._validate_config(config)
    
    return config
```

### 設定アクセス
```python
def get(self, key: str, default: Any = None) -> Any:
    """
    ドット記法で設定値を取得
    例: config.get("llm.endpoints.extract_v1.temperature")
    """
    return get_nested_value(self.config, key, default)

def get_endpoint_config(self, endpoint: str) -> Dict:
    """エンドポイント別設定を取得"""
    return self.get(f"llm.endpoints.{endpoint}", {})

def get_field_weight(self, field_name: str) -> float:
    """フィールドの重みを取得"""
    field_weights = self.config.get("field_weights", {})
    
    # カテゴリから検索
    for category_name, category in field_weights.items():
        if category_name == "default_weight":
            continue
        if isinstance(category, dict) and field_name in category.get("fields", []):
            return category["weight"]
    
    # デフォルト
    return field_weights.get("default_weight", 1.0)
```

### 動的更新
```python
def reload(self) -> None:
    """設定を再読み込み"""
    self.config = self._load_config()

def update(self, key: str, value: Any) -> None:
    """実行時に設定を更新（一時的）"""
    set_nested_value(self.config, key, value)
```

## 設定の検証

### スキーマ検証
```python
config_schema = {
    "type": "object",
    "required": ["app", "api", "llm"],
    "properties": {
        "app": {
            "type": "object",
            "required": ["name", "version"]
        },
        # ... 他のスキーマ定義
    }
}
```

### カスタム検証
```python
def _validate_config(self, config: Dict) -> None:
    # 必須項目チェック
    if not config.get("llm", {}).get("endpoints"):
        raise ConfigurationError("No LLM endpoints defined")
    
    # 値の範囲チェック
    for endpoint in config["llm"]["endpoints"].values():
        if not 0 <= endpoint.get("temperature", 0) <= 1:
            raise ConfigurationError("Temperature must be between 0 and 1")
```

## 使用例

### アプリケーションでの使用
```python
# 初期化
config_service = ConfigurationService()

# 設定値の取得
api_port = config_service.get("api.port", 8000)
gemini_key = config_service.get("gemini.api_key")

# エンドポイント設定
endpoint_config = config_service.get_endpoint_config("extract_v1")

# フィールド重み
weight = config_service.get_field_weight("total_price")
```

## ベストプラクティス

### 1. 機密情報の管理
- APIキーは環境変数で管理
- 設定ファイルには含めない

### 2. バリデーション
- 起動時に設定を検証
- 不正な設定で起動しない
- エラーメッセージを明確に

### 3. ドキュメント
- すべての設定項目を文書化
- デフォルト値を明記
- 変更時の影響を記載