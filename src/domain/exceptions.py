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
