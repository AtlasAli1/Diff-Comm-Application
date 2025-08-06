"""Custom exception hierarchy for Commission Calculator Pro."""

from typing import Optional, Dict, Any


class CommissionCalculatorError(Exception):
    """Base exception for Commission Calculator Pro."""

    def __init__(self, message: str, error_code: Optional[str] = None,
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}

    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class DataValidationError(CommissionCalculatorError):
    """Raised when data validation fails."""

    def __init__(self, message: str, field_name: Optional[str] = None,
                 invalid_value: Optional[Any] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.field_name = field_name
        self.invalid_value = invalid_value


class DataProcessingError(CommissionCalculatorError):
    """Raised when data processing operations fail."""
    pass


class CommissionCalculationError(CommissionCalculatorError):
    """Raised when commission calculations fail."""

    def __init__(self, message: str, employee_name: Optional[str] = None,
                 business_unit: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.employee_name = employee_name
        self.business_unit = business_unit


class ConfigurationError(CommissionCalculatorError):
    """Raised when configuration is invalid or missing."""
    pass


class AuthenticationError(CommissionCalculatorError):
    """Raised when authentication fails."""
    pass


class AuthorizationError(CommissionCalculatorError):
    """Raised when user lacks required permissions."""

    def __init__(self, message: str, required_role: Optional[str] = None,
                 user_role: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.required_role = required_role
        self.user_role = user_role


class DatabaseError(CommissionCalculatorError):
    """Raised when database operations fail."""
    pass


class ExportError(CommissionCalculatorError):
    """Raised when export operations fail."""

    def __init__(self, message: str, export_format: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.export_format = export_format


class ImportError(CommissionCalculatorError):
    """Raised when import operations fail."""

    def __init__(self, message: str, file_path: Optional[str] = None,
                 line_number: Optional[int] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.file_path = file_path
        self.line_number = line_number


class AnalyticsError(CommissionCalculatorError):
    """Raised when analytics calculations fail."""
    pass


class BusinessRuleError(CommissionCalculatorError):
    """Raised when business rule violations occur."""

    def __init__(self, message: str, rule_name: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.rule_name = rule_name


# Error code constants
class ErrorCodes:
    """Standard error codes for the application."""

    # Data validation errors
    MISSING_REQUIRED_FIELD = "VALIDATION_001"
    INVALID_DATA_TYPE = "VALIDATION_002"
    INVALID_VALUE_RANGE = "VALIDATION_003"
    DUPLICATE_ENTRY = "VALIDATION_004"

    # Commission calculation errors
    MISSING_COMMISSION_RATE = "COMMISSION_001"
    INVALID_COMMISSION_SETUP = "COMMISSION_002"
    CALCULATION_OVERFLOW = "COMMISSION_003"
    DIVISION_BY_ZERO = "COMMISSION_004"

    # Configuration errors
    MISSING_CONFIG = "CONFIG_001"
    INVALID_CONFIG_VALUE = "CONFIG_002"
    CONFIG_VERSION_MISMATCH = "CONFIG_003"

    # Authentication/Authorization errors
    INVALID_CREDENTIALS = "AUTH_001"
    INSUFFICIENT_PERMISSIONS = "AUTH_002"
    SESSION_EXPIRED = "AUTH_003"

    # Database errors
    CONNECTION_FAILED = "DB_001"
    QUERY_FAILED = "DB_002"
    TRANSACTION_FAILED = "DB_003"

    # Import/Export errors
    FILE_NOT_FOUND = "IO_001"
    INVALID_FILE_FORMAT = "IO_002"
    EXPORT_FAILED = "IO_003"
    IMPORT_FAILED = "IO_004"

    # Analytics errors
    INSUFFICIENT_DATA = "ANALYTICS_001"
    CALCULATION_ERROR = "ANALYTICS_002"

    # Business rule errors
    NEGATIVE_HOURS = "BUSINESS_001"
    EXCESSIVE_OVERTIME = "BUSINESS_002"
    INVALID_COMMISSION_RATE = "BUSINESS_003"
    MISSING_EMPLOYEE_DATA = "BUSINESS_004"


def handle_exception(func):
    """Decorator to handle and log exceptions consistently."""
    import functools
    from loguru import logger

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except CommissionCalculatorError as e:
            logger.error(f"Application error in {func.__name__}: {e}")
            if e.context:
                logger.error(f"Error context: {e.context}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            raise CommissionCalculatorError(
                f"Unexpected error in {func.__name__}: {str(e)}",
                error_code="UNEXPECTED_ERROR",
                context={'function': func.__name__, 'args': str(args)}
            )

    return wrapper
