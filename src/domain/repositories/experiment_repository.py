"""実験リポジトリインターフェース"""
from abc import ABC, abstractmethod
from typing import Optional
from pathlib import Path

from ...application.dto.experiment_dto import ExperimentDto

class ExperimentRepository(ABC):
    """実験リポジトリのインターフェース"""
    
    @abstractmethod
    def save(self, experiment_dto: ExperimentDto) -> Path:
        """
        実験を保存
        
        Args:
            experiment_dto: 保存する実験DTO
            
        Returns:
            保存先のパス
        """
        pass
    
    @abstractmethod
    def load(self, experiment_id: str) -> Optional[ExperimentDto]:
        """
        実験を読み込み
        
        Args:
            experiment_id: 実験ID
            
        Returns:
            実験DTO（見つからない場合はNone）
        """
        pass
