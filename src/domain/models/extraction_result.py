"""文書評価結果エンティティ"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime

from .field_result import FieldEvaluationResult, FieldEvaluationResultCollection


@dataclass
class DocumentEvaluationResult:
    """
    文書の評価結果を表すエンティティ
    
    文書レベルの抽出結果と評価の集約を管理する
    
    Attributes:
        document_id: 文書ID
        expected_data: 期待される抽出データ
        extracted_data: 実際に抽出されたデータ
        field_results: 各フィールドの評価結果
        extraction_time_ms: 抽出にかかった時間（ミリ秒）
        error: エラーメッセージ（エラー時のみ）
        created_at: 作成日時
    """
    document_id: str
    expected_data: Dict[str, Any]
    extracted_data: Dict[str, Any]
    field_results: List[FieldEvaluationResult] = field(default_factory=list)
    extraction_time_ms: Optional[int] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def is_success(self) -> bool:
        """抽出が成功したかを判定"""
        return self.error is None
    
    def calculate_accuracy(self) -> float:
        """全体の精度を計算（0.0〜1.0）"""
        if not self.field_results:
            return 0.0
            
        collection = FieldEvaluationResultCollection(self.field_results)
        analysis_service = collection.get_analysis_service()
        return analysis_service.calculate_overall_accuracy()
    
    def get_field_accuracies(self) -> Dict[str, bool]:
        """各フィールドの正解/不正解を取得"""
        collection = FieldEvaluationResultCollection(self.field_results)
        analysis_service = collection.get_analysis_service()
        return analysis_service.get_field_accuracies()
    
    def get_field_results_collection(self) -> FieldEvaluationResultCollection:
        """FieldEvaluationResultCollectionを取得"""
        return FieldEvaluationResultCollection(self.field_results)