"""実験エンティティ"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ExperimentStatus(Enum):
    """実験のステータス"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Experiment:
    """
    精度検証実験を表すエンティティ（集約ルート）
    
    Attributes:
        id: 実験ID
        name: 実験名
        prompt_name: 使用するプロンプト名（Langfuse）
        dataset_name: 使用するデータセット名（Langfuse）
        llm_endpoint: 使用するLLMエンドポイント
        description: 実験の説明
        status: 実験のステータス
        results: 抽出結果のリスト
        metadata: その他のメタデータ
        created_at: 作成日時
        completed_at: 完了日時
    """
    id: str
    name: str
    prompt_name: str = ""
    dataset_name: str = ""
    llm_endpoint: str = ""
    description: Optional[str] = None
    status: ExperimentStatus = ExperimentStatus.PENDING
    results: List = field(default_factory=list)  # DocumentEvaluationDto のリスト
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def add_result(self, result) -> None:  # DocumentEvaluationDto
        """抽出結果を追加"""
        self.results.append(result)
        
    def mark_as_running(self) -> None:
        """実験を実行中に変更"""
        self.status = ExperimentStatus.RUNNING
        
    def mark_as_completed(self) -> None:
        """実験を完了に変更"""
        self.status = ExperimentStatus.COMPLETED
        self.completed_at = datetime.now()
        
    def mark_as_failed(self, error: str) -> None:
        """実験を失敗に変更"""
        self.status = ExperimentStatus.FAILED
        self.metadata["error"] = error
        self.completed_at = datetime.now()
        
    def calculate_overall_accuracy(self) -> float:
        """全体の精度を計算"""
        if not self.results:
            return 0.0
            
        successful_results = [r for r in self.results if not r.error]
        if not successful_results:
            return 0.0
            
        # DTOから精度を計算
        accuracies = []
        for result in successful_results:
            if result.field_results:
                total_score = sum(fr.score for fr in result.field_results)
                total_weight = sum(fr.weight for fr in result.field_results)
                if total_weight > 0:
                    accuracies.append(total_score / total_weight)
        
        return sum(accuracies) / len(accuracies) if accuracies else 0.0
    
    def calculate_field_accuracies(self) -> Dict[str, float]:
        """フィールド別の精度を計算"""
        field_stats: Dict[str, Dict[str, int]] = {}
        
        for result in self.results:
            if result.error:
                continue
                
            for field_result in result.field_results:
                field_name = field_result.field_name
                if field_result.item_index is not None:
                    field_name = f"{field_name}[{field_result.item_index}]"
                
                if field_name not in field_stats:
                    field_stats[field_name] = {"correct": 0, "total": 0}
                    
                field_stats[field_name]["total"] += 1
                if field_result.is_correct:
                    field_stats[field_name]["correct"] += 1
        
        return {
            field_name: stats["correct"] / stats["total"] if stats["total"] > 0 else 0.0
            for field_name, stats in field_stats.items()
        }
    
    def calculate_field_scores(self) -> Dict[str, Dict[str, float]]:
        """フィールド別の重み付きスコアを計算"""
        field_scores: Dict[str, Dict[str, float]] = {}
        
        for result in self.results:
            if result.error:
                continue
                
            for field_result in result.field_results:
                field_name = field_result.field_name
                if field_result.item_index is not None:
                    field_name = f"{field_name}[{field_result.item_index}]"
                    
                if field_name not in field_scores:
                    field_scores[field_name] = {
                        "total_weight": 0.0,
                        "total_score": 0.0,
                        "weight": field_result.weight
                    }
                field_scores[field_name]["total_weight"] += field_result.weight
                field_scores[field_name]["total_score"] += field_result.score
        
        # 平均スコアを計算
        result = {}
        for field_name, scores in field_scores.items():
            if scores["total_weight"] > 0:
                result[field_name] = {
                    "score": scores["total_score"] / scores["total_weight"],
                    "weight": scores["weight"]
                }
            else:
                result[field_name] = {
                    "score": 0.0,
                    "weight": scores["weight"]
                }
        
        return result
    
    def get_summary(self) -> Dict[str, Any]:
        """実験のサマリーを取得"""
        successful_count = sum(1 for r in self.results if not r.error)
        failed_count = sum(1 for r in self.results if r.error)
        
        return {
            "total_documents": len(self.results),
            "successful_count": successful_count,
            "failed_count": failed_count,
            "overall_accuracy": self.calculate_overall_accuracy(),
            "field_accuracies": self.calculate_field_accuracies(),
            "field_scores": self.calculate_field_scores(),
            "status": self.status.value,
            "execution_time_ms": self._calculate_execution_time()
        }
    
    def _calculate_execution_time(self) -> Optional[int]:
        """実行時間を計算（ミリ秒）"""
        if self.completed_at and self.created_at:
            delta = self.completed_at - self.created_at
            return int(delta.total_seconds() * 1000)
        return None
    
    def to_dto(self):
        """エンティティをDTOに変換"""
        from ...application.dto.experiment_dto import ExperimentDto
        
        # DocumentEvaluationDtoをdictに変換
        results_data = []
        for result in self.results:
            result_dict = {
                "document_id": result.document_id,
                "expected_data": result.expected_data,
                "extracted_data": result.extracted_data,
                "field_results": [
                    {
                        "field_name": fr.field_name,
                        "expected_value": fr.expected_value,
                        "actual_value": fr.actual_value,
                        "score": fr.score,
                        "weight": fr.weight,
                        "is_correct": fr.is_correct,
                        "item_index": fr.item_index
                    }
                    for fr in result.field_results
                ],
                "extraction_time_ms": result.extraction_time_ms,
                "error": result.error
            }
            results_data.append(result_dict)
        
        return ExperimentDto(
            id=self.id,
            name=self.name,
            prompt_name=self.prompt_name,
            dataset_name=self.dataset_name,
            llm_endpoint=self.llm_endpoint,
            description=self.description,
            status=self.status.value,
            results=results_data,
            created_at=self.created_at,
            started_at=getattr(self, 'started_at', None),  # 存在しない場合はNone
            completed_at=self.completed_at,
            error_message=self.metadata.get("error")
        )