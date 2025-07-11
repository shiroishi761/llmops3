"""FieldScoreCalculator → FieldResultAnalysisService の流れの例"""

from src.domain.models.field_result import FieldResult, FieldResultCollection
from src.domain.services.field_score_calculator import FieldScoreCalculatorFactory
from src.domain.services.accuracy_evaluation_service import AccuracyEvaluationService


def demonstrate_evaluation_flow():
    """評価から分析までの流れを示す"""
    
    # === 1. データの準備 ===
    expected_data = {
        "total_price": 1000,
        "tax_price": 100,
        "issuer": "株式会社テスト",
        "items": [
            {"name": "商品A", "quantity": 2, "price": 500},
            {"name": "商品B", "quantity": 1, "price": 300}
        ]
    }
    
    actual_data = {
        "total_price": 1000,    # 正解
        "tax_price": 105,       # 5円の誤差（tax_priceは10円以下許容）
        "issuer": "㈱テスト",    # 表記揺れ（会社名正規化で正解）
        "items": [
            {"name": "商品A", "quantity": 2, "price": 500},  # 正解
            {"name": "商品B", "quantity": 1, "price": 280}   # 価格が違う
        ]
    }
    
    field_weights = {
        "total_price": 3.0,
        "tax_price": 2.0,
        "issuer": 2.0,
        "items.name": 3.0,
        "items.quantity": 2.0,
        "items.price": 2.0
    }
    
    print("=== 1. FieldScoreCalculator による評価 ===")
    
    # === 2. AccuracyEvaluationService による評価実行 ===
    evaluation_service = AccuracyEvaluationService()
    field_results = evaluation_service.evaluate_extraction(
        expected_data, actual_data, field_weights, default_weight=1.0
    )
    
    # 各FieldResultを表示
    print("\n個別フィールドの評価結果:")
    for result in field_results:
        print(f"  {result.get_display_name()}: {result.score:.1f}/{result.weight:.1f} {'✓' if result.is_correct else '✗'}")
    
    print("\n=== 2. FieldResultAnalysisService による集計・分析 ===")
    
    # === 3. FieldResultCollectionを作成 ===
    collection = FieldResultCollection(field_results)
    analysis_service = collection.get_analysis_service()
    
    # === 4. 様々な分析を実行 ===
    
    # 全体精度の計算
    overall_accuracy = analysis_service.calculate_overall_accuracy()
    print(f"\n全体精度: {overall_accuracy:.1%}")
    
    # フィールド別の正解状況
    print("\nフィールド別正解状況:")
    field_accuracies = analysis_service.get_field_accuracies()
    for field_name, is_correct in field_accuracies.items():
        print(f"  {field_name}: {'✓' if is_correct else '✗'}")
    
    # アイテム関連の精度
    items_accuracy = analysis_service.calculate_items_accuracy()
    print(f"\nアイテム関連精度: {items_accuracy:.1%}")
    
    # アイテム別サマリー
    print("\nアイテム別サマリー:")
    item_summary = analysis_service.get_item_summary()
    for item_index, summary in item_summary.items():
        print(f"  アイテム{item_index}: {summary['accuracy']:.1%} ({summary['correct_count']}/{summary['field_count']})")
    
    # フィールド別詳細サマリー
    print("\nフィールド別詳細サマリー:")
    field_summary = analysis_service.get_field_accuracy_summary()
    for field_name, summary in field_summary.items():
        print(f"  {field_name}:")
        print(f"    精度: {summary['accuracy']:.1%}")
        print(f"    重み付き精度: {summary['weighted_accuracy']:.1%}")
        print(f"    正解数/総数: {summary['correct_count']}/{summary['total_count']}")
    
    # === 5. 検索・分類機能 ===
    print("\n=== 3. 検索・分類機能 ===")
    
    # フィールド名による検索
    items_name_results = analysis_service.get_by_field_name("items.name")
    print(f"\nitems.nameフィールドの結果数: {len(items_name_results)}")
    
    # アイテムインデックスによる検索
    item_0_results = analysis_service.get_by_item_index(0)
    print(f"アイテム0の結果数: {len(item_0_results)}")
    
    # アイテム関連/非関連の分類
    items_results = analysis_service.get_items_results()
    non_items_results = analysis_service.get_non_items_results()
    print(f"アイテム関連: {len(items_results)}個, 非関連: {len(non_items_results)}個")
    
    return field_results, analysis_service


def demonstrate_calculator_internals():
    """各Calculatorの内部動作を示す"""
    print("\n=== Calculator内部動作の詳細 ===")
    
    factory = FieldScoreCalculatorFactory()
    
    # 1. 文字列フィールドの評価
    print("\n1. 文字列フィールド (SimpleCalculator):")
    simple_calc = factory.get_calculator("doc_type")
    result = simple_calc.calculate_score("doc_type", "請求書", "請求書", 1.5)
    print(f"  doc_type: {result.score:.1f}/{result.weight:.1f} {'✓' if result.is_correct else '✗'}")
    
    # 2. 金額フィールドの評価
    print("\n2. 金額フィールド (AmountCalculator):")
    amount_calc = factory.get_calculator("total_price")
    result = amount_calc.calculate_score("total_price", 1000, "1,000", 3.0)
    print(f"  total_price: {result.score:.1f}/{result.weight:.1f} {'✓' if result.is_correct else '✗'}")
    
    # 3. 日付フィールドの評価
    print("\n3. 日付フィールド (DateCalculator):")
    date_calc = factory.get_calculator("doc_date")
    result = date_calc.calculate_score("doc_date", "2024-01-15", "2024年1月15日", 1.5)
    print(f"  doc_date: {result.score:.1f}/{result.weight:.1f} {'✓' if result.is_correct else '✗'}")
    
    # 4. 明細項目フィールドの評価
    print("\n4. 明細項目フィールド (ItemsCalculator):")
    items_calc = factory.get_calculator("items")
    expected_items = [{"name": "商品A", "quantity": 2, "price": 500}]
    actual_items = [{"name": "商品A", "quantity": 2, "price": 500}]
    field_weights = {"items.name": 3.0, "items.quantity": 2.0, "items.price": 2.0}
    
    results = items_calc.calculate("items", expected_items, actual_items, field_weights, 1.0)
    print(f"  items評価結果: {len(results)}個のFieldResult")
    for result in results:
        print(f"    {result.get_display_name()}: {result.score:.1f}/{result.weight:.1f} {'✓' if result.is_correct else '✗'}")


if __name__ == "__main__":
    print("FieldScoreCalculator → FieldResultAnalysisService の流れ")
    print("=" * 60)
    
    # メインの流れを実行
    field_results, analysis_service = demonstrate_evaluation_flow()
    
    # Calculator内部動作の詳細
    demonstrate_calculator_internals()
    
    print("\n" + "=" * 60)
    print("評価・分析の完了")