"""フィールド評価結果エンティティ"""
from dataclasses import dataclass, field
from typing import Optional, Any, List, Dict


@dataclass(frozen=True)
class FieldEvaluationResult:
    """
    フィールドの評価結果を表すエンティティ
    
    各フィールドの評価結果を統一的に管理する
    """
    field_name: str
    expected_value: Optional[Any]
    actual_value: Optional[Any]
    weight: float
    score: float  # 正解なら重み、不正解なら0
    is_correct: bool
    item_index: Optional[int] = None  # アイテムのインデックス（0, 1, 2...）
    details: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """バリデーション"""
        if self.weight < 0:
            raise ValueError("重みは0以上である必要があります")
        if self.score < 0:
            raise ValueError("スコアは0以上である必要があります")
        if self.is_correct and self.score != self.weight:
            raise ValueError("正解の場合、スコアは重みと同じである必要があります")
        if not self.is_correct and self.score != 0:
            raise ValueError("不正解の場合、スコアは0である必要があります")
    
    @classmethod
    def create_correct(
        cls, 
        field_name: str, 
        expected: Any, 
        actual: Any, 
        weight: float,
        item_index: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> 'FieldEvaluationResult':
        """正解のフィールド評価結果を作成"""
        return cls(
            field_name=field_name,
            expected_value=expected,
            actual_value=actual,
            weight=weight,
            score=weight,
            is_correct=True,
            item_index=item_index,
            details=details
        )
    
    @classmethod
    def create_incorrect(
        cls, 
        field_name: str, 
        expected: Any, 
        actual: Any, 
        weight: float,
        item_index: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> 'FieldEvaluationResult':
        """不正解のフィールド評価結果を作成"""
        return cls(
            field_name=field_name,
            expected_value=expected,
            actual_value=actual,
            weight=weight,
            score=0.0,
            is_correct=False,
            item_index=item_index,
            details=details
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換（レポート生成用）"""
        result = {
            "field_name": self.field_name,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
            "weight": self.weight,
            "is_correct": self.is_correct,
            "field_score": self.score
        }
        
        if self.item_index is not None:
            result["item_index"] = self.item_index
            
        if self.details:
            result["details"] = self.details
            
        return result
    
    def get_display_name(self) -> str:
        """表示用のフィールド名を取得"""
        if self.item_index is not None:
            return f"{self.field_name}[{self.item_index}]"
        return self.field_name


class FieldEvaluationResultCollection:
    """FieldEvaluationResultのコレクション管理"""
    
    def __init__(self, field_results: List[FieldEvaluationResult]):
        self.field_results = field_results
    
    def get_analysis_service(self):
        """分析サービスを取得"""
        from ..services.field_evaluation_analysis_service import FieldEvaluationAnalysisService
        return FieldEvaluationAnalysisService(self.field_results)
    
    def to_dict_list(self) -> List[Dict[str, Any]]:
        """辞書リストに変換"""
        return [r.to_dict() for r in self.field_results]