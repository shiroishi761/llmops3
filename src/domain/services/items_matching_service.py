"""明細項目のマッチングサービス"""

from typing import List, Dict, Any, Tuple, Optional
import json
from dataclasses import dataclass


@dataclass
class ItemMatch:
    """アイテムマッチング結果"""
    expected_item: Dict[str, Any]
    matched_item: Optional[Dict[str, Any]]
    match_score: float
    field_matches: Dict[str, bool]
    match_reason: Optional[str] = None  # LLMによるマッチング理由


class ItemsMatchingService:
    """明細項目の高度なマッチングを行うサービス"""
    
    def __init__(self, llm_matching_service=None, config_service=None):
        # 設定サービスから重みを取得
        if config_service:
            self.field_weights = config_service.get_items_field_weights()
            # デフォルトの重みを設定に含まれていないフィールド用に保持
            self._default_weight = config_service.get_items_field_weight("default_weight")
        else:
            # 設定サービスがない場合はデフォルト値を使用
            self.field_weights = {
                'name': 3.0,  # 品目名は最重要
                'quantity': 2.0,
                'price': 2.0,
                'sub_total': 2.0,
                'unit': 1.0,
                'spec': 1.0,
                'note': 0.5,
                'account_item': 1.0
            }
            self._default_weight = 1.0
        self.llm_matching_service = llm_matching_service
    
    def match_items(
        self,
        expected_items: List[Dict[str, Any]],
        actual_items: List[Dict[str, Any]]
    ) -> List['ItemMatch']:
        """
        期待されるアイテムと実際のアイテムをマッチング
        
        Returns:
            マッチング結果のリスト
        """
        _, matches = self.calculate_items_accuracy(expected_items, actual_items)
        
        # ItemMatchオブジェクトのリストを返すが、expected/matchedフィールドを持つ形式に変換
        result = []
        for match in matches:
            result.append(ItemMatch(
                expected_item=match.expected_item,
                matched_item=match.matched_item,
                match_score=match.match_score,
                field_matches=match.field_matches,
                match_reason=match.match_reason
            ))
        return result
    
    def calculate_items_accuracy(
        self,
        expected_items: List[Dict[str, Any]],
        actual_items: List[Dict[str, Any]]
    ) -> Tuple[float, List[ItemMatch]]:
        """
        明細項目の精度を計算
        
        Returns:
            - 全体精度スコア (0.0-1.0)
            - 各項目のマッチング結果
        """
        if not expected_items:
            # 期待値が空の場合、実際も空なら100%、そうでなければ0%
            return (1.0 if not actual_items else 0.0), []
        
        if not actual_items:
            # 実際が空の場合は0%
            return 0.0, [ItemMatch(item, None, 0.0, {}) for item in expected_items]
        
        # LLMマッチングサービスが利用可能な場合は使用
        if self.llm_matching_service:
            return self._calculate_with_llm(expected_items, actual_items)
        
        # 従来のルールベースマッチング
        return self._calculate_with_rules(expected_items, actual_items)
    
    def _calculate_with_llm(
        self,
        expected_items: List[Dict[str, Any]],
        actual_items: List[Dict[str, Any]]
    ) -> Tuple[float, List[ItemMatch]]:
        """LLMを使用したマッチング"""
        # LLMでマッチングを実行
        llm_matches = self.llm_matching_service.match_items(expected_items, actual_items)
        
        matches = []
        for exp_idx, act_idx, confidence in llm_matches:
            expected_item = expected_items[exp_idx]
            
            if act_idx >= 0 and act_idx < len(actual_items):
                actual_item = actual_items[act_idx]
                # フィールドごとの詳細比較
                _, field_matches = self._calculate_item_similarity(expected_item, actual_item)
                
                matches.append(ItemMatch(
                    expected_item=expected_item,
                    matched_item=actual_item,
                    match_score=confidence,
                    field_matches=field_matches,
                    match_reason=f"LLM信頼度: {confidence:.2f}"
                ))
            else:
                matches.append(ItemMatch(
                    expected_item=expected_item,
                    matched_item=None,
                    match_score=0.0,
                    field_matches={},
                    match_reason="対応する項目なし"
                ))
        
        # 全体精度を計算
        total_score = sum(match.match_score for match in matches) / len(matches)
        
        return total_score, matches
    
    def _calculate_with_rules(
        self,
        expected_items: List[Dict[str, Any]],
        actual_items: List[Dict[str, Any]]
    ) -> Tuple[float, List[ItemMatch]]:
        """従来のルールベースマッチング"""
        # 各期待値項目に対して最適なマッチを見つける
        matches = []
        used_actual_indices = set()
        
        for expected_item in expected_items:
            best_match, best_score, best_index, field_matches = self._find_best_match(
                expected_item, actual_items, used_actual_indices
            )
            
            if best_index is not None:
                used_actual_indices.add(best_index)
            
            matches.append(ItemMatch(
                expected_item=expected_item,
                matched_item=best_match,
                match_score=best_score,
                field_matches=field_matches
            ))
        
        # 全体精度を計算
        total_score = sum(match.match_score for match in matches) / len(matches)
        
        return total_score, matches
    
    def _find_best_match(
        self,
        expected_item: Dict[str, Any],
        actual_items: List[Dict[str, Any]],
        used_indices: set
    ) -> Tuple[Optional[Dict[str, Any]], float, Optional[int], Dict[str, bool]]:
        """期待値項目に最も近い実際の項目を見つける"""
        best_match = None
        best_score = 0.0
        best_index = None
        best_field_matches = {}
        
        for i, actual_item in enumerate(actual_items):
            if i in used_indices:
                continue
            
            score, field_matches = self._calculate_item_similarity(expected_item, actual_item)
            
            if score > best_score:
                best_match = actual_item
                best_score = score
                best_index = i
                best_field_matches = field_matches
        
        return best_match, best_score, best_index, best_field_matches
    
    def _calculate_item_similarity(
        self,
        expected_item: Dict[str, Any],
        actual_item: Dict[str, Any]
    ) -> Tuple[float, Dict[str, bool]]:
        """2つのアイテムの類似度を計算"""
        total_weight = 0.0
        weighted_score = 0.0
        field_matches = {}
        
        # すべてのフィールドを取得（期待値と実際値の両方から）
        all_fields = set(expected_item.keys()) | set(actual_item.keys())
        
        for field in all_fields:
            # フィールドの重みを取得（設定にない場合はデフォルト）
            weight = self.field_weights.get(field, self._default_weight)
            expected_value = expected_item.get(field)
            actual_value = actual_item.get(field)
            
            # 両方ともNoneまたは空の場合でも、field_matchesには含める
            if self._is_empty(expected_value) and self._is_empty(actual_value):
                field_matches[field] = True  # 両方空なら一致とみなす
                continue
            
            total_weight += weight
            
            # フィールド値の比較
            if field == 'name':
                # 品目名は部分一致も考慮
                is_match = self._name_match(expected_value, actual_value)
            else:
                # その他のフィールドは正規化して比較
                is_match = self._normalize_and_compare(expected_value, actual_value)
            
            field_matches[field] = is_match
            
            if is_match:
                weighted_score += weight
        
        # 類似度スコアを計算（0.0-1.0）
        similarity = weighted_score / total_weight if total_weight > 0 else 0.0
        
        return similarity, field_matches
    
    def _name_match(self, expected: Any, actual: Any) -> bool:
        """品目名のマッチング（部分一致を考慮）"""
        if expected is None or actual is None:
            return False
        
        expected_str = str(expected).strip().lower()
        actual_str = str(actual).strip().lower()
        
        # 完全一致
        if expected_str == actual_str:
            return True
        
        # 部分一致（期待値が実際の値に含まれる、またはその逆）
        if expected_str in actual_str or actual_str in expected_str:
            return True
        
        # カタカナの濁点・半濁点を考慮（ポンプ → ホンプ）
        import unicodedata
        expected_normalized = unicodedata.normalize('NFKC', expected_str)
        actual_normalized = unicodedata.normalize('NFKC', actual_str)
        
        # 濁点を除去してマッチング
        expected_no_dakuten = expected_normalized.replace('゛', '').replace('゜', '')
        actual_no_dakuten = actual_normalized.replace('゛', '').replace('゜', '')
        
        if expected_no_dakuten in actual_no_dakuten or actual_no_dakuten in expected_no_dakuten:
            return True
        
        # 主要な単語での一致（スペースや記号で分割）
        expected_words = set(expected_str.replace('-', ' ').replace('_', ' ').split())
        actual_words = set(actual_str.replace('-', ' ').replace('_', ' ').split())
        
        # 共通単語が一定割合以上あれば一致とみなす
        if expected_words and actual_words:
            common_words = expected_words & actual_words
            match_ratio = len(common_words) / min(len(expected_words), len(actual_words))
            return match_ratio >= 0.5
        
        return False
    
    def _normalize_and_compare(self, expected: Any, actual: Any) -> bool:
        """値を正規化して比較"""
        # None, 空文字列、0の扱い
        if self._is_empty(expected) and self._is_empty(actual):
            return True
        
        if expected is None or actual is None:
            return False
        
        # 数値の比較
        try:
            expected_num = float(str(expected).replace(',', ''))
            actual_num = float(str(actual).replace(',', ''))
            return abs(expected_num - actual_num) < 0.01
        except (ValueError, TypeError):
            pass
        
        # 文字列として比較
        return str(expected).strip().lower() == str(actual).strip().lower()
    
    def _is_empty(self, value: Any) -> bool:
        """値が空かどうかを判定"""
        return value is None or value == "" or value == 0
    
    def create_items_metric(
        self,
        expected_items: List[Dict[str, Any]],
        actual_items: List[Dict[str, Any]],
        base_weight: float = 5.0
    ) -> Dict[str, Any]:
        """
        明細項目の精度メトリクスを生成
        AccuracyMetricと互換性のある辞書形式で返す
        """
        accuracy, matches = self.calculate_items_accuracy(expected_items, actual_items)
        
        # AccuracyMetricのインスタンスではなく、拡張された辞書を返す
        return {
            "field_name": "items",
            "expected_value": json.dumps(expected_items, ensure_ascii=False, sort_keys=True),
            "actual_value": json.dumps(actual_items, ensure_ascii=False, sort_keys=True),
            "weight": base_weight,
            "is_correct": accuracy >= 0.8,  # 80%以上で正解とする
            "field_score": base_weight * accuracy,
            # 追加情報
            "items_accuracy": accuracy,
            "items_matches": [
                {
                    "expected": match.expected_item,
                    "matched": match.matched_item,
                    "score": match.match_score,
                    "field_matches": match.field_matches,
                    "reason": match.match_reason
                }
                for match in matches
            ]
        }