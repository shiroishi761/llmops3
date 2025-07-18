"""ドメイン例外クラス"""


class DomainException(Exception):
    """ドメイン層の基底例外クラス"""
    pass


class ValidationError(DomainException):
    """検証エラー"""
    pass


class ExternalServiceError(DomainException):
    """外部サービスエラー"""
    pass


class NotFoundError(DomainException):
    """リソースが見つからないエラー"""
    pass


class ConfigurationError(DomainException):
    """設定エラー"""
    pass


class PromptNotFoundError(NotFoundError):
    """プロンプトが見つからないエラー"""
    pass


class DatasetNotFoundError(NotFoundError):
    """データセットが見つからないエラー"""
    pass


class ExtractionFailedError(ExternalServiceError):
    """文書抽出に失敗したエラー"""
    pass


class AccuracyEvaluationError(DomainException):
    """精度評価に失敗したエラー"""
    pass