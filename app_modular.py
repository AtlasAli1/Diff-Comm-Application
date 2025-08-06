"""
Commission Calculator Pro - Modular Version
Main application orchestrator that coordinates all UI modules
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import UI modules
from ui.utils import safe_session_get, safe_session_init, apply_custom_css, get_project_root
from ui.dashboard import display_dashboard_tab
from ui.data_management import display_data_management_tab
from ui.commission_calc import display_commission_calculate
from ui.company_setup import display_company_setup_tab
from ui.reports import display_reports_tab

# Page configuration
st.set_page_config(
    page_title="Commission Calculator Pro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def initialize_session_state():
    """Initialize all session state variables"""
    
    # Basic initialization
    safe_session_init('initialized', False)
    
    if not st.session_state.initialized:
        # User session
        safe_session_init('user', {'username': 'admin', 'role': 'admin'})
        safe_session_init('logged_in', True)
        
        # Data storage
        safe_session_init('uploaded_timesheet_data', None)
        safe_session_init('uploaded_revenue_data', None)
        safe_session_init('saved_timesheet_data', None)
        safe_session_init('saved_revenue_data', None)
        
        # File tracking
        safe_session_init('timesheet_file_name', None)
        safe_session_init('revenue_file_name', None)
        safe_session_init('data_updated', False)
        safe_session_init('last_timesheet_save', None)
        safe_session_init('last_revenue_save', None)
        
        # Auto-load test data if available
        auto_load_test_data()
        
        # Employee data
        safe_session_init('employee_data', pd.DataFrame())
        
        # Commission settings
        safe_session_init('business_unit_rates', {})
        safe_session_init('business_unit_commission_settings', {})
        safe_session_init('employee_commission_overrides', {})
        safe_session_init('commission_rates', {})
        safe_session_init('config_saved', False)
        
        # Timesheet overrides
        safe_session_init('timesheet_hour_overrides', {})
        
        # Exclusion list
        safe_session_init('exclusion_list', [])
        
        # UI state
        safe_session_init('active_tab', 'Dashboard')
        
        # Mark as initialized
        st.session_state.initialized = True

def auto_load_test_data():
    """Auto-load test data files if they exist"""
    
    project_root = get_project_root()
    
    # Try to load Revenue.xlsx
    try:
        revenue_path = project_root / "Revenue.xlsx"
        if revenue_path.exists():
            revenue_data = pd.read_excel(revenue_path)
            st.session_state.saved_revenue_data = revenue_data
            st.session_state.revenue_file_name = "Revenue.xlsx"
            st.session_state.data_updated = True
            print(f"✅ Auto-loaded Revenue.xlsx: {len(revenue_data)} rows")
    except Exception as e:
        print(f"❌ Could not auto-load Revenue.xlsx: {e}")
        
    # Try to load Timesheet 1.xlsx
    try:
        timesheet_path = project_root / "Timesheet 1.xlsx"
        if timesheet_path.exists():
            timesheet_data = pd.read_excel(timesheet_path)
            st.session_state.saved_timesheet_data = timesheet_data
            st.session_state.timesheet_file_name = "Timesheet 1.xlsx"
            st.session_state.data_updated = True
            print(f"✅ Auto-loaded Timesheet 1.xlsx: {len(timesheet_data)} rows")
    except Exception as e:
        print(f"❌ Could not auto-load Timesheet 1.xlsx: {e}")

def display_header():
    """Display application header"""
    
    st.markdown("""
    <div style="background: linear-gradient(90deg, #2C5F75 0%, #922B3E 100%); 
                padding: 1rem; border-radius: 10px; color: white; text-align: center; margin-bottom: 2rem;">
        <h1 style="margin: 0; font-size: 2.5rem;">💰 Commission Calculator Pro</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem;">Professional Commission Management System</p>
    </div>
    """, unsafe_allow_html=True)

def display_navigation():
    """Display main navigation"""
    
    tabs = st.tabs([
        "🏠 Dashboard",
        "⚙️ Company Setup",
        "📊 Data Management", 
        "🧮 Commission Calc",
        "📈 Reports"
    ])
    
    return tabs

def display_status_bar():
    """Display status bar with data availability"""
    
    revenue_available = safe_session_get('saved_revenue_data') is not None
    timesheet_available = safe_session_get('saved_timesheet_data') is not None
    employee_available = not safe_session_get('employee_data', pd.DataFrame()).empty
    
    status_col1, status_col2, status_col3, status_col4 = st.columns([1, 1, 1, 1])
    
    with status_col1:
        status = "✅ Loaded" if revenue_available else "⏳ Missing"
        color = "green" if revenue_available else "orange"
        st.markdown(f"<small style='color: {color};'>📊 Revenue: {status}</small>", unsafe_allow_html=True)
    
    with status_col2:
        status = "✅ Loaded" if timesheet_available else "⏳ Missing"
        color = "green" if timesheet_available else "orange"
        st.markdown(f"<small style='color: {color};'>⏰ Timesheet: {status}</small>", unsafe_allow_html=True)
    
    with status_col3:
        status = "✅ Loaded" if employee_available else "⏳ Missing"
        color = "green" if employee_available else "orange"
        st.markdown(f"<small style='color: {color};'>👥 Employees: {status}</small>", unsafe_allow_html=True)
    
    with status_col4:
        user_info = safe_session_get('user', {'username': 'Unknown'})
        st.markdown(f"<small style='color: gray;'>👤 User: {user_info['username']}</small>", unsafe_allow_html=True)

def main():
    """Main application function"""
    
    # Apply custom CSS
    apply_custom_css()
    
    # Initialize session state
    initialize_session_state()
    
    # Display header
    display_header()
    
    # Display status bar
    display_status_bar()
    
    # Add some spacing
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Main navigation
    tabs = display_navigation()
    
    # Dashboard Tab
    with tabs[0]:
        try:
            display_dashboard_tab()
        except Exception as e:
            st.error(f"❌ Error loading dashboard: {str(e)}")
            st.text("Please check the error details and refresh the page.")
    
    # Company Setup Tab
    with tabs[1]:
        try:
            display_company_setup_tab()
        except Exception as e:
            st.error(f"❌ Error loading company setup: {str(e)}")
            st.text("Please check the error details and refresh the page.")
    
    # Data Management Tab  
    with tabs[2]:
        try:
            display_data_management_tab()
        except Exception as e:
            st.error(f"❌ Error loading data management: {str(e)}")
            st.text("Please check the error details and refresh the page.")
    
    # Commission Calculation Tab
    with tabs[3]:
        try:
            display_commission_calculate()
        except Exception as e:
            st.error(f"❌ Error loading commission calculator: {str(e)}")
            st.text("Please check the error details and refresh the page.")
    
    # Reports Tab
    with tabs[4]:
        try:
            display_reports_tab()
        except Exception as e:
            st.error(f"❌ Error loading reports: {str(e)}")
            st.text("Please check the error details and refresh the page.")
    
    # Footer
    display_footer()

def display_footer():
    """Display application footer"""
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: gray; padding: 1rem;">
        <small>
            Commission Calculator Pro v2.0 | 
            Modular Architecture | 
            Generated: {timestamp}
        </small>
    </div>
    """.format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)

def cleanup_memory():
    """Clean up memory by removing temporary session state variables"""
    
    temp_keys = [k for k in st.session_state.keys() if k.startswith('temp_')]
    for key in temp_keys:
        del st.session_state[key]

# Performance optimization
@st.cache_data
def load_cached_data(file_path: str):
    """Load data with caching for better performance"""
    try:
        if file_path.endswith('.xlsx'):
            return pd.read_excel(file_path)
        elif file_path.endswith('.csv'):
            return pd.read_csv(file_path)
    except Exception:
        return pd.DataFrame()

if __name__ == "__main__":
    try:
        main()
        
        # Clean up memory periodically
        if st.session_state.get('cleanup_counter', 0) % 50 == 0:
            cleanup_memory()
        
        safe_session_init('cleanup_counter', 0)
        st.session_state.cleanup_counter += 1
        
    except Exception as e:
        st.error(f"❌ Application Error: {str(e)}")
        st.text("Please refresh the page and try again.")
        
        # Show debug info in development
        if st.checkbox("Show Debug Info"):
            import traceback
            st.text("Full traceback:")
            st.text(traceback.format_exc())