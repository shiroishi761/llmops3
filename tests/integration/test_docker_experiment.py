"""Docker環境での実験実行統合テスト"""
import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.application.use_cases.run_experiment import RunExperimentUseCase
from src.infrastructure.external_services.llm_client import LLMClient
from src.domain.exceptions import ExternalServiceError


class TestDockerExperimentIntegration:
    """Docker環境での実験実行統合テスト"""
    
    def test_llm_client_connection_error_handling(self):
        """LLMClientの接続エラーハンドリングテスト"""
        # 存在しないサーバーへの接続をテスト
        client = LLMClient(base_url="http://nonexistent:8000")
        
        with pytest.raises(ExternalServiceError) as exc_info:
            client.extract(
                llm_endpoint="llm/gemini/1.5-flash",
                prompt_name="test_prompt",
                input_data={"key": "value"}
            )
        
        # エラーメッセージに接続エラーが含まれることを確認
        assert "Connection refused" in str(exc_info.value) or "Name or service not known" in str(exc_info.value)
    
    def test_llm_client_with_docker_service_name(self):
        """Docker環境でのサービス名による接続テスト"""
        # 環境変数でAPI_BASE_URLを設定
        with patch.dict(os.environ, {"API_BASE_URL": "http://app:8000"}):
            client = LLMClient()
            assert client.base_url == "http://app:8000"
    
    def test_llm_client_timeout_handling(self):
        """LLMClientのタイムアウトハンドリングテスト"""
        client = LLMClient(base_url="http://localhost:8000")
        
        # httpx.TimeoutExceptionをモック
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.post.side_effect = \
                Exception("Timeout occurred")
            
            with pytest.raises(ExternalServiceError) as exc_info:
                client.extract(
                    llm_endpoint="llm/gemini/1.5-flash",
                    prompt_name="test_prompt",
                    input_data={"key": "value"}
                )
            
            assert "request failed" in str(exc_info.value)
    
    def test_field_result_compatibility(self):
        """FieldResultの互換性テスト"""
        from src.domain.models.field_result import FieldResult
        
        result = FieldResult.create_incorrect(
            field_name="test_field",
            expected="expected",
            actual="actual", 
            weight=2.0
        )
        
        # 必要なメソッドが存在することを確認
        assert hasattr(result, 'score')
        assert hasattr(result, 'is_correct')
        assert result.score == 0.0
        assert result.is_correct == False
    
    def test_experiment_config_validation(self):
        """実験設定ファイルのバリデーションテスト"""
        use_case = RunExperimentUseCase()
        
        # 存在しないファイル
        with pytest.raises(FileNotFoundError):
            use_case._load_experiment_config("nonexistent.yml")
        
        # 不正なYAMLファイル
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            f.flush()
            
            with pytest.raises(Exception):  # YAMLパースエラー
                use_case._load_experiment_config(f.name)
        
        # 必須フィールドが不足
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("""
            experiment_name: "test"
            # prompt_name が不足
            dataset_name: "test_dataset"
            llm_endpoint: "llm/gemini/1.5-flash"
            """)
            f.flush()
            
            with pytest.raises(ValueError, match="必須フィールドがありません"):
                use_case._load_experiment_config(f.name)
    
    def test_experiment_name_not_found(self):
        """存在しない実験名のエラーハンドリングテスト"""
        use_case = RunExperimentUseCase()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("""
            experiments:
              - experiment_name: "existing_experiment"
                prompt_name: "test_prompt"
                dataset_name: "test_dataset"
                llm_endpoint: "llm/gemini/1.5-flash"
            """)
            f.flush()
            
            with pytest.raises(ValueError, match="実験名が見つかりません"):
                use_case._load_experiment_config(f.name, "nonexistent_experiment")
    
    def test_cli_interactive_input_handling(self):
        """CLIの対話的入力のハンドリングテスト"""
        # 実際のCLIテストは複雑なので、入力ハンドリングの基本的なテスト
        from src.cli import generate_report
        
        # 存在しないファイル
        with pytest.raises(SystemExit):
            generate_report("nonexistent.json")
    
    @patch('src.application.use_cases.run_experiment.RunExperimentUseCase.execute')
    def test_run_experiment_error_handling(self, mock_execute):
        """実験実行時のエラーハンドリングテスト"""
        from src.cli import run_experiment
        
        # 実験実行時のエラー
        mock_execute.side_effect = Exception("Test error")
        
        with pytest.raises(SystemExit):
            run_experiment("test_config.yml", "test_experiment")
    
    def test_field_result_score_migration(self):
        """FieldResultスコアへの移行テスト"""
        # 新しいシステムでFieldResultが使われることを確認
        from src.domain.models.field_result import FieldResult
        
        result = FieldResult.create_correct(
            field_name="test",
            expected="expected",
            actual="expected",  # 正解
            weight=3.0
        )
        
        # scoreが正しく計算されることを確認
        assert result.score == 3.0
        assert result.is_correct == True
        
        # 不正解の場合
        result_wrong = FieldResult.create_incorrect(
            field_name="test",
            expected="expected",
            actual="actual",  # 不正解
            weight=3.0
        )
        
        assert result_wrong.score == 0.0
        assert result_wrong.is_correct == False