"""HTMLレポート生成のユニットテスト"""

import json
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

from src.infrastructure.report.html_report_generator import HTMLReportGenerator


class TestHTMLReportGenerator:
    """HTMLReportGeneratorのテスト"""
    
    @pytest.fixture
    def generator(self, tmp_path):
        """テスト用のレポートジェネレーター"""
        return HTMLReportGenerator(output_dir=tmp_path / "reports")
    
    @pytest.fixture
    def sample_experiment_data(self):
        """サンプル実験データ"""
        return {
            "id": "exp-123",
            "name": "テスト実験",
            "prompt_name": "test_prompt_v1",
            "dataset_name": "test_dataset",
            "llm_endpoint": "test_endpoint",
            "status": "completed",
            "created_at": "2024-01-15T10:00:00Z",
            "completed_at": "2024-01-15T10:30:00Z",
            "results": [
                {
                    "document_id": "doc-1",
                    "is_success": True,
                    "accuracy": 0.85,
                    "expected_data": {
                        "doc_type": "請求書",
                        "total_price": 10000,
                        "items": [
                            {"name": "商品A", "quantity": 2, "price": 5000, "sub_total": 10000}
                        ]
                    },
                    "extracted_data": {
                        "doc_type": "請求書",
                        "total_price": 10000,
                        "items": [
                            {"name": "商品A", "quantity": 2, "price": 5000, "sub_total": 10000}
                        ]
                    },
                    "accuracy_metrics": [
                        {
                            "field_name": "doc_type",
                            "expected_value": "請求書",
                            "actual_value": "請求書",
                            "weight": 1.0,
                            "is_correct": True,
                            "field_score": 1.0
                        },
                        {
                            "field_name": "total_price",
                            "expected_value": 10000,
                            "actual_value": 10000,
                            "weight": 3.0,
                            "is_correct": True,
                            "field_score": 3.0
                        }
                    ]
                }
            ],
            "summary": {
                "total_documents": 1,
                "successful_count": 1,
                "failed_count": 0,
                "overall_accuracy": 0.85,
                "field_accuracies": {
                    "doc_type": 1.0,
                    "total_price": 1.0
                }
            }
        }
    
    def test_generate_creates_html_file(self, generator, sample_experiment_data):
        """HTMLファイルが生成されることを確認"""
        # 実行
        output_path = generator.generate(sample_experiment_data)
        
        # 検証
        assert Path(output_path).exists()
        assert output_path.endswith(".html")
        
        # HTMLの内容を確認
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "テスト実験" in content
            assert "test_prompt_v1" in content
            assert "85.0%" in content  # 精度
    
    def test_generate_from_result_file(self, generator, tmp_path, sample_experiment_data):
        """結果ファイルからHTMLを生成できることを確認"""
        # 結果ファイルを作成
        result_file = tmp_path / "test_result.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(sample_experiment_data, f)
        
        # 実行
        output_path = generator.generate_from_result_file(str(result_file))
        
        # 検証
        assert Path(output_path).exists()
    
    def test_items_parsing(self, generator, sample_experiment_data):
        """itemsフィールドが正しくパースされることを確認"""
        # itemsをJSON文字列として設定
        sample_experiment_data["results"][0]["expected_data"]["items"] = json.dumps([
            {"name": "商品B", "quantity": 3}
        ])
        
        # 実行
        output_path = generator.generate(sample_experiment_data)
        
        # HTMLの内容を確認
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "商品B" in content
    
    def test_error_handling(self, generator, sample_experiment_data):
        """エラーが含まれる結果でも正しく表示されることを確認"""
        # エラーデータを追加
        sample_experiment_data["results"].append({
            "document_id": "doc-2",
            "is_success": False,
            "error_message": "LLM API エラー",
            "accuracy": 0.0
        })
        
        # 実行
        output_path = generator.generate(sample_experiment_data)
        
        # HTMLの内容を確認
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "LLM API エラー" in content
    
    def test_sanitize_filename(self, generator):
        """ファイル名のサニタイズが正しく動作することを確認"""
        # 特殊文字を含む実験名
        data = {
            "name": "実験/テスト:2024*",
            "results": [],
            "summary": {
                "total_documents": 0,
                "successful_count": 0,
                "failed_count": 0,
                "overall_accuracy": 0
            }
        }
        
        # 実行
        output_path = generator.generate(data)
        
        # ファイル名に特殊文字が含まれていないことを確認
        filename = Path(output_path).name
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            assert char not in filename