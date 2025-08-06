"""
Configuration Management System for Commission Calculator Pro
Handles application settings, performance tuning, and scaling parameters
"""
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from .utils import safe_session_get, safe_session_init

@dataclass
class PerformanceConfig:
    """Performance and scaling configuration"""
    # Caching settings
    cache_ttl_seconds: int = 3600  # 1 hour default
    commission_cache_ttl: int = 1800  # 30 minutes for commission calculations
    dashboard_cache_ttl: int = 300  # 5 minutes for dashboard data
    
    # Batch processing
    batch_size_large_datasets: int = 1000
    max_rows_before_batching: int = 5000
    progress_update_interval: int = 100
    
    # Memory optimization
    enable_memory_optimization: bool = True
    auto_downcast_numbers: bool = True
    category_threshold: float = 0.5  # Convert to category if <50% unique
    
    # UI responsiveness
    lazy_load_reports: bool = True
    paginate_large_tables: bool = True
    max_rows_per_page: int = 50
    
    # File processing
    max_file_size_mb: float = 100
    chunk_size_excel: int = 1000
    
@dataclass
class BusinessConfig:
    """Business logic configuration"""
    # Pay period defaults
    default_pay_schedule: str = "Bi-weekly"
    default_overtime_multiplier: float = 1.5
    default_doubletime_multiplier: float = 2.0
    
    # Commission defaults
    default_lead_gen_rate: float = 2.0
    default_sales_rate: float = 3.0
    default_work_done_rate: float = 1.5
    
    # Employee defaults
    default_hourly_rate: float = 25.0
    default_commission_plan: str = "Efficiency Pay"
    
    # Validation rules
    min_hourly_rate: float = 15.0
    max_hourly_rate: float = 200.0
    max_commission_rate: float = 50.0

@dataclass
class UIConfig:
    """User interface configuration"""
    # Theme and styling
    primary_color: str = "#2C5F75"
    secondary_color: str = "#922B3E"
    
    # Layout
    sidebar_default_expanded: bool = False
    wide_mode_default: bool = True
    
    # Tables and charts
    default_chart_height: int = 400
    default_table_height: int = 300
    
    # Navigation
    sticky_navigation: bool = True
    show_breadcrumbs: bool = True

class ConfigManager:
    """Centralized configuration management"""
    
    def __init__(self):
        self.performance = PerformanceConfig()
        self.business = BusinessConfig()
        self.ui = UIConfig()
        self._load_from_session()
    
    def _load_from_session(self):
        """Load configuration from session state"""
        perf_config = safe_session_get('performance_config', {})
        business_config = safe_session_get('business_config', {})
        ui_config = safe_session_get('ui_config', {})
        
        # Update configurations with saved values
        for key, value in perf_config.items():
            if hasattr(self.performance, key):
                setattr(self.performance, key, value)
                
        for key, value in business_config.items():
            if hasattr(self.business, key):
                setattr(self.business, key, value)
                
        for key, value in ui_config.items():
            if hasattr(self.ui, key):
                setattr(self.ui, key, value)
    
    def save_to_session(self):
        """Save configuration to session state"""
        import streamlit as st
        st.session_state['performance_config'] = asdict(self.performance)
        st.session_state['business_config'] = asdict(self.business)
        st.session_state['ui_config'] = asdict(self.ui)
    
    def get_performance_setting(self, key: str, default: Any = None) -> Any:
        """Get performance configuration setting"""
        return getattr(self.performance, key, default)
    
    def get_business_setting(self, key: str, default: Any = None) -> Any:
        """Get business configuration setting"""
        return getattr(self.business, key, default)
    
    def get_ui_setting(self, key: str, default: Any = None) -> Any:
        """Get UI configuration setting"""
        return getattr(self.ui, key, default)
    
    def update_performance_config(self, **kwargs):
        """Update performance configuration"""
        for key, value in kwargs.items():
            if hasattr(self.performance, key):
                setattr(self.performance, key, value)
        self.save_to_session()
    
    def update_business_config(self, **kwargs):
        """Update business configuration"""
        for key, value in kwargs.items():
            if hasattr(self.business, key):
                setattr(self.business, key, value)
        self.save_to_session()
    
    def update_ui_config(self, **kwargs):
        """Update UI configuration"""
        for key, value in kwargs.items():
            if hasattr(self.ui, key):
                setattr(self.ui, key, value)
        self.save_to_session()
    
    def get_environment_config(self) -> Dict[str, Any]:
        """Get environment-specific configuration"""
        env = os.getenv('ENVIRONMENT', 'development')
        
        if env == 'production':
            return {
                'debug': False,
                'cache_ttl_multiplier': 2.0,  # Longer caching in production
                'batch_size_multiplier': 2.0,  # Larger batches in production
                'enable_profiling': False
            }
        elif env == 'development':
            return {
                'debug': True,
                'cache_ttl_multiplier': 0.5,  # Shorter caching in development
                'batch_size_multiplier': 0.5,  # Smaller batches for testing
                'enable_profiling': True
            }
        else:
            return {
                'debug': False,
                'cache_ttl_multiplier': 1.0,
                'batch_size_multiplier': 1.0,
                'enable_profiling': False
            }
    
    def get_adaptive_batch_size(self, data_size: int) -> int:
        """Get adaptive batch size based on data size"""
        env_config = self.get_environment_config()
        base_batch_size = self.performance.batch_size_large_datasets
        
        # Adjust batch size based on environment and data size
        multiplier = env_config.get('batch_size_multiplier', 1.0)
        adjusted_batch_size = int(base_batch_size * multiplier)
        
        # Scale batch size based on data size
        if data_size < 1000:
            return min(adjusted_batch_size, data_size)
        elif data_size > 50000:
            return max(adjusted_batch_size, 2000)  # Minimum batch size for very large datasets
        else:
            return adjusted_batch_size

# Global configuration manager instance
config_manager = ConfigManager()

def get_config() -> ConfigManager:
    """Get the global configuration manager"""
    return config_manager

def optimize_for_data_size(data_size: int) -> Dict[str, Any]:
    """Get optimized settings based on data size"""
    config = get_config()
    
    if data_size < 1000:
        # Small datasets - prioritize responsiveness
        return {
            'batch_size': min(data_size, 100),
            'enable_caching': False,
            'memory_optimization': False,
            'progress_updates': False
        }
    elif data_size < 10000:
        # Medium datasets - balanced approach
        return {
            'batch_size': config.get_adaptive_batch_size(data_size),
            'enable_caching': True,
            'memory_optimization': True,
            'progress_updates': True
        }
    else:
        # Large datasets - prioritize performance
        return {
            'batch_size': config.get_adaptive_batch_size(data_size),
            'enable_caching': True,
            'memory_optimization': True,
            'progress_updates': True,
            'lazy_loading': True
        }