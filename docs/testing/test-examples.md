# テスト実装例

## ドメイン層のテスト例

### Experimentエンティティのテスト
```python
# tests/unit/domain/models/test_experiment.py
import pytest
from datetime import datetime
from src.domain.models.experiment import Experiment, ExperimentStatus
from src.domain.models.extraction_result import ExtractionResult
from src.domain.models.accuracy_metric import AccuracyMetric

class TestExperiment:
    def test_create_experiment(self):
        """実験エンティティの作成テスト"""
        experiment = Experiment(
            id="exp-001",
            name="請求書抽出テスト",
            prompt_name="invoice_prompt_v1",
            dataset_name="invoice_dataset_202401",
            llm_endpoint="extract_v1",
            created_at=datetime.now()
        )
        
        assert experiment.id == "exp-001"
        assert experiment.status == ExperimentStatus.PENDING
        assert len(experiment.results) == 0
        
    def test_add_extraction_result(self):
        """抽出結果の追加テスト"""
        experiment = Experiment(
            id="exp-001",
            name="テスト実験"
        )
        
        result = ExtractionResult(
            document_id="doc-001",
            expected_data={"total_price": "1000"},
            extracted_data={"total_price": "1000"},
            accuracy_metrics=[
                AccuracyMetric("total_price", "1000", "1000", 3.0)
            ]
        )
        
        experiment.add_result(result)
        
        assert len(experiment.results) == 1
        assert experiment.results[0].document_id == "doc-001"
        
    def test_calculate_overall_accuracy(self):
        """全体精度計算のテスト"""
        experiment = Experiment(id="exp-001", name="テスト")
        
        # 100%正解のケース
        result1 = ExtractionResult(
            document_id="doc-001",
            accuracy_metrics=[
                AccuracyMetric("total_price", "1000", "1000", 3.0),
                AccuracyMetric("customer_id", "C001", "C001", 2.0)
            ]
        )
        
        # 部分的に正解のケース
        result2 = ExtractionResult(
            document_id="doc-002",
            accuracy_metrics=[
                AccuracyMetric("total_price", "2000", "2000", 3.0),
                AccuracyMetric("customer_id", "C002", "C003", 2.0)  # 不一致
            ]
        )
        
        experiment.add_result(result1)
        experiment.add_result(result2)
        
        accuracy = experiment.calculate_overall_accuracy()
        
        # (3.0 + 2.0 + 3.0 + 0.0) / (3.0 + 2.0 + 3.0 + 2.0) = 8.0 / 10.0 = 0.8
        assert accuracy == 0.8
```

### AccuracyEvaluationServiceのテスト
```python
# tests/unit/domain/services/test_accuracy_evaluation_service.py
import pytest
from src.domain.services.accuracy_evaluation_service import AccuracyEvaluationService
from src.domain.models.accuracy_metric import AccuracyMetric

class TestAccuracyEvaluationService:
    def setup_method(self):
        self.service = AccuracyEvaluationService()
        self.field_weights = {
            "total_price": 3.0,
            "customer_id": 2.0,
            "items": 2.5
        }
        
    def test_evaluate_extraction_exact_match(self):
        """完全一致の評価テスト"""
        expected = {
            "total_price": "10000",
            "customer_id": "C12345",
            "items": [{"name": "商品A", "price": "5000"}]
        }
        actual = expected.copy()
        
        metrics = self.service.evaluate_extraction(
            expected, actual, self.field_weights
        )
        
        assert len(metrics) == 3
        assert all(metric.is_correct() for metric in metrics)
        
    def test_evaluate_extraction_with_errors(self):
        """エラーがある場合の評価テスト"""
        expected = {
            "total_price": "10000",
            "customer_id": "C12345"
        }
        actual = {
            "total_price": "10000",
            "customer_id": "C54321"  # 不一致
        }
        
        metrics = self.service.evaluate_extraction(
            expected, actual, self.field_weights
        )
        
        assert metrics[0].is_correct() == True   # total_price
        assert metrics[1].is_correct() == False  # customer_id
        
    def test_evaluate_missing_fields(self):
        """欠損フィールドの評価テスト"""
        expected = {
            "total_price": "10000",
            "customer_id": "C12345"
        }
        actual = {
            "total_price": "10000"
            # customer_id が欠損
        }
        
        metrics = self.service.evaluate_extraction(
            expected, actual, self.field_weights
        )
        
        customer_metric = next(m for m in metrics if m.field_name == "customer_id")
        assert customer_metric.is_correct() == False
        assert customer_metric.actual_value is None
```

## アプリケーション層のテスト例

### RunExperimentUseCaseのテスト
```python
# tests/unit/application/use_cases/test_run_experiment_use_case.py
import pytest
from unittest.mock import Mock, patch
from src.application.use_cases.run_experiment import RunExperimentUseCase
from src.application.dto.experiment_dto import ExperimentConfigDto

class TestRunExperimentUseCase:
    def setup_method(self):
        self.use_case = RunExperimentUseCase()
        
    @patch('src.infrastructure.external_services.langfuse_service.LangfuseService')
    @patch('src.infrastructure.external_services.gemini_service.GeminiService')
    def test_execute_success(self, mock_gemini, mock_langfuse):
        """正常実行のテスト"""
        # モックの設定
        mock_langfuse_instance = mock_langfuse.return_value
        mock_langfuse_instance.get_prompt.return_value = "Extract: {document}"
        mock_langfuse_instance.get_dataset.return_value = [
            {
                "id": "item-1",
                "document": "請求書内容...",
                "expected": {"total_price": "10000"}
            }
        ]
        
        mock_gemini_instance = mock_gemini.return_value
        mock_gemini_instance.extract.return_value = {"total_price": "10000"}
        
        # 実行
        config = ExperimentConfigDto(
            experiment_name="テスト実験",
            prompt_name="test_prompt",
            dataset_name="test_dataset",
            llm_endpoint="extract_v1"
        )
        
        result = self.use_case.execute_from_config(config)
        
        # 検証
        assert result.status == "completed"
        assert result.summary.total_documents == 1
        assert result.summary.successful_count == 1
        assert result.summary.overall_accuracy == 1.0
        
    @patch('src.infrastructure.external_services.langfuse_service.LangfuseService')
    def test_execute_with_invalid_prompt(self, mock_langfuse):
        """無効なプロンプトでのエラーテスト"""
        mock_langfuse_instance = mock_langfuse.return_value
        mock_langfuse_instance.get_prompt.side_effect = Exception("Prompt not found")
        
        config = ExperimentConfigDto(
            experiment_name="テスト実験",
            prompt_name="invalid_prompt",
            dataset_name="test_dataset",
            llm_endpoint="extract_v1"
        )
        
        with pytest.raises(Exception) as exc_info:
            self.use_case.execute_from_config(config)
            
        assert "Prompt not found" in str(exc_info.value)
```

## インフラストラクチャ層のテスト例

### ConfigurationServiceのテスト
```python
# tests/unit/infrastructure/config/test_configuration_service.py
import pytest
import tempfile
import yaml
from src.infrastructure.config.configuration_service import ConfigurationService

class TestConfigurationService:
    def test_load_config_file(self):
        """設定ファイル読み込みのテスト"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            config_data = {
                'field_weights': {
                    'amount': {
                        'weight': 3.0,
                        'fields': ['total_price']
                    },
                    'default_weight': 1.0
                }
            }
            yaml.dump(config_data, f)
            config_path = f.name
            
        service = ConfigurationService(config_path)
        
        assert service.get_field_weight('total_price') == 3.0
        assert service.get_field_weight('unknown_field') == 1.0
        
    def test_environment_variable_override(self, monkeypatch):
        """環境変数による上書きテスト"""
        monkeypatch.setenv('GEMINI_API_KEY', 'test-key-123')
        
        service = ConfigurationService()
        
        assert service.get('gemini_api_key') == 'test-key-123'
```

### FileExperimentRepositoryのテスト
```python
# tests/unit/infrastructure/repositories/test_file_experiment_repository.py
import pytest
import tempfile
import json
from datetime import datetime
from src.infrastructure.repositories.file_experiment_repository import FileExperimentRepository
from src.domain.models.experiment import Experiment

class TestFileExperimentRepository:
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repository = FileExperimentRepository(self.temp_dir)
        
    def test_save_experiment(self):
        """実験結果の保存テスト"""
        experiment = Experiment(
            id="exp-001",
            name="テスト実験",
            created_at=datetime.now()
        )
        
        file_path = self.repository.save(experiment)
        
        assert file_path.exists()
        
        with open(file_path) as f:
            data = json.load(f)
            assert data['id'] == "exp-001"
            assert data['name'] == "テスト実験"
            
    def test_load_experiment(self):
        """実験結果の読み込みテスト"""
        # まず保存
        experiment = Experiment(id="exp-001", name="テスト実験")
        file_path = self.repository.save(experiment)
        
        # 読み込み
        loaded = self.repository.load(file_path)
        
        assert loaded.id == experiment.id
        assert loaded.name == experiment.name
```

## 統合テストの例

### 実験フロー全体のテスト
```python
# tests/integration/test_experiment_integration.py
import pytest
import os
from src.application.use_cases.run_experiment import RunExperimentUseCase

@pytest.mark.integration
class TestExperimentIntegration:
    def test_full_experiment_flow(self, test_langfuse_setup, test_config):
        """実験の完全なフローテスト（実際の外部サービスを使用）"""
        # テスト用のLangfuseデータをセットアップ
        # （test_langfuse_setupフィクスチャで事前準備）
        
        use_case = RunExperimentUseCase()
        result = use_case.execute("tests/fixtures/integration_test.yml")
        
        # 結果の検証
        assert result.status == "completed"
        assert os.path.exists(result.result_file_path)
        
        # 詳細な結果の確認
        with open(result.result_file_path) as f:
            data = json.load(f)
            assert len(data['results']) > 0
            assert 'overall_accuracy' in data['summary']
```

## テストフィクスチャの例

### conftest.py
```python
# tests/conftest.py
import pytest
import os
from unittest.mock import Mock

@pytest.fixture
def mock_env(monkeypatch):
    """テスト用環境変数"""
    monkeypatch.setenv('GEMINI_API_KEY', 'test-gemini-key')
    monkeypatch.setenv('LANGFUSE_PUBLIC_KEY', 'test-public-key')
    monkeypatch.setenv('LANGFUSE_SECRET_KEY', 'test-secret-key')
    
@pytest.fixture
def field_weights():
    """テスト用フィールド重み"""
    return {
        'total_price': 3.0,
        'customer_id': 2.0,
        'items': 2.5,
        'default_weight': 1.0
    }
    
@pytest.fixture
def sample_experiment_config():
    """テスト用実験設定"""
    return {
        'experiment_name': 'テスト実験',
        'prompt_name': 'test_prompt',
        'dataset_name': 'test_dataset',
        'llm_endpoint': 'extract_v1'
    }
    
@pytest.fixture
def mock_langfuse_response():
    """Langfuseレスポンスのモック"""
    return {
        'prompt': 'Extract data from: {document}',
        'dataset': [
            {
                'id': 'item-1',
                'document': 'Invoice #12345\nTotal: $1000',
                'expected': {
                    'invoice_number': '12345',
                    'total_price': '1000'
                }
            }
        ]
    }
```