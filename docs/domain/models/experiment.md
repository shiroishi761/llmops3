# 実験ドメインモデル

## 概要
LLMの精度検証実験を表現するドメインモデル。実験の設定、実行、結果を管理する集約ルート。

## Experiment エンティティ

### 責務
- 実験の一貫性を保証
- 実験状態の管理
- 実験結果の集約（FieldResultベース）

### 主要な属性

#### 実験識別情報
- `id`: 実験の一意識別子
- `name`: 実験名
- `created_at`: 作成日時
- `completed_at`: 完了日時（完了時のみ）

#### 実験設定
- `prompt_name`: 使用するプロンプト名（Langfuse参照）
- `dataset_name`: 使用するデータセット名（Langfuse参照）
- `llm_endpoint`: 使用するLLMエンドポイント
- `description`: 実験の説明（任意）

#### 実験状態
- `status`: 実験状態（ExperimentStatus enum）
- `results`: 各ドキュメントの結果コレクション（List[ExtractionResult]）
- `metadata`: 追加メタデータ（辞書形式）

### 主要なメソッド

#### 結果追加
```python
def add_result(self, result: ExtractionResult) -> None:
    """抽出結果を追加"""
    self.results.append(result)
```

#### 状態遷移
```python
def mark_as_running(self) -> None:
    """実験を実行中に変更"""
    self.status = ExperimentStatus.RUNNING

def mark_as_completed(self) -> None:
    """実験を完了に変更"""
    self.status = ExperimentStatus.COMPLETED
    self.completed_at = datetime.now()

def mark_as_failed(self, error: str) -> None:
    """実験を失敗に変更"""
    self.status = ExperimentStatus.FAILED
    self.metadata["error"] = error
    self.completed_at = datetime.now()
```

#### 全体精度計算
```python
def calculate_overall_accuracy(self) -> float:
    """全体の精度を計算"""
    if not self.results:
        return 0.0
        
    successful_results = [r for r in self.results if r.is_success()]
    if not successful_results:
        return 0.0
        
    accuracies = [r.calculate_accuracy() for r in successful_results]
    return sum(accuracies) / len(accuracies)
```

#### フィールド別精度計算
```python
def calculate_field_accuracies(self) -> Dict[str, float]:
    """フィールド別の精度を計算"""
    field_stats: Dict[str, Dict[str, int]] = {}
    
    for result in self.results:
        if not result.is_success():
            continue
            
        for field_name, is_correct in result.get_field_accuracies().items():
            if field_name not in field_stats:
                field_stats[field_name] = {"correct": 0, "total": 0}
                
            field_stats[field_name]["total"] += 1
            if is_correct:
                field_stats[field_name]["correct"] += 1
    
    return {
        field_name: stats["correct"] / stats["total"] if stats["total"] > 0 else 0.0
        for field_name, stats in field_stats.items()
    }
```

#### フィールド別スコア計算
```python
def calculate_field_scores(self) -> Dict[str, Dict[str, float]]:
    """フィールド別の重み付きスコアを計算"""
    field_scores: Dict[str, Dict[str, float]] = {}
    
    for result in self.results:
        if not result.is_success():
            continue
            
        for field_result in result.field_results:
            field_name = field_result.get_display_name()
            if field_name not in field_scores:
                field_scores[field_name] = {
                    "total_weight": 0.0,
                    "total_score": 0.0,
                    "weight": field_result.weight
                }
            field_scores[field_name]["total_weight"] += field_result.weight
            field_scores[field_name]["total_score"] += field_result.score
    
    # 平均スコアを計算
    result = {}
    for field_name, scores in field_scores.items():
        if scores["total_weight"] > 0:
            result[field_name] = {
                "score": scores["total_score"] / scores["total_weight"],
                "weight": scores["weight"]
            }
        else:
            result[field_name] = {
                "score": 0.0,
                "weight": scores["weight"]
            }
    
    return result
```

#### 実験サマリー取得
```python
def get_summary(self) -> Dict[str, Any]:
    """実験のサマリーを取得"""
    successful_count = sum(1 for r in self.results if r.is_success())
    failed_count = sum(1 for r in self.results if not r.is_success())
    
    return {
        "total_documents": len(self.results),
        "successful_count": successful_count,
        "failed_count": failed_count,
        "overall_accuracy": self.calculate_overall_accuracy(),
        "field_accuracies": self.calculate_field_accuracies(),
        "field_scores": self.calculate_field_scores(),
        "status": self.status.value,
        "execution_time_ms": self._calculate_execution_time()
    }
```

## ExperimentStatus Enum

```python
class ExperimentStatus(Enum):
    """実験のステータス"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
```

## 典型的な使用例

### 基本的な実験実行
```python
# 実験の作成
experiment = Experiment(
    id="exp-001",
    name="請求書抽出実験",
    prompt_name="invoice_prompt_v1",
    dataset_name="invoice_dataset",
    llm_endpoint="llm/gemini/1.5-flash"
)

# 実験開始
experiment.mark_as_running()

# 各ドキュメントの処理結果を追加
for document in documents:
    result = process_document(document)
    experiment.add_result(result)

# 実験完了
experiment.mark_as_completed()

# サマリーの取得
summary = experiment.get_summary()
print(f"全体精度: {summary['overall_accuracy']:.1%}")
```

### フィールド別分析
```python
# フィールド別精度の確認
field_accuracies = experiment.calculate_field_accuracies()
for field_name, accuracy in field_accuracies.items():
    print(f"{field_name}: {accuracy:.1%}")

# フィールド別スコア（重み付き）の確認
field_scores = experiment.calculate_field_scores()
for field_name, score_info in field_scores.items():
    print(f"{field_name}: {score_info['score']:.2f} (重み: {score_info['weight']})")
```

## FieldResultとの統合

### 関係性
- ExperimentはExtractionResultのコレクションを保持
- ExtractionResultはFieldResultのコレクションを保持
- 階層的な集計が可能

### 集計機能
```python
# 実験全体のFieldResultを収集
all_field_results = []
for result in experiment.results:
    if result.is_success():
        all_field_results.extend(result.field_results)

# 全体的な分析
collection = FieldResultCollection(all_field_results)
overall_accuracy = collection.calculate_overall_accuracy()
item_summary = collection.get_item_summary()
```

## データ構造の例

### 実験サマリー
```json
{
  "total_documents": 10,
  "successful_count": 8,
  "failed_count": 2,
  "overall_accuracy": 0.85,
  "field_accuracies": {
    "total_price": 0.9,
    "tax_price": 0.8,
    "items.name[0]": 0.85,
    "items.quantity[0]": 0.9
  },
  "field_scores": {
    "total_price": {
      "score": 0.9,
      "weight": 3.0
    },
    "tax_price": {
      "score": 0.8,
      "weight": 2.0
    }
  },
  "status": "completed",
  "execution_time_ms": 45000
}
```

## 集約ルートとしての責務

### 1. 整合性の保証
- 実験状態と結果の一貫性を維持
- 実験完了時の自動的なサマリー更新

### 2. ビジネスルールの実装
- 状態遷移のルール（PENDING → RUNNING → COMPLETED/FAILED）
- 結果の有効性チェック

### 3. 集約操作の提供
- 複数の結果を横断した統計計算
- フィールド別、アイテム別の詳細分析

## 不変条件

1. **結果の一貫性**: successful_count + failed_count = total_documents
2. **精度の範囲**: すべての精度スコアは0.0から1.0の範囲
3. **状態の妥当性**: 完了状態では処理が完了している
4. **時刻の一貫性**: completed_at >= created_at

## 設計パターン

### 1. 集約ルートパターン
- Experimentが関連するすべてのエンティティを管理
- 外部からの操作は必ずExperimentを通じて実行

### 2. 状態パターン
- ExperimentStatusによる明確な状態管理
- 状態遷移の制御と検証

### 3. 戦略パターン
- 異なる精度計算方法の選択
- 集計方法のカスタマイズ

## 移行履歴

### v1.0 → v2.0 (FieldResult統合)
- AccuracyMetricからFieldResultへの移行
- 集計メソッドの更新
- サマリー形式の統一

### 後方互換性
- 基本的なAPIインターフェースは維持
- サマリーの構造は変更されたが、計算結果は等価