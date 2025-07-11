# 実験リポジトリインターフェース

## 概要
実験エンティティの永続化を抽象化するリポジトリインターフェース。ドメイン層で定義し、インフラストラクチャ層で実装する。

## ExperimentRepository インターフェース

### 責務
- 実験エンティティの保存と取得
- 実験の検索機能提供
- ドメイン層の永続化要求を抽象化

### メソッド定義

#### save
```
save(experiment: Experiment) -> None
```
実験を保存する。新規作成と更新の両方に対応。

**前提条件**:
- experimentは有効なExperimentインスタンス
- experiment_idが設定されている

**事後条件**:
- 実験が永続化される
- 既存の場合は更新される

#### find_by_id
```
find_by_id(experiment_id: str) -> Optional[Experiment]
```
IDで実験を取得する。

**戻り値**:
- 存在する場合: Experimentインスタンス
- 存在しない場合: None

#### find_by_name
```
find_by_name(name: str) -> List[Experiment]
```
名前で実験を検索する。部分一致で検索。

**戻り値**:
- マッチする実験のリスト（0件の場合は空リスト）

#### find_recent
```
find_recent(limit: int = 10) -> List[Experiment]
```
最近の実験を取得する。

**パラメータ**:
- limit: 取得する実験数（デフォルト: 10）

**戻り値**:
- 実行日時の降順でソートされた実験リスト

#### find_by_status
```
find_by_status(status: ExperimentStatus) -> List[Experiment]
```
ステータスで実験を検索する。

**戻り値**:
- 指定ステータスの実験リスト

#### find_by_dataset
```
find_by_dataset(dataset_name: str) -> List[Experiment]
```
使用したデータセット名で実験を検索する。

**戻り値**:
- 指定データセットを使用した実験リスト

#### exists
```
exists(experiment_id: str) -> bool
```
実験の存在確認。

**戻り値**:
- 存在する場合: True
- 存在しない場合: False

### トランザクション境界
- 各メソッドは独立したトランザクション境界を持つ
- アプリケーション層でより大きなトランザクションを管理

### 実装時の考慮事項

#### パフォーマンス
- 大量の実験データに対応できる実装
- インデックスの適切な使用
- ページネーションのサポート（将来）

#### 整合性
- 実験の状態遷移時の排他制御
- 同時更新の防止

#### エラーハンドリング
- 永続化失敗時の適切な例外
- リトライ可能なエラーの識別

## 関連インターフェース

### ExperimentResultRepository
実験結果の詳細データを管理する場合に使用（オプション）。

```
save_results(experiment_id: str, results: List[DocumentResult]) -> None
find_results(experiment_id: str) -> List[DocumentResult]
```

### ExperimentQueryService
複雑な検索要件に対応する読み取り専用サービス（CQRS適用時）。

```
search(criteria: SearchCriteria) -> SearchResult
get_statistics(period: DateRange) -> ExperimentStatistics
```

## 実装例の配置
具体的な実装は以下に配置：
- `infrastructure/repositories/file_experiment_repository.py`
- `infrastructure/repositories/langfuse_experiment_repository.py`

これらの実装はこのインターフェースに準拠する必要がある。