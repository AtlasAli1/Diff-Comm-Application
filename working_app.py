#!/usr/bin/env python3
"""
Working Commission Calculator Pro - Simplified Navigation
"""
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

def init_session_state():
    """Initialize session state"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.user = {'username': 'admin', 'role': 'admin'}  # Skip auth for now
        
        # Initialize calculator and other components
        try:
            from models import CommissionCalculator
            from utils import DatabaseManager, DataValidator, ExportManager
            
            st.session_state.calculator = CommissionCalculator()
            st.session_state.db_manager = DatabaseManager()
            st.session_state.validator = DataValidator()
            st.session_state.export_manager = ExportManager()
        except Exception as e:
            st.error(f"Component initialization error: {str(e)}")
            # Minimal fallback
            from models import CommissionCalculator
            st.session_state.calculator = CommissionCalculator()
    
    # Ensure calculator always exists
    if 'calculator' not in st.session_state:
        from models import CommissionCalculator
        st.session_state.calculator = CommissionCalculator()

def main():
    """Main application"""
    init_session_state()
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 💰 Commission Calculator Pro")
        st.markdown(f"Welcome, **{st.session_state.user['username']}**!")
        
        if st.button("🚪 Logout"):
            if 'user' in st.session_state:
                del st.session_state.user
            st.rerun()
    
    # Main navigation using radio buttons (simpler than selectbox)
    st.markdown("## Navigation")
    
    page_choice = st.radio(
        "Choose a page:",
        ["📤 Data Management", "⚙️ System Configuration", 
         "📊 Analytics Dashboard", "📋 Commission Reports", 
         "🔧 Advanced Settings"],
        horizontal=True
    )
    
    st.markdown("---")
    
    # Load selected page
    try:
        if page_choice == "📤 Data Management":
            st.title("📤 Data Management")
            from pages.data_management import data_management_page
            data_management_page()
            
        elif page_choice == "⚙️ System Configuration":
            st.title("⚙️ System Configuration") 
            from pages.system_configuration import system_configuration_page
            system_configuration_page()
            
        elif page_choice == "📊 Analytics Dashboard":
            st.title("📊 Analytics Dashboard")
            from pages.analytics_dashboard import analytics_dashboard_page
            analytics_dashboard_page()
            
        elif page_choice == "📋 Commission Reports":
            st.title("📋 Commission Reports")
            from pages.commission_reports import commission_reports_page
            commission_reports_page()
            
        elif page_choice == "🔧 Advanced Settings":
            st.title("🔧 Advanced Settings")
            from pages.advanced_settings import advanced_settings_page
            advanced_settings_page()
            
    except Exception as e:
        st.error(f"Error loading page: {str(e)}")
        
        with st.expander("🔍 Error Details"):
            import traceback
            st.code(traceback.format_exc())
        
        # Fallback content
        st.markdown("### 🔧 Troubleshooting")
        st.info("The page failed to load. This could be due to missing dependencies or import errors.")
        
        if st.button("🔄 Reload Page"):
            st.rerun()

if __name__ == "__main__":
    main()