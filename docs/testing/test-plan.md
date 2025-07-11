# テスト計画

## 概要

LLMOps精度検証プラットフォームのテスト計画書。4層アーキテクチャ（DDD）に基づいたテスト戦略を定義します。

## テスト方針

### 基本方針
- 各層は独立してテスト可能
- ドメイン層は外部依存なしでテスト
- 外部サービスはモックを使用
- テストピラミッドの原則に従う（ユニットテスト > 統合テスト > E2Eテスト）

### テストカバレッジ目標
- ドメイン層: 90%以上
- アプリケーション層: 80%以上
- インフラストラクチャ層: 70%以上
- 全体: 80%以上

## テスト構成

```
tests/
├── unit/                    # ユニットテスト
│   ├── domain/             # ドメイン層のテスト
│   ├── application/        # アプリケーション層のテスト
│   └── infrastructure/     # インフラストラクチャ層のテスト
├── integration/            # 統合テスト
│   ├── external_services/  # 外部サービス連携テスト
│   └── use_cases/         # ユースケース統合テスト
├── e2e/                    # エンドツーエンドテスト
├── fixtures/               # テストデータ
└── conftest.py            # pytest設定

```

## 層別テスト計画

### 1. ドメイン層テスト

#### テスト対象
- エンティティ（Experiment, ExtractionResult）
- 値オブジェクト（AccuracyMetric, ExperimentStatus）
- ドメインサービス（AccuracyEvaluationService, ExperimentManagementService）

#### テスト例
```python
# tests/unit/domain/test_accuracy_metric.py
def test_accuracy_metric_calculation():
    """精度計算のテスト"""
    metric = AccuracyMetric(
        field_name="total_price",
        expected_value="1000",
        actual_value="1000",
        weight=3.0
    )
    assert metric.is_correct() == True
    assert metric.weighted_score() == 3.0

def test_accuracy_metric_with_error():
    """不一致時の精度計算テスト"""
    metric = AccuracyMetric(
        field_name="total_price",
        expected_value="1000",
        actual_value="2000",
        weight=3.0
    )
    assert metric.is_correct() == False
    assert metric.weighted_score() == 0.0
```

### 2. アプリケーション層テスト

#### テスト対象
- ユースケース（RunExperimentUseCase, ExtractDocumentUseCase）
- DTO変換

#### テスト例
```python
# tests/unit/application/test_run_experiment_use_case.py
def test_run_experiment_use_case(mock_langfuse, mock_gemini):
    """実験実行ユースケースのテスト"""
    # モックの設定
    mock_langfuse.get_prompt.return_value = "Extract data from {document}"
    mock_langfuse.get_dataset.return_value = [
        {"document": "invoice1.pdf", "expected": {...}}
    ]
    mock_gemini.extract.return_value = {"total_price": "1000"}
    
    # 実行
    use_case = RunExperimentUseCase()
    result = use_case.execute("experiments/test.yml")
    
    # 検証
    assert result.status == "completed"
    assert result.summary.total_documents == 1
```

### 3. インフラストラクチャ層テスト

#### テスト対象
- 外部サービス連携（LangfuseService, GeminiService）
- リポジトリ実装（FileExperimentRepository）
- 設定管理（ConfigurationService）

#### テスト例
```python
# tests/unit/infrastructure/test_langfuse_service.py
def test_langfuse_service_get_prompt(mock_langfuse_client):
    """Langfuseからプロンプト取得のテスト"""
    mock_langfuse_client.get_prompt.return_value = Mock(
        compile=lambda: "Test prompt"
    )
    
    service = LangfuseService()
    prompt = service.get_prompt("test_prompt")
    
    assert prompt == "Test prompt"
```

### 4. 統合テスト

#### テスト対象
- 複数層にまたがる処理フロー
- 外部サービスとの実際の連携（テスト環境）

#### テスト例
```python
# tests/integration/test_experiment_flow.py
@pytest.mark.integration
def test_complete_experiment_flow():
    """実験の完全なフローテスト"""
    # 実際のLangfuseテスト環境を使用
    config_path = "tests/fixtures/test_experiment.yml"
    
    use_case = RunExperimentUseCase()
    result = use_case.execute(config_path)
    
    # 結果ファイルの確認
    assert os.path.exists(result.result_file_path)
    
    # 結果の検証
    with open(result.result_file_path) as f:
        data = json.load(f)
        assert data["experiment_name"] == "テスト実験"
```

### 5. E2Eテスト

#### テスト対象
- CLIからの実験実行
- API経由の実験実行（将来実装時）

#### テスト例
```python
# tests/e2e/test_cli.py
def test_cli_run_experiment():
    """CLIから実験実行のテスト"""
    result = subprocess.run(
        ["python", "-m", "src.cli", "run-experiment", "tests/fixtures/test.yml"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert "実験が完了しました" in result.stdout
```

## テストデータ管理

### fixtures/ディレクトリ構成
```
tests/fixtures/
├── test_experiment.yml      # テスト用実験設定
├── mock_responses/         # モックレスポンスデータ
│   ├── langfuse/
│   └── gemini/
└── expected_results/       # 期待される結果データ
```

### テストデータの原則
- 本番データは使用しない
- 最小限のデータで最大限のケースをカバー
- エッジケースを含む

## モック戦略

### 外部サービスのモック
```python
# tests/conftest.py
@pytest.fixture
def mock_langfuse(mocker):
    """Langfuseサービスのモック"""
    return mocker.patch('src.infrastructure.external_services.langfuse.Langfuse')

@pytest.fixture
def mock_gemini(mocker):
    """Gemini APIのモック"""
    return mocker.patch('src.infrastructure.external_services.gemini.genai')
```

### 環境変数のモック
```python
@pytest.fixture
def test_env(monkeypatch):
    """テスト用環境変数"""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "test-public-key")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "test-secret-key")
```

## テスト実行

### ローカル実行
```bash
# 全テスト実行
pytest

# ユニットテストのみ
pytest tests/unit/

# カバレッジ付き
pytest --cov=src --cov-report=html

# 特定のマーカーのみ
pytest -m "not integration"
```

### Docker実行
```bash
# 全テスト
make test

# 特定のテスト
docker-compose run --rm app pytest tests/unit/domain/
```

## CI/CD統合

### GitHub Actions設定例
```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          docker-compose build
          docker-compose run --rm app pytest --cov=src
```

## テストのベストプラクティス

### 1. テストの命名規則
- `test_[対象]_[条件]_[期待結果]`
- 例: `test_accuracy_metric_with_matching_values_returns_correct`

### 2. テストの構成（AAA）
- Arrange: テストデータの準備
- Act: テスト対象の実行
- Assert: 結果の検証

### 3. テストの独立性
- 各テストは他のテストに依存しない
- テスト順序に依存しない
- テスト後のクリーンアップ

### 4. テストの速度
- ユニットテストは高速に（< 1秒）
- 外部依存はモックを使用
- 統合テストは必要最小限に

## 段階的なテスト実装計画

### フェーズ1: 基本的なユニットテスト（初期実装）
1. ドメイン層の主要モデルのテスト
2. 精度計算ロジックのテスト
3. 基本的なユースケースのテスト

### フェーズ2: 統合テストの追加
1. 外部サービス連携のテスト
2. ファイル入出力のテスト
3. 設定管理のテスト

### フェーズ3: E2Eテストとカバレッジ向上
1. CLIの完全なテスト
2. エラーケースの網羅
3. パフォーマンステストの追加