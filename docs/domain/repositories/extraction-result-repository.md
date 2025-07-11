# 抽出結果リポジトリインターフェース

## 概要
抽出結果エンティティの永続化を抽象化するリポジトリインターフェース。実験結果の保存と検索機能を提供する。

## ExtractionResultRepository インターフェース

### 責務
- 抽出結果の保存と取得
- ドキュメントIDによる検索
- バッチ処理のサポート

### メソッド定義

#### save
```
save(result: ExtractionResult) -> None
```
抽出結果を保存する。

**前提条件**:
- resultは有効なExtractionResultインスタンス
- document_idが設定されている

**事後条件**:
- 抽出結果が永続化される

#### save_batch
```
save_batch(results: List[ExtractionResult]) -> None
```
複数の抽出結果を一括保存する。

**前提条件**:
- すべてのresultが有効
- トランザクション内で実行

**事後条件**:
- すべての結果が保存されるか、すべて失敗する（原子性）

#### find_by_id
```
find_by_id(result_id: str) -> Optional[ExtractionResult]
```
IDで抽出結果を取得する。

**戻り値**:
- 存在する場合: ExtractionResultインスタンス
- 存在しない場合: None

#### find_by_document_id
```
find_by_document_id(document_id: str) -> List[ExtractionResult]
```
ドキュメントIDで抽出結果を検索する。

**戻り値**:
- 同一ドキュメントの全抽出結果（複数バージョンを含む）
- 時系列順でソート

#### find_by_experiment
```
find_by_experiment(experiment_id: str) -> List[ExtractionResult]
```
実験IDに関連する全抽出結果を取得する。

**戻り値**:
- 指定実験の全抽出結果
- ドキュメントID順でソート

#### find_latest_by_document
```
find_latest_by_document(document_id: str) -> Optional[ExtractionResult]
```
ドキュメントの最新の抽出結果を取得する。

**戻り値**:
- 最新の抽出結果
- 存在しない場合: None

### 検索条件

#### DocumentFilter
```
{
  document_type: Optional[DocumentType]
  date_range: Optional[DateRange]
  customer_id: Optional[int]
}
```

#### find_by_criteria
```
find_by_criteria(filter: DocumentFilter) -> List[ExtractionResult]
```
条件に基づいて抽出結果を検索する。

### パフォーマンス考慮事項

#### インデックス推奨
- document_id
- experiment_id
- created_at
- document_type

#### バッチ処理
- 大量データの効率的な保存
- ストリーミング対応の検索

## 関連インターフェース

### AccuracyMetricRepository
精度評価結果を別途管理する場合のインターフェース。

```
save_metric(
  extraction_result_id: str,
  metric: AccuracyMetric
) -> None

find_metric(
  extraction_result_id: str
) -> Optional[AccuracyMetric]
```

### ExtractionResultQueryService
複雑な分析クエリ用の読み取り専用サービス。

```
get_accuracy_trends(
  period: DateRange,
  grouping: TimeGrouping
) -> AccuracyTrend

get_field_statistics(
  field_name: str
) -> FieldStatistics
```

## 実装の配置
具体的な実装：
- `infrastructure/repositories/file_extraction_result_repository.py`
- `infrastructure/repositories/database_extraction_result_repository.py`

## トランザクション管理
- save_batchは原子性を保証
- 実験との整合性はアプリケーション層で管理