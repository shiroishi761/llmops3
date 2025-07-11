"""Experimentエンティティのテスト"""
import pytest
from datetime import datetime
from src.domain.models.experiment import Experiment, ExperimentStatus
from src.domain.models.extraction_result import ExtractionResult
from src.domain.models.field_result import FieldResult


class TestExperiment:
    def test_create_experiment(self):
        """実験エンティティの作成テスト"""
        experiment = Experiment(
            id="exp-001",
            name="請求書抽出テスト",
            prompt_name="invoice_prompt_v1",
            dataset_name="invoice_dataset_202401",
            llm_endpoint="extract_v1"
        )
        
        assert experiment.id == "exp-001"
        assert experiment.name == "請求書抽出テスト"
        assert experiment.status == ExperimentStatus.PENDING
        assert len(experiment.results) == 0
        assert experiment.completed_at is None
    
    def test_add_extraction_result(self):
        """抽出結果の追加テスト"""
        experiment = Experiment(id="exp-001", name="テスト実験")
        
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
    
    def test_status_transitions(self):
        """ステータス遷移のテスト"""
        experiment = Experiment(id="exp-001", name="テスト")
        
        # 初期状態
        assert experiment.status == ExperimentStatus.PENDING
        
        # 実行中に変更
        experiment.mark_as_running()
        assert experiment.status == ExperimentStatus.RUNNING
        
        # 完了に変更
        experiment.mark_as_completed()
        assert experiment.status == ExperimentStatus.COMPLETED
        assert experiment.completed_at is not None
    
    def test_mark_as_failed(self):
        """失敗状態へのテスト"""
        experiment = Experiment(id="exp-001", name="テスト")
        
        experiment.mark_as_failed("API接続エラー")
        
        assert experiment.status == ExperimentStatus.FAILED
        assert experiment.metadata["error"] == "API接続エラー"
        assert experiment.completed_at is not None
    
    def test_calculate_overall_accuracy(self):
        """全体精度計算のテスト"""
        experiment = Experiment(id="exp-001", name="テスト")
        
        # 100%正解のケース
        result1 = ExtractionResult(
            document_id="doc-001",
            expected_data={"total_price": "1000", "customer_id": "C001"},
            extracted_data={"total_price": "1000", "customer_id": "C001"},
            accuracy_metrics=[
                AccuracyMetric("total_price", "1000", "1000", 3.0),
                AccuracyMetric("customer_id", "C001", "C001", 2.0)
            ]
        )
        
        # 部分的に正解のケース
        result2 = ExtractionResult(
            document_id="doc-002",
            expected_data={"total_price": "2000", "customer_id": "C002"},
            extracted_data={"total_price": "2000", "customer_id": "C003"},
            accuracy_metrics=[
                AccuracyMetric("total_price", "2000", "2000", 3.0),
                AccuracyMetric("customer_id", "C002", "C003", 2.0)
            ]
        )
        
        experiment.add_result(result1)
        experiment.add_result(result2)
        
        accuracy = experiment.calculate_overall_accuracy()
        
        # result1: 100% (5.0/5.0)
        # result2: 60% (3.0/5.0)
        # 平均: 80%
        assert accuracy == 0.8
    
    def test_calculate_field_accuracies(self):
        """フィールド別精度計算のテスト"""
        experiment = Experiment(id="exp-001", name="テスト")
        
        # 3つの結果を追加
        results = [
            ExtractionResult(
                document_id=f"doc-{i}",
                expected_data={"total_price": "1000", "customer_id": "C001"},
                extracted_data={"total_price": "1000", "customer_id": "C001" if i < 2 else "C002"},
                accuracy_metrics=[
                    AccuracyMetric("total_price", "1000", "1000", 3.0),
                    AccuracyMetric("customer_id", "C001", "C001" if i < 2 else "C002", 2.0)
                ]
            )
            for i in range(3)
        ]
        
        for result in results:
            experiment.add_result(result)
        
        field_accuracies = experiment.calculate_field_accuracies()
        
        # total_price: 3/3 = 100%
        assert field_accuracies["total_price"] == 1.0
        
        # customer_id: 2/3 = 66.7%
        assert field_accuracies["customer_id"] == pytest.approx(2/3)
    
    def test_get_summary(self):
        """サマリー取得のテスト"""
        experiment = Experiment(id="exp-001", name="テスト")
        experiment.mark_as_running()
        
        # 成功と失敗の結果を追加
        success_result = ExtractionResult(
            document_id="doc-001",
            expected_data={"total_price": "1000"},
            extracted_data={"total_price": "1000"},
            accuracy_metrics=[AccuracyMetric("total_price", "1000", "1000", 3.0)]
        )
        
        failed_result = ExtractionResult(
            document_id="doc-002",
            expected_data={"total_price": "2000"},
            extracted_data={},
            error="抽出エラー"
        )
        
        experiment.add_result(success_result)
        experiment.add_result(failed_result)
        experiment.mark_as_completed()
        
        summary = experiment.get_summary()
        
        assert summary["total_documents"] == 2
        assert summary["successful_count"] == 1
        assert summary["failed_count"] == 1
        assert summary["status"] == "completed"
        assert summary["execution_time_ms"] is not None