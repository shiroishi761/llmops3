# フィールドスコア計算サービス

## 概要
戦略パターンを用いてフィールドタイプに応じた精度評価ロジックを提供するサービス。FieldResultシステムの中核となる計算エンジン。

## FieldScoreCalculator 基底クラス

### 責務
- フィールドスコア計算の統一インターフェース
- 異なる評価ロジックの抽象化
- 拡張可能な評価システムの基盤

### 主要メソッド

#### calculate_score (抽象メソッド)
```python
@abstractmethod
def calculate_score(self, field_name: str, expected: Any, actual: Any, weight: float, item_index: Optional[int] = None) -> FieldResult:
    """
    フィールドスコアを計算
    
    Args:
        field_name: フィールド名
        expected: 期待値
        actual: 実際の値
        weight: 重み
        item_index: アイテムインデックス（明細項目用）
        
    Returns:
        FieldResult: 計算結果
    """
```

#### calculate (デフォルト実装)
```python
def calculate(self, field_name: str, expected: Any, actual: Any, weight: float) -> List[FieldResult]:
    """
    フィールドを評価してリストで返す（デフォルト実装）
    
    Args:
        field_name: フィールド名
        expected: 期待値
        actual: 実際の値
        weight: 重み
        
    Returns:
        List[FieldResult]: 計算結果のリスト
    """
    result = self.calculate_score(field_name, expected, actual, weight)
    return [result]
```

## 具体的な Calculator クラス

### 1. SimpleFieldCalculator
文字列フィールドの基本的な比較を行うCalculator。

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
    
    def _is_match(self, expected: Any, actual: Any) -> bool:
        """値が一致するかを判定"""
        if expected is None and actual is None:
            return True
        if expected is None or actual is None:
            return False
        
        # 文字列として比較（前後空白除去、大文字小文字区別なし）
        expected_str = str(expected).strip().lower()
        actual_str = str(actual).strip().lower()
        
        return expected_str == actual_str
```

#### 特徴
- 前後の空白を除去
- 大文字小文字を区別しない
- null値の適切な処理

### 2. AmountFieldCalculator
金額フィールド専用の計算ロジック。

```python
class AmountFieldCalculator(FieldScoreCalculator):
    """金額フィールド専用の計算"""
    
    def calculate_score(self, field_name: str, expected: Any, actual: Any, weight: float, item_index: Optional[int] = None) -> FieldResult:
        """金額として比較"""
        is_correct = self._is_amount_match(expected, actual)
        
        if is_correct:
            return FieldResult.create_correct(field_name, expected, actual, weight, item_index)
        else:
            return FieldResult.create_incorrect(field_name, expected, actual, weight, item_index)
    
    def _is_amount_match(self, expected: Any, actual: Any) -> bool:
        """金額として比較"""
        if expected is None and actual is None:
            return True
        if expected is None or actual is None:
            return False
        
        try:
            expected_amount = self._parse_amount(expected)
            actual_amount = self._parse_amount(actual)
            
            # 小数点以下の誤差を考慮
            return abs(expected_amount - actual_amount) < 0.01
        except (ValueError, TypeError):
            # 数値に変換できない場合は文字列比較
            return str(expected).strip() == str(actual).strip()
    
    def _parse_amount(self, value: Any) -> float:
        """金額を数値に変換"""
        if isinstance(value, (int, float)):
            return float(value)
        
        # 文字列の場合、カンマと通貨記号を除去
        value_str = str(value).strip()
        value_str = re.sub(r'[,¥$€£]', '', value_str)
        
        return float(value_str)
```

#### 特徴
- カンマ区切りの除去
- 通貨記号の除去
- 小数点以下の誤差を考慮（0.01以下）
- 数値変換エラー時の文字列比較フォールバック

### 3. DateFieldCalculator
日付フィールドの比較を行うCalculator。

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
    
    def calculate_score(self, field_name: str, expected: Any, actual: Any, weight: float, item_index: Optional[int] = None) -> FieldResult:
        """日付として比較"""
        is_correct = self._is_date_match(expected, actual)
        
        if is_correct:
            return FieldResult.create_correct(field_name, expected, actual, weight, item_index)
        else:
            return FieldResult.create_incorrect(field_name, expected, actual, weight, item_index)
    
    def _is_date_match(self, expected: Any, actual: Any) -> bool:
        """日付として比較"""
        if expected is None and actual is None:
            return True
        if expected is None or actual is None:
            return False
        
        try:
            expected_date = self._parse_date(expected)
            actual_date = self._parse_date(actual)
            
            return expected_date == actual_date
        except (ValueError, TypeError):
            # 日付に変換できない場合は文字列比較
            return str(expected).strip() == str(actual).strip()
    
    def _parse_date(self, value: Any) -> datetime:
        """日付を標準形式に変換"""
        if isinstance(value, datetime):
            return value.replace(hour=0, minute=0, second=0, microsecond=0)
        
        value_str = str(value).strip()
        
        for fmt in self.DATE_FORMATS:
            try:
                return datetime.strptime(value_str, fmt)
            except ValueError:
                continue
        
        raise ValueError(f"日付形式を解析できません: {value_str}")
```

#### 特徴
- 複数の日付フォーマットに対応
- 時分秒を無視した日付比較
- 日本語フォーマット（年月日）にも対応
- 変換エラー時の文字列比較フォールバック

### 4. ItemsFieldCalculator
明細項目フィールドの特別な評価ロジック。

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

#### 特徴
- 明細項目の順序比較
- サブフィールドごとの個別評価
- `item_index`による明細項目の識別
- 金額フィールドの特別処理

## FieldScoreCalculatorFactory

### 責務
- フィールド名に応じた適切なCalculatorの選択
- Calculatorインスタンスの管理
- フィールドマッピングの設定

### 実装
```python
class FieldScoreCalculatorFactory:
    """フィールドに応じて適切なCalculatorを選択するFactory"""
    
    def __init__(self, items_matching_service=None):
        self.items_matching_service = items_matching_service
        self._calculators = {
            'simple': SimpleFieldCalculator(),
            'amount': AmountFieldCalculator(),
            'date': DateFieldCalculator(),
            'items': ItemsFieldCalculator(items_matching_service)
        }
        
        # フィールド名とCalculatorのマッピング
        self._field_mappings = {
            'total_price': 'amount',
            'tax_price': 'amount',
            'sub_total': 'amount',
            'doc_date': 'date',
            'expiration_date': 'date',
            'items': 'items'
        }
    
    def get_calculator(self, field_name: str) -> FieldScoreCalculator:
        """フィールド名に応じて適切なCalculatorを返す"""
        calculator_type = self._field_mappings.get(field_name, 'simple')
        return self._calculators[calculator_type]
    
    def add_field_mapping(self, field_name: str, calculator_type: str):
        """フィールドマッピングを追加"""
        if calculator_type not in self._calculators:
            raise ValueError(f"Unknown calculator type: {calculator_type}")
        self._field_mappings[field_name] = calculator_type
```

### フィールドマッピング
| フィールド名 | Calculatorタイプ | 説明 |
|-------------|------------------|------|
| total_price | amount | 合計金額 |
| tax_price | amount | 税額 |
| sub_total | amount | 小計 |
| doc_date | date | 文書日付 |
| expiration_date | date | 有効期限 |
| items | items | 明細項目 |
| その他 | simple | 文字列比較 |

## 使用例

### 基本的な使用
```python
# Factoryの初期化
factory = FieldScoreCalculatorFactory()

# 文字列フィールドの評価
calculator = factory.get_calculator('doc_type')
result = calculator.calculate_score('doc_type', '請求書', '請求書', 1.5)
print(f"結果: {result.is_correct}, スコア: {result.score}")

# 金額フィールドの評価
calculator = factory.get_calculator('total_price')
result = calculator.calculate_score('total_price', 1000, '1,000', 3.0)
print(f"結果: {result.is_correct}, スコア: {result.score}")

# 日付フィールドの評価
calculator = factory.get_calculator('doc_date')
result = calculator.calculate_score('doc_date', '2024-01-15', '2024年1月15日', 1.5)
print(f"結果: {result.is_correct}, スコア: {result.score}")
```

### 明細項目の評価
```python
# 明細項目の評価
expected_items = [
    {"name": "商品A", "quantity": 2, "price": 1000, "sub_total": 2000}
]
actual_items = [
    {"name": "商品A", "quantity": 2, "price": 1000, "sub_total": 2000}
]

field_weights = {
    "items.name": 3.0,
    "items.quantity": 2.0,
    "items.price": 2.0,
    "items.sub_total": 2.0
}

calculator = factory.get_calculator('items')
results = calculator.calculate(
    'items', expected_items, actual_items, field_weights, 1.0
)

for result in results:
    print(f"{result.get_display_name()}: {result.score:.1f}/{result.weight:.1f}")
```

### カスタムCalculatorの追加

#### 1. 汎用的なタイプ別Calculator
```python
class PhoneNumberFieldCalculator(FieldScoreCalculator):
    """電話番号フィールド専用の計算"""
    
    def calculate_score(self, field_name: str, expected: Any, actual: Any, weight: float, item_index: Optional[int] = None) -> FieldResult:
        """電話番号として比較"""
        is_correct = self._is_phone_match(expected, actual)
        
        if is_correct:
            return FieldResult.create_correct(field_name, expected, actual, weight, item_index)
        else:
            return FieldResult.create_incorrect(field_name, expected, actual, weight, item_index)
    
    def _is_phone_match(self, expected: Any, actual: Any) -> bool:
        """電話番号として比較（ハイフンを無視）"""
        if expected is None and actual is None:
            return True
        if expected is None or actual is None:
            return False
        
        # ハイフンを除去して比較
        expected_clean = str(expected).replace('-', '').replace(' ', '')
        actual_clean = str(actual).replace('-', '').replace(' ', '')
        
        return expected_clean == actual_clean

# Factoryに追加
factory._calculators['phone'] = PhoneNumberFieldCalculator()
factory.add_field_mapping('phone_number', 'phone')
```

#### 2. 特定フィールド専用Calculator
特定のフィールドに特化した詳細な評価ロジックを実装できます：

```python
class TotalPriceCalculator(FieldScoreCalculator):
    """total_priceフィールド専用の計算"""
    
    def calculate_score(self, field_name: str, expected: Any, actual: Any, weight: float, item_index: Optional[int] = None) -> FieldResult:
        """total_priceの特別な評価ロジック"""
        is_correct = self._is_total_price_match(expected, actual)
        
        if is_correct:
            return FieldResult.create_correct(field_name, expected, actual, weight, item_index)
        else:
            return FieldResult.create_incorrect(field_name, expected, actual, weight, item_index)
    
    def _is_total_price_match(self, expected: Any, actual: Any) -> bool:
        """total_price専用の比較ロジック"""
        if expected is None and actual is None:
            return True
        if expected is None or actual is None:
            return False
        
        try:
            expected_amount = self._parse_amount(expected)
            actual_amount = self._parse_amount(actual)
            
            # total_priceは特に厳密に評価（誤差を1円以下に）
            return abs(expected_amount - actual_amount) < 1.0
        except (ValueError, TypeError):
            return False
    
    def _parse_amount(self, value: Any) -> float:
        """金額を数値に変換"""
        if isinstance(value, (int, float)):
            return float(value)
        
        import re
        value_str = str(value).strip()
        value_str = re.sub(r'[,¥$€£]', '', value_str)
        return float(value_str)


class TaxPriceCalculator(FieldScoreCalculator):
    """tax_priceフィールド専用の計算"""
    
    def _is_tax_price_match(self, expected: Any, actual: Any) -> bool:
        """tax_price専用の比較ロジック"""
        try:
            expected_amount = float(expected) if expected else 0.0
            actual_amount = float(actual) if actual else 0.0
            
            # 税額は計算により若干の誤差を許容（10円以下）
            return abs(expected_amount - actual_amount) <= 10.0
        except (ValueError, TypeError):
            return False


class CompanyNameCalculator(FieldScoreCalculator):
    """会社名フィールド専用の計算"""
    
    def _is_company_name_match(self, expected: Any, actual: Any) -> bool:
        """会社名専用の比較ロジック"""
        if expected is None and actual is None:
            return True
        if expected is None or actual is None:
            return False
        
        # 会社名は「株式会社」「有限会社」などの表記揺れを許容
        expected_normalized = self._normalize_company_name(str(expected))
        actual_normalized = self._normalize_company_name(str(actual))
        
        return expected_normalized == actual_normalized
    
    def _normalize_company_name(self, company_name: str) -> str:
        """会社名を正規化"""
        import re
        name = company_name.lower()
        name = re.sub(r'株式会社|㈱|\(株\)', 'kabushikigaisha', name)
        name = re.sub(r'有限会社|㈲|\(有\)', 'yuugengaisha', name)
        name = re.sub(r'\s+', '', name)
        return name

# 特定フィールド専用Calculatorのセットアップ
factory._calculators['total_price_specific'] = TotalPriceCalculator()
factory._calculators['tax_price_specific'] = TaxPriceCalculator()
factory._calculators['company_name_specific'] = CompanyNameCalculator()

# フィールドマッピングの設定
factory.add_field_mapping('total_price', 'total_price_specific')
factory.add_field_mapping('tax_price', 'tax_price_specific')
factory.add_field_mapping('issuer', 'company_name_specific')
factory.add_field_mapping('destination', 'company_name_specific')
```

## 設計原則

### 1. 戦略パターン
- フィールドタイプに応じた異なる評価ロジック
- ランタイムでの動的な選択
- 新しい評価方法の追加が容易

### 2. 単一責任の原則
- 各Calculatorは特定のフィールドタイプのみを処理
- 評価ロジックの独立性を保証

### 3. 開放閉鎖の原則
- 新しいCalculatorの追加は容易（開放）
- 既存のCalculatorの修正は不要（閉鎖）

### 4. 依存性逆転の原則
- 抽象的なインターフェースに依存
- 具体的な実装に依存しない

## 拡張性

### 新しいCalculatorの追加
1. `FieldScoreCalculator`を継承
2. `calculate_score`メソッドを実装
3. `FieldScoreCalculatorFactory`に登録
4. フィールドマッピングを追加

### フィールド特化の粒度レベル
1. **汎用タイプ別** - 文字列、日付、金額など
2. **特定フィールド専用** - total_price、tax_price、issuerなど
3. **条件付き特化** - 値の範囲や条件に応じた評価
4. **複合評価** - 複数フィールドの関係性を考慮

### 高度な評価ロジック
- 機械学習による類似度判定
- 正規表現による部分マッチング
- 外部APIによる検証
- 複数フィールドの複合評価
- フィールド値に応じた動的な評価基準

## 移行メモ

### v1.0からv2.0への移行
- AccuracyMetricの複雑な継承構造を単純化
- 戦略パターンの導入により拡張性を向上
- 統一的なFieldResultによる一貫性の確保
- テストの簡素化と保守性の向上