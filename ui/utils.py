"""
Common utilities and helper functions for UI modules
"""
import streamlit as st
import pandas as pd
from pathlib import Path
from typing import Tuple, Any, Optional, Dict, List
from datetime import datetime, timedelta
import hashlib
import pickle

# Session State Safety Helper Functions
def safe_session_get(key: str, default: Any = None) -> Any:
    """Safely get value from session state with default fallback"""
    return st.session_state.get(key, default)

def safe_session_check(key: str) -> bool:
    """Safely check if key exists in session state"""
    return key in st.session_state

def safe_session_init(key: str, default_value: Any) -> Any:
    """Safely initialize session state key if it doesn't exist"""
    if key not in st.session_state:
        st.session_state[key] = default_value
    return st.session_state[key]

# File Validation Functions
def validate_file_size(uploaded_file, max_size_mb: float = 50) -> Tuple[bool, str]:
    """Validate uploaded file size"""
    if uploaded_file is None:
        return True, ""
    
    file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
    if file_size_mb > max_size_mb:
        return False, f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed size ({max_size_mb}MB)"
    return True, f"File size: {file_size_mb:.1f}MB"

def validate_file_content(uploaded_file) -> Tuple[bool, str]:
    """Basic validation of file content"""
    if uploaded_file is None:
        return True, ""
    
    try:
        # Check if file is readable
        content = uploaded_file.getvalue()
        if len(content) == 0:
            return False, "File is empty"
        
        # Basic file type validation by content
        file_ext = uploaded_file.name.lower()
        if file_ext.endswith(('.xlsx', '.xls')):
            # For Excel files, check for basic Excel magic bytes
            if not content.startswith(b'PK'):  # Excel files are ZIP-based
                return False, "Invalid Excel file format"
        elif file_ext.endswith('.csv'):
            # For CSV, try to decode as text
            try:
                content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    content.decode('latin-1')
                except UnicodeDecodeError:
                    return False, "Invalid CSV file encoding"
        
        return True, "File content validation passed"
    except Exception as e:
        return False, f"File validation error: {str(e)}"

# Data Processing Helpers
def get_project_root() -> Path:
    """Get the project root directory"""
    return Path(__file__).parent.parent

def format_currency(value: float) -> str:
    """Format value as currency"""
    return f"${value:,.2f}"

def format_percentage(value: float, decimals: int = 1) -> str:
    """Format value as percentage"""
    return f"{value:.{decimals}f}%"

# DataFrame Helpers
def safe_dataframe_operation(df: pd.DataFrame, operation: str, column: str = None, default: Any = None) -> Any:
    """Safely perform operations on DataFrames"""
    if df is None or df.empty:
        return default
    
    try:
        if operation == 'columns':
            return list(df.columns)
        elif operation == 'length':
            return len(df)
        elif operation == 'get_column' and column:
            return df.get(column, pd.Series())
        else:
            return default
    except Exception:
        return default

def get_revenue_column(df: pd.DataFrame) -> Optional[str]:
    """Detect the revenue column name in the DataFrame"""
    if df is None or df.empty:
        return None
    
    # Possible revenue column names in order of preference
    revenue_columns = [
        'Jobs Total Revenue',
        'Total Revenue', 
        'Revenue',
        'Job Revenue',
        'Total',
        'Amount',
        'Job Total'
    ]
    
    for col_name in revenue_columns:
        if col_name in df.columns:
            return col_name
    
    # Fallback: look for columns containing 'revenue' (case insensitive)
    for col in df.columns:
        if 'revenue' in str(col).lower():
            return col
    
    return None

def get_safe_revenue_data(df: pd.DataFrame, revenue_column: str = None) -> pd.Series:
    """Safely extract revenue data as numeric series"""
    if df is None or df.empty:
        return pd.Series()
    
    if revenue_column is None:
        revenue_column = get_revenue_column(df)
    
    if revenue_column is None or revenue_column not in df.columns:
        return pd.Series()
    
    try:
        return pd.to_numeric(df[revenue_column], errors='coerce').fillna(0)
    except Exception:
        return pd.Series()

# Memory Management
def cleanup_session_state(prefix: str = None):
    """Clean up session state variables"""
    if prefix:
        keys_to_remove = [k for k in st.session_state.keys() if k.startswith(prefix)]
    else:
        # Clean up temporary keys
        keys_to_remove = [k for k in st.session_state.keys() if k.startswith('temp_')]
    
    for key in keys_to_remove:
        del st.session_state[key]
    
    return len(keys_to_remove)

# Progress Indicator Helper
def show_progress(message: str, current: int, total: int):
    """Show progress indicator"""
    if total > 0:
        progress = current / total
        st.progress(progress)
        st.text(f"{message}: {current}/{total} ({progress*100:.1f}%)")

# Styling Helpers
def apply_custom_css():
    """Apply custom CSS styling"""
    st.markdown("""
    <style>
        .main-header {
            background: linear-gradient(90deg, #2C5F75 0%, #922B3E 100%);
            padding: 2rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
        }
        .feature-card {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            margin: 1rem 0;
            border-left: 4px solid #2C5F75;
            border: 1px solid #dee2e6;
        }
        .feature-card h4 {
            color: #2C5F75;
            margin-bottom: 0.5rem;
        }
        .metric-card {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            text-align: center;
        }
        .success-message {
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 1rem;
            border-radius: 5px;
            margin: 1rem 0;
        }
        .warning-message {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 1rem;
            border-radius: 5px;
            margin: 1rem 0;
        }
        .stButton > button {
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        /* Hide sidebar */
        section[data-testid="stSidebar"] {
            display: none;
        }
    </style>
    """, unsafe_allow_html=True)

# Pay Period Utility Functions
def get_current_pay_period() -> Optional[Dict]:
    """Get the current pay period based on today's date"""
    pay_periods = safe_session_get('pay_periods', [])
    today = datetime.now().date()
    
    for period in pay_periods:
        if period['start_date'] <= today <= period['end_date']:
            return period
    
    # If no current period found, return the most recent past period
    past_periods = [p for p in pay_periods if p['end_date'] < today]
    if past_periods:
        return past_periods[-1]
    
    # Or return the next future period
    future_periods = [p for p in pay_periods if p['start_date'] > today]
    if future_periods:
        return future_periods[0]
    
    return None

def get_selected_pay_period() -> Optional[Dict]:
    """Get the currently selected pay period from session state"""
    return safe_session_get('selected_pay_period', get_current_pay_period())

def format_pay_period(period: Dict) -> str:
    """Format a pay period for display"""
    if not period:
        return "No pay period selected"
    
    return f"Period {period['number']}: {period['start_date'].strftime('%b %d')} - {period['end_date'].strftime('%b %d, %Y')}"

def is_pay_period_configured() -> bool:
    """Check if pay periods have been configured"""
    pay_settings = safe_session_get('pay_period_settings', {})
    return pay_settings.get('configured', False)

def get_pay_period_by_date(date) -> Optional[Dict]:
    """Get the pay period that contains a specific date"""
    pay_periods = safe_session_get('pay_periods', [])
    
    for period in pay_periods:
        if period['start_date'] <= date <= period['end_date']:
            return period
    
    return None

def get_employee_hours_with_overrides(employee_name: str, timesheet_data: pd.DataFrame) -> Tuple[float, float, float]:
    """Get employee hours, using overrides if available"""
    
    overrides = safe_session_get('timesheet_hour_overrides', {})
    
    # Check for overrides first
    if employee_name in overrides:
        override_data = overrides[employee_name]
        return (
            override_data.get('regular_hours', 0),
            override_data.get('ot_hours', 0),
            override_data.get('dt_hours', 0)
        )
    
    # Fall back to timesheet data
    if timesheet_data is not None and not timesheet_data.empty and 'Employee Name' in timesheet_data.columns:
        emp_data = timesheet_data[timesheet_data['Employee Name'] == employee_name]
        
        if not emp_data.empty:
            # Handle different column naming conventions
            regular_hours = 0
            if 'Reg Hours' in emp_data.columns:
                regular_hours = pd.to_numeric(emp_data['Reg Hours'], errors='coerce').sum()
            elif 'Regular Hours' in emp_data.columns:
                regular_hours = pd.to_numeric(emp_data['Regular Hours'], errors='coerce').sum()
            
            ot_hours = pd.to_numeric(emp_data.get('OT Hours', 0), errors='coerce').sum()
            dt_hours = pd.to_numeric(emp_data.get('DT Hours', 0), errors='coerce').sum()
            
            return (regular_hours, ot_hours, dt_hours)
    
    return (0, 0, 0)

# Data Caching and Performance Optimization
def generate_data_hash(*args) -> str:
    """Generate hash for data caching based on input arguments"""
    hash_input = str(args)
    return hashlib.md5(hash_input.encode()).hexdigest()[:8]

def cache_expensive_operation(operation_key: str, operation_func, *args, ttl_seconds: int = 3600):
    """Cache expensive operations with TTL"""
    # Create cache key with data hash
    data_hash = generate_data_hash(*args)
    cache_key = f"cached_{operation_key}_{data_hash}"
    cache_time_key = f"{cache_key}_timestamp"
    
    # Check if cached result exists and is still valid
    cached_result = safe_session_get(cache_key)
    cache_time = safe_session_get(cache_time_key, 0)
    
    current_time = datetime.now().timestamp()
    
    if cached_result is not None and (current_time - cache_time) < ttl_seconds:
        return cached_result
    
    # Execute operation and cache result
    result = operation_func(*args)
    st.session_state[cache_key] = result
    st.session_state[cache_time_key] = current_time
    
    return result

@st.cache_data(ttl=3600)  # Cache for 1 hour
def cached_dataframe_groupby(df: pd.DataFrame, group_cols: List[str], agg_dict: Dict) -> pd.DataFrame:
    """Cached DataFrame groupby operation"""
    if df.empty:
        return pd.DataFrame()
    return df.groupby(group_cols).agg(agg_dict).reset_index()

@st.cache_data(ttl=1800)  # Cache for 30 minutes  
def cached_commission_calculation(revenue_data: pd.DataFrame, business_unit_settings: Dict, 
                                selected_employees: List[str], start_date, end_date) -> pd.DataFrame:
    """Cached commission calculation for performance"""
    if revenue_data.empty:
        return pd.DataFrame()
    
    # This would contain the core commission calculation logic
    # Simplified version for now
    results = []
    revenue_column = get_revenue_column(revenue_data)
    
    if not revenue_column:
        return pd.DataFrame()
    
    for business_unit, settings in business_unit_settings.items():
        unit_revenue = revenue_data[revenue_data['Business Unit'] == business_unit] if 'Business Unit' in revenue_data.columns else revenue_data
        
        if unit_revenue.empty:
            continue
            
        # Process each commission type more efficiently
        for employee in selected_employees:
            # Lead Generation
            if 'Lead Generated By' in unit_revenue.columns and settings.get('lead_gen_rate', 0) > 0:
                lead_jobs = unit_revenue[unit_revenue['Lead Generated By'] == employee]
                if not lead_jobs.empty:
                    total_revenue = pd.to_numeric(lead_jobs[revenue_column], errors='coerce').sum()
                    commission = total_revenue * (settings['lead_gen_rate'] / 100)
                    if commission > 0:
                        results.append({
                            'Employee': employee,
                            'Type': 'Lead Generation', 
                            'Business Unit': business_unit,
                            'Revenue': total_revenue,
                            'Commission': commission
                        })
    
    return pd.DataFrame(results)

def get_or_compute_employee_summary(employee_data: pd.DataFrame) -> Dict:
    """Get cached employee summary or compute if needed"""
    def compute_summary(df):
        if df.empty:
            return {}
        
        return {
            'total_employees': len(df),
            'active_employees': len(df[df['Status'] == 'Active']),
            'commission_eligible': len(df[df.get('Commission Eligible', False) == True]),
            'efficiency_pay_count': len(df[df.get('Commission Plan') == 'Efficiency Pay']),
            'avg_hourly_rate': df.get('Hourly Rate', pd.Series([0])).astype(float).mean()
        }
    
    return cache_expensive_operation('employee_summary', compute_summary, employee_data.to_json())

def optimize_dataframe_memory(df: pd.DataFrame) -> pd.DataFrame:
    """Optimize DataFrame memory usage"""
    if df.empty:
        return df
    
    optimized_df = df.copy()
    
    # Convert object columns to category if they have few unique values
    for col in optimized_df.select_dtypes(include=['object']):
        if optimized_df[col].dtype == 'object':
            unique_ratio = optimized_df[col].nunique() / len(optimized_df)
            if unique_ratio < 0.5:  # Less than 50% unique values
                optimized_df[col] = optimized_df[col].astype('category')
    
    # Downcast numeric types
    for col in optimized_df.select_dtypes(include=['int64']):
        if optimized_df[col].min() >= 0:
            optimized_df[col] = pd.to_numeric(optimized_df[col], downcast='unsigned')
        else:
            optimized_df[col] = pd.to_numeric(optimized_df[col], downcast='integer')
    
    for col in optimized_df.select_dtypes(include=['float64']):
        optimized_df[col] = pd.to_numeric(optimized_df[col], downcast='float')
    
    return optimized_df

def batch_process_large_dataset(df: pd.DataFrame, process_func, batch_size: int = 1000, *args, **kwargs):
    """Process large datasets in batches to avoid memory issues"""
    if len(df) <= batch_size:
        return process_func(df, *args, **kwargs)
    
    results = []
    total_batches = (len(df) - 1) // batch_size + 1
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i + batch_size]
        batch_result = process_func(batch, *args, **kwargs)
        results.append(batch_result)
        
        # Update progress
        progress = (i // batch_size + 1) / total_batches
        progress_bar.progress(progress)
        status_text.text(f"Processing batch {i//batch_size + 1} of {total_batches}")
    
    progress_bar.empty()
    status_text.empty()
    
    # Combine results
    if results and isinstance(results[0], pd.DataFrame):
        return pd.concat(results, ignore_index=True)
    else:
        return results