import streamlit as st
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Page configuration
st.set_page_config(
    page_title="Commission Calculator Pro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🐛 Debug Main App")

# Test each import step by step
st.subheader("Step 1: Testing Imports")

try:
    from models import Employee, BusinessUnit, CommissionCalculator
    st.success("✅ Models imported successfully")
except Exception as e:
    st.error(f"❌ Models import failed: {e}")
    st.stop()

try:
    from utils import DatabaseManager, AuthManager, ExportManager, DataValidator
    st.success("✅ Core utils imported successfully")
except Exception as e:
    st.error(f"❌ Core utils import failed: {e}")
    st.stop()

try:
    from utils.notifications import (
        NotificationManager, 
        display_notification_center, 
        display_notification_badge,
        notify_commission_calculated,
        notify_data_import_complete
    )
    st.success("✅ Notifications imported successfully")
except Exception as e:
    st.warning(f"⚠️ Notifications import failed: {e}")

try:
    from pages import (
        data_management_page,
        system_configuration_page,
        analytics_dashboard_page,
        commission_reports_page,
        advanced_settings_page
    )
    st.success("✅ Pages imported successfully")
except Exception as e:
    st.error(f"❌ Pages import failed: {e}")
    st.stop()

st.subheader("Step 2: Testing Session State Initialization")

def safe_init_session_state():
    """Safely initialize session state variables"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        
        # Initialize basic calculator first
        st.session_state.calculator = CommissionCalculator()
        st.success("✅ Calculator initialized")
        
        try:
            st.session_state.db_manager = DatabaseManager()
            st.success("✅ Database manager initialized")
        except Exception as e:
            st.warning(f"⚠️ Database manager failed: {e}")
            st.session_state.db_manager = None
        
        try:
            if st.session_state.db_manager:
                st.session_state.auth_manager = AuthManager(st.session_state.db_manager)
                st.success("✅ Auth manager initialized")
            else:
                st.session_state.auth_manager = None
                st.warning("⚠️ Auth manager skipped (no database)")
        except Exception as e:
            st.warning(f"⚠️ Auth manager failed: {e}")
            st.session_state.auth_manager = None
        
        try:
            st.session_state.export_manager = ExportManager()
            st.success("✅ Export manager initialized")
        except Exception as e:
            st.warning(f"⚠️ Export manager failed: {e}")
            st.session_state.export_manager = None
        
        try:
            st.session_state.validator = DataValidator()
            st.success("✅ Validator initialized")
        except Exception as e:
            st.warning(f"⚠️ Validator failed: {e}")
            st.session_state.validator = None
        
        # Set default user for testing
        if 'user' not in st.session_state:
            st.session_state.user = {'username': 'admin', 'role': 'admin'}
            st.success("✅ Default user set")

# Initialize session state
safe_init_session_state()

st.subheader("Step 3: Testing Basic Navigation")

# Simple navigation test
pages = {
    "🏠 Home": "home",
    "📤 Data Management": "data",
    "⚙️ System Configuration": "config",
    "📊 Analytics Dashboard": "analytics",
    "📋 Commission Reports": "reports",
    "🔧 Advanced Settings": "advanced"
}

selected_page = st.selectbox("Select Page", list(pages.keys()))

if selected_page == "🏠 Home":
    st.success("✅ Home page selected")
    st.write("Welcome to Commission Calculator Pro!")
    
    # Show session state status
    st.subheader("Session State Status")
    for key, value in st.session_state.items():
        if key != 'initialized':
            status = "✅" if value is not None else "❌"
            st.write(f"{status} {key}: {type(value).__name__}")

elif pages[selected_page] == "data":
    st.info("Testing Data Management Page...")
    try:
        data_management_page()
    except Exception as e:
        st.error(f"Data management page error: {e}")

elif pages[selected_page] == "config":
    st.info("Testing System Configuration Page...")
    try:
        system_configuration_page()
    except Exception as e:
        st.error(f"System configuration page error: {e}")

elif pages[selected_page] == "analytics":
    st.info("Testing Analytics Dashboard Page...")
    try:
        analytics_dashboard_page()
    except Exception as e:
        st.error(f"Analytics dashboard page error: {e}")

elif pages[selected_page] == "reports":
    st.info("Testing Commission Reports Page...")
    try:
        commission_reports_page()
    except Exception as e:
        st.error(f"Commission reports page error: {e}")

elif pages[selected_page] == "advanced":
    st.info("Testing Advanced Settings Page...")
    try:
        advanced_settings_page()
    except Exception as e:
        st.error(f"Advanced settings page error: {e}")

st.subheader("Debug Complete")
st.success("🎉 Debug app completed successfully!")