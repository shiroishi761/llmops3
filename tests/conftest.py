"""pytest設定とフィクスチャ"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock

@pytest.fixture
def mock_env(monkeypatch):
    """テスト用環境変数"""
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "test-public-key")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "test-secret-key")
    

@pytest.fixture
def test_config_file(tmp_path):
    """テスト用設定ファイル"""
    config_content = """
field_weights:
  amount:
    weight: 3.0
    fields:
      - total_price
      - tax_price
  customer:
    weight: 2.0
    fields:
      - customer_id
  default_weight: 1.0
"""
    config_path = tmp_path / "config.yml"
    config_path.write_text(config_content)
    return str(config_path)


@pytest.fixture
def sample_experiment_config(tmp_path):
    """テスト用実験設定"""
    config_content = """
experiment_name: テスト実験
prompt_name: test_prompt
dataset_name: test_dataset
llm_endpoint: extract_v1
description: テスト用の実験
"""
    config_path = tmp_path / "test_experiment.yml"
    config_path.write_text(config_content)
    return str(config_path)


@pytest.fixture
def mock_langfuse_response():
    """Langfuseレスポンスのモック"""
    return {
        "prompt": "Extract data from: {document}",
        "dataset": [
            {
                "id": "item-1",
                "document": "請求書 #12345\\n合計: 10,000円",
                "expected": {
                    "invoice_number": "12345",
                    "total_price": "10000"
                }
            }
        ]
    }


@pytest.fixture
def mock_gemini_response():
    """Geminiレスポンスのモック"""
    return {
        "data": {
            "invoice_number": "12345",
            "total_price": "10000"
        },
        "execution_time_ms": 500,
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150
        }
    }