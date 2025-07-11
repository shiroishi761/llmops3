# 文書抽出ユースケース

## 概要
OCR結果から構造化データを抽出するユースケース。オンライン（Rails連携）とオフライン（実験）の両方で使用される。

## ExtractDocumentUseCase

### 責務
- 抽出リクエストの処理
- プロンプトの組み立て
- LLM呼び出しの調整
- 結果の検証と返却

### 依存関係
- Domain層: ExtractionResult, AccountClassificationService
- Infrastructure層: GeminiService, LangfuseService（オプション）

### 主要メソッド

#### extract
```
extract(request: ExtractRequestDto) -> ExtractResponseDto
```
文書からデータを抽出する。

**処理フロー**:
1. リクエストの検証
2. プロンプトの準備
3. LLM呼び出し
4. レスポンスの解析
5. 結果の検証

#### extract_with_prompt
```
extract_with_prompt(
  request: ExtractRequestDto,
  prompt_template: str
) -> ExtractResponseDto
```
指定されたプロンプトテンプレートで抽出を実行。

### 処理の詳細

#### 1. リクエスト検証
```
- OCRコンテンツの存在確認
- 必須メタデータの確認
- エンドポイントの有効性確認
```

#### 2. プロンプト準備
```
変数の埋め込み:
- {ocr_content}: OCR結果
- {company_name}: 自社名
- {customers_json}: 顧客マスタ（JSON形式）
- {account_items}: 勘定科目リスト
- {system_instruction}: システム指示
- {extraction_rules}: 抽出ルール
- {response_format}: 期待するレスポンス形式
```

#### 3. LLM呼び出し
```
- エンドポイントに応じた設定を適用
- Gemini APIを呼び出し
- レスポンスを取得
```

#### 4. レスポンス解析
```
- JSONパース
- スキーマ検証
- デフォルト値の適用
```

#### 5. 後処理
```
- 勘定科目の自動分類（必要に応じて）
- 顧客IDのマッチング強化
- 金額の整合性チェック
```

### エンドポイント別の処理

#### extract_v1（標準）
- 基本的な抽出処理
- デフォルトのプロンプト使用

#### extract_v2（実験的）
- 改良版プロンプト
- 追加の後処理

#### extract_with_cot（Chain of Thought）
- 思考過程を含むプロンプト
- より詳細な解析

### 入出力DTO

#### ExtractRequestDto
```
{
  endpoint: str
  ocr_content: str
  document_id: str
  company_name: str
  customers: Dict[str, int]
  account_items: List[str]
  request_id: Optional[str]
}
```

#### ExtractResponseDto
```
{
  status: str  # "success" | "error"
  data: Optional[ExtractedDataDto]
  error: Optional[ErrorDto]
  metadata: ResponseMetadataDto
}
```

#### ExtractedDataDto
ExtractionResultドメインモデルに対応するDTO。
全フィールドの詳細は`domain/models/extraction-result.md`参照。

#### ResponseMetadataDto
```
{
  execution_time_ms: int
  llm_model: str
  prompt_version: str
  endpoint_used: str
}
```

### エラーハンドリング

#### 検証エラー
- InvalidRequestError: リクエスト形式不正
- MissingFieldError: 必須フィールド欠落

#### 処理エラー
- LLMError: API呼び出し失敗
- ParsingError: レスポンス解析失敗
- ValidationError: スキーマ検証失敗

### キャッシュ戦略
```
- 同一OCRコンテンツ: 5分間キャッシュ
- プロンプトテンプレート: 1時間キャッシュ
- 顧客マスタ: 10分間キャッシュ
```

### パフォーマンス最適化

#### タイムアウト設定
```
- LLM呼び出し: 30秒
- 全体処理: 45秒
```

#### 並行処理
- 明細項目の多い文書は分割処理を検討
- 非同期処理オプション

### モニタリング

#### メトリクス
- 処理時間
- 成功率
- エラー率（種類別）

#### トレーシング
- Langfuseへの記録（オプション）
- 実行ログの詳細記録

## 協調するユースケース
- `RunExperimentUseCase`: 実験での大量実行
- `ValidateAccuracyUseCase`: 精度検証

## 実装時の注意点

### セキュリティ
- 顧客情報の適切な処理
- APIキーの安全な管理

### 拡張性
- 新しいエンドポイントの追加が容易
- プロンプト戦略の切り替えが可能