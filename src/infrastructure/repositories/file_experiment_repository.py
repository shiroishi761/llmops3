"""ファイルベースの実験リポジトリ"""
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from ...application.dto.experiment_dto import ExperimentDto
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
        
    def save(self, experiment_dto: ExperimentDto) -> Path:
        """
        実験を保存
        
        Args:
            experiment_dto: 保存する実験DTO
            
        Returns:
            保存先のパス
        """
        # ファイル名を生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{experiment_dto.name}_{timestamp}.json"
        # ファイル名をサニタイズ
        filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
        filepath = self.base_path / filename
        
        # 実験データを辞書に変換
        data = self._experiment_dto_to_dict(experiment_dto)
        
        # JSONファイルとして保存
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        return filepath
    
    def load(self, experiment_id: str) -> Optional[ExperimentDto]:
        """
        実験を読み込み（未実装）
        
        Args:
            experiment_id: 実験ID
            
        Returns:
            実験DTO（見つからない場合はNone）
        """
        # 初期実装では読み込み機能は省略
        return None
    
    def _experiment_dto_to_dict(self, experiment_dto: ExperimentDto) -> dict:
        """実験DTOを辞書に変換"""
        return {
            "id": experiment_dto.id,
            "name": experiment_dto.name,
            "prompt_name": experiment_dto.prompt_name,
            "dataset_name": experiment_dto.dataset_name,
            "llm_endpoint": experiment_dto.llm_endpoint,
            "description": experiment_dto.description,
            "status": experiment_dto.status,
            "results": experiment_dto.results,  # 既にdict形式
            "created_at": experiment_dto.created_at.isoformat(),
            "started_at": experiment_dto.started_at.isoformat() if experiment_dto.started_at else None,
            "completed_at": experiment_dto.completed_at.isoformat() if experiment_dto.completed_at else None,
            "error_message": experiment_dto.error_message
        }