import streamlit as st
import streamlit_extras.colored_header as colored_header
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_extras.badges import badge
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from models import Employee, BusinessUnit, CommissionCalculator
from utils import DatabaseManager, AuthManager, ExportManager, DataValidator
from utils.notifications import (
    NotificationManager, 
    display_notification_center, 
    display_notification_badge,
    notify_commission_calculated,
    notify_data_import_complete
)
from pages import (
    data_management_page,
    system_configuration_page,
    analytics_dashboard_page,
    commission_reports_page,
    advanced_settings_page
)

# Page configuration
st.set_page_config(
    page_title="Commission Calculator Pro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/commission-calculator-pro',
        'Report a bug': 'https://github.com/yourusername/commission-calculator-pro/issues',
        'About': 'Commission Calculator Pro v2.0 - Enhanced commission management system'
    }
)

# Custom CSS with animations and modern styling
st.markdown("""
<style>
    /* CSS Variables */
    :root {
        --primary-color: #2C5F75;
        --secondary-color: #922B3E;
        --success-color: #28a745;
        --warning-color: #ffc107;
        --danger-color: #dc3545;
        --info-color: #17a2b8;
        --dark-bg: #1e1e1e;
        --light-bg: #f8f9fa;
    }
    
    /* Main container styling */
    .main {
        padding: 2rem;
        animation: fadeIn 0.5s ease-in;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: var(--primary-color);
    }
    
    /* Headers with gradient */
    h1, h2, h3 {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: slideDown 0.5s ease-out;
    }
    
    /* Card styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: rgba(44, 95, 117, 0.05);
        padding: 0.5rem;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: var(--primary-color);
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--primary-color) !important;
        color: white !important;
    }
    
    /* Metric cards */
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border: 1px solid rgba(44, 95, 117, 0.2);
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 25px;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
    }
    
    /* Success/Error messages */
    .stSuccess, .stError, .stWarning, .stInfo {
        padding: 1rem;
        border-radius: 10px;
        animation: slideIn 0.5s ease-out;
    }
    
    /* DataFrames */
    .dataframe {
        border: none !important;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes slideDown {
        from { transform: translateY(-20px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    
    @keyframes slideIn {
        from { transform: translateX(-20px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        animation: progress 2s ease-in-out infinite;
    }
    
    @keyframes progress {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
    
    /* Sidebar navigation items */
    .sidebar-nav-item {
        padding: 0.5rem 1rem;
        margin: 0.25rem 0;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    
    .sidebar-nav-item:hover {
        background-color: rgba(255, 255, 255, 0.1);
        transform: translateX(5px);
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.875rem;
        font-weight: bold;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """Initialize session state variables"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        try:
            st.session_state.db_manager = DatabaseManager()
            st.session_state.auth_manager = AuthManager(st.session_state.db_manager)
            st.session_state.export_manager = ExportManager()
            st.session_state.validator = DataValidator()
            st.session_state.calculator = CommissionCalculator()
            
            # Load data from database
            load_data_from_db()
        except Exception as e:
            st.error(f"Initialization error: {str(e)}")
            # Fallback initialization
            st.session_state.user = {'username': 'admin', 'role': 'admin'}
            st.session_state.calculator = CommissionCalculator()
    
    # Ensure calculator always exists
    if 'calculator' not in st.session_state:
        st.session_state.calculator = CommissionCalculator()

def load_data_from_db():
    """Load data from database into calculator"""
    try:
        # Load employees
        employees = st.session_state.db_manager.get_employees()
        for emp_data in employees:
            employee = Employee(**emp_data)
            st.session_state.calculator.add_employee(employee)
        
        # Load business units
        units = st.session_state.db_manager.get_business_units()
        for unit_data in units:
            unit = BusinessUnit(**unit_data)
            st.session_state.calculator.add_business_unit(unit)
        
        # Load commissions
        commissions = st.session_state.db_manager.get_commissions()
        # Process commissions as needed
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")

def check_system_status():
    """Check and display system status"""
    status = {
        'data_uploaded': False,
        'rates_configured': False,
        'ready_to_calculate': False
    }
    
    calc = st.session_state.calculator
    
    # Check data upload
    if calc.employees and calc.business_units:
        status['data_uploaded'] = True
    
    # Check rate configuration
    if status['data_uploaded']:
        has_hourly_rates = all(emp.hourly_rate > 0 for emp in calc.employees.values())
        has_commission_rates = all(unit.commission_rate > 0 for unit in calc.business_units.values())
        if has_hourly_rates and has_commission_rates:
            status['rates_configured'] = True
    
    status['ready_to_calculate'] = status['data_uploaded'] and status['rates_configured']
    
    return status

def display_sidebar():
    """Display sidebar with navigation and status"""
    with st.sidebar:
        # Logo/Title
        st.markdown("""
        <div style='text-align: center; padding: 1rem 0;'>
            <h1 style='color: white; margin: 0;'>💰</h1>
            <h3 style='color: white; margin: 0;'>Commission Calculator Pro</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # User info if logged in
        if 'user' in st.session_state:
            user = st.session_state.user
            st.markdown(f"""
            <div style='background-color: rgba(255,255,255,0.1); padding: 1rem; border-radius: 10px;'>
                <p style='margin: 0; color: white;'>👤 {user['username']}</p>
                <p style='margin: 0; color: white; font-size: 0.875rem;'>Role: {user['role'].title()}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Notification section
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button("🔔 Notifications", use_container_width=True):
                    st.session_state.show_notifications = True
            with col2:
                display_notification_badge()
            
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.auth_manager.logout()
        
        st.divider()
        
        # System Status
        st.subheader("📊 System Status")
        try:
            status = check_system_status()
            
            col1, col2 = st.columns(2)
            with col1:
                if status['data_uploaded']:
                    st.success("Data ✓")
                else:
                    st.error("Data ✗")
            
            with col2:
                if status['rates_configured']:
                    st.success("Rates ✓")
                else:
                    st.error("Rates ✗")
            
            if status['ready_to_calculate']:
                st.success("✅ Ready to calculate commissions")
            else:
                st.warning("⚠️ Complete setup to calculate")
            
            st.divider()
            
            # Quick Stats
            if hasattr(st.session_state, 'calculator'):
                calc = st.session_state.calculator
                st.metric("Employees", len(calc.employees))
                st.metric("Business Units", len(calc.business_units))
                st.metric("Active Commissions", len([c for c in calc.commissions if hasattr(c, 'status') and c.status == 'pending']))
            else:
                st.metric("Employees", "0")
                st.metric("Business Units", "0")
                st.metric("Active Commissions", "0")
                
        except Exception as e:
            st.error(f"Status error: {str(e)}")
            st.metric("System", "Error")
        
        st.divider()
        
        # Quick Actions
        st.subheader("⚡ Quick Actions")
        
        if st.button("💾 Save to Database", use_container_width=True):
            save_all_to_database()
        
        if st.button("🔄 Create Backup", use_container_width=True):
            backup_path = st.session_state.db_manager.create_backup()
            st.success(f"Backup created: {backup_path}")
        
        if st.button("📊 Export All Data", use_container_width=True):
            export_all_data()

def save_all_to_database():
    """Save all current data to database"""
    try:
        calc = st.session_state.calculator
        db = st.session_state.db_manager
        
        # Save employees
        for employee in calc.employees.values():
            db.save_employee(employee.to_dict())
        
        # Save business units
        for unit in calc.business_units.values():
            db.save_business_unit(unit.to_dict())
        
        # Save commissions
        for commission in calc.commissions:
            db.save_commission(commission.to_dict())
        
        st.success("✅ All data saved to database")
        
    except Exception as e:
        st.error(f"Error saving data: {str(e)}")

def export_all_data():
    """Export all data to Excel"""
    try:
        calc = st.session_state.calculator
        export_mgr = st.session_state.export_manager
        
        # Prepare datasets
        datasets = {
            'Employees': pd.DataFrame([emp.to_dict() for emp in calc.employees.values()]),
            'Business Units': pd.DataFrame([unit.to_dict() for unit in calc.business_units.values()]),
            'Analytics': pd.DataFrame([calc.get_analytics_data()]),
        }
        
        if calc.commissions:
            datasets['Commissions'] = pd.DataFrame([c.to_dict() for c in calc.commissions])
        
        # Generate Excel file
        excel_data = export_mgr.export_to_excel(datasets)
        
        # Download button
        st.download_button(
            label="📥 Download Excel Report",
            data=excel_data,
            file_name=f"commission_data_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except Exception as e:
        st.error(f"Error exporting data: {str(e)}")

def main():
    """Main application entry point"""
    init_session_state()
    
    # Authentication check
    if 'user' not in st.session_state:
        if hasattr(st.session_state, 'auth_manager'):
            st.session_state.auth_manager.login_page()
        else:
            # Fallback login
            st.title("🔐 Login")
            with st.form("login_form"):
                username = st.text_input("Username", value="admin")
                password = st.text_input("Password", type="password", value="admin123")
                if st.form_submit_button("Login"):
                    if username == "admin" and password == "admin123":
                        st.session_state.user = {'username': 'admin', 'role': 'admin'}
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
        return
    
    # Display sidebar
    display_sidebar()
    
    # Check if notification center should be shown
    if st.session_state.get('show_notifications', False):
        st.session_state.show_notifications = False
        display_notification_center()
        if st.button("← Back to Main", use_container_width=False):
            st.rerun()
        return
    
    # Main navigation
    pages = {
        "📤 Data Management": data_management_page,
        "⚙️ System Configuration": system_configuration_page,
        "📊 Analytics Dashboard": analytics_dashboard_page,
        "📋 Commission Reports": commission_reports_page,
        "🔧 Advanced Settings": advanced_settings_page
    }
    
    # Page selection
    selected_page = st.selectbox(
        "Navigation",
        list(pages.keys()),
        label_visibility="collapsed"
    )
    
    # Display selected page
    try:
        pages[selected_page]()
    except Exception as e:
        st.error(f"Error loading page: {str(e)}")
        with st.expander("Error Details"):
            st.code(str(e))

if __name__ == "__main__":
    main()