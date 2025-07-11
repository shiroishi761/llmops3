"""フィールド評価結果分析サービス"""
from typing import List, Dict, Any, Optional
from ..models.field_result import FieldEvaluationResult


class FieldEvaluationAnalysisService:
    """FieldEvaluationResultの分析・集計を行うドメインサービス"""
    
    def __init__(self, field_results: List[FieldEvaluationResult]):
        self.field_results = field_results
    
    def get_by_field_name(self, field_name: str) -> List[FieldEvaluationResult]:
        """指定フィールド名の結果を取得"""
        return [r for r in self.field_results if r.field_name == field_name]
    
    def get_by_item_index(self, item_index: int) -> List[FieldEvaluationResult]:
        """指定アイテムインデックスの結果を取得"""
        return [r for r in self.field_results if r.item_index == item_index]
    
    def get_by_field_and_item(self, field_name: str, item_index: int) -> Optional[FieldEvaluationResult]:
        """指定フィールド名とアイテムインデックスの結果を取得"""
        for result in self.field_results:
            if result.field_name == field_name and result.item_index == item_index:
                return result
        return None
    
    def get_items_results(self) -> List[FieldEvaluationResult]:
        """アイテム関連の結果を取得"""
        return [r for r in self.field_results if r.field_name.startswith("items.")]
    
    def get_non_items_results(self) -> List[FieldEvaluationResult]:
        """アイテム以外の結果を取得"""
        return [r for r in self.field_results if not r.field_name.startswith("items.")]
    
    def calculate_overall_accuracy(self) -> float:
        """全体精度を計算"""
        if not self.field_results:
            return 0.0
        
        total_score = sum(r.score for r in self.field_results)
        total_weight = sum(r.weight for r in self.field_results)
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def calculate_items_accuracy(self) -> float:
        """アイテム関連の精度を計算"""
        items_results = self.get_items_results()
        if not items_results:
            return 0.0
        
        total_score = sum(r.score for r in items_results)
        total_weight = sum(r.weight for r in items_results)
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def get_item_summary(self) -> Dict[int, Dict[str, Any]]:
        """アイテム別のサマリーを取得"""
        items_results = self.get_items_results()
        if not items_results:
            return {}
        
        # アイテムインデックスごとにグループ化
        item_groups = {}
        for result in items_results:
            if result.item_index not in item_groups:
                item_groups[result.item_index] = []
            item_groups[result.item_index].append(result)
        
        # 各アイテムの精度を計算
        summary = {}
        for item_index, results in item_groups.items():
            total_score = sum(r.score for r in results)
            total_weight = sum(r.weight for r in results)
            accuracy = total_score / total_weight if total_weight > 0 else 0.0
            
            summary[item_index] = {
                "accuracy": accuracy,
                "total_score": total_score,
                "total_weight": total_weight,
                "field_count": len(results)
            }
        
        return summary
    
    def get_field_accuracy_summary(self) -> Dict[str, Dict[str, Any]]:
        """フィールド別の精度サマリーを取得"""
        field_groups = {}
        
        # フィールド名ごとにグループ化
        for result in self.field_results:
            display_name = result.get_display_name()
            if display_name not in field_groups:
                field_groups[display_name] = []
            field_groups[display_name].append(result)
        
        # 各フィールドの統計を計算
        summary = {}
        for field_name, results in field_groups.items():
            correct_count = sum(1 for r in results if r.is_correct)
            total_count = len(results)
            total_score = sum(r.score for r in results)
            total_weight = sum(r.weight for r in results)
            
            summary[field_name] = {
                "accuracy": correct_count / total_count if total_count > 0 else 0.0,
                "weighted_accuracy": total_score / total_weight if total_weight > 0 else 0.0,
                "correct_count": correct_count,
                "total_count": total_count,
                "total_score": total_score,
                "total_weight": total_weight
            }
        
        return summary
    
    def get_field_accuracies(self) -> Dict[str, bool]:
        """各フィールドの正解/不正解を取得"""
        result = {}
        for field_result in self.field_results:
            display_name = field_result.get_display_name()
            result[display_name] = field_result.is_correct
        return result