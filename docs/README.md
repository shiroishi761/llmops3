# LLMOps精度検証基盤 仕様書

## 概要
既存のRailsプロダクトからLLM機能を分離し、プロンプト管理・精度検証・モニタリング基盤を構築するプロジェクトの仕様書。レイヤードアーキテクチャとドメイン駆動設計（DDD）に基づいて設計されています。

## システム構成
```
Rails Product → FastAPI (LLM API) ← Langfuse (プロンプト管理・モニタリング)
```

## アーキテクチャ

### レイヤー構成
本システムは4層のレイヤードアーキテクチャを採用：

1. **インターフェース層** - 外部との通信を管理
2. **アプリケーション層** - ユースケースの実装
3. **ドメイン層** - ビジネスロジック（他層に依存しない）
4. **インフラストラクチャ層** - 技術的詳細の実装

詳細は[アーキテクチャ概要](architecture/overview.md)を参照。

## ドキュメント構成

### architecture/ - アーキテクチャ設計
- [アーキテクチャ概要](architecture/overview.md)
- [レイヤー依存関係](architecture/layer-dependencies.md)

### domain/ - ドメイン層
ビジネスロジックとルールの定義。

#### models/ - ドメインモデル
- [抽出結果](domain/models/extraction-result.md)
- [実験](domain/models/experiment.md)
- [フィールド結果](domain/models/field-result.md) - 統一的な精度評価システム

#### services/ - ドメインサービス
- [精度評価サービス](domain/services/accuracy-evaluation-service.md)
- [フィールドスコア計算サービス](domain/services/field-score-calculator.md)
- [フィールド結果分析サービス](domain/services/field-result-analysis-service.md)
- [実験管理サービス](domain/services/experiment-management-service.md)

#### repositories/ - リポジトリインターフェース
- [実験リポジトリ](domain/repositories/experiment-repository.md)
- [抽出結果リポジトリ](domain/repositories/extraction-result-repository.md)

### application/ - アプリケーション層
ユースケースとデータ転送オブジェクトの定義。

#### use-cases/ - ユースケース
- [実験実行](application/use-cases/run-experiment.md)
- [文書抽出](application/use-cases/extract-document.md)
- [実験比較](application/use-cases/compare-experiments.md)

#### dto/ - データ転送オブジェクト
- [DTO定義](application/dto/dto-definitions.md)

### infrastructure/ - インフラストラクチャ層
外部サービスとの連携や永続化の実装。

#### external-services/ - 外部サービス
- [Langfuse連携](infrastructure/external-services/langfuse.md)
- [Gemini API連携](infrastructure/external-services/gemini.md)

#### repositories/ - リポジトリ実装
- [ファイルリポジトリ](infrastructure/repositories/file-repositories.md)

#### config/ - 設定管理
- [設定管理](infrastructure/config/configuration.md)

### interfaces/ - インターフェース層
APIエンドポイントとスキーマ定義。

#### api/ - APIエンドポイント
- [エンドポイント仕様](interfaces/api/endpoints.md)

#### schemas/ - スキーマ定義
- [リクエスト・レスポンス](interfaces/schemas/request-response.md)

## 主要な特徴

### 1. 動的なエンドポイント選択
リクエストで`endpoint`を指定し、様々な抽出手法を試せる設計。

### 2. 統一された精度評価（FieldResultシステム）
- 全フィールドを統一的なFieldResultで管理
- 明細項目も`item_index`で個別管理
- 戦略パターンによる柔軟な評価ロジック
- 全環境で同じ重み付けとルールで評価し、公平な比較を実現

### 3. 実験管理
- YMLファイルで実験設定を管理
- Langfuseとローカル両方に結果を保存
- 実験結果の比較機能

### 4. エラーハンドリング
- 最大5回のリトライ
- 詳細なエラーコード体系
- エラーパターンの分析

### 5. 拡張性
- 新しい抽出手法の追加が容易
- エージェント機能への対応を考慮
- 設定の外部化により柔軟な調整が可能
- FieldScoreCalculatorによる評価ロジックの拡張

## 開発の流れ

1. **データセット準備**: Langfuseにテストデータを登録
2. **プロンプト作成**: Langfuseでプロンプトを管理
3. **実験実行**: YMLファイルで設定して実行
4. **結果分析**: 精度比較して最適な手法を選択
5. **本番適用**: 最も精度の高いエンドポイントを使用

## プロジェクト構成

```
llmops/
├── src/
│   ├── domain/              # ドメイン層
│   ├── application/         # アプリケーション層
│   ├── infrastructure/      # インフラストラクチャ層
│   └── interfaces/          # インターフェース層
├── tests/                   # テストコード
├── experiments/             # 実験設定
├── results/                 # 実験結果
├── config/                  # 設定ファイル
└── docs/                    # このドキュメント
```

## 実装時の注意点

### 依存関係の方向
- 上位層は下位層に依存できるが、逆は禁止
- ドメイン層は他の層に依存しない
- 詳細は[レイヤー依存関係](architecture/layer-dependencies.md)を参照

### AIツールへの指針
- 各層の責務を理解して適切な場所に実装
- ドメイン層にフレームワーク固有のコードを含めない
- DTOを使用して層間のデータを受け渡す

## システム変更履歴

### v2.0 - FieldResultシステム統合 (2025-01-11)

#### 主要な変更
- **AccuracyMetric → FieldResult**: 精度評価システムの完全リニューアル
- **統一的なアーキテクチャ**: 単一クラスによるシンプルな設計
- **戦略パターン**: FieldScoreCalculatorによる柔軟な評価ロジック
- **明細項目管理**: item_indexによる統一的な管理

#### 技術的改善
- **コード品質向上**: 複雑な継承構造から統一システムへ
- **保守性向上**: 単一クラスによる管理の簡素化
- **テスト容易性向上**: 統一されたAPIによる簡潔なテスト
- **パフォーマンス改善**: メモリ使用量と処理時間の最適化

#### データ形式変更
- **JSONフォーマット**: `accuracy_metrics` → `field_results`
- **メソッド名**: `field_score()` → `score` プロパティ
- **正解判定**: `is_correct()` → `is_correct` プロパティ

#### 後方互換性
- 基本的なJSONフォーマットの構造は維持
- 集計計算の結果は同等
- APIインターフェースの変更は最小限

### v1.0 - 初期実装 (2024-12-01)
- 基本的なLLMOpsプラットフォームの構築
- AccuracyMetricシステムの実装
- LangfuseとGemini APIの統合
- 実験実行基盤の構築

## 次のステップ
1. 環境構築とFastAPIプロジェクトの初期化
2. ドメイン層のモデルとサービスの実装
3. インフラストラクチャ層の外部サービス連携
4. アプリケーション層のユースケース実装
5. インターフェース層のAPI実装
6. テストコードの作成
7. 初回実験の実施