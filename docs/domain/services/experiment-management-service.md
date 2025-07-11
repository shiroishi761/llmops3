# 実験管理ドメインサービス

## 概要
LLM精度検証実験の実行と管理を行うドメインサービス。実験のライフサイクル全体を制御する。

## ExperimentManagementService

### 責務
- 実験の作成と初期化
- 実験状態の管理
- 実験実行の調整
- 結果の集約

### 主要メソッド

#### create_experiment
```
create_experiment(
  name: str,
  prompt_name: str,
  dataset_name: str,
  endpoint: str,
  config: ExperimentConfig
) -> Experiment
```
新しい実験を作成し、初期状態で保存。

#### start_experiment
```
start_experiment(experiment_id: str) -> None
```
実験を開始し、状態をRUNNINGに変更。

#### process_document_result
```
process_document_result(
  experiment_id: str,
  document_id: str,
  result: DocumentResult
) -> None
```
個別ドキュメントの処理結果を記録。

#### complete_experiment
```
complete_experiment(experiment_id: str) -> ExperimentSummary
```
実験を完了し、最終的なサマリーを生成。

### 実験実行フロー

1. **実験の準備**
   - 実験設定の検証
   - データセットの存在確認
   - プロンプトの存在確認

2. **実行管理**
   - 並列実行数の制御
   - 進捗の追跡
   - エラーハンドリング

3. **結果の集約**
   - 個別結果の収集
   - 統計情報の計算
   - サマリーの生成

### ビジネスルール

#### 状態遷移
```
PENDING → RUNNING → COMPLETED
              ↓
           FAILED
```

#### 並列実行制御
- デフォルト: 5並列
- 最大: 20並列
- 最小: 1（順次実行）

#### リトライポリシー
- 最大リトライ: 5回
- バックオフ: 指数関数的（1, 2, 4, 8, 16秒）
- リトライ対象: タイムアウト、一時的エラー

### 協調するモデル・サービス
- `Experiment`: 実験エンティティ
- `ExperimentRepository`: 実験の永続化
- `AccuracyEvaluationService`: 精度評価の実行

## ExperimentComparisonService

### 責務
- 複数実験の比較
- ランキングの生成
- 改善点の特定

### 主要メソッド

#### compare_experiments
```
compare_experiments(
  experiment_ids: List[str]
) -> ComparisonResult
```
複数の実験を比較し、ランキングを生成。

#### find_best_experiment
```
find_best_experiment(
  criteria: ComparisonCriteria
) -> Experiment
```
指定された基準で最良の実験を特定。

### 比較基準
- **精度順**: overall_accuracyで降順ソート
- **速度順**: average_execution_timeで昇順ソート
- **成功率順**: success_rateで降順ソート
- **複合評価**: 重み付きスコアで評価

## ExperimentValidationService

### 責務
- 実験設定の妥当性検証
- 前提条件の確認
- 警告の生成

### 主要メソッド

#### validate_configuration
```
validate_configuration(
  config: ExperimentConfig
) -> ValidationResult
```
実験設定の妥当性を検証。

#### check_prerequisites
```
check_prerequisites(
  prompt_name: str,
  dataset_name: str,
  endpoint: str
) -> PrerequisiteCheckResult
```
実験実行の前提条件を確認。

### 検証項目
1. **設定値の範囲**
   - 並列実行数: 1-20
   - タイムアウト: 30-600秒
   - リトライ回数: 0-10

2. **リソースの存在**
   - プロンプトの登録確認
   - データセットの存在確認
   - エンドポイントの有効性

3. **データセットの妥当性**
   - 最小サンプル数: 1
   - 最大サンプル数: 10000
   - データ形式の一貫性

## ドメインイベント

実験管理で発生するイベント：

### ExperimentStarted
```
{
  experiment_id: str
  started_at: datetime
  total_documents: int
}
```

### DocumentProcessed
```
{
  experiment_id: str
  document_id: str
  success: bool
  accuracy: float
  processed_at: datetime
}
```

### ExperimentCompleted
```
{
  experiment_id: str
  completed_at: datetime
  summary: ExperimentSummary
}
```

これらのイベントは監査ログや通知に使用される。