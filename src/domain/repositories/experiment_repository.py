"""実験リポジトリインターフェース"""
from abc import ABC, abstractmethod
from typing import Optional
from pathlib import Path

from ..models.experiment import Experiment


class ExperimentRepository(ABC):
    """実験リポジトリのインターフェース"""
    
    @abstractmethod
    def save(self, experiment: Experiment) -> Path:
        """
        実験を保存
        
        Args:
            experiment: 保存する実験
            
        Returns:
            保存先のパス
        """
        pass
    
    @abstractmethod
    def load(self, experiment_id: str) -> Optional[Experiment]:
        """
        実験を読み込み
        
        Args:
            experiment_id: 実験ID
            
        Returns:
            実験インスタンス（見つからない場合はNone）
        """
        pass