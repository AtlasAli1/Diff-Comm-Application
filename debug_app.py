#!/usr/bin/env python3
"""
Debug version to identify page loading issues
"""
import streamlit as st
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

st.set_page_config(
    page_title="Debug Commission Calculator Pro",
    page_icon="🔍",
    layout="wide"
)

def test_imports():
    """Test all page imports"""
    st.subheader("🔍 Testing Page Imports")
    
    # Test each page import individually
    try:
        from pages.data_management import data_management_page
        st.success("✅ data_management_page imported successfully")
    except Exception as e:
        st.error(f"❌ data_management_page failed: {str(e)}")
        st.code(str(e))
    
    try:
        from pages.system_configuration import system_configuration_page
        st.success("✅ system_configuration_page imported successfully")
    except Exception as e:
        st.error(f"❌ system_configuration_page failed: {str(e)}")
        st.code(str(e))
    
    try:
        from pages.analytics_dashboard import analytics_dashboard_page
        st.success("✅ analytics_dashboard_page imported successfully")
    except Exception as e:
        st.error(f"❌ analytics_dashboard_page failed: {str(e)}")
        st.code(str(e))
    
    try:
        from pages.commission_reports import commission_reports_page
        st.success("✅ commission_reports_page imported successfully")
    except Exception as e:
        st.error(f"❌ commission_reports_page failed: {str(e)}")
        st.code(str(e))
    
    try:
        from pages.advanced_settings import advanced_settings_page
        st.success("✅ advanced_settings_page imported successfully")
    except Exception as e:
        st.error(f"❌ advanced_settings_page failed: {str(e)}")
        st.code(str(e))

def test_page_execution():
    """Test actually running a page function"""
    st.subheader("🚀 Testing Page Execution")
    
    try:
        from pages.data_management import data_management_page
        
        if st.button("Test Data Management Page"):
            with st.container():
                data_management_page()
                st.success("✅ Data Management page executed successfully!")
                
    except Exception as e:
        st.error(f"❌ Page execution failed: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

def main():
    st.title("🔍 Debug Commission Calculator Pro")
    st.markdown("Let's identify what's preventing the navigation from working...")
    
    # Test session state setup
    st.subheader("💾 Session State Test")
    if 'debug_counter' not in st.session_state:
        st.session_state.debug_counter = 0
    
    if st.button("Test Session State"):
        st.session_state.debug_counter += 1
    
    st.success(f"✅ Session state working: {st.session_state.debug_counter}")
    
    st.markdown("---")
    
    # Test imports
    test_imports()
    
    st.markdown("---")
    
    # Test page execution
    test_page_execution()
    
    st.markdown("---")
    
    # Test navigation simulation
    st.subheader("🧭 Navigation Simulation")
    
    pages = {
        "📤 Data Management": "data_management_page",
        "⚙️ System Configuration": "system_configuration_page", 
        "📊 Analytics Dashboard": "analytics_dashboard_page",
        "📋 Commission Reports": "commission_reports_page",
        "🔧 Advanced Settings": "advanced_settings_page"
    }
    
    selected_page = st.selectbox("Select a page:", list(pages.keys()))
    st.info(f"Selected: {selected_page} -> {pages[selected_page]}")
    
    if st.button("Try to Load Selected Page"):
        try:
            if selected_page == "📤 Data Management":
                from pages.data_management import data_management_page
                data_management_page()
            elif selected_page == "⚙️ System Configuration":
                from pages.system_configuration import system_configuration_page
                system_configuration_page()
            elif selected_page == "📊 Analytics Dashboard":
                from pages.analytics_dashboard import analytics_dashboard_page
                analytics_dashboard_page()
            elif selected_page == "📋 Commission Reports":
                from pages.commission_reports import commission_reports_page
                commission_reports_page()
            else:
                from pages.advanced_settings import advanced_settings_page
                advanced_settings_page()
                
            st.success("✅ Page loaded successfully!")
            
        except Exception as e:
            st.error(f"❌ Failed to load page: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

if __name__ == "__main__":
    main()