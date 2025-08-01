#!/usr/bin/env python3
"""
Minimal Commission Calculator Pro - Debugging Version
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Minimal page configuration
st.set_page_config(
    page_title="Commission Calculator Pro",
    page_icon="💰",
    layout="wide"
)

def test_imports():
    """Test all imports and report any issues"""
    import_results = []
    
    # Test models
    try:
        from models import Employee, BusinessUnit, CommissionCalculator
        import_results.append("✅ Models: OK")
    except Exception as e:
        import_results.append(f"❌ Models: {str(e)}")
    
    # Test utils
    try:
        from utils import DatabaseManager, AuthManager, ExportManager, DataValidator
        import_results.append("✅ Utils: OK")
    except Exception as e:
        import_results.append(f"❌ Utils: {str(e)}")
    
    # Test pages
    try:
        from pages import data_management_page, system_configuration_page
        import_results.append("✅ Pages: OK")
    except Exception as e:
        import_results.append(f"❌ Pages: {str(e)}")
    
    return import_results

def main():
    st.title("💰 Commission Calculator Pro - Diagnostic Mode")
    
    st.markdown("### 🔍 System Diagnostic")
    
    # Test imports
    st.markdown("#### Import Test Results:")
    import_results = test_imports()
    
    for result in import_results:
        if "✅" in result:
            st.success(result)
        else:
            st.error(result)
    
    st.markdown("---")
    
    # Test basic functionality
    st.markdown("### 📊 Basic Functionality Test")
    
    try:
        # Test data creation
        sample_data = {
            'Employee': ['John Doe', 'Jane Smith', 'Bob Johnson'],
            'Hours': [40, 38, 42],
            'Rate': [25.0, 30.0, 28.0],
            'Earnings': [1000, 1140, 1176]
        }
        
        df = pd.DataFrame(sample_data)
        st.success("✅ Pandas DataFrame creation: OK")
        st.dataframe(df)
        
        # Test plotting
        fig = px.bar(df, x='Employee', y='Earnings', title='Sample Earnings Chart')
        st.success("✅ Plotly chart creation: OK")
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Basic functionality error: {str(e)}")
    
    st.markdown("---")
    
    # Test session state
    st.markdown("### 💾 Session State Test")
    
    if 'test_counter' not in st.session_state:
        st.session_state.test_counter = 0
    
    if st.button("Increment Counter"):
        st.session_state.test_counter += 1
    
    st.success(f"✅ Session state working: Counter = {st.session_state.test_counter}")
    
    st.markdown("---")
    
    # Database test
    st.markdown("### 🗄️ Database Test")
    
    try:
        from utils import DatabaseManager
        db = DatabaseManager("test.db", "test_backups")
        st.success("✅ Database manager created successfully")
        
        # Test database connection
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result[0] == 1:
                st.success("✅ Database connection working")
    except Exception as e:
        st.error(f"❌ Database test failed: {str(e)}")
    
    st.markdown("---")
    
    # Model test
    st.markdown("### 🏗️ Model Test")
    
    try:
        from models import Employee, BusinessUnit, CommissionCalculator
        from decimal import Decimal
        
        # Test employee creation
        emp = Employee(
            name="Test Employee",
            hourly_rate=Decimal('25.00'),
            regular_hours=Decimal('40')
        )
        st.success(f"✅ Employee model: {emp.name} created")
        
        # Test business unit creation
        unit = BusinessUnit(
            name="Test Unit",
            revenue=Decimal('10000.00'),
            commission_rate=Decimal('10.0')
        )
        st.success(f"✅ Business unit model: {unit.name} created")
        
        # Test calculator
        calc = CommissionCalculator()
        calc.add_employee(emp)
        calc.add_business_unit(unit)
        st.success(f"✅ Calculator: {len(calc.employees)} employees, {len(calc.business_units)} units")
        
    except Exception as e:
        st.error(f"❌ Model test failed: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
    
    st.markdown("---")
    
    # System info
    st.markdown("### 🖥️ System Information")
    
    info_cols = st.columns(3)
    
    with info_cols[0]:
        st.info(f"**Python Version:** {sys.version.split()[0]}")
    
    with info_cols[1]:
        st.info(f"**Streamlit Version:** {st.__version__}")
    
    with info_cols[2]:
        st.info(f"**Pandas Version:** {pd.__version__}")
    
    # Environment variables
    import os
    st.markdown("### 🌍 Environment")
    st.write(f"**Working Directory:** {os.getcwd()}")
    st.write(f"**Python Path:** {sys.path[0]}")
    
    if st.button("🔄 Refresh Diagnostics"):
        st.rerun()

if __name__ == "__main__":
    main()