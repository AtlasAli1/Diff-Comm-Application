"""
Session state utilities for consistent initialization
"""
import streamlit as st

def ensure_session_state():
    """Ensure all required session state components are initialized"""
    
    # Initialize calculator
    if 'calculator' not in st.session_state:
        from models import CommissionCalculator
        st.session_state.calculator = CommissionCalculator()
    
    # Initialize database manager
    if 'db_manager' not in st.session_state:
        try:
            from utils import DatabaseManager
            st.session_state.db_manager = DatabaseManager()
        except Exception:
            pass  # Fail silently
    
    # Initialize validator
    if 'validator' not in st.session_state:
        try:
            from utils import DataValidator
            st.session_state.validator = DataValidator()
        except Exception:
            pass  # Fail silently
    
    # Initialize export manager
    if 'export_manager' not in st.session_state:
        try:
            from utils import ExportManager
            st.session_state.export_manager = ExportManager()
        except Exception:
            pass  # Fail silently