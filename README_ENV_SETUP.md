# 環境変数設定ガイド

プロンプト同期機能を使用するには、`.env`ファイルに以下の環境変数を設定する必要があります。

## 手順

1. **`.env`ファイルを作成**:
   ```bash
   cp .env.example .env
   ```

2. **Langfuseの設定を取得**:
   - [Langfuse Console](https://cloud.langfuse.com)にログイン
   - プロジェクト設定から以下を取得:
     - `LANGFUSE_PUBLIC_KEY`
     - `LANGFUSE_SECRET_KEY`

3. **Gemini APIキーを取得**:
   - [Google AI Studio](https://aistudio.google.com/app/apikey)でAPIキーを作成
   - `GEMINI_API_KEY`に設定

4. **`.env`ファイルを編集**:
   ```bash
   # Langfuse設定
   LANGFUSE_PUBLIC_KEY=pk_lf_xxx
   LANGFUSE_SECRET_KEY=sk_lf_xxx
   LANGFUSE_HOST=https://cloud.langfuse.com

   # Gemini API設定
   GEMINI_API_KEY=your-actual-gemini-api-key
   ```

## プロンプト同期の実行

環境変数を設定後、以下のコマンドでプロンプトを同期できます：

```bash
# ローカル環境
python -m src.cli sync-prompt invoice_extraction_prompt_v1

# Docker環境
docker-compose run --rm cli python -m src.cli sync-prompt invoice_extraction_prompt_v1
```

## 注意事項

- `.env`ファイルは`.gitignore`に含まれており、Gitにコミットされません
- APIキーは秘匿情報として適切に管理してください