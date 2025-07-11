# 精度評価ドメインサービス

## 概要
抽出結果の精度を評価するドメインサービス。FieldResultシステムを使用して、期待値と実際値を比較し、精度結果を算出する。

## AccuracyEvaluationService

### 責務
- 抽出結果と期待値の比較評価
- FieldResultの生成
- FieldScoreCalculatorとの連携
- 統一的な評価ロジックの提供

### 主要メソッド

#### evaluate_extraction
```python
def evaluate_extraction(
    self,
    expected: Dict[str, Any],
    actual: Dict[str, Any],
    field_weights: Dict[str, float],
    default_weight: float = 1.0
) -> List[FieldResult]:
    """
    抽出結果の精度を評価
    
    Args:
        expected: 期待される抽出データ
        actual: 実際の抽出データ
        field_weights: フィールドごとの重み
        default_weight: デフォルトの重み
        
    Returns:
        各フィールドの精度結果のリスト
    """
```

### 内部構造

#### 1. FieldScoreCalculatorとの連携
```python
def __init__(self, config_service=None):
    self.config_service = config_service
    self.calculator_factory = FieldScoreCalculatorFactory()
```

#### 2. フィールド別評価
```python
# 適切なCalculatorを取得して評価
calculator = self.calculator_factory.get_calculator(field_name)
field_results = calculator.calculate(
    field_name, expected_value, actual_value, weight
)
results.extend(field_results)
```

#### 3. 明細項目の特別処理
```python
# itemsフィールドの特別処理
if field_name == 'items':
    expected_items = expected.get(field_name, [])
    actual_items = actual.get(field_name, [])
    
    # ItemsCalculatorによる評価
    items_results = self._evaluate_items_fields(
        expected_items, actual_items, field_weights, default_weight
    )
    results.extend(items_results)
```

### 評価ロジック

#### 1. フィールドタイプ別評価
各フィールドタイプに応じた評価ロジック：

**文字列フィールド（SimpleCalculator）**
- 前後の空白を除去
- 大文字小文字を区別しない
- 完全一致で重み分のスコア、不一致で0.0

**金額フィールド（AmountCalculator）**
- カンマ、通貨記号を除去
- 数値として比較
- 小数点以下の誤差を考慮（0.01以下）

**日付フィールド（DateCalculator）**
- 複数の日付フォーマットに対応
- yyyy-mm-dd形式に統一して比較
- 完全一致で重み分のスコア

**明細項目（ItemsCalculator）**
- 各明細項目を個別に評価
- item_indexによる明細項目の管理
- サブフィールドごとの詳細評価

#### 2. 明細項目の評価詳細
```python
def _evaluate_items_fields(
    self,
    expected_items: List[Dict[str, Any]],
    actual_items: List[Dict[str, Any]],
    field_weights: Dict[str, float],
    default_weight: float
) -> List[FieldResult]:
    """明細項目を評価してFieldResultのリストを返す"""
    results = []
    
    # ItemsCalculatorを使用
    calculator = self.calculator_factory.get_calculator('items')
    
    # items全体を評価（各サブフィールドとアイテムインデックスを考慮）
    items_results = calculator.calculate(
        'items', expected_items, actual_items, 
        field_weights, default_weight
    )
    results.extend(items_results)
    
    return results
```

## FieldScoreCalculatorFactory

### 責務
- フィールド名に応じた適切なCalculatorの選択
- Calculatorインスタンスの管理
- フィールドマッピングの管理

### 主要メソッド

#### get_calculator
```python
def get_calculator(self, field_name: str) -> FieldScoreCalculator:
    """フィールド名に応じて適切なCalculatorを返す"""
    calculator_type = self._field_mappings.get(field_name, 'simple')
    return self._calculators[calculator_type]
```

### フィールドマッピング
```python
self._field_mappings = {
    'total_price': 'amount',
    'tax_price': 'amount',
    'sub_total': 'amount',
    'doc_date': 'date',
    'expiration_date': 'date',
    'items': 'items'
}
```

## FieldScoreCalculator戦略

### 1. SimpleFieldCalculator
```python
class SimpleFieldCalculator(FieldScoreCalculator):
    """単純な文字列比較による計算"""
    
    def calculate_score(self, field_name: str, expected: Any, actual: Any, weight: float, item_index: Optional[int] = None) -> FieldResult:
        """文字列として比較し、完全一致で正解"""
        is_correct = self._is_match(expected, actual)
        
        if is_correct:
            return FieldResult.create_correct(field_name, expected, actual, weight, item_index)
        else:
            return FieldResult.create_incorrect(field_name, expected, actual, weight, item_index)
```

### 2. AmountFieldCalculator
```python
class AmountFieldCalculator(FieldScoreCalculator):
    """金額フィールド専用の計算"""
    
    def _parse_amount(self, value: Any) -> float:
        """金額を数値に変換"""
        if isinstance(value, (int, float)):
            return float(value)
        
        # 文字列の場合、カンマと通貨記号を除去
        value_str = str(value).strip()
        value_str = re.sub(r'[,¥$€£]', '', value_str)
        
        return float(value_str)
```

### 3. DateFieldCalculator
```python
class DateFieldCalculator(FieldScoreCalculator):
    """日付フィールド専用の計算"""
    
    DATE_FORMATS = [
        '%Y-%m-%d',
        '%Y/%m/%d',
        '%Y年%m月%d日',
        '%m/%d/%Y',
        '%d/%m/%Y'
    ]
```

### 4. ItemsFieldCalculator
```python
class ItemsFieldCalculator(FieldScoreCalculator):
    """明細項目フィールド専用の計算"""
    
    def calculate(self, field_name: str, expected_items: List[Dict], actual_items: List[Dict], 
                  field_weights: Dict[str, float], default_weight: float) -> List[FieldResult]:
        """明細項目を評価してフィールド結果のリストを返す"""
        results = []
        
        # シンプルなアプローチ: 各アイテムを順序で比較
        max_items = max(len(expected_items), len(actual_items))
        
        for item_index in range(max_items):
            expected_item = expected_items[item_index] if item_index < len(expected_items) else {}
            actual_item = actual_items[item_index] if item_index < len(actual_items) else {}
            
            # 各サブフィールドを評価
            sub_fields = ['name', 'quantity', 'price', 'sub_total', 'unit', 'spec', 'note', 'account_item']
            
            for sub_field in sub_fields:
                field_key = f'items.{sub_field}'
                weight = field_weights.get(field_key, default_weight)
                
                expected_value = expected_item.get(sub_field)
                actual_value = actual_item.get(sub_field)
                
                # 適切なCalculatorで評価
                if sub_field in ['price', 'sub_total']:
                    calculator = AmountFieldCalculator()
                else:
                    calculator = SimpleFieldCalculator()
                
                result = calculator.calculate_score(
                    field_key, expected_value, actual_value, weight, item_index
                )
                results.append(result)
        
        return results
```

## 典型的な使用例

### 基本的な評価
```python
# サービスの初期化
service = AccuracyEvaluationService()

# 評価データの準備
expected = {
    "total_price": 1000,
    "tax_price": 100,
    "items": [
        {"name": "商品A", "quantity": 2, "price": 500}
    ]
}

actual = {
    "total_price": 1000,
    "tax_price": 90,
    "items": [
        {"name": "商品A", "quantity": 2, "price": 500}
    ]
}

# フィールド重みの定義
field_weights = {
    "total_price": 3.0,
    "tax_price": 2.0,
    "items.name": 3.0,
    "items.quantity": 2.0,
    "items.price": 2.0
}

# 評価の実行
field_results = service.evaluate_extraction(
    expected, actual, field_weights, default_weight=1.0
)

# 結果の確認
for result in field_results:
    print(f"{result.get_display_name()}: {result.score:.1f}/{result.weight:.1f}")
```

### ExtractionResultとの統合
```python
# 抽出結果の作成
extraction_result = ExtractionResult(
    document_id="doc-123",
    expected_data=expected,
    extracted_data=actual,
    field_results=field_results
)

# 精度の計算
accuracy = extraction_result.calculate_accuracy()
field_accuracies = extraction_result.get_field_accuracies()

print(f"全体精度: {accuracy:.1%}")
for field_name, is_correct in field_accuracies.items():
    print(f"{field_name}: {'✓' if is_correct else '✗'}")
```

## 設計原則

### 1. 戦略パターンの活用
- フィールドタイプに応じた評価ロジックの選択
- 新しいフィールドタイプの追加が容易

### 2. 統一性の保証
- 全てのフィールドはFieldResultとして統一的に表現
- 一貫した評価インターフェース

### 3. 拡張性の確保
- 新しいCalculatorの追加が容易
- カスタム評価ロジックの実装が可能

### 4. 明確な責務分離
- AccuracyEvaluationService: 全体の評価フロー
- FieldScoreCalculator: 個別フィールドの評価ロジック
- FieldResult: 評価結果の表現

## 設定とカスタマイズ

### フィールド重みの設定
```yaml
# config/config.yml
field_weights:
  # 金額関連（高重要度）
  total_price: 3.0
  tax_price: 3.0
  sub_total: 3.0
  
  # 明細項目（中重要度）
  items.name: 3.0
  items.quantity: 2.0
  items.price: 2.0
  items.sub_total: 2.0
  
  # 基本情報（低重要度）
  doc_type: 1.5
  doc_date: 1.5
  
  # デフォルト重み
  default_weight: 1.0
```

### カスタムCalculatorの追加
```python
class CustomFieldCalculator(FieldScoreCalculator):
    """カスタム評価ロジック"""
    
    def calculate_score(self, field_name: str, expected: Any, actual: Any, weight: float, item_index: Optional[int] = None) -> FieldResult:
        # カスタムロジックを実装
        pass

# Factoryへの追加
factory.add_field_mapping('custom_field', 'custom')
factory._calculators['custom'] = CustomFieldCalculator()
```

## 移行履歴

### v1.0 → v2.0 (FieldResult統合)
- AccuracyMetricからFieldResultへの完全移行
- 戦略パターンの導入
- 統一的なCalculatorインターフェース
- 明細項目のインデックス管理

### 後方互換性
- 評価結果の数値は同等
- フィールド重み設定の形式は維持
- 基本的な評価ロジックは変更なし