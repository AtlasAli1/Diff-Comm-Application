#!/usr/bin/env python3
"""
Error scan fixes and improvements for Commission Calculator Pro
This script contains additional validation and error handling improvements
"""

import pandas as pd
import streamlit as st
from typing import Optional, Any, List, Dict, Tuple
import logging

# Configure logging
logger = logging.getLogger(__name__)

def safe_dataframe_access(df: pd.DataFrame, index: int = 0, column: Optional[str] = None, 
                         default: Any = None) -> Any:
    """
    Safely access DataFrame elements with comprehensive error handling
    
    Args:
        df: DataFrame to access
        index: Row index (default 0)
        column: Column name (optional)
        default: Default value if access fails
        
    Returns:
        Value at specified location or default
    """
    try:
        # Check if DataFrame is None or empty
        if df is None or df.empty:
            logger.warning("DataFrame is None or empty")
            return default
            
        # Check if index is within bounds
        if index >= len(df) or index < 0:
            logger.warning(f"Index {index} out of bounds for DataFrame with {len(df)} rows")
            return default
            
        # Access value
        if column:
            if column not in df.columns:
                logger.warning(f"Column '{column}' not found in DataFrame")
                return default
            return df.iloc[index][column]
        else:
            return df.iloc[index]
            
    except Exception as e:
        logger.error(f"Error accessing DataFrame: {str(e)}")
        return default

def safe_division(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Perform division with zero protection and type checking
    
    Args:
        numerator: The number to divide
        denominator: The number to divide by
        default: Default value if division fails
        
    Returns:
        Result of division or default value
    """
    try:
        # Type conversion
        num = float(numerator)
        den = float(denominator)
        
        # Zero check
        if den == 0:
            logger.warning(f"Division by zero attempted: {num} / {den}")
            return default
            
        return num / den
        
    except (TypeError, ValueError) as e:
        logger.error(f"Invalid types for division: {type(numerator)} / {type(denominator)}")
        return default
    except Exception as e:
        logger.error(f"Unexpected error in division: {str(e)}")
        return default

def validate_commission_rates(rates: Dict[str, float]) -> Tuple[bool, List[str]]:
    """
    Validate commission rates with comprehensive checks
    
    Args:
        rates: Dictionary of commission rates
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    if not rates:
        errors.append("No commission rates provided")
        return False, errors
    
    total_rate = 0
    
    for rate_type, rate_value in rates.items():
        try:
            rate_float = float(rate_value)
            
            # Check for negative rates
            if rate_float < 0:
                errors.append(f"{rate_type}: Negative rate ({rate_float}%) not allowed")
                
            # Check for excessive rates
            elif rate_float > 100:
                errors.append(f"{rate_type}: Rate exceeds 100% ({rate_float}%)")
                
            # Add to total
            total_rate += rate_float
            
        except (TypeError, ValueError):
            errors.append(f"{rate_type}: Invalid rate value ({rate_value})")
    
    # Check total doesn't exceed 100%
    if total_rate > 100:
        errors.append(f"Total commission rate ({total_rate}%) exceeds 100%")
    
    return len(errors) == 0, errors

def safe_employee_lookup(employee_name: str, employee_data: pd.DataFrame) -> Optional[pd.Series]:
    """
    Safely lookup employee data with validation
    
    Args:
        employee_name: Name of employee to find
        employee_data: DataFrame containing employee data
        
    Returns:
        Employee data as Series or None if not found
    """
    try:
        if employee_data is None or employee_data.empty:
            logger.warning("Employee data is empty")
            return None
            
        if 'Name' not in employee_data.columns:
            logger.error("'Name' column not found in employee data")
            return None
            
        # Clean employee name
        clean_name = str(employee_name).strip()
        if not clean_name:
            logger.warning("Empty employee name provided")
            return None
            
        # Find employee
        matches = employee_data[employee_data['Name'] == clean_name]
        
        if len(matches) == 0:
            logger.warning(f"Employee '{clean_name}' not found")
            return None
        elif len(matches) > 1:
            logger.warning(f"Multiple employees found with name '{clean_name}', using first match")
            
        return matches.iloc[0]
        
    except Exception as e:
        logger.error(f"Error looking up employee '{employee_name}': {str(e)}")
        return None

def validate_revenue_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Comprehensive validation of revenue data
    
    Args:
        df: Revenue DataFrame to validate
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    if df is None or df.empty:
        errors.append("Revenue data is empty")
        return False, errors
    
    # Check for required columns
    required_cols = ['Business Unit', 'Revenue']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {', '.join(missing_cols)}")
    
    # Validate revenue values
    if 'Revenue' in df.columns:
        # Check for negative revenue
        negative_count = (df['Revenue'] < 0).sum()
        if negative_count > 0:
            errors.append(f"{negative_count} rows have negative revenue")
            
        # Check for non-numeric revenue
        try:
            pd.to_numeric(df['Revenue'], errors='raise')
        except:
            errors.append("Revenue column contains non-numeric values")
    
    # Check for duplicate entries
    if 'Business Unit' in df.columns and 'Lead Generated By' in df.columns:
        duplicates = df.duplicated(subset=['Business Unit', 'Lead Generated By'])
        dup_count = duplicates.sum()
        if dup_count > 0:
            errors.append(f"{dup_count} duplicate entries found")
    
    return len(errors) == 0, errors

def safe_technician_split(technicians_str: str, separator_list: List[str] = [',', '&', 'and']) -> List[str]:
    """
    Safely split technician string with multiple separators
    
    Args:
        technicians_str: String containing technician names
        separator_list: List of separators to use
        
    Returns:
        List of technician names
    """
    try:
        if not technicians_str or not isinstance(technicians_str, str):
            return []
            
        # Clean string
        result = str(technicians_str).strip()
        
        # Split by each separator
        for separator in separator_list:
            parts = []
            for part in result.split(separator):
                clean_part = part.strip()
                if clean_part and clean_part not in parts:
                    parts.append(clean_part)
            result = ' '.join(parts) if parts else result
            
        # Final split and clean
        technicians = []
        for tech in result.split():
            tech_clean = tech.strip()
            if tech_clean and tech_clean not in technicians:
                technicians.append(tech_clean)
                
        return technicians
        
    except Exception as e:
        logger.error(f"Error splitting technicians: {str(e)}")
        return []

def create_startup_checks() -> Dict[str, bool]:
    """
    Perform startup checks for the application
    
    Returns:
        Dictionary of check results
    """
    checks = {}
    
    # Check Python version
    import sys
    checks['python_version'] = sys.version_info >= (3, 8)
    
    # Check required modules
    required_modules = ['streamlit', 'pandas', 'plotly', 'numpy']
    for module in required_modules:
        try:
            __import__(module)
            checks[f'module_{module}'] = True
        except ImportError:
            checks[f'module_{module}'] = False
    
    # Check file permissions
    import os
    checks['can_write_logs'] = os.access('.', os.W_OK)
    
    return checks

def enhanced_error_handler(func):
    """
    Enhanced decorator for comprehensive error handling
    """
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except pd.errors.EmptyDataError:
            logger.error(f"{func.__name__}: Empty data error")
            st.error("❌ No data available to process")
            return None
        except FileNotFoundError as e:
            logger.error(f"{func.__name__}: File not found - {str(e)}")
            st.error(f"❌ File not found: {str(e)}")
            return None
        except PermissionError as e:
            logger.error(f"{func.__name__}: Permission denied - {str(e)}")
            st.error(f"❌ Permission denied: {str(e)}")
            return None
        except ValueError as e:
            logger.error(f"{func.__name__}: Value error - {str(e)}")
            st.error(f"❌ Invalid value: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"{func.__name__}: Unexpected error - {str(e)}")
            st.error(f"❌ An unexpected error occurred: {str(e)}")
            with st.expander("Error Details"):
                st.code(traceback.format_exc())
            return None
    
    return wrapper

# Example usage in Streamlit app
if __name__ == "__main__":
    print("Error handling utilities loaded successfully")
    
    # Run startup checks
    print("\n🔍 Running startup checks...")
    checks = create_startup_checks()
    
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check}: {result}")
    
    # Test division safety
    print("\n🧪 Testing safe division...")
    print(f"10 / 2 = {safe_division(10, 2)}")
    print(f"10 / 0 = {safe_division(10, 0, default=-1)}")
    
    # Test commission rate validation
    print("\n🧪 Testing commission rate validation...")
    rates = {'lead_gen': 5.0, 'sales': 7.5, 'work_done': 3.0}
    is_valid, errors = validate_commission_rates(rates)
    print(f"Valid rates: {is_valid}")
    
    rates_invalid = {'lead_gen': 50.0, 'sales': 60.0}
    is_valid, errors = validate_commission_rates(rates_invalid)
    print(f"Invalid rates: {is_valid}, Errors: {errors}")