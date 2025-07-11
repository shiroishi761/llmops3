# 実験設定ファイルの作成方法

このディレクトリには、精度検証実験の設定ファイル（YAML形式）を配置します。

## 実験設定ファイルの構成

### 必須項目
```yaml
experiment_name: "実験の名前"
prompt_name: "Langfuseで管理されているプロンプト名"
dataset_name: "Langfuseで管理されているデータセット名"
llm_endpoint: "使用するLLMエンドポイント"
```

### 任意項目
```yaml
description: "実験の説明（目的、変更点など）"
```

## 実験設定ファイルの例

### 基本的な実験
```yaml
# experiments/invoice_test.yml
experiment_name: "請求書抽出実験_v1"
prompt_name: "invoice_extraction_prompt_v1"
dataset_name: "invoice_dataset_202401"
llm_endpoint: "extract_v1"
```

### 説明付きの実験
```yaml
# experiments/invoice_test_v2.yml
experiment_name: "請求書抽出実験_v2_改善版"
prompt_name: "invoice_extraction_prompt_v2"
dataset_name: "invoice_dataset_202401"
llm_endpoint: "extract_v1"
description: "明細行の抽出精度を改善したプロンプトのテスト"
```

## 実験の実行

作成した設定ファイルを使って実験を実行：
```bash
python -m src.cli run-experiment experiments/invoice_test.yml
```

実験結果は`results/`ディレクトリに自動的に保存されます。