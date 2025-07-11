# フィールド結果ドメインモデル

## 概要
フィールドの評価結果を表現するドメインモデル。統一的なフィールド評価システムの中核。

## FieldResult エンティティ

### 責務
- フィールドの評価結果を統一的に管理
- アイテムインデックスによる明細項目の個別管理
- スコア計算とバリデーション

### 主要な属性

#### 基本情報
- `field_name`: フィールド名
- `expected_value`: 期待値
- `actual_value`: 実際の値
- `weight`: フィールドの重み（0.0以上）

#### 評価結果
- `score`: フィールドスコア（正解なら重み、不正解なら0.0）
- `is_correct`: 正解かどうか（boolean）

#### 拡張情報
- `item_index`: アイテムのインデックス（0, 1, 2...）※明細項目用
- `details`: 詳細情報（複雑な比較結果など）

### クラスメソッド

#### 正解の結果作成
```python
FieldResult.create_correct(
    field_name="total_price",
    expected=1000,
    actual=1000,
    weight=3.0,
    item_index=None  # 通常フィールド
)
```

#### 不正解の結果作成
```python
FieldResult.create_incorrect(
    field_name="tax_price",
    expected=1000,
    actual=2000,
    weight=3.0
)
```

#### 明細項目の結果作成
```python
FieldResult.create_correct(
    field_name="items.name",
    expected="商品A",
    actual="商品A",
    weight=3.0,
    item_index=0  # 1番目の明細項目
)
```

### インスタンスメソッド

#### 表示名取得
```python
field_result.get_display_name()
# 通常: "total_price"
# 明細: "items.name[0]"
```

#### 辞書変換
```python
field_result.to_dict()
# レポート生成用の辞書形式
```

## FieldResultCollection クラス

### 責務
- FieldResultのコレクション管理
- 分析サービスへのアクセス提供

### 主要メソッド

#### 分析サービス取得
```python
analysis_service = collection.get_analysis_service()
```

#### 辞書変換
```python
collection.to_dict_list()  # 辞書リストに変換
```


## 使用例

### 基本的な使用例
```python
# 結果作成
results = [
    FieldResult.create_correct("total_price", 1000, 1000, 3.0),
    FieldResult.create_incorrect("tax_price", 1000, 2000, 3.0),
    FieldResult.create_correct("items.name", "商品A", "商品A", 3.0, item_index=0),
    FieldResult.create_correct("items.quantity", 2, 2, 2.0, item_index=0),
]

# コレクション作成
collection = FieldResultCollection(results)

# 分析サービス取得
analysis_service = collection.get_analysis_service()

# 全体精度計算
accuracy = analysis_service.calculate_overall_accuracy()
print(f"全体精度: {accuracy:.1%}")

# アイテム別分析
item_summary = analysis_service.get_item_summary()
for item_idx, summary in item_summary.items():
    print(f"アイテム{item_idx}: {summary['accuracy']:.1%}")
```

### 明細項目の詳細管理
```python
# 2つの明細項目を持つドキュメント
expected_items = [
    {"name": "商品A", "quantity": 2, "price": 1000},
    {"name": "商品B", "quantity": 1, "price": 2000}
]

actual_items = [
    {"name": "商品A", "quantity": 2, "price": 1000},
    {"name": "商品B", "quantity": 1, "price": 1500}  # 価格が違う
]

# 各明細項目の各フィールドを個別評価
results = []
for item_idx, (expected, actual) in enumerate(zip(expected_items, actual_items)):
    # 商品名
    results.append(FieldResult.create_correct(
        "items.name", expected["name"], actual["name"], 3.0, item_idx
    ))
    
    # 数量
    results.append(FieldResult.create_correct(
        "items.quantity", expected["quantity"], actual["quantity"], 2.0, item_idx
    ))
    
    # 価格（アイテム1は不正解）
    if expected["price"] == actual["price"]:
        results.append(FieldResult.create_correct(
            "items.price", expected["price"], actual["price"], 2.0, item_idx
        ))
    else:
        results.append(FieldResult.create_incorrect(
            "items.price", expected["price"], actual["price"], 2.0, item_idx
        ))

# 結果分析
collection = FieldResultCollection(results)
analysis_service = collection.get_analysis_service()
item_summary = analysis_service.get_item_summary()
# アイテム0: 100% (全て正解)
# アイテム1: 71.4% (価格のみ不正解)
```

## バリデーション

### 不変条件
1. **重みの非負性**: `weight >= 0`
2. **スコアの非負性**: `score >= 0`
3. **正解時の一貫性**: `is_correct == True` なら `score == weight`
4. **不正解時の一貫性**: `is_correct == False` なら `score == 0`

### エラーハンドリング
```python
# 不正な値でのバリデーションエラー
try:
    FieldResult(
        field_name="test",
        expected_value="expected",
        actual_value="actual",
        weight=-1.0,  # 負の重み
        score=0.0,
        is_correct=False
    )
except ValueError as e:
    print(f"バリデーションエラー: {e}")
```

## 関連クラス

### FieldScoreCalculator
FieldResultを生成するStrategy パターンの実装。フィールドタイプに応じた評価ロジックを提供。

### FieldResultCollection
FieldResultのコレクション管理と分析サービスへのアクセス提供。

### FieldResultAnalysisService
FieldResultの高度な集計・分析機能を提供。詳細は[FieldResultAnalysisService](../services/field-result-analysis-service.md)を参照。

### ExtractionResult
FieldResultのコレクションを保持し、文書全体の抽出結果を管理。

## アーキテクチャ上の位置づけ

FieldResultは精度評価システムの中核として、以下の役割を担います：

1. **統一的な評価結果の表現** - すべてのフィールドを同じ形式で管理
2. **明細項目の個別管理** - item_indexによる階層構造の平坦化
3. **拡張可能な詳細情報** - detailsフィールドによる柔軟な情報格納
4. **集計処理の基盤** - FieldResultAnalysisServiceによる高度な分析