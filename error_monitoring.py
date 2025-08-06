#!/usr/bin/env python3
"""
Error monitoring and logging utilities for Commission Calculator Pro
"""

import logging
import functools
import traceback
from datetime import datetime
import sys
import os

# Configure logging
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{log_dir}/commission_calculator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('CommissionCalculator')

def error_handler(func):
    """Decorator to handle errors gracefully in Streamlit functions"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # For Streamlit, show user-friendly error
            try:
                import streamlit as st
                st.error(f"❌ An error occurred in {func.__name__}: {str(e)}")
                
                with st.expander("🔍 Technical Details", expanded=False):
                    st.code(traceback.format_exc())
                    
            except ImportError:
                print(f"Error in {func.__name__}: {str(e)}")
            
            return None
    return wrapper

def validate_dataframe(df, required_columns=None, min_rows=1, name="DataFrame"):
    """Validate DataFrame with comprehensive checks"""
    errors = []
    
    if df is None:
        errors.append(f"{name} is None")
        return errors
    
    if df.empty:
        errors.append(f"{name} is empty")
    
    if len(df) < min_rows:
        errors.append(f"{name} has {len(df)} rows, minimum required: {min_rows}")
    
    if required_columns:
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            errors.append(f"{name} missing required columns: {missing_cols}")
    
    # Check for data quality issues
    if not df.empty:
        # Check for all-null columns
        null_cols = [col for col in df.columns if df[col].isnull().all()]
        if null_cols:
            errors.append(f"{name} has all-null columns: {null_cols}")
        
        # Check for duplicate rows
        if df.duplicated().any():
            dup_count = df.duplicated().sum()
            errors.append(f"{name} has {dup_count} duplicate rows")
    
    return errors

def safe_divide(numerator, denominator, default=0):
    """Safely divide two numbers with zero protection"""
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ZeroDivisionError):
        return default

def safe_percentage(part, total, decimal_places=1):
    """Safely calculate percentage with zero protection"""
    if total == 0:
        return 0
    try:
        return round((part / total) * 100, decimal_places)
    except (TypeError, ZeroDivisionError):
        return 0

def log_operation(operation_name, details=None):
    """Log an operation for auditing"""
    timestamp = datetime.now().isoformat()
    log_entry = f"Operation: {operation_name} at {timestamp}"
    
    if details:
        log_entry += f" - Details: {details}"
    
    logger.info(log_entry)

def check_session_state_health():
    """Check session state for potential issues"""
    try:
        import streamlit as st
        
        issues = []
        
        # Check critical session state keys
        required_keys = ['logged_in', 'user', 'initialized']
        for key in required_keys:
            if key not in st.session_state:
                issues.append(f"Missing session state key: {key}")
        
        # Check data integrity
        if 'revenue_data' in st.session_state and st.session_state.revenue_data is not None:
            df_errors = validate_dataframe(st.session_state.revenue_data, name="Revenue Data")
            issues.extend(df_errors)
        
        if 'timesheet_data' in st.session_state and st.session_state.timesheet_data is not None:
            df_errors = validate_dataframe(st.session_state.timesheet_data, name="Timesheet Data")
            issues.extend(df_errors)
        
        return issues
        
    except ImportError:
        return ["Streamlit not available for session state check"]
    except Exception as e:
        return [f"Error checking session state: {str(e)}"]

if __name__ == "__main__":
    # Test the error monitoring functions
    print("🔍 Testing Error Monitoring Functions")
    print("=" * 50)
    
    # Test safe divide
    print(f"Safe divide 10/2: {safe_divide(10, 2)}")
    print(f"Safe divide 10/0: {safe_divide(10, 0)}")
    print(f"Safe divide 10/0 with default 999: {safe_divide(10, 0, 999)}")
    
    # Test safe percentage
    print(f"Safe percentage 25/100: {safe_percentage(25, 100)}%")
    print(f"Safe percentage 10/0: {safe_percentage(10, 0)}%")
    
    # Test logging
    log_operation("Test Operation", {"test": "data"})
    
    print("\n✅ Error monitoring functions working correctly!")