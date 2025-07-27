# 実験設定ファイルのガイドライン

## プロンプト設定の規約

### エントリポイントの指定

データセット入力を受け取るプロンプト（エントリポイント）は、サービス名を `entry` にしてください。

```yaml
prompts:
  # ✅ 良い例: サービス名が entry
  - service_name: "entry"
    prompt_name: "invoice_extraction_prompt_v1"
  
  # ❌ 悪い例: エントリポイントが不明確
  - service_name: "extraction_service"
    prompt_name: "invoice_extraction_prompt_v1"
```

### 単一プロンプトの場合

単一プロンプトの実験では、エントリポイントの指定は不要です（自動的に使用されます）。

```yaml
prompts:
  - service_name: "gemini_service"
    prompt_name: "invoice_extraction_prompt_v1"
```

### エージェント型の実験

複数プロンプトを使用する場合は、必ずエントリポイントを明示してください。

```yaml
prompts:
  - service_name: "entry"  # エントリポイント
    prompt_name: "invoice_extraction_prompt_v1"
  - service_name: "validation"
    prompt_name: "invoice_validation_prompt"
  - service_name: "correction"
    prompt_name: "invoice_correction_prompt"
```

## 命名規約

- **エントリポイント**: サービス名を `entry` にする
- **後続サービス**: 処理内容を表す名前（validation, correction, enhancement など）
- **プロンプト名**: 用途と版番号を含める（例: invoice_extraction_prompt_v1）