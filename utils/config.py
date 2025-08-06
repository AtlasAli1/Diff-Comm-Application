"""Configuration management for Commission Calculator Pro."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from loguru import logger


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    path: str = "commission_calculator.db"
    backup_interval: int = 24  # hours
    max_backups: int = 7
    

@dataclass
class UIConfig:
    """UI configuration settings."""
    theme: str = "light"
    page_title: str = "Commission Calculator Pro"
    sidebar_state: str = "expanded"
    default_chart_type: str = "bar"
    records_per_page: int = 50
    

@dataclass
class SecurityConfig:
    """Security configuration settings."""
    session_timeout: int = 480  # minutes
    password_min_length: int = 8
    max_login_attempts: int = 5
    lockout_duration: int = 30  # minutes
    

@dataclass
class BusinessConfig:
    """Business rule configuration settings."""
    max_overtime_hours: float = 20.0
    max_double_time_hours: float = 8.0
    max_commission_rate: float = 50.0  # percentage
    default_commission_rates: Dict[str, float] = None
    
    def __post_init__(self):
        if self.default_commission_rates is None:
            self.default_commission_rates = {
                'lead_generated_by': 2.0,
                'sold_by': 3.0,
                'work_done': 5.0
            }


@dataclass
class ExportConfig:
    """Export configuration settings."""
    default_format: str = "xlsx"
    include_metadata: bool = True
    max_export_records: int = 10000
    export_directory: str = "exports"
    

@dataclass
class AppConfig:
    """Main application configuration."""
    database: DatabaseConfig
    ui: UIConfig
    security: SecurityConfig
    business: BusinessConfig
    export: ExportConfig
    
    def __init__(self):
        self.database = DatabaseConfig()
        self.ui = UIConfig()
        self.security = SecurityConfig()
        self.business = BusinessConfig()
        self.export = ExportConfig()


class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path or "config.json")
        self.config = AppConfig()
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                
                # Update configuration with loaded data
                if 'database' in config_data:
                    self.config.database = DatabaseConfig(**config_data['database'])
                
                if 'ui' in config_data:
                    self.config.ui = UIConfig(**config_data['ui'])
                
                if 'security' in config_data:
                    self.config.security = SecurityConfig(**config_data['security'])
                
                if 'business' in config_data:
                    business_data = config_data['business']
                    # Handle default_commission_rates separately
                    if 'default_commission_rates' not in business_data:
                        business_data['default_commission_rates'] = None
                    self.config.business = BusinessConfig(**business_data)
                
                if 'export' in config_data:
                    self.config.export = ExportConfig(**config_data['export'])
                
                logger.info(f"Configuration loaded from {self.config_path}")
            else:
                logger.info("No configuration file found, using defaults")
                self.save_config()  # Create default config file
                
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            logger.info("Using default configuration")
    
    def save_config(self) -> None:
        """Save configuration to file."""
        try:
            config_data = {
                'database': asdict(self.config.database),
                'ui': asdict(self.config.ui),
                'security': asdict(self.config.security),
                'business': asdict(self.config.business),
                'export': asdict(self.config.export)
            }
            
            # Ensure config directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            logger.info(f"Configuration saved to {self.config_path}")
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def get_config(self) -> AppConfig:
        """Get current configuration."""
        return self.config
    
    def update_config(self, section: str, updates: Dict[str, Any]) -> None:
        """Update configuration section.
        
        Args:
            section: Configuration section name ('database', 'ui', etc.)
            updates: Dictionary of updates to apply
        """
        try:
            if section == 'database':
                for key, value in updates.items():
                    if hasattr(self.config.database, key):
                        setattr(self.config.database, key, value)
            
            elif section == 'ui':
                for key, value in updates.items():
                    if hasattr(self.config.ui, key):
                        setattr(self.config.ui, key, value)
            
            elif section == 'security':
                for key, value in updates.items():
                    if hasattr(self.config.security, key):
                        setattr(self.config.security, key, value)
            
            elif section == 'business':
                for key, value in updates.items():
                    if hasattr(self.config.business, key):
                        setattr(self.config.business, key, value)
            
            elif section == 'export':
                for key, value in updates.items():
                    if hasattr(self.config.export, key):
                        setattr(self.config.export, key, value)
            
            else:
                raise ValueError(f"Unknown configuration section: {section}")
            
            self.save_config()
            logger.info(f"Configuration section '{section}' updated")
            
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults."""
        self.config = AppConfig()
        self.save_config()
        logger.info("Configuration reset to defaults")
    
    def validate_config(self) -> tuple[bool, list[str]]:
        """Validate current configuration.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate database config
        if not self.config.database.path:
            errors.append("Database path cannot be empty")
        
        if self.config.database.backup_interval < 1:
            errors.append("Backup interval must be at least 1 hour")
        
        if self.config.database.max_backups < 1:
            errors.append("Maximum backups must be at least 1")
        
        # Validate security config
        if self.config.security.session_timeout < 30:
            errors.append("Session timeout must be at least 30 minutes")
        
        if self.config.security.password_min_length < 4:
            errors.append("Minimum password length must be at least 4")
        
        # Validate business config
        if self.config.business.max_commission_rate > 100:
            errors.append("Maximum commission rate cannot exceed 100%")
        
        if self.config.business.max_overtime_hours < 0:
            errors.append("Maximum overtime hours cannot be negative")
        
        # Validate export config
        if self.config.export.max_export_records < 1:
            errors.append("Maximum export records must be at least 1")
        
        return len(errors) == 0, errors
    
    def get_environment_overrides(self) -> Dict[str, Any]:
        """Get configuration overrides from environment variables."""
        overrides = {}
        
        # Database overrides
        if db_path := os.getenv('CC_DB_PATH'):
            overrides.setdefault('database', {})['path'] = db_path
        
        # Security overrides
        if session_timeout := os.getenv('CC_SESSION_TIMEOUT'):
            try:
                overrides.setdefault('security', {})['session_timeout'] = int(session_timeout)
            except ValueError:
                logger.warning(f"Invalid session timeout value: {session_timeout}")
        
        # UI overrides
        if theme := os.getenv('CC_THEME'):
            overrides.setdefault('ui', {})['theme'] = theme
        
        return overrides
    
    def apply_environment_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        overrides = self.get_environment_overrides()
        
        for section, updates in overrides.items():
            self.update_config(section, updates)
            logger.info(f"Applied environment overrides to {section}: {updates}")


# Global configuration instance
_config_manager = None


def get_config_manager(config_path: Optional[str] = None) -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigManager(config_path)
    
    return _config_manager


def get_config() -> AppConfig:
    """Get the current application configuration."""
    return get_config_manager().get_config()
