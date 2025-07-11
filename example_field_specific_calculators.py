"""特定フィールド専用のCalculator例"""

from typing import Any, Optional
from src.domain.models.field_result import FieldResult
from src.domain.services.field_score_calculator import FieldScoreCalculator, FieldScoreCalculatorFactory


class TotalPriceCalculator(FieldScoreCalculator):
    """total_priceフィールド専用の計算クラス"""
    
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
        
        # 文字列の場合、カンマと通貨記号を除去
        import re
        value_str = str(value).strip()
        value_str = re.sub(r'[,¥$€£]', '', value_str)
        
        return float(value_str)


class TaxPriceCalculator(FieldScoreCalculator):
    """tax_priceフィールド専用の計算クラス"""
    
    def calculate_score(self, field_name: str, expected: Any, actual: Any, weight: float, item_index: Optional[int] = None) -> FieldResult:
        """tax_priceの特別な評価ロジック"""
        is_correct = self._is_tax_price_match(expected, actual)
        
        if is_correct:
            return FieldResult.create_correct(field_name, expected, actual, weight, item_index)
        else:
            return FieldResult.create_incorrect(field_name, expected, actual, weight, item_index)
    
    def _is_tax_price_match(self, expected: Any, actual: Any) -> bool:
        """tax_price専用の比較ロジック"""
        if expected is None and actual is None:
            return True
        if expected is None or actual is None:
            return False
        
        try:
            expected_amount = float(expected) if expected else 0.0
            actual_amount = float(actual) if actual else 0.0
            
            # 税額は計算により若干の誤差を許容（10円以下）
            return abs(expected_amount - actual_amount) <= 10.0
        except (ValueError, TypeError):
            return False


class CompanyNameCalculator(FieldScoreCalculator):
    """会社名フィールド専用の計算クラス"""
    
    def calculate_score(self, field_name: str, expected: Any, actual: Any, weight: float, item_index: Optional[int] = None) -> FieldResult:
        """会社名の特別な評価ロジック"""
        is_correct = self._is_company_name_match(expected, actual)
        
        if is_correct:
            return FieldResult.create_correct(field_name, expected, actual, weight, item_index)
        else:
            return FieldResult.create_incorrect(field_name, expected, actual, weight, item_index)
    
    def _is_company_name_match(self, expected: Any, actual: Any) -> bool:
        """会社名専用の比較ロジック"""
        if expected is None and actual is None:
            return True
        if expected is None or actual is None:
            return False
        
        expected_str = str(expected).strip()
        actual_str = str(actual).strip()
        
        # 会社名は「株式会社」「有限会社」などの表記揺れを許容
        expected_normalized = self._normalize_company_name(expected_str)
        actual_normalized = self._normalize_company_name(actual_str)
        
        return expected_normalized == actual_normalized
    
    def _normalize_company_name(self, company_name: str) -> str:
        """会社名を正規化"""
        # 「株式会社」「(株)」「㈱」などを統一
        import re
        name = company_name.lower()
        name = re.sub(r'株式会社|㈱|\(株\)', 'kabushikigaisha', name)
        name = re.sub(r'有限会社|㈲|\(有\)', 'yuugengaisha', name)
        name = re.sub(r'合同会社|㈱|\(合\)', 'goudougaisha', name)
        # 空白を除去
        name = re.sub(r'\s+', '', name)
        return name


# 使用例
def setup_field_specific_calculators():
    """フィールド専用のCalculatorをセットアップ"""
    factory = FieldScoreCalculatorFactory()
    
    # 特定フィールド専用のCalculatorを追加
    factory._calculators['total_price_specific'] = TotalPriceCalculator()
    factory._calculators['tax_price_specific'] = TaxPriceCalculator()
    factory._calculators['company_name_specific'] = CompanyNameCalculator()
    
    # フィールドマッピングを設定
    factory.add_field_mapping('total_price', 'total_price_specific')
    factory.add_field_mapping('tax_price', 'tax_price_specific')
    factory.add_field_mapping('issuer', 'company_name_specific')
    factory.add_field_mapping('destination', 'company_name_specific')
    
    return factory


# 使用例
if __name__ == "__main__":
    # カスタムCalculatorのセットアップ
    factory = setup_field_specific_calculators()
    
    # total_priceの評価
    total_price_calculator = factory.get_calculator('total_price')
    result = total_price_calculator.calculate_score('total_price', 1000, '1,000', 3.0)
    print(f"total_price評価結果: {result.is_correct}")
    
    # tax_priceの評価
    tax_price_calculator = factory.get_calculator('tax_price')
    result = tax_price_calculator.calculate_score('tax_price', 100, 105, 2.0)  # 10円以下なので正解
    print(f"tax_price評価結果: {result.is_correct}")
    
    # 会社名の評価
    company_calculator = factory.get_calculator('issuer')
    result = company_calculator.calculate_score('issuer', '株式会社テスト', '㈱テスト', 2.0)
    print(f"会社名評価結果: {result.is_correct}")