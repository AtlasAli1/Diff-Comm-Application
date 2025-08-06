"""
UI Module Package for Commission Calculator Pro
This package contains all UI components organized by functionality
"""

from .utils import (
    safe_session_get,
    safe_session_check,
    safe_session_init,
    validate_file_size,
    validate_file_content,
    get_revenue_column,
    get_safe_revenue_data,
    get_current_pay_period,
    get_selected_pay_period,
    format_pay_period,
    is_pay_period_configured,
    get_pay_period_by_date,
    get_employee_hours_with_overrides,
    cache_expensive_operation,
    cached_dataframe_groupby,
    cached_commission_calculation,
    get_or_compute_employee_summary,
    optimize_dataframe_memory,
    batch_process_large_dataset
)
from .config import get_config, optimize_for_data_size, ConfigManager

__all__ = [
    'safe_session_get',
    'safe_session_check',
    'safe_session_init',
    'validate_file_size',
    'validate_file_content',
    'get_revenue_column',
    'get_safe_revenue_data',
    'get_current_pay_period',
    'get_selected_pay_period',
    'format_pay_period',
    'is_pay_period_configured',
    'get_pay_period_by_date',
    'get_employee_hours_with_overrides',
    'cache_expensive_operation',
    'cached_dataframe_groupby', 
    'cached_commission_calculation',
    'get_or_compute_employee_summary',
    'optimize_dataframe_memory',
    'batch_process_large_dataset',
    'get_config',
    'optimize_for_data_size',
    'ConfigManager'
]