# CLAUDE.md

このファイルは、Claude Code (claude.ai/code) がこのリポジトリで作業する際のガイダンスを提供します。

**重要**: このリポジトリで作業する際は、必ず日本語で返答してください。

## プロジェクト概要

これは、LLMベースの文書抽出精度を検証するためのLLMOps精度検証プラットフォームです。既存のRailsプロダクトからLLM機能を分離し、精度実験を実行するためのFastAPIベースのサービスを提供します。

## アーキテクチャ

本プロジェクトは、厳格な4層アーキテクチャを持つドメイン駆動設計（DDD）に従っています：

1. **インターフェース層** (`src/interfaces/`) - APIエンドポイントとリクエスト/レスポンススキーマ
2. **アプリケーション層** (`src/application/`) - ユースケースとデータ転送オブジェクト（DTO）
3. **ドメイン層** (`src/domain/`) - コアビジネスロジック（外部依存なし）
4. **インフラストラクチャ層** (`src/infrastructure/`) - 外部サービスと永続化

**重要なルール:**
- ドメイン層は他の層に依存してはいけない
- 依存関係は内向き: Interface → Application → Domain ← Infrastructure
- インフラストラクチャサービスには依存性注入を使用
- 層間のデータ転送にはDTOを使用

## 主要コマンド

## Docker を使用する場合（推奨）

```bash
# 初回セットアップ
docker-compose build

# 開発サーバーの起動
docker-compose up

# 実験の実行
docker-compose run --rm cli python -m src.cli run-experiment experiments/invoice_test.yml

# コンテナ内でコマンド実行
docker-compose exec app bash

# テストの実行
docker-compose run --rm app pytest
docker-compose run --rm app pytest tests/unit/
docker-compose run --rm app pytest -v
```

## ローカル環境の場合

```bash
# 仮想環境のセットアップ
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt

# 実験の実行
python -m src.cli run-experiment experiments/invoice_test.yml

# 開発サーバーの起動（API利用時）
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# テストの実行
pytest
pytest tests/unit/
pytest -v
```

## 環境設定

必要な環境変数（.envファイルに記載）:
```bash
GEMINI_API_KEY=your-gemini-api-key
LANGFUSE_PUBLIC_KEY=your-langfuse-public-key
LANGFUSE_SECRET_KEY=your-langfuse-secret-key
```

設定ファイル:
- `config/config.yml` - フィールド重み設定のみ

## ドメイン概念（ユビキタス言語）

- **実験（Experiment）**: 設定を持つ特定の精度検証実行
- **抽出結果（ExtractionResult）**: LLMによって文書から抽出された構造化データ
- **精度指標（AccuracyMetric）**: 正解データに対する抽出精度の測定値
- **プロンプトテンプレート（PromptTemplate）**: LLM用の再利用可能な指示テンプレート
- **実験ステータス（ExperimentStatus）**: 状態（pending, running, completed, failed）
- **抽出方法（ExtractionMethod）**: 文書抽出のための異なるアプローチ

## 外部サービス統合

1. **Langfuse** （プロンプト管理＆モニタリング）
   - プロンプトテンプレートの管理
   - LLMインタラクションの追跡
   - 実験結果の保存

2. **Gemini API** （GoogleのLLM）
   - 文書抽出の実行
   - APIキーの設定が必要

## テスト戦略

- **ユニットテスト**: ドメインロジックを単独でテスト
- **統合テスト**: モックを使用した外部サービス統合のテスト
- **エンドツーエンドテスト**: 完全なAPIワークフローのテスト
- FastAPIテスト用の非同期サポート付きpytestを使用

## エラーハンドリング

- リトライロジックの実装（指数バックオフで最大5回）
- 適切なコンテキストですべてのエラーをログ記録
- APIから構造化されたエラーレスポンスを返す
- 外部サービスの障害を適切に処理

## 開発ガイドライン

1. **新機能を実装する際:**
   - ドメインモデルとロジックから開始
   - アプリケーション層でユースケースを作成
   - インフラストラクチャサービスを実装
   - 最後にAPIエンドポイントを追加

2. **コード構成:**
   - 1ファイルに1クラス
   - 関連ファイルはサブディレクトリにグループ化
   - ドメインモデルは純粋に保つ（フレームワークコードなし）
   - 全体を通して型ヒントを使用

3. **API設計:**
   - RESTful規約に従う
   - 検証にPydanticモデルを使用
   - OpenAPIドキュメントを含める
   - 必要に応じてAPIをバージョン管理

## プロジェクトステータス

現在仕様フェーズ。実装の優先順位:
1. ドメインモデル（Experiment, ExtractionResult, AccuracyMetric）
2. リポジトリインターフェースと実装
3. 外部サービス統合（Langfuse、Gemini）
4. ユースケース（RunExperiment、ExtractDocument）
5. FastAPIエンドポイント
6. 設定管理（config.yml）
7. 基本的なエラーハンドリング
8. 基本的なテスト

## 初期実装で省略する機能

- 並列実行（まずは順次実行）
- キャッシュ機能
- 実験比較機能（CompareExperiments）
- 詳細なリトライロジック
- 環境別設定ファイル
- API経由での実行（まずはCLIのみ）

## 実験の実行方法

### 1. 事前準備
Langfuseで以下を作成：
- プロンプトテンプレート（例: "invoice_extraction_prompt_v1"）
- データセット（例: "invoice_dataset_202401"）正解データ含む

### 2. 実験設定ファイルの作成
`experiments/`ディレクトリに実験設定YAMLファイルを作成：

```yaml
# experiments/invoice_test.yml
experiment_name: "請求書抽出実験_v1"
prompt_name: "invoice_extraction_prompt_v1"  # Langfuseで管理
dataset_name: "invoice_dataset_202401"       # Langfuseで管理
llm_endpoint: "extract_v1"                   # 使用するLLMエンドポイント
description: "初回の精度検証実験"            # 任意
```

### 3. 実験の実行
```bash
python -m src.cli run-experiment experiments/invoice_test.yml
```

### 4. 結果の確認
実験結果は`results/`ディレクトリに自動保存：
```bash
cat results/invoice_test_20240115_143052.json
```