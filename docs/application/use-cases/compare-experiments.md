# 実験比較ユースケース

## 概要
複数の実験結果を比較し、最適な設定を特定するユースケース。

## CompareExperimentsUseCase

### 責務
- 実験結果の読み込み
- 比較基準に基づく評価
- ランキングの生成
- 改善提案の作成

### 依存関係
- Domain層: Experiment, ExperimentComparisonService
- Infrastructure層: FileService, ExperimentRepository

### 主要メソッド

#### compare
```
compare(
  experiment_ids: List[str],
  criteria: ComparisonCriteriaDto
) -> ComparisonResultDto
```
指定された実験を比較する。

#### compare_all_recent
```
compare_all_recent(
  limit: int = 10,
  criteria: ComparisonCriteriaDto = None
) -> ComparisonResultDto
```
最近の実験を比較する。

### 比較基準

#### ComparisonCriteriaDto
```
{
  primary_metric: str  # "accuracy" | "speed" | "success_rate"
  secondary_metrics: List[str]
  weights: Dict[str, float]
  minimum_thresholds: Dict[str, float]
}
```

#### デフォルト基準
```
{
  primary_metric: "accuracy",
  weights: {
    "accuracy": 0.6,
    "speed": 0.2,
    "success_rate": 0.2
  }
}
```

### 処理の詳細

#### 1. 実験データの収集
```
- 指定された実験を読み込み
- 必要なメトリクスを抽出
- データの正規化
```

#### 2. スコア計算
```
for each experiment:
  score = Σ(metric_value × weight)
  normalized_score = score / max_possible_score
```

#### 3. ランキング生成
```
- スコア順でソート
- 同点の場合は実行日時で判定
- 上位N件を選出
```

#### 4. 分析結果の生成
```
- 最良実験の特定
- 各実験の強み・弱み
- 改善提案
```

### 出力DTO

#### ComparisonResultDto
```
{
  comparison_id: str
  compared_at: datetime
  experiments: List[ExperimentComparisonDto]
  best_experiment: ExperimentSummaryDto
  analysis: AnalysisDto
}
```

#### ExperimentComparisonDto
```
{
  experiment_id: str
  name: str
  rank: int
  overall_score: float
  metrics: Dict[str, float]
  strengths: List[str]
  weaknesses: List[str]
}
```

#### AnalysisDto
```
{
  summary: str
  recommendations: List[str]
  trends: List[TrendDto]
}
```

### 比較ビュー

#### 表形式出力
```
実験比較結果:
┌─────────────────┬──────────┬────────┬──────────┐
│ 実験名          │ 精度     │ 速度   │ 成功率   │
├─────────────────┼──────────┼────────┼──────────┤
│ prompt_v2_exp   │ 94.0%    │ 2.5s   │ 96.0%    │
│ prompt_v1_exp   │ 92.0%    │ 2.2s   │ 98.0%    │
└─────────────────┴──────────┴────────┴──────────┘
```

#### フィールド別比較
```
フィールド精度比較:
- total_price:    v2: 98% > v1: 95%
- items:          v2: 88% < v1: 90%
- doc_type:       v2: 99% = v1: 99%
```

### 高度な分析

#### トレンド分析
```
- 時系列での精度推移
- プロンプト変更の影響
- エラー率の変化
```

#### 相関分析
```
- データセットサイズと精度
- 実行時間と成功率
- プロンプト長と精度
```

### フィルタリング

#### 実験の絞り込み
```
- 期間指定
- データセット指定
- 最小精度指定
```

### 実装時の注意点

#### パフォーマンス
- 大量実験データの効率的な読み込み
- メモリ効率的な比較処理

#### 拡張性
- 新しい比較基準の追加
- カスタムメトリクスのサポート

## 協調するユースケース
- `RunExperimentUseCase`: 実験実行
- `ExportResultsUseCase`: 比較結果のエクスポート