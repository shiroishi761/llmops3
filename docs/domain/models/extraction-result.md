# 抽出結果ドメインモデル

## 概要
文書からの抽出結果を表現するドメインモデル。FieldResultシステムと統合されており、精度評価結果も含む。

## ExtractionResult エンティティ

### 責務
- 文書の抽出結果を統一的に管理
- FieldResultコレクションによる精度評価結果の管理
- 抽出処理の成功/失敗状態の管理

### 主要な属性

#### 基本情報
- `document_id`: 文書の一意識別子
- `expected_data`: 期待される抽出データ（辞書形式）
- `extracted_data`: 実際に抽出されたデータ（辞書形式）
- `created_at`: 作成日時

#### 結果情報
- `field_results`: フィールド評価結果のリスト（List[FieldResult]）
- `extraction_time_ms`: 抽出にかかった時間（ミリ秒）
- `error`: エラーメッセージ（エラー時のみ）

### 主要なメソッド

#### 成功判定
```python
def is_success(self) -> bool:
    """抽出が成功したかを判定"""
    return self.error is None
```

#### 全体精度計算
```python
def calculate_accuracy(self) -> float:
    """全体の精度を計算（0.0〜1.0）"""
    if not self.field_results:
        return 0.0
    
    collection = FieldResultCollection(self.field_results)
    return collection.calculate_overall_accuracy()
```

#### フィールド別精度取得
```python
def get_field_accuracies(self) -> Dict[str, bool]:
    """各フィールドの正解/不正解を取得"""
    result = {}
    for field_result in self.field_results:
        display_name = field_result.get_display_name()
        result[display_name] = field_result.is_correct
    return result
```

#### FieldResultCollection取得
```python
def get_field_results_collection(self) -> FieldResultCollection:
    """FieldResultCollectionを取得"""
    return FieldResultCollection(self.field_results)
```

## FieldResultとの統合

### 関係性
- ExtractionResultは複数のFieldResultを保持
- FieldResultCollectionを通じて高度な集計・分析が可能

### 典型的な使用パターン

#### 基本的な評価
```python
# 抽出結果の作成
result = ExtractionResult(
    document_id="doc-123",
    expected_data={"total_price": 1000, "tax_price": 100},
    extracted_data={"total_price": 1000, "tax_price": 90},
    field_results=[
        FieldResult.create_correct("total_price", 1000, 1000, 3.0),
        FieldResult.create_incorrect("tax_price", 100, 90, 2.0)
    ]
)

# 全体精度の計算
accuracy = result.calculate_accuracy()  # 0.6 (3.0 / 5.0)

# フィールド別精度
field_accuracies = result.get_field_accuracies()
# {"total_price": True, "tax_price": False}
```

#### 明細項目の評価
```python
# 明細項目を含む結果
result = ExtractionResult(
    document_id="doc-456",
    expected_data={"items": [{"name": "商品A", "quantity": 2}]},
    extracted_data={"items": [{"name": "商品A", "quantity": 2}]},
    field_results=[
        FieldResult.create_correct("items.name", "商品A", "商品A", 3.0, item_index=0),
        FieldResult.create_correct("items.quantity", 2, 2, 2.0, item_index=0)
    ]
)

# アイテム別分析
collection = result.get_field_results_collection()
item_summary = collection.get_item_summary()
# {0: {'accuracy': 1.0, 'total_weight': 5.0, 'total_score': 5.0}}
```

## データ構造の例

### 正常な抽出結果
```json
{
  "document_id": "doc-123",
  "expected_data": {
    "total_price": 1000,
    "tax_price": 100,
    "items": [
      {"name": "商品A", "quantity": 2, "price": 500}
    ]
  },
  "extracted_data": {
    "total_price": 1000,
    "tax_price": 90,
    "items": [
      {"name": "商品A", "quantity": 2, "price": 500}
    ]
  },
  "field_results": [
    {
      "field_name": "total_price",
      "expected_value": 1000,
      "actual_value": 1000,
      "weight": 3.0,
      "score": 3.0,
      "is_correct": true,
      "item_index": null
    },
    {
      "field_name": "tax_price",
      "expected_value": 100,
      "actual_value": 90,
      "weight": 2.0,
      "score": 0.0,
      "is_correct": false,
      "item_index": null
    },
    {
      "field_name": "items.name",
      "expected_value": "商品A",
      "actual_value": "商品A",
      "weight": 3.0,
      "score": 3.0,
      "is_correct": true,
      "item_index": 0
    }
  ],
  "extraction_time_ms": 1200,
  "error": null,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### エラー時の結果
```json
{
  "document_id": "doc-456",
  "expected_data": {"total_price": 1000},
  "extracted_data": {},
  "field_results": [],
  "extraction_time_ms": null,
  "error": "LLM request failed: Connection timeout",
  "created_at": "2024-01-15T10:35:00Z"
}
```

## 設計原則

### 1. 統一性
- 全てのフィールドはFieldResultとして統一的に管理
- 明細項目もitem_indexを用いて統一的に処理

### 2. 透明性
- 抽出結果と期待結果の両方を保存
- エラー情報も含めて完全な実行履歴を記録

### 3. 分析可能性
- FieldResultCollectionによる高度な集計機能
- アイテム別、フィールド別の詳細分析が可能

### 4. 拡張性
- 新しいフィールドタイプの追加が容易
- カスタムCalculatorによる評価ロジックの拡張が可能

## ドメインサービスとの連携

### AccuracyEvaluationService
```python
# 精度評価サービスによる評価
service = AccuracyEvaluationService()
field_results = service.evaluate_extraction(
    expected_data, extracted_data, field_weights, default_weight
)

# 結果の作成
result = ExtractionResult(
    document_id=document_id,
    expected_data=expected_data,
    extracted_data=extracted_data,
    field_results=field_results
)
```

### Experimentとの連携
```python
# 実験への結果追加
experiment = Experiment(id="exp-001", name="テスト実験")
experiment.add_result(result)

# 実験全体の精度計算
overall_accuracy = experiment.calculate_overall_accuracy()
```

## 移行履歴

### v1.0 → v2.0 (FieldResult統合)
- `accuracy_metrics` → `field_results`
- AccuracyMetricクラスの削除
- FieldResultシステムの統合
- 統一的なスコア計算方式の採用

### 後方互換性
- JSONフォーマットの基本構造は維持
- 集計計算の結果は同等
- API インターフェースの変更は最小限