# フィールド結果分析サービス

## 概要
FieldResultの分析・集計機能を提供するドメインサービス。FieldResultCollectionから分離されたビジネスロジックを担当。

## FieldResultAnalysisService クラス

### 責務
- FieldResultの分析・集計機能の提供
- 検索・分類機能の提供
- 精度計算とサマリー生成

### 主要メソッド

#### 検索機能
```python
def get_by_field_name(self, field_name: str) -> List[FieldResult]:
    """指定フィールド名の結果を取得"""

def get_by_item_index(self, item_index: int) -> List[FieldResult]:
    """指定アイテムインデックスの結果を取得"""

def get_by_field_and_item(self, field_name: str, item_index: int) -> Optional[FieldResult]:
    """指定フィールド名とアイテムインデックスの結果を取得"""
```

#### 分類機能
```python
def get_items_results(self) -> List[FieldResult]:
    """アイテム関連の結果を取得"""

def get_non_items_results(self) -> List[FieldResult]:
    """アイテム以外の結果を取得"""
```

#### 集計機能
```python
def calculate_overall_accuracy(self) -> float:
    """全体精度を計算"""

def calculate_items_accuracy(self) -> float:
    """アイテム関連の精度を計算"""

def get_item_summary(self) -> Dict[int, Dict[str, Any]]:
    """アイテム別のサマリーを取得"""

def get_field_accuracy_summary(self) -> Dict[str, Dict[str, Any]]:
    """フィールド別の精度サマリーを取得"""

def get_field_accuracies(self) -> Dict[str, bool]:
    """各フィールドの正解/不正解を取得"""
```

## 使用例

### 基本的な使用方法
```python
from src.domain.models.field_result import FieldResult, FieldResultCollection

# FieldResultのリストを作成
results = [
    FieldResult.create_correct("total_price", 1000, 1000, 3.0),
    FieldResult.create_incorrect("tax_price", 1000, 2000, 3.0),
    FieldResult.create_correct("items.name", "商品A", "商品A", 3.0, item_index=0),
    FieldResult.create_correct("items.quantity", 2, 2, 2.0, item_index=0),
]

# コレクションを作成して分析サービスを取得
collection = FieldResultCollection(results)
analysis_service = collection.get_analysis_service()

# 全体精度を計算
overall_accuracy = analysis_service.calculate_overall_accuracy()
print(f"全体精度: {overall_accuracy:.1%}")  # 全体精度: 72.7%
```

### 検索機能の使用
```python
# フィールド名による検索
items_name_results = analysis_service.get_by_field_name("items.name")
print(f"items.nameの結果数: {len(items_name_results)}")

# アイテムインデックスによる検索
item_0_results = analysis_service.get_by_item_index(0)
print(f"アイテム0の結果数: {len(item_0_results)}")

# 特定のフィールドとアイテムの組み合わせ
specific_result = analysis_service.get_by_field_and_item("items.name", 0)
if specific_result:
    print(f"items.name[0]: {specific_result.is_correct}")
```

### 分類機能の使用
```python
# アイテム関連の結果のみ取得
items_results = analysis_service.get_items_results()
print(f"アイテム関連の結果数: {len(items_results)}")

# アイテム以外の結果のみ取得
non_items_results = analysis_service.get_non_items_results()
print(f"アイテム以外の結果数: {len(non_items_results)}")
```

### 集計機能の使用
```python
# アイテム別サマリーの取得
item_summary = analysis_service.get_item_summary()
for item_index, summary in item_summary.items():
    print(f"アイテム{item_index}:")
    print(f"  精度: {summary['accuracy']:.1%}")
    print(f"  フィールド数: {summary['field_count']}")
    print(f"  正解数: {summary['correct_count']}")

# フィールド別精度サマリーの取得
field_summary = analysis_service.get_field_accuracy_summary()
for field_name, summary in field_summary.items():
    print(f"{field_name}:")
    print(f"  精度: {summary['accuracy']:.1%}")
    print(f"  重み付き精度: {summary['weighted_accuracy']:.1%}")
    print(f"  正解数/総数: {summary['correct_count']}/{summary['total_count']}")

# フィールド別正解状況の取得
field_accuracies = analysis_service.get_field_accuracies()
for field_name, is_correct in field_accuracies.items():
    status = "✓" if is_correct else "✗"
    print(f"{field_name}: {status}")
```

## ExtractionResultとの統合

ExtractionResultクラスでは、FieldResultAnalysisServiceを使用して精度計算を行います。

```python
from src.domain.models.extraction_result import ExtractionResult

# 抽出結果の作成
extraction_result = ExtractionResult(
    document_id="doc-123",
    expected_data=expected_data,
    extracted_data=extracted_data,
    field_results=field_results
)

# 精度の計算（内部でFieldResultAnalysisServiceを使用）
accuracy = extraction_result.calculate_accuracy()
field_accuracies = extraction_result.get_field_accuracies()

print(f"全体精度: {accuracy:.1%}")
for field_name, is_correct in field_accuracies.items():
    print(f"{field_name}: {'✓' if is_correct else '✗'}")
```

## 設計原則

### 1. 単一責任の原則
- FieldResultAnalysisServiceは分析・集計機能のみを担当
- FieldResultCollectionはコレクション管理のみを担当

### 2. 関心の分離
- ビジネスロジックをモデル層から分離
- 適切なサービス層での実装

### 3. 依存性の管理
- FieldResultCollectionからの遅延読み込み
- 循環参照の回避

## アーキテクチャ上の位置づけ

FieldResultAnalysisServiceは以下の役割を担います：

1. **FieldResultの高度な分析** - 複数のFieldResultを横断した分析
2. **集計処理の実装** - 精度計算やサマリー生成
3. **検索・分類機能** - 条件に基づくFieldResultの抽出
4. **ビジネスロジックの集約** - 評価に関するドメインロジック

この設計により、FieldResultCollectionはシンプルなコレクションクラスとして保たれ、複雑なビジネスロジックは適切なサービスクラスに分離されています。