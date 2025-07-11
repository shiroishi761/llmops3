"""LLMを使用した明細項目マッチングサービス"""

import json
from typing import List, Dict, Any, Tuple, Optional
import logging

from ...domain.services.items_matching_service import ItemMatch


logger = logging.getLogger(__name__)


class LLMMatchingService:
    """LLMを使用して明細項目の高度なマッチングを行うサービス"""
    
    def __init__(self, gemini_service):
        self.gemini_service = gemini_service
        
    def match_items(
        self,
        expected_items: List[Dict[str, Any]],
        actual_items: List[Dict[str, Any]]
    ) -> List[Tuple[int, int, float]]:
        """
        LLMを使用して期待値と実際の項目をマッチング
        
        Returns:
            各期待値項目に対する (期待値インデックス, 実際値インデックス, 信頼度スコア) のリスト
            マッチしない場合は実際値インデックスが-1
        """
        if not expected_items or not actual_items:
            return []
        
        # マッチング用のプロンプトを作成
        prompt = self._create_matching_prompt(expected_items, actual_items)
        
        try:
            # Geminiに問い合わせ
            response = self.gemini_service.extract(prompt)
            
            # レスポンスからマッチング結果を抽出
            matches = self._parse_matching_response(response, len(expected_items))
            
            return matches
            
        except Exception as e:
            logger.error(f"LLMマッチングエラー: {str(e)}")
            # エラー時は空のマッチングを返す
            return [(i, -1, 0.0) for i in range(len(expected_items))]
    
    def _create_matching_prompt(
        self,
        expected_items: List[Dict[str, Any]],
        actual_items: List[Dict[str, Any]]
    ) -> str:
        """マッチング用のプロンプトを作成"""
        prompt = """以下の期待値リストと実際値リストの項目をマッチングしてください。

# 期待値リスト
"""
        for i, item in enumerate(expected_items):
            prompt += f"{i}: {self._format_item(item)}\n"
        
        prompt += "\n# 実際値リスト\n"
        for i, item in enumerate(actual_items):
            prompt += f"{i}: {self._format_item(item)}\n"
        
        prompt += """
# マッチングルール
1. 品目名が同じまたは類似している項目をマッチングしてください
2. 略語、表記ゆれ、部分一致も考慮してください（例：「ポンプ」と「ホンプモータユニット」）
3. 数量と単価が一致する場合は優先的にマッチングしてください
4. 支給品（価格0円）は特別扱いしてください

# 出力形式
JSON形式で以下のように出力してください：
{
  "matches": [
    {"expected_index": 0, "actual_index": 3, "confidence": 0.95, "reason": "品目名と数量が一致"},
    {"expected_index": 1, "actual_index": -1, "confidence": 0.0, "reason": "対応する項目なし"},
    ...
  ]
}

期待値の各項目について必ず1つのマッチング結果を出力してください。
対応する実際値がない場合は actual_index を -1 にしてください。
"""
        
        return prompt
    
    def _format_item(self, item: Dict[str, Any]) -> str:
        """項目を読みやすい形式にフォーマット"""
        parts = []
        
        if item.get('name'):
            parts.append(f"品目:{item['name']}")
        if item.get('quantity') is not None:
            unit = item.get('unit', '')
            parts.append(f"数量:{item['quantity']}{unit}")
        if item.get('price') is not None:
            parts.append(f"単価:{item['price']:,}円")
        if item.get('spec'):
            parts.append(f"仕様:{item['spec']}")
        if item.get('note'):
            parts.append(f"備考:{item['note']}")
        
        return " / ".join(parts)
    
    def _parse_matching_response(
        self,
        response: Dict[str, Any],
        expected_count: int
    ) -> List[Tuple[int, int, float]]:
        """LLMのレスポンスからマッチング結果を抽出"""
        try:
            # レスポンスからJSONデータを抽出
            if 'data' in response and isinstance(response['data'], dict):
                data = response['data']
            else:
                # テキストレスポンスの場合はJSONを抽出
                text = str(response)
                # JSON部分を抽出
                start = text.find('{')
                end = text.rfind('}') + 1
                if start >= 0 and end > start:
                    data = json.loads(text[start:end])
                else:
                    raise ValueError("JSONデータが見つかりません")
            
            matches = data.get('matches', [])
            
            # 結果を整理
            result = []
            matched_expected = set()
            
            for match in matches:
                exp_idx = match.get('expected_index', -1)
                act_idx = match.get('actual_index', -1)
                confidence = match.get('confidence', 0.0)
                
                if 0 <= exp_idx < expected_count and exp_idx not in matched_expected:
                    result.append((exp_idx, act_idx, confidence))
                    matched_expected.add(exp_idx)
            
            # マッチング結果がない期待値項目を追加
            for i in range(expected_count):
                if i not in matched_expected:
                    result.append((i, -1, 0.0))
            
            # 期待値インデックスでソート
            result.sort(key=lambda x: x[0])
            
            return result
            
        except Exception as e:
            logger.error(f"マッチングレスポンスのパースエラー: {str(e)}")
            # エラー時は空のマッチングを返す
            return [(i, -1, 0.0) for i in range(expected_count)]