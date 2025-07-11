# AccuracyMetric → FieldResult 完全移行テスト計画

## 概要
AccuracyMetricからFieldResultへの完全移行を安全に実行するためのテスト計画。

## 移行対象ファイル

### 1. ドメインモデル
- [x] `src/domain/models/accuracy_metric.py` → 削除
- [x] `src/domain/models/field_result.py` → 既存

### 2. サービス層
- [ ] `src/domain/services/accuracy_evaluation_service.py` → FieldResultを使用するように変更
- [x] `src/domain/services/field_score_calculator.py` → 既存

### 3. アプリケーション層
- [ ] `src/application/use_cases/run_experiment.py` → FieldResultを使用するように変更

### 4. インフラストラクチャ層
- [ ] `src/infrastructure/repositories/file_experiment_repository.py` → FieldResultを使用するように変更
- [ ] `src/domain/models/extraction_result.py` → FieldResultを使用するように変更
- [ ] `src/domain/models/experiment.py` → FieldResultを使用するように変更

## テスト戦略

### Phase 1: 単体テストの作成/修正
1. **FieldResultの単体テスト**
   - 基本的な作成・操作
   - バリデーション
   - 表示名生成
   - 辞書変換

2. **FieldResultCollectionの単体テスト**
   - 検索機能
   - 集計機能
   - アイテム別分析

3. **新AccuracyEvaluationServiceの単体テスト**
   - FieldScoreCalculatorとの統合
   - 各種フィールドタイプの処理

### Phase 2: 統合テストの作成/修正
1. **ExtractionResultの統合テスト**
   - FieldResultとの統合
   - 精度計算の正確性

2. **Experimentの統合テスト**
   - FieldResultの集計
   - サマリー生成

3. **RunExperimentUseCaseの統合テスト**
   - 実験実行フロー
   - 結果保存フロー

### Phase 3: エンドツーエンドテスト
1. **実験実行テスト**
   - 完全な実験実行フロー
   - 結果ファイルの形式確認
   - HTMLレポート生成

2. **Docker環境テスト**
   - Docker環境での実験実行
   - 結果の整合性確認

## テスト項目詳細

### 1. 機能テスト

#### A. FieldResult基本機能
- [x] 正解/不正解の判定
- [x] スコア計算（重み×正解/不正解）
- [x] アイテムインデックスの管理
- [x] 表示名生成（items.name[0]など）
- [x] 辞書変換

#### B. FieldResultCollection機能
- [x] フィールド名による検索
- [x] アイテムインデックスによる検索
- [x] 全体精度計算
- [x] アイテム別精度計算
- [x] アイテムサマリー生成

#### C. FieldScoreCalculator機能
- [x] 各種Calculator（Simple、Amount、Date、Items）
- [x] Factory による適切なCalculator選択
- [x] アイテムインデックスの処理

### 2. 互換性テスト

#### A. データ形式の互換性
- [ ] 結果JSONファイルの形式
- [ ] HTMLレポートの形式
- [ ] 実験サマリーの形式

#### B. API互換性
- [ ] ExtractionResult.calculate_accuracy()
- [ ] ExtractionResult.get_field_accuracies()
- [ ] Experiment.get_summary()

### 3. 回帰テスト

#### A. 精度計算の正確性
- [ ] 同じ入力で同じ精度結果が得られるか
- [ ] 重み付きスコアの計算が正確か
- [ ] フィールド別精度の計算が正確か

#### B. 実験実行の正確性
- [ ] 実験実行が正常に完了するか
- [ ] 結果ファイルが正しく生成されるか
- [ ] HTMLレポートが正しく生成されるか

### 4. パフォーマンステスト

#### A. 大量データ処理
- [ ] 100個のフィールドでの処理時間
- [ ] 50個のアイテムでの処理時間
- [ ] メモリ使用量の確認

#### B. 処理速度の比較
- [ ] 旧システムとの処理時間比較
- [ ] メモリ使用量の比較

## 実行手順

### Step 1: 事前準備
```bash
# 現在のブランチでテストを実行し、ベースラインを確認
docker-compose run --rm cli python -m pytest tests/ -v
docker-compose run --rm cli python -m src.cli run-experiment --name "消火設備見積書データ抽出テスト_Gemini1.5"
```

### Step 2: 単体テスト実行
```bash
# 新しいFieldResultシステムのテスト
docker-compose run --rm cli python -m pytest tests/unit/domain/models/test_field_result.py -v
docker-compose run --rm cli python -m pytest tests/unit/domain/services/test_field_score_calculator.py -v
```

### Step 3: 移行実装
1. AccuracyEvaluationServiceをFieldResultベースに変更
2. ExtractionResultをFieldResultベースに変更
3. ExperimentをFieldResultベースに変更
4. RunExperimentUseCaseをFieldResultベースに変更
5. FileExperimentRepositoryをFieldResultベースに変更

### Step 4: 統合テスト実行
```bash
# 各コンポーネントの統合テスト
docker-compose run --rm cli python -m pytest tests/integration/ -v
```

### Step 5: エンドツーエンドテスト実行
```bash
# 実験実行テスト
docker-compose run --rm cli python -m src.cli run-experiment --name "消火設備見積書データ抽出テスト_Gemini1.5"

# 結果ファイルの確認
ls -la results/
cat results/最新の結果ファイル.json | jq .

# HTMLレポート生成テスト
docker-compose run --rm cli python -m src.cli generate-report "results/最新の結果ファイル.json"
```

### Step 6: 回帰テスト実行
```bash
# 移行前後の結果比較
# 1. 移行前の結果をバックアップ
# 2. 移行後の結果を生成
# 3. 精度計算結果を比較
```

## 成功基準

### 1. 機能面
- [ ] 全ての単体テストが成功
- [ ] 全ての統合テストが成功
- [ ] エンドツーエンドテストが成功
- [ ] 移行前後で精度計算結果が同じ

### 2. 性能面
- [ ] 処理時間が移行前の120%以内
- [ ] メモリ使用量が移行前の150%以内

### 3. 品質面
- [ ] コードカバレッジが80%以上
- [ ] 全てのエラーケースが処理される
- [ ] ドキュメントが更新される

## リスク対策

### 1. 移行失敗時の回復方法
- 前回のコミット（ea2ec9a）にロールバック
- 段階的移行の再検討

### 2. データ破損の防止
- 移行前の結果ファイルのバックアップ
- テストデータでの事前検証

### 3. パフォーマンス劣化の対策
- プロファイリングツールの使用
- 必要に応じたボトルネックの改善

## 実行スケジュール

1. **テスト作成**: 30分
2. **移行実装**: 60分
3. **テスト実行**: 30分
4. **回帰テスト**: 30分
5. **ドキュメント更新**: 15分

**総予定時間**: 2時間45分