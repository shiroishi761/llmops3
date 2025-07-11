"""ファイルベースの実験リポジトリ"""
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from ...domain.models.experiment import Experiment, ExperimentStatus
from ...domain.models.extraction_result import ExtractionResult
from ...domain.models.field_result import FieldResult
from ...domain.repositories.experiment_repository import ExperimentRepository


class FileExperimentRepository(ExperimentRepository):
    """ファイルシステムに実験を保存するリポジトリ"""
    
    def __init__(self, base_path: str = "results"):
        """
        初期化
        
        Args:
            base_path: 保存先のベースパス
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
    def save(self, experiment: Experiment) -> Path:
        """
        実験を保存
        
        Args:
            experiment: 保存する実験
            
        Returns:
            保存先のパス
        """
        # ファイル名を生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{experiment.name}_{timestamp}.json"
        # ファイル名をサニタイズ
        filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
        filepath = self.base_path / filename
        
        # 実験データを辞書に変換
        data = self._experiment_to_dict(experiment)
        
        # JSONファイルとして保存
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        return filepath
    
    def load(self, experiment_id: str) -> Optional[Experiment]:
        """
        実験を読み込み（未実装）
        
        Args:
            experiment_id: 実験ID
            
        Returns:
            実験インスタンス（見つからない場合はNone）
        """
        # 初期実装では読み込み機能は省略
        return None
    
    def _experiment_to_dict(self, experiment: Experiment) -> dict:
        """実験オブジェクトを辞書に変換"""
        return {
            "id": experiment.id,
            "name": experiment.name,
            "prompt_name": experiment.prompt_name,
            "dataset_name": experiment.dataset_name,
            "llm_endpoint": experiment.llm_endpoint,
            "description": experiment.description,
            "status": experiment.status.value,
            "results": [self._result_to_dict(r) for r in experiment.results],
            "summary": experiment.get_summary(),
            "metadata": experiment.metadata,
            "created_at": experiment.created_at.isoformat(),
            "completed_at": experiment.completed_at.isoformat() if experiment.completed_at else None
        }
    
    def _result_to_dict(self, result: ExtractionResult) -> dict:
        """抽出結果オブジェクトを辞書に変換"""
        return {
            "document_id": result.document_id,
            "expected_data": result.expected_data,
            "extracted_data": result.extracted_data,
            "field_results": [
                self._field_result_to_dict(fr) 
                for fr in result.field_results
            ],
            "extraction_time_ms": result.extraction_time_ms,
            "error": result.error,
            "is_success": result.is_success(),
            "accuracy": result.calculate_accuracy(),
            "created_at": result.created_at.isoformat()
        }
    
    def _field_result_to_dict(self, field_result: FieldResult) -> dict:
        """フィールド結果オブジェクトを辞書に変換"""
        return {
            "field_name": field_result.field_name,
            "expected_value": field_result.expected_value,
            "actual_value": field_result.actual_value,
            "weight": field_result.weight,
            "score": field_result.score,
            "is_correct": field_result.is_correct,
            "item_index": field_result.item_index,
            "details": field_result.details,
            "display_name": field_result.get_display_name()
        }