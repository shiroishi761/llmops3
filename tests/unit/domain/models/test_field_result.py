"""FieldResultのテスト"""
import pytest
from src.domain.models.field_result import FieldResult, FieldResultCollection


class TestFieldResult:
    """FieldResultのテスト"""

    def test_create_correct(self):
        """正解の結果作成"""
        result = FieldResult.create_correct(
            "total_price", 1000, 1000, 3.0
        )
        
        assert result.field_name == "total_price"
        assert result.expected_value == 1000
        assert result.actual_value == 1000
        assert result.weight == 3.0
        assert result.score == 3.0
        assert result.is_correct == True
        assert result.item_index is None

    def test_create_incorrect(self):
        """不正解の結果作成"""
        result = FieldResult.create_incorrect(
            "tax_price", 1000, 2000, 3.0
        )
        
        assert result.field_name == "tax_price"
        assert result.expected_value == 1000
        assert result.actual_value == 2000
        assert result.weight == 3.0
        assert result.score == 0.0
        assert result.is_correct == False
        assert result.item_index is None

    def test_create_with_item_index(self):
        """アイテムインデックス付きの結果作成"""
        result = FieldResult.create_correct(
            "items.name", "商品A", "商品A", 3.0, item_index=0
        )
        
        assert result.field_name == "items.name"
        assert result.item_index == 0
        assert result.get_display_name() == "items.name[0]"

    def test_get_display_name(self):
        """表示名の取得"""
        # 通常のフィールド
        result = FieldResult.create_correct(
            "total_price", 1000, 1000, 3.0
        )
        assert result.get_display_name() == "total_price"
        
        # アイテムフィールド
        result = FieldResult.create_correct(
            "items.name", "商品A", "商品A", 3.0, item_index=0
        )
        assert result.get_display_name() == "items.name[0]"

    def test_validation_negative_weight(self):
        """負の重みでバリデーションエラー"""
        with pytest.raises(ValueError, match="重みは0以上である必要があります"):
            FieldResult(
                field_name="test",
                expected_value="expected",
                actual_value="actual",
                weight=-1.0,
                score=0.0,
                is_correct=False
            )

    def test_validation_negative_score(self):
        """負のスコアでバリデーションエラー"""
        with pytest.raises(ValueError, match="スコアは0以上である必要があります"):
            FieldResult(
                field_name="test",
                expected_value="expected",
                actual_value="actual",
                weight=1.0,
                score=-1.0,
                is_correct=False
            )

    def test_validation_correct_score_mismatch(self):
        """正解時のスコア不一致でバリデーションエラー"""
        with pytest.raises(ValueError, match="正解の場合、スコアは重みと同じである必要があります"):
            FieldResult(
                field_name="test",
                expected_value="expected",
                actual_value="actual",
                weight=3.0,
                score=1.0,
                is_correct=True
            )

    def test_validation_incorrect_score_mismatch(self):
        """不正解時のスコア不一致でバリデーションエラー"""
        with pytest.raises(ValueError, match="不正解の場合、スコアは0である必要があります"):
            FieldResult(
                field_name="test",
                expected_value="expected",
                actual_value="actual",
                weight=3.0,
                score=1.0,
                is_correct=False
            )

    def test_to_dict(self):
        """辞書変換"""
        result = FieldResult.create_correct(
            "total_price", 1000, 1000, 3.0
        )
        
        result_dict = result.to_dict()
        
        # 必要なフィールドが存在するか確認
        assert result_dict["field_name"] == "total_price"
        assert result_dict["expected_value"] == 1000
        assert result_dict["actual_value"] == 1000
        assert result_dict["weight"] == 3.0
        assert result_dict["is_correct"] == True
        # field_scoreからscoreに変更された可能性があるため、両方を確認
        assert result_dict.get("field_score", result_dict.get("score")) == 3.0


class TestFieldResultCollection:
    """FieldResultCollectionのテスト"""

    def test_calculate_overall_accuracy(self):
        """全体精度の計算"""
        results = [
            FieldResult.create_correct("total_price", 1000, 1000, 3.0),
            FieldResult.create_incorrect("tax_price", 1000, 2000, 3.0),
            FieldResult.create_correct("items.name", "商品A", "商品A", 3.0, item_index=0),
            FieldResult.create_correct("items.quantity", 2, 2, 2.0, item_index=0),
        ]
        
        collection = FieldResultCollection(results)
        analysis_service = collection.get_analysis_service()
        accuracy = analysis_service.calculate_overall_accuracy()
        
        # 期待値: (3.0 + 0.0 + 3.0 + 2.0) / (3.0 + 3.0 + 3.0 + 2.0) = 8.0 / 11.0 ≈ 0.727
        assert abs(accuracy - 8.0 / 11.0) < 0.001

    def test_get_by_field_name(self):
        """フィールド名による検索"""
        results = [
            FieldResult.create_correct("total_price", 1000, 1000, 3.0),
            FieldResult.create_correct("items.name", "商品A", "商品A", 3.0, item_index=0),
            FieldResult.create_correct("items.name", "商品B", "商品B", 3.0, item_index=1),
        ]
        
        collection = FieldResultCollection(results)
        analysis_service = collection.get_analysis_service()
        items_name_results = analysis_service.get_by_field_name("items.name")
        
        assert len(items_name_results) == 2
        assert items_name_results[0].item_index == 0
        assert items_name_results[1].item_index == 1

    def test_get_by_item_index(self):
        """アイテムインデックスによる検索"""
        results = [
            FieldResult.create_correct("total_price", 1000, 1000, 3.0),
            FieldResult.create_correct("items.name", "商品A", "商品A", 3.0, item_index=0),
            FieldResult.create_correct("items.quantity", 2, 2, 2.0, item_index=0),
            FieldResult.create_correct("items.name", "商品B", "商品B", 3.0, item_index=1),
        ]
        
        collection = FieldResultCollection(results)
        analysis_service = collection.get_analysis_service()
        item_0_results = analysis_service.get_by_item_index(0)
        
        assert len(item_0_results) == 2
        assert all(r.item_index == 0 for r in item_0_results)

    def test_get_item_summary(self):
        """アイテム別サマリー"""
        results = [
            FieldResult.create_correct("total_price", 1000, 1000, 3.0),
            FieldResult.create_correct("items.name", "商品A", "商品A", 3.0, item_index=0),
            FieldResult.create_correct("items.quantity", 2, 2, 2.0, item_index=0),
            FieldResult.create_correct("items.name", "商品B", "商品B", 3.0, item_index=1),
            FieldResult.create_incorrect("items.quantity", 1, 2, 2.0, item_index=1),
        ]
        
        collection = FieldResultCollection(results)
        analysis_service = collection.get_analysis_service()
        summary = analysis_service.get_item_summary()
        
        assert 0 in summary
        assert 1 in summary
        
        # アイテム0: 全て正解 (3.0 + 2.0) / (3.0 + 2.0) = 1.0
        assert summary[0]['accuracy'] == 1.0
        assert summary[0]['total_weight'] == 5.0
        assert summary[0]['total_score'] == 5.0
        
        # アイテム1: 1つ不正解 (3.0 + 0.0) / (3.0 + 2.0) = 0.6
        assert summary[1]['accuracy'] == 0.6
        assert summary[1]['total_weight'] == 5.0
        assert summary[1]['total_score'] == 3.0

    def test_get_items_results(self):
        """アイテム関連の結果のみ取得"""
        results = [
            FieldResult.create_correct("total_price", 1000, 1000, 3.0),
            FieldResult.create_correct("items.name", "商品A", "商品A", 3.0, item_index=0),
            FieldResult.create_correct("items.quantity", 2, 2, 2.0, item_index=0),
        ]
        
        collection = FieldResultCollection(results)
        analysis_service = collection.get_analysis_service()
        items_results = analysis_service.get_items_results()
        
        assert len(items_results) == 2
        assert all(r.item_index is not None for r in items_results)

    def test_get_non_items_results(self):
        """アイテム以外の結果のみ取得"""
        results = [
            FieldResult.create_correct("total_price", 1000, 1000, 3.0),
            FieldResult.create_correct("items.name", "商品A", "商品A", 3.0, item_index=0),
            FieldResult.create_correct("items.quantity", 2, 2, 2.0, item_index=0),
        ]
        
        collection = FieldResultCollection(results)
        analysis_service = collection.get_analysis_service()
        non_items_results = analysis_service.get_non_items_results()
        
        assert len(non_items_results) == 1
        assert all(r.item_index is None for r in non_items_results)