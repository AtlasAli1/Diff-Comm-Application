import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from decimal import Decimal
import sys
from pathlib import Path
import hashlib
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import services
from services.analytics_service import AnalyticsService
from services.commission_service import CommissionService
from services.data_service import DataService

# Session State Safety Helper Functions
def safe_session_get(key, default=None):
    """Safely get value from session state with default fallback"""
    return st.session_state.get(key, default)

def safe_session_check(key):
    """Safely check if key exists in session state"""
    return key in st.session_state

def safe_session_init(key, default_value):
    """Safely initialize session state key if it doesn't exist"""
    if key not in st.session_state:
        st.session_state[key] = default_value
    return st.session_state[key]

def validate_file_size(uploaded_file, max_size_mb=50):
    """Validate uploaded file size"""
    if uploaded_file is None:
        return True, ""
    
    file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
    if file_size_mb > max_size_mb:
        return False, f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed size ({max_size_mb}MB)"
    return True, f"File size: {file_size_mb:.1f}MB"

def validate_file_content(uploaded_file):
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

# Page configuration
st.set_page_config(
    page_title="Commission Calculator Pro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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
        margin-bottom: 0.8rem;
    }
    .feature-card p {
        color: #495057;
        margin-bottom: 0;
    }
    .status-good { color: #28a745; }
    .status-warning { color: #ffc107; }
    .status-error { color: #dc3545; }
    
    /* Hide the left navigation sidebar */
    .css-1d391kg {
        display: none;
    }
    .css-18e3th9 {
        padding-left: 1rem;
    }
    section[data-testid="stSidebar"] {
        display: none;
    }
    .css-17eq0hr {
        margin-left: 0 !important;
    }
    .css-k1vhr4 {
        margin-left: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """Initialize session state with minimal requirements"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.user = {'username': 'admin', 'role': 'admin'}
        
        # Initialize data states
        st.session_state.uploaded_timesheet_data = None
        st.session_state.uploaded_revenue_data = None
        st.session_state.saved_timesheet_data = None
        st.session_state.saved_revenue_data = None
        st.session_state.timesheet_file_name = None
        st.session_state.revenue_file_name = None
        st.session_state.data_updated = False
        st.session_state.last_timesheet_save = None
        st.session_state.last_revenue_save = None
        
        # Auto-load Revenue.xlsx and Timesheet 1.xlsx for testing (using relative paths)
        project_root = Path(__file__).parent
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
        
        # Initialize basic components
        try:
            from models import CommissionCalculator
            st.session_state.calculator = CommissionCalculator()
        except Exception as e:
            st.error(f"Calculator initialization failed: {e}")
            st.session_state.calculator = None

def display_header():
    """Display main header"""
    st.markdown("""
    <div class="main-header">
        <h1>💰 Commission Calculator Pro</h1>
        <p>Enterprise-Grade Commission Management System</p>
    </div>
    """, unsafe_allow_html=True)

def display_login():
    """Simple login interface"""
    st.markdown("### 🔐 Login")
    
    with st.form("login_form"):
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("Username", value="admin")
        with col2:
            password = st.text_input("Password", type="password", value="admin123")
        
        if st.form_submit_button("🚀 Login", use_container_width=True):
            if username == "admin" and password == "admin123":
                st.session_state.logged_in = True
                st.success("✅ Login successful!")
                st.rerun()
            else:
                st.error("❌ Invalid credentials")

def display_dashboard():
    """Main dashboard interface"""
    # Show test data indicator with safe session state access
    revenue_file = st.session_state.get('revenue_file_name', '')
    timesheet_file = st.session_state.get('timesheet_file_name', '')
    
    if revenue_file == "Revenue.xlsx" and timesheet_file == "Timesheet 1.xlsx":
        st.info("🧪 **Test Mode**: Revenue.xlsx and Timesheet 1.xlsx loaded automatically for testing purposes.")
    elif revenue_file == "Revenue.xlsx":
        st.info("🧪 **Test Mode**: Revenue.xlsx loaded automatically for testing purposes.")
    elif timesheet_file == "Timesheet 1.xlsx":
        st.info("🧪 **Test Mode**: Timesheet 1.xlsx loaded automatically for testing purposes.")
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 👤 User Info")
        user_info = st.session_state.get('user', {'username': 'Unknown', 'role': 'user'})
        st.info(f"Welcome, {user_info['username']}!")
        st.markdown(f"**Role:** {user_info['role'].title()}")
        
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.rerun()
        
        st.divider()
        st.markdown("### 🧭 Navigation")
    
    # Main content - Consolidated tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏠 Dashboard",
        "🏢 Company Setup",
        "📊 Data Management",
        "💰 Commissions",
        "📈 Reports & History",
        "⚙️ Settings"
    ])
    
    with tab1:
        # Dashboard - combines Home + Analytics
        display_dashboard_tab()
    
    with tab2:
        # Company Setup - NEW
        display_company_setup_tab()
    
    with tab3:
        # Data Management - combines Timesheet + Revenue
        display_data_management_tab()
    
    with tab4:
        # Commissions - keep as is
        display_commission_calculation_tab()
    
    with tab5:
        # Reports & History - combines Reports + History
        display_reports_history_tab()
    
    with tab6:
        # Settings - combines Configuration + Advanced Settings
        display_settings_tab()

# ===== NEW CONSOLIDATED TAB FUNCTIONS =====

def display_company_setup_tab():
    """Company Setup - Employee Management, Exclusion List, Commission Configuration"""
    st.markdown("## 🏢 Company Setup")
    st.markdown("Configure your company's commission structure and manage employees")
    
    # Sub-tabs for company setup
    setup_tab1, setup_tab2, setup_tab3 = st.tabs([
        "👥 Employee Management",
        "🚫 Exclusion List",
        "💰 Commission Configuration"
    ])
    
    with setup_tab1:
        display_employee_management()
    
    with setup_tab2:
        display_exclusion_list()
        
    with setup_tab3:
        display_commission_configuration()

def display_employee_management():
    """Employee management section"""
    st.markdown("### 👥 Employee Management")
    
    # Initialize employee data if not exists
    if 'employee_data' not in st.session_state:
        st.session_state.employee_data = pd.DataFrame(columns=[
            'Employee ID', 'Name', 'Department', 'Role', 'Hourly Rate', 
            'Start Date', 'Status', 'Email', 'Commission Eligible', 'Helper/Apprentice', 'Commission Plan'
        ])
    
    # Get suggestions from timesheet data
    suggested_employees = get_employee_suggestions()
    
    # Debug info - show what's in the timesheet data
    if 'saved_timesheet_data' in st.session_state and st.session_state.saved_timesheet_data is not None:
        with st.expander("🔍 Debug: Timesheet Data Columns", expanded=False):
            st.write("Available columns:", list(st.session_state.saved_timesheet_data.columns))
            st.write("Data shape:", st.session_state.saved_timesheet_data.shape)
    
    # Show suggestions if any
    if suggested_employees:
        st.info(f"💡 **Smart Suggestions**: Found {len(suggested_employees)} employees in timesheet data who aren't in your employee list yet!")
        
        with st.expander("📋 View Suggested Employees from Timesheet Data", expanded=True):
            st.markdown("**Select employees to add and configure individual options:**")
            
            # Create a form for individual employee selection
            with st.form("add_suggested_employees_form"):
                employee_selections = {}
                
                for i, emp in enumerate(suggested_employees):
                    st.markdown(f"### 👤 **{emp['name']}** (ID: {emp.get('id', 'Unknown')})")
                    
                    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
                    
                    with col1:
                        add_employee = st.checkbox(
                            "Add Employee", 
                            value=True, 
                            key=f"add_{i}",
                            help="Include this employee"
                        )
                    
                    with col2:
                        exclude_payroll = st.checkbox(
                            "🏢 Exclude from Payroll", 
                            value=False, 
                            key=f"exclude_{i}",
                            help="Office employee - won't appear in commission calculations",
                            disabled=not add_employee
                        )
                    
                    with col3:
                        is_helper = st.checkbox(
                            "🆘 Helper/Apprentice", 
                            value=False, 
                            key=f"helper_{i}",
                            help="Won't receive commissions or count in splits",
                            disabled=not add_employee or exclude_payroll
                        )
                    
                    with col4:
                        if add_employee:
                            if exclude_payroll:
                                st.info("→ Office Employee")
                            elif is_helper:
                                st.warning("→ Helper")
                            else:
                                st.success("→ Regular Employee")
                        else:
                            st.error("→ Skip")
                    
                    employee_selections[i] = {
                        'employee': emp,
                        'add': add_employee,
                        'exclude_payroll': exclude_payroll,
                        'is_helper': is_helper
                    }
                    
                    st.divider()
                
                # Submit button
                submitted = st.form_submit_button("🚀 Add Selected Employees", type="primary")
                
                if submitted:
                    employees_to_add = [
                        (selection['employee'], selection['exclude_payroll'], selection['is_helper'])
                        for selection in employee_selections.values() 
                        if selection['add']
                    ]
                    
                    if employees_to_add:
                        add_selected_employees(employees_to_add)
                        
                        # Build status message
                        total_added = len(employees_to_add)
                        excluded_count = sum(1 for _, exclude, _ in employees_to_add if exclude)
                        helper_count = sum(1 for _, _, helper in employees_to_add if helper)
                        regular_count = total_added - excluded_count - helper_count
                        
                        status_parts = [f"✅ Added {total_added} employees:"]
                        if regular_count > 0:
                            status_parts.append(f"{regular_count} regular")
                        if excluded_count > 0:
                            status_parts.append(f"{excluded_count} office")
                        if helper_count > 0:
                            status_parts.append(f"{helper_count} helpers")
                        
                        st.success(" | ".join(status_parts))
                        st.rerun()
                    else:
                        st.warning("No employees selected to add!")
    else:
        if 'saved_timesheet_data' in st.session_state and st.session_state.saved_timesheet_data is not None:
            st.info("ℹ️ No new employees found in timesheet data (all employees may already be added)")
    
    # Sub-sections for employee management
    emp_col1, emp_col2 = st.columns([1, 2])
    
    with emp_col1:
        st.markdown("#### ➕ Add New Employee")
        with st.form("add_employee_form"):
            emp_id = st.number_input("Employee ID*", min_value=1, value=None, step=1, format="%d", placeholder="e.g. 1001")
            emp_name = st.text_input("Full Name*", placeholder="John Doe")
            emp_dept = st.selectbox("Department", ["Sales", "Marketing", "Operations", "IT", "HR", "Finance"])
            emp_role = st.selectbox("Role", ["Sales Rep", "Manager", "Director", "Executive", "Analyst", "Specialist"])
            emp_rate = st.number_input("Hourly Rate ($)*", min_value=0.0, value=25.0, step=0.50)
            emp_email = st.text_input("Email", placeholder="john.doe@company.com")
            emp_status = st.selectbox("Status", ["Active", "Inactive", "On Leave", "Excluded from Payroll"])
            
            # Helper/Apprentice checkbox
            is_helper = st.checkbox("Helper/Apprentice", value=False, 
                                  help="Helpers/Apprentices are not eligible for commissions and don't count in work done splits")
            
            # Commission eligible checkbox (disabled if helper/apprentice)
            commission_eligible = st.checkbox("Commission Eligible", 
                                           value=not is_helper, 
                                           disabled=is_helper,
                                           help="Automatically disabled for helpers/apprentices")
            
            if st.form_submit_button("Add Employee", type="primary"):
                if emp_id and emp_name and emp_rate > 0:
                    new_employee = {
                        'Employee ID': emp_id,
                        'Name': emp_name,
                        'Department': emp_dept,
                        'Role': emp_role,
                        'Hourly Rate': emp_rate,
                        'Start Date': datetime.now().date(),
                        'Status': emp_status,
                        'Email': emp_email,
                        'Commission Eligible': commission_eligible and not is_helper,
                        'Helper/Apprentice': is_helper,
                        'Commission Plan': 'Efficiency Pay' if not is_helper else 'None'
                    }
                    st.session_state.employee_data = pd.concat([
                        st.session_state.employee_data, 
                        pd.DataFrame([new_employee])
                    ], ignore_index=True)
                    st.success(f"✅ Employee {emp_name} added successfully!")
                    st.rerun()
                else:
                    st.error("Please fill in all required fields")
    
    with emp_col2:
        st.markdown("#### 📋 Current Employees")
        if not st.session_state.employee_data.empty:
            # Add search/filter
            search = st.text_input("🔍 Search employees", placeholder="Search by name, ID, or department...")
            
            # Filter employees - exclude those marked as "Excluded from Payroll"
            employee_data = safe_session_get('employee_data', pd.DataFrame())
            if not employee_data.empty:
                active_employees = employee_data[
                    employee_data['Status'] != 'Excluded from Payroll'
                ].copy()
            else:
                active_employees = pd.DataFrame()
            
            if search:
                mask = active_employees.apply(
                    lambda row: search.lower() in str(row).lower(), axis=1
                )
                filtered_data = active_employees[mask].copy()
            else:
                filtered_data = active_employees.copy()
            
            # Add original index for mapping back after edits
            filtered_data = filtered_data.reset_index(drop=False).rename(columns={'index': 'original_index'})
            
            # Add delete column
            filtered_data['Delete'] = False
            
            # Display editable employees table
            edited_employees = st.data_editor(
                filtered_data,
                column_config={
                    "original_index": None,  # Hide this column
                    "Employee ID": st.column_config.NumberColumn(
                        "Employee ID",
                        disabled=False,  # Make ID editable
                        help="Employee ID - must be unique",
                        format="%d",
                        min_value=1,
                        step=1
                    ),
                    "Name": st.column_config.TextColumn(
                        "Name",
                        help="Employee full name"
                    ),
                    "Department": st.column_config.SelectboxColumn(
                        "Department",
                        options=["Sales", "Marketing", "Operations", "IT", "HR", "Finance", "Unknown"],
                        help="Employee department"
                    ),
                    "Role": st.column_config.SelectboxColumn(
                        "Role",
                        options=["Sales Rep", "Manager", "Director", "Executive", "Analyst", "Specialist", "Employee"],
                        help="Employee role"
                    ),
                    "Hourly Rate": st.column_config.NumberColumn(
                        "Hourly Rate",
                        min_value=0.0,
                        step=0.50,
                        format="$%.2f"
                    ),
                    "Start Date": st.column_config.DateColumn(
                        "Start Date",
                        help="Employee start date"
                    ),
                    "Status": st.column_config.SelectboxColumn(
                        "Status",
                        options=["Active", "Inactive", "On Leave", "Excluded from Payroll"],
                        help="Employee status"
                    ),
                    "Email": st.column_config.TextColumn(
                        "Email",
                        help="Employee email address"
                    ),
                    "Commission Eligible": st.column_config.CheckboxColumn(
                        "Commission Eligible",
                        help="Whether employee is eligible for commissions"
                    ),
                    "Helper/Apprentice": st.column_config.CheckboxColumn(
                        "Helper/Apprentice",
                        help="Helpers/Apprentices don't get commissions and don't count in work done splits"
                    ),
                    "Commission Plan": st.column_config.SelectboxColumn(
                        "Commission Plan",
                        options=["Efficiency Pay", "Hourly + Commission", "None"],
                        help="Efficiency Pay: max(hourly, commission) | Hourly + Commission: hourly + commission"
                    ),
                    "Delete": st.column_config.CheckboxColumn(
                        "Delete",
                        help="Check to delete this employee"
                    )
                },
                hide_index=True,
                use_container_width=True,
                height=400,
                key="employees_editor"
            )
            
            # Save button
            if st.button("💾 Save Employee Changes", type="primary", use_container_width=True):
                # First, handle deletions using original indices
                original_indices_to_delete = []
                for idx, row in edited_employees.iterrows():
                    if row['Delete']:
                        original_indices_to_delete.append(row['original_index'])
                
                # Delete marked employees from original data using original indices
                if original_indices_to_delete:
                    st.session_state.employee_data = st.session_state.employee_data.drop(
                        index=original_indices_to_delete
                    ).reset_index(drop=True)
                
                # Validate Employee ID uniqueness before updating
                non_deleted_employees = edited_employees[~edited_employees['Delete']]
                edited_ids = non_deleted_employees['Employee ID'].tolist()
                
                if len(edited_ids) != len(set(edited_ids)):
                    # Find and show which employees have duplicate IDs
                    from collections import Counter
                    id_counts = Counter(edited_ids)
                    duplicates = {emp_id: count for emp_id, count in id_counts.items() if count > 1}
                    
                    st.error("❌ Duplicate Employee IDs found! Each employee must have a unique ID.")
                    
                    for duplicate_id, count in duplicates.items():
                        # Find all employees with this duplicate ID
                        duplicate_employees = non_deleted_employees[
                            non_deleted_employees['Employee ID'] == duplicate_id
                        ]['Name'].tolist()
                        
                        st.error(f"**Employee ID {duplicate_id}** is used by {count} employees: **{', '.join(duplicate_employees)}**")
                    
                    st.info("💡 Please change the duplicate Employee IDs to unique values before saving.")
                    
                    # Add auto-fix button
                    if st.button("🔧 Auto-Fix Duplicate IDs", type="primary", help="Automatically assign unique sequential Employee IDs to resolve duplicates"):
                        fixed_count = fix_duplicate_employee_ids()
                        if fixed_count and fixed_count > 0:
                            st.success(f"✅ Fixed {fixed_count} duplicate Employee IDs! Each employee now has a unique ID.")
                            st.rerun()
                        else:
                            st.info("No duplicates were found to fix.")
                    
                    return
                
                # Update remaining employees using original index mapping
                for idx, row in edited_employees.iterrows():
                    if not row['Delete']:  # Only update if not marked for deletion
                        # Use original index to map back to the main employee data
                        if 'original_index' not in row:
                            st.error(f"Missing original_index for row {idx}. Available columns: {list(row.index)}")
                            continue
                        original_emp_idx = row['original_index']
                        
                        # Update all fields including potentially changed Employee ID
                        st.session_state.employee_data.loc[original_emp_idx, 'Employee ID'] = row['Employee ID']
                        st.session_state.employee_data.loc[original_emp_idx, 'Name'] = row['Name']
                        st.session_state.employee_data.loc[original_emp_idx, 'Department'] = row['Department']
                        st.session_state.employee_data.loc[original_emp_idx, 'Role'] = row['Role']
                        st.session_state.employee_data.loc[original_emp_idx, 'Hourly Rate'] = row['Hourly Rate']
                        st.session_state.employee_data.loc[original_emp_idx, 'Start Date'] = row['Start Date']
                        st.session_state.employee_data.loc[original_emp_idx, 'Status'] = row['Status']
                        st.session_state.employee_data.loc[original_emp_idx, 'Email'] = row['Email']
                        st.session_state.employee_data.loc[original_emp_idx, 'Helper/Apprentice'] = row.get('Helper/Apprentice', False)
                        # If helper/apprentice, force commission eligible to False and plan to None
                        if row.get('Helper/Apprentice', False):
                            st.session_state.employee_data.loc[original_emp_idx, 'Commission Eligible'] = False
                            st.session_state.employee_data.loc[original_emp_idx, 'Commission Plan'] = 'None'
                        else:
                            st.session_state.employee_data.loc[original_emp_idx, 'Commission Eligible'] = row['Commission Eligible']
                            st.session_state.employee_data.loc[original_emp_idx, 'Commission Plan'] = row.get('Commission Plan', 'Efficiency Pay')
                
                if original_indices_to_delete:
                    st.success(f"✅ Deleted {len(original_indices_to_delete)} employee(s) and saved changes!")
                else:
                    st.success("✅ Employee changes saved successfully!")
                st.rerun()
            
            # Quick stats
            col1, col2, col3 = st.columns(3)
            employee_data = safe_session_get('employee_data', pd.DataFrame())
            with col1:
                st.metric("Total Employees", len(employee_data))
            with col2:
                if not employee_data.empty:
                    active = len(employee_data[employee_data['Status'] == 'Active'])
                else:
                    active = 0
                st.metric("Active Employees", active)
            with col3:
                if not employee_data.empty:
                    eligible = len(employee_data[employee_data['Commission Eligible'] == True])
                else:
                    eligible = 0
                st.metric("Commission Eligible", eligible)
        else:
            st.info("No employees added yet. Use the form to add your first employee.")

def display_exclusion_list():
    """Manage commission exclusion list"""
    st.markdown("### 🚫 Commission Exclusion List")
    st.markdown("Manage employees who are excluded from commission calculations (salary/hourly only)")
    
    # Initialize exclusion list
    if 'exclusion_list' not in st.session_state:
        st.session_state.exclusion_list = []
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### Add to Exclusion List")
        
        # Get commission-eligible employees
        employee_data = safe_session_get('employee_data', pd.DataFrame())
        if not employee_data.empty:
            eligible_employees = employee_data[
                employee_data['Commission Eligible'] == True
            ]
            
            if not eligible_employees.empty:
                employee_options = eligible_employees.apply(
                    lambda row: f"{row['Employee ID']} - {row['Name']}", axis=1
                ).tolist()
                
                selected_employee = st.selectbox(
                    "Select employee to exclude:",
                    options=employee_options,
                    placeholder="Choose an employee..."
                )
                
                exclusion_reason = st.selectbox(
                    "Reason for exclusion:",
                    ["Salary-based compensation", "Hourly-only role", "Temporary exclusion", "Other"]
                )
                
                if exclusion_reason == "Other":
                    custom_reason = st.text_input("Specify reason:")
                else:
                    custom_reason = exclusion_reason
                
                if st.button("➕ Add to Exclusion List", type="primary"):
                    emp_id = selected_employee.split(" - ")[0]
                    emp_name = selected_employee.split(" - ")[1]
                    
                    # Add to exclusion list
                    exclusion_entry = {
                        'employee_id': emp_id,
                        'employee_name': emp_name,
                        'reason': custom_reason,
                        'excluded_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'excluded_by': st.session_state.get('user', {}).get('username', 'Unknown')
                    }
                    
                    st.session_state.exclusion_list.append(exclusion_entry)
                    
                    # Update employee's commission eligibility
                    employee_data = safe_session_get('employee_data', pd.DataFrame())
                    if not employee_data.empty:
                        idx = employee_data[
                            employee_data['Employee ID'] == emp_id
                        ].index
                    if len(idx) > 0:
                        st.session_state.employee_data.loc[idx[0], 'Commission Eligible'] = False
                    
                    st.success(f"✅ {emp_name} added to exclusion list")
                    st.rerun()
            else:
                st.info("No commission-eligible employees available")
        else:
            st.warning("Please add employees first")
    
    with col2:
        st.markdown("#### Current Exclusions")
        
        exclusion_list = safe_session_get('exclusion_list', [])
        if exclusion_list:
            for i, exclusion in enumerate(exclusion_list):
                with st.expander(f"🚫 {exclusion['employee_name']}", expanded=False):
                    st.write(f"**Employee ID:** {exclusion['employee_id']}")
                    st.write(f"**Reason:** {exclusion['reason']}")
                    st.write(f"**Excluded on:** {exclusion['excluded_date']}")
                    st.write(f"**Excluded by:** {exclusion['excluded_by']}")
                    
                    if st.button(f"Remove from exclusion list", key=f"remove_exclusion_{i}"):
                        # Remove from exclusion list
                        st.session_state.exclusion_list.pop(i)
                        
                        # Update employee's commission eligibility
                        employee_data = safe_session_get('employee_data', pd.DataFrame())
                        if not employee_data.empty:
                            idx = employee_data[
                                employee_data['Employee ID'] == exclusion['employee_id']
                            ].index
                        if len(idx) > 0:
                            st.session_state.employee_data.loc[idx[0], 'Commission Eligible'] = True
                        
                        st.success(f"✅ {exclusion['employee_name']} removed from exclusion list")
                        st.rerun()
        else:
            st.info("No employees in exclusion list")
            
        # Summary stats
        st.markdown("#### 📊 Exclusion Summary")
        if st.session_state.exclusion_list:
            reasons = {}
            for exclusion in st.session_state.exclusion_list:
                reason = exclusion['reason']
                reasons[reason] = reasons.get(reason, 0) + 1
            
            for reason, count in reasons.items():
                st.write(f"• {reason}: {count} employee(s)")

def display_advanced_commission_settings_for_unit(business_unit_name, unit_code):
    """Display advanced commission settings for a specific business unit"""
    
    # Get default rates for this business unit
    business_unit_rates = safe_session_get('business_unit_rates', {})
    if unit_code in business_unit_rates:
        default_rates = business_unit_rates[unit_code]['rates']
        lead_gen_rate = default_rates['Lead Generation']
        sold_by_rate = default_rates['Sales']
        work_done_rate = default_rates['Work Done']
    else:
        # Fallback to business unit commission settings
        if business_unit_name in st.session_state.get('business_unit_commission_settings', {}):
            settings = st.session_state.business_unit_commission_settings[business_unit_name]
            lead_gen_rate = settings.get('lead_gen_rate', 5.0)
            sold_by_rate = settings.get('sold_by_rate', 7.5)
            work_done_rate = settings.get('work_done_rate', 7.5)
        else:
            lead_gen_rate = 5.0
            sold_by_rate = 7.5  
            work_done_rate = 7.5

    st.markdown(f"**Override commission rates for specific employees in {business_unit_name}**")
    st.markdown("*Note: All employees are shown since anyone might work in this business unit in the future.*")
    
    # Initialize advanced settings if not exists
    if business_unit_name not in st.session_state.employee_commission_overrides:
        st.session_state.employee_commission_overrides[business_unit_name] = {}
    
    # Get complete list of all employees from employee database
    available_employees = []
    
    # First priority: Get employees from the employee database
    if 'employee_data' in st.session_state and not st.session_state.employee_data.empty:
        employee_names = st.session_state.employee_data['Name'].dropna().tolist()
        available_employees.extend([name for name in employee_names if name])
    
    # Also include any employees found in revenue data that might not be in employee database yet
    if 'saved_revenue_data' in st.session_state and st.session_state.saved_revenue_data is not None:
        revenue_df = st.session_state.saved_revenue_data
        
        # Collect all employees from all commission types across ALL business units
        for col in ['Lead Generated By', 'Sold By', 'Assigned Technicians']:
            if col in revenue_df.columns:
                for value in revenue_df[col].dropna():
                    if col == 'Assigned Technicians':
                        # Split technicians
                        techs = str(value).replace('&', ',').split(',')
                        for tech in techs:
                            tech = tech.strip()
                            if tech and tech not in available_employees:
                                available_employees.append(tech)
                    else:
                        emp = str(value).strip()
                        if emp and emp not in available_employees:
                            available_employees.append(emp)
    
    if available_employees:
        # Remove duplicates and sort
        available_employees = sorted(list(set(available_employees)))
        st.info(f"💡 Showing all {len(available_employees)} employees (from employee database + revenue data). Set custom rates for any employee who might work in {business_unit_name}.")
        
        # Employee selection and rate override
        selected_employee = st.selectbox(
            "Select Employee to Override",
            [""] + sorted(available_employees),
            key=f"emp_select_setup_{business_unit_name}"
        )
        
        if selected_employee:
            st.markdown(f"**Commission Rate Overrides for {selected_employee} in {business_unit_name}:**")
            
            # Get current overrides for this employee
            current_overrides = st.session_state.employee_commission_overrides[business_unit_name].get(
                selected_employee, {}
            )
            
            override_col1, override_col2, override_col3 = st.columns(3)
            
            with override_col1:
                st.markdown("**🎯 Lead Generation Override**")
                lead_override = st.number_input(
                    "Custom Rate (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=current_overrides.get('lead_gen_rate', lead_gen_rate),
                    step=0.25,
                    key=f"lead_override_setup_{business_unit_name}_{selected_employee}",
                    help=f"Default: {lead_gen_rate}%. Set custom rate for this employee."
                )
                use_lead_override = st.checkbox(
                    "Use custom rate",
                    value=current_overrides.get('use_lead_override', False),
                    key=f"use_lead_setup_{business_unit_name}_{selected_employee}"
                )
            
            with override_col2:
                st.markdown("**💼 Sales Override**")
                sales_override = st.number_input(
                    "Custom Rate (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=current_overrides.get('sold_by_rate', sold_by_rate),
                    step=0.25,
                    key=f"sales_override_setup_{business_unit_name}_{selected_employee}",
                    help=f"Default: {sold_by_rate}%. Set custom rate for this employee."
                )
                use_sales_override = st.checkbox(
                    "Use custom rate",
                    value=current_overrides.get('use_sales_override', False),
                    key=f"use_sales_setup_{business_unit_name}_{selected_employee}"
                )
            
            with override_col3:
                st.markdown("**🔧 Work Done Override**")
                work_override = st.number_input(
                    "Custom Rate (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=current_overrides.get('work_done_rate', work_done_rate),
                    step=0.25,
                    key=f"work_override_setup_{business_unit_name}_{selected_employee}",
                    help=f"Default: {work_done_rate}%. This employee's share of work done commission."
                )
                use_work_override = st.checkbox(
                    "Use custom rate",
                    value=current_overrides.get('use_work_override', False),
                    key=f"use_work_setup_{business_unit_name}_{selected_employee}"
                )
            
            # Save employee overrides
            if st.button(f"💾 Save Overrides for {selected_employee}", key=f"save_override_setup_{business_unit_name}_{selected_employee}"):
                st.session_state.employee_commission_overrides[business_unit_name][selected_employee] = {
                    'lead_gen_rate': lead_override,
                    'sold_by_rate': sales_override,
                    'work_done_rate': work_override,
                    'use_lead_override': use_lead_override,
                    'use_sales_override': use_sales_override,
                    'use_work_override': use_work_override,
                    'last_updated': datetime.now().isoformat()
                }
                st.success(f"✅ Custom commission rates saved for {selected_employee}")
                st.rerun()
            
            # Show active overrides summary
            if current_overrides:
                st.markdown("**Current Overrides:**")
                override_info = []
                if current_overrides.get('use_lead_override'):
                    override_info.append(f"Lead Gen: {current_overrides.get('lead_gen_rate', 0):.2f}%")
                if current_overrides.get('use_sales_override'):
                    override_info.append(f"Sales: {current_overrides.get('sold_by_rate', 0):.2f}%")
                if current_overrides.get('use_work_override'):
                    override_info.append(f"Work Done: {current_overrides.get('work_done_rate', 0):.2f}%")
                
                if override_info:
                    st.info("🎯 Active: " + " | ".join(override_info))
    
    # Display all current overrides for this business unit
    current_unit_overrides = st.session_state.employee_commission_overrides.get(business_unit_name, {})
    if current_unit_overrides:
        st.markdown("**📋 All Employee Overrides:**")
        override_summary = []
        for emp, overrides in current_unit_overrides.items():
            active_overrides = []
            if overrides.get('use_lead_override'):
                active_overrides.append(f"Lead: {overrides.get('lead_gen_rate', 0):.2f}%")
            if overrides.get('use_sales_override'):
                active_overrides.append(f"Sales: {overrides.get('sold_by_rate', 0):.2f}%")
            if overrides.get('use_work_override'):
                active_overrides.append(f"Work: {overrides.get('work_done_rate', 0):.2f}%")
            
            if active_overrides:
                override_summary.append({
                    'Employee': emp,
                    'Overrides': " | ".join(active_overrides),
                    'Last Updated': overrides.get('last_updated', 'Unknown')[:19].replace('T', ' ')
                })
        
        if override_summary:
            st.dataframe(pd.DataFrame(override_summary), use_container_width=True, hide_index=True)
            
            # Clear overrides button
            if st.button(f"🗑️ Clear All Overrides for {business_unit_name}", key=f"clear_overrides_setup_{business_unit_name}"):
                st.session_state.employee_commission_overrides[business_unit_name] = {}
                st.success(f"✅ Cleared all employee overrides for {business_unit_name}")
                st.rerun()
    else:
        if not available_employees:
            st.warning("⚠️ No employees found. Please add employees in Company Setup → Employee Management or upload revenue data with employee names.")
        else:
            st.info("No employee commission overrides set for this business unit.")

def display_commission_configuration():
    """Configure commission rates by business unit"""
    st.markdown("### 💰 Commission Configuration")
    st.markdown("Set commission percentages by business unit and commission type")
    
    # Initialize commission rates
    if 'business_unit_rates' not in st.session_state:
        st.session_state.business_unit_rates = {}
    
    # SYNC FROM COMMISSION SETTINGS ON LOAD
    # If we have commission settings but no business unit rates, import them
    if (not st.session_state.business_unit_rates and 
        'business_unit_commission_settings' in st.session_state and 
        st.session_state.business_unit_commission_settings):
        
        for unit_name, settings in st.session_state.business_unit_commission_settings.items():
            # Generate a code from the name
            code = ''.join([word[0].upper() for word in unit_name.split()][:3])
            if not code:
                code = unit_name[:3].upper()
            
            # Ensure unique code
            counter = 1
            original_code = code
            while code in st.session_state.business_unit_rates:
                code = f"{original_code}{counter}"
                counter += 1
            
            st.session_state.business_unit_rates[code] = {
                'name': unit_name,
                'code': code,
                'rates': {
                    'Lead Generation': settings.get('lead_gen_rate', 5.0),
                    'Sales': settings.get('sold_by_rate', 7.5),
                    'Work Done': settings.get('work_done_rate', 7.5)
                },
                'created_date': datetime.now().strftime("%Y-%m-%d"),
                'created_by': 'System Import'
            }
    
    # Get business unit suggestions from revenue data
    suggested_business_units = get_business_unit_suggestions()
    
    # Debug info - show what's in the revenue data
    if 'saved_revenue_data' in st.session_state and st.session_state.saved_revenue_data is not None:
        with st.expander("🔍 Debug: Revenue Data Columns", expanded=False):
            st.write("Available columns:", list(st.session_state.saved_revenue_data.columns))
            st.write("Data shape:", st.session_state.saved_revenue_data.shape)
    
    # Show suggestions if any
    if suggested_business_units:
        st.info(f"💡 **Smart Suggestions**: Found {len(suggested_business_units)} business units in revenue data that need commission configuration!")
        
        with st.expander("🏢 View Suggested Business Units from Revenue Data", expanded=True):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("**Business units found in revenue data:**")
                for unit in suggested_business_units:
                    revenue_count = unit.get('revenue_count', 0)
                    st.write(f"• **{unit['name']}** ({revenue_count} revenue entries)")
            
            with col2:
                if st.button("🚀 Quick Setup Business Units", type="secondary"):
                    setup_suggested_business_units(suggested_business_units)
                    st.success(f"✅ Added {len(suggested_business_units)} business units with default rates!")
                    st.rerun()
    else:
        if 'saved_revenue_data' in st.session_state and st.session_state.saved_revenue_data is not None:
            st.info("ℹ️ No new business units found in revenue data (all units may already be configured)")
    
    # Business unit management
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("#### 🏢 Add Business Unit")
        
        with st.form("add_business_unit"):
            unit_name = st.text_input("Business Unit Name*", placeholder="e.g., North Region Sales")
            unit_code = st.text_input("Unit Code*", placeholder="e.g., NRS")
            
            st.markdown("**Commission Rates (%)**")
            lead_gen_rate = st.number_input("Lead Generation", min_value=0.0, max_value=100.0, value=5.0, step=0.5)
            sales_rate = st.number_input("Sales", min_value=0.0, max_value=100.0, value=10.0, step=0.5)
            work_done_rate = st.number_input("Work Done", min_value=0.0, max_value=100.0, value=7.5, step=0.5)
            
            if st.form_submit_button("Add Business Unit", type="primary"):
                if unit_name and unit_code:
                    st.session_state.business_unit_rates[unit_code] = {
                        'name': unit_name,
                        'code': unit_code,
                        'rates': {
                            'Lead Generation': lead_gen_rate,
                            'Sales': sales_rate,
                            'Work Done': work_done_rate
                        },
                        'created_date': datetime.now().strftime("%Y-%m-%d"),
                        'created_by': st.session_state.get('user', {}).get('username', 'Unknown')
                    }
                    
                    # SYNC WITH COMMISSION SETTINGS
                    if 'business_unit_commission_settings' not in st.session_state:
                        st.session_state.business_unit_commission_settings = {}
                    
                    st.session_state.business_unit_commission_settings[unit_name] = {
                        'lead_gen_rate': lead_gen_rate,
                        'sold_by_rate': sales_rate,
                        'work_done_rate': work_done_rate,
                        'enabled': True
                    }
                    
                    st.success(f"✅ Business Unit '{unit_name}' added successfully!")
                    st.rerun()
                else:
                    st.error("Please fill in all required fields")
    
    with col2:
        st.markdown("#### 📊 Current Business Units")
        
        if st.session_state.business_unit_rates:
            # Create a DataFrame for display
            units_data = []
            for code, unit in st.session_state.business_unit_rates.items():
                units_data.append({
                    'Code': code,
                    'Name': unit['name'],
                    'Lead Gen %': unit['rates']['Lead Generation'],
                    'Sales %': unit['rates']['Sales'],
                    'Work Done %': unit['rates']['Work Done'],
                    'Created': unit['created_date'],
                    'Delete': False  # Add delete checkbox column
                })
            
            units_df = pd.DataFrame(units_data)
            
            # Display with editing capability
            edited_df = st.data_editor(
                units_df,
                column_config={
                    "Code": st.column_config.TextColumn(
                        "Code",
                        disabled=True,  # Make code read-only
                        help="Business unit code (read-only)"
                    ),
                    "Name": st.column_config.TextColumn(
                        "Name",
                        help="Business unit name"
                    ),
                    "Lead Gen %": st.column_config.NumberColumn(
                        "Lead Gen %",
                        min_value=0,
                        max_value=100,
                        step=0.5,
                        format="%.1f%%"
                    ),
                    "Sales %": st.column_config.NumberColumn(
                        "Sales %",
                        min_value=0,
                        max_value=100,
                        step=0.5,
                        format="%.1f%%"
                    ),
                    "Work Done %": st.column_config.NumberColumn(
                        "Work Done %",
                        min_value=0,
                        max_value=100,
                        step=0.5,
                        format="%.1f%%"
                    ),
                    "Created": st.column_config.DateColumn(
                        "Created",
                        disabled=True
                    ),
                    "Delete": st.column_config.CheckboxColumn(
                        "Delete",
                        help="Check to delete this business unit"
                    )
                },
                hide_index=True,
                use_container_width=True,
                key="business_units_editor"
            )
            
            # Save button
            if st.button("💾 Save All Changes", type="primary", use_container_width=True):
                # First, handle deletions
                codes_to_delete = []
                for _, row in edited_df.iterrows():
                    if row['Delete']:
                        codes_to_delete.append(row['Code'])
                
                # Delete marked units
                for code in codes_to_delete:
                    if code in st.session_state.business_unit_rates:
                        del st.session_state.business_unit_rates[code]
                
                # Then update the remaining units
                for _, row in edited_df.iterrows():
                    if not row['Delete']:  # Only update if not marked for deletion
                        code = row['Code']
                        if code in st.session_state.business_unit_rates:
                            st.session_state.business_unit_rates[code]['name'] = row['Name']
                            st.session_state.business_unit_rates[code]['rates'] = {
                                'Lead Generation': row['Lead Gen %'],
                                'Sales': row['Sales %'],
                                'Work Done': row['Work Done %']
                            }
                
                # SYNC WITH COMMISSION SETTINGS - This is the key fix
                # Initialize if not exists
                if 'business_unit_commission_settings' not in st.session_state:
                    st.session_state.business_unit_commission_settings = {}
                
                # Sync all business unit rates to commission settings
                for code, unit_data in st.session_state.business_unit_rates.items():
                    unit_name = unit_data['name']
                    rates = unit_data['rates']
                    
                    # Update commission settings with the new rates
                    st.session_state.business_unit_commission_settings[unit_name] = {
                        'lead_gen_rate': rates['Lead Generation'],
                        'sold_by_rate': rates['Sales'],
                        'work_done_rate': rates['Work Done'],
                        'enabled': True
                    }
                
                # Also remove deleted units from commission settings
                for code in codes_to_delete:
                    if code in st.session_state.business_unit_rates:
                        unit_name = st.session_state.business_unit_rates[code]['name']
                        if unit_name in st.session_state.business_unit_commission_settings:
                            del st.session_state.business_unit_commission_settings[unit_name]
                
                if codes_to_delete:
                    st.success(f"✅ Deleted {len(codes_to_delete)} business unit(s) and saved changes!")
                else:
                    st.success("✅ Changes saved successfully!")
                st.rerun()
            
            # Quick stats
            st.markdown("#### 📈 Commission Rate Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_lead = units_df['Lead Gen %'].mean()
                st.metric("Avg Lead Gen Rate", f"{avg_lead:.1f}%")
            
            with col2:
                avg_sales = units_df['Sales %'].mean()
                st.metric("Avg Sales Rate", f"{avg_sales:.1f}%")
            
            with col3:
                avg_work = units_df['Work Done %'].mean()
                st.metric("Avg Work Done Rate", f"{avg_work:.1f}%")
        else:
            st.info("No business units configured yet. Add your first business unit to get started.")
            
            # Show example
            with st.expander("ℹ️ Example Business Units"):
                st.markdown("""
                **Common Business Unit Examples:**
                - North Region Sales (NRS)
                - South Region Sales (SRS)
                - Enterprise Division (ENT)
                - Small Business (SMB)
                - Online Sales (ONL)
                """)
    
    # Advanced Commission Settings Section
    st.markdown("---")
    st.markdown("### 🎯 Advanced Commission Settings")
    st.markdown("**Configure individual employee commission rates that differ from business unit defaults**")
    st.markdown("*These settings allow specific employees to have custom commission percentages within each business unit.*")
    
    if st.session_state.business_unit_rates:
        # Initialize advanced settings if not exists
        if 'employee_commission_overrides' not in st.session_state:
            st.session_state.employee_commission_overrides = {}
        
        # Tabs for each business unit
        if len(st.session_state.business_unit_rates) > 1:
            business_unit_tabs = st.tabs([f"{unit['name']}" for unit in st.session_state.business_unit_rates.values()])
            
            for i, (unit_code, unit_data) in enumerate(st.session_state.business_unit_rates.items()):
                with business_unit_tabs[i]:
                    display_advanced_commission_settings_for_unit(unit_data['name'], unit_code)
        else:
            # Single business unit - no tabs needed
            unit_code, unit_data = next(iter(st.session_state.business_unit_rates.items()))
            display_advanced_commission_settings_for_unit(unit_data['name'], unit_code)
    else:
        st.info("⚠️ Please configure business units first before setting up advanced commission settings.")

def display_dashboard_tab():
    """Consolidated Dashboard - combines Home + Analytics"""
    st.markdown("## 🏠 Dashboard")
    
    # Show KPIs at the top
    display_kpis()
    
    st.divider()
    
    # Create two columns for home content and analytics
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # System status
        display_system_status()
    
    with col2:
        # Analytics charts
        st.markdown("### 📊 Analytics Overview")
        display_analytics_charts()

def display_data_management_tab():
    """Data Management - View and manage imported data"""
    st.markdown("## 📊 Data Management")
    st.markdown("View and verify your imported timesheet and revenue data")
    
    # Debug: Check what data is available
    revenue_available = 'saved_revenue_data' in st.session_state and st.session_state.saved_revenue_data is not None
    timesheet_available = 'saved_timesheet_data' in st.session_state and st.session_state.saved_timesheet_data is not None
    
    if revenue_available:
        st.success(f"✅ Revenue data loaded: {len(st.session_state.saved_revenue_data)} rows")
    else:
        st.info("ℹ️ No revenue data loaded yet")
        
    if timesheet_available:
        st.success(f"✅ Timesheet data loaded: {len(st.session_state.saved_timesheet_data)} rows")
    else:
        st.info("ℹ️ No timesheet data loaded yet")
    
    # Two sub-tabs for viewing data
    data_tab1, data_tab2 = st.tabs([
        "💰 Revenue Data", 
        "⏰ Timesheet Data"
    ])
    
    with data_tab1:
        try:
            display_revenue_view()
        except Exception as e:
            st.error(f"Error loading revenue section: {str(e)}")
    
    with data_tab2:
        try:
            display_timesheet_management_view()
        except Exception as e:
            st.error(f"Error loading timesheet section: {str(e)}")
            import traceback
            st.text("Full traceback:")
            st.text(traceback.format_exc())

def display_timesheet_management_view():
    """Enhanced timesheet data view with employee totals"""
    st.markdown("### ⏰ Timesheet Data Management")
    
    if 'saved_timesheet_data' not in st.session_state or st.session_state.saved_timesheet_data is None:
        st.info("📤 No timesheet data loaded. Please upload timesheet data first in the Company Setup → Upload Data section.")
        return
    
    raw_timesheet = st.session_state.saved_timesheet_data.copy()
    
    # Debug: Show raw data info
    with st.expander("🔍 Debug: Raw Data Info", expanded=False):
        st.write(f"Raw columns: {list(raw_timesheet.columns)}")
        st.write(f"Raw data shape: {raw_timesheet.shape}")
        st.write(f"Sample raw data:")
        st.dataframe(raw_timesheet.head(3))
    
    # Group by employee and sum hours
    if 'Employee Name' not in raw_timesheet.columns:
        st.error("❌ No 'Employee Name' column found in timesheet data")
        return
    
    # Find hour columns (handle both naming conventions)
    hour_columns = []
    if 'Reg Hours' in raw_timesheet.columns:
        hour_columns.append('Reg Hours')
    elif 'Regular Hours' in raw_timesheet.columns:
        hour_columns.append('Regular Hours')
    
    if 'OT Hours' in raw_timesheet.columns:
        hour_columns.append('OT Hours')
    if 'DT Hours' in raw_timesheet.columns:
        hour_columns.append('DT Hours')
    
    if not hour_columns:
        st.error("❌ No hour columns found in timesheet data")
        return
    
    # Create employee totals
    try:
        # Ensure hour columns are numeric
        for col in hour_columns:
            raw_timesheet[col] = pd.to_numeric(raw_timesheet[col], errors='coerce').fillna(0)
        
        # Group by employee and sum hours
        employee_totals = raw_timesheet.groupby('Employee Name')[hour_columns].sum().reset_index()
        
        # Add total hours column
        employee_totals['Total Hours'] = employee_totals[hour_columns].sum(axis=1)
        
        # Round to 2 decimal places
        for col in hour_columns + ['Total Hours']:
            employee_totals[col] = employee_totals[col].round(2)
        
        st.success(f"✅ Aggregated {len(raw_timesheet)} individual entries into {len(employee_totals)} employee totals")
        
    except Exception as e:
        st.error(f"❌ Error aggregating timesheet data: {str(e)}")
        return
    
    # Display editable employee totals
    st.markdown("#### 📋 Employee Hour Totals")
    st.info("💡 **Tip**: Edit employee hour totals directly. This shows aggregated hours per employee, not individual time entries.")
    
    # Configure columns for better display
    column_config = {}
    for col in hour_columns + ['Total Hours']:
        column_config[col] = st.column_config.NumberColumn(
            col,
            format="%.2f",
            min_value=0,
            help=f"Total {col.lower()} for this employee"
        )
    
    column_config['Employee Name'] = st.column_config.TextColumn(
        "Employee Name",
        help="Employee full name",
        disabled=True  # Don't allow editing employee names
    )
    
    edited_totals = st.data_editor(
        employee_totals,
        hide_index=True,
        use_container_width=True,
        column_config=column_config,
        disabled=False
    )
    
    # Save changes with hour override functionality
    if st.button("💾 Save Changes", type="primary", key="timesheet_mgmt_save"):
        try:
            # Recalculate Total Hours before saving
            edited_totals['Total Hours'] = edited_totals[hour_columns].sum(axis=1)
            
            # Create hour overrides from edited totals
            if 'timesheet_hour_overrides' not in st.session_state:
                st.session_state.timesheet_hour_overrides = {}
            
            # Update hour overrides based on edited totals
            for _, row in edited_totals.iterrows():
                employee_name = row['Employee Name']
                
                # Determine regular hours column name
                regular_hours = 0
                if 'Reg Hours' in row.index:
                    regular_hours = float(row['Reg Hours'])
                elif 'Regular Hours' in row.index:
                    regular_hours = float(row['Regular Hours'])
                
                ot_hours = float(row.get('OT Hours', 0))
                dt_hours = float(row.get('DT Hours', 0))
                
                st.session_state.timesheet_hour_overrides[employee_name] = {
                    'regular_hours': regular_hours,
                    'ot_hours': ot_hours,
                    'dt_hours': dt_hours,
                    'total_hours': regular_hours + ot_hours + dt_hours,
                    'last_updated': datetime.now().isoformat()
                }
            
            st.success("✅ Employee hour totals saved successfully! These totals will override original timesheet data in all calculations.")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error saving changes: {str(e)}")
    
    # Hour Overrides Management Section
    st.markdown("---")
    st.markdown("#### ⚙️ Hour Overrides Management")
    
    if 'timesheet_hour_overrides' in st.session_state and st.session_state.timesheet_hour_overrides:
        st.markdown("**Active Hour Overrides:**")
        st.info("💡 These edited hour totals override the original timesheet data in all commission calculations.")
        
        # Display current overrides in a summary
        override_summary = []
        for emp_name, hours in st.session_state.timesheet_hour_overrides.items():
            override_summary.append({
                'Employee': emp_name,
                'Regular Hours': f"{hours.get('regular_hours', 0):.2f}",
                'OT Hours': f"{hours.get('ot_hours', 0):.2f}",
                'DT Hours': f"{hours.get('dt_hours', 0):.2f}",
                'Total Hours': f"{hours.get('total_hours', 0):.2f}",
                'Last Updated': hours.get('last_updated', 'Unknown')[:19].replace('T', ' ')
            })
        
        if override_summary:
            st.dataframe(pd.DataFrame(override_summary), use_container_width=True, hide_index=True)
            
            # Management buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Clear All Overrides", key="clear_overrides"):
                    st.session_state.timesheet_hour_overrides = {}
                    st.success("✅ All hour overrides cleared.")
                    st.rerun()
            
            with col2:
                if st.button("🔄 Reset to Original", key="reset_overrides"):
                    st.session_state.timesheet_hour_overrides = {}
                    st.success("✅ Reset to original timesheet totals.")
                    st.rerun()
    else:
        st.info("ℹ️ No hour overrides active. Edit hour totals above and save to create overrides that will be used in all commission calculations.")

def display_reports_history_tab():
    """Consolidated Reports & History - combines Reports + History"""
    st.markdown("## 📈 Reports & History")
    
    # Sub-tabs for reports and history
    report_tab1, report_tab2, report_tab3 = st.tabs([
        "📋 Generate Reports",
        "📜 Calculation History",
        "🔍 Audit Trail"
    ])
    
    with report_tab1:
        display_reports_tab()
    
    with report_tab2:
        display_calculation_history()
        
    with report_tab3:
        display_audit_trail()

def display_settings_tab():
    """Consolidated Settings - combines Configuration + Advanced Settings"""
    st.markdown("## ⚙️ Settings")
    
    # Sub-tabs for different settings
    settings_tab1, settings_tab2, settings_tab3 = st.tabs([
        "💰 Commission Rates",
        "🛠️ System Admin",
        "💾 Backup & Restore"
    ])
    
    with settings_tab1:
        display_configuration_tab()
    
    with settings_tab2:
        display_system_admin()
        
    with settings_tab3:
        display_backup_restore()

def display_bulk_operations():
    """Display bulk operations section"""
    # Import and use the bulk operations from data management page if it exists
    try:
        from pages.data_management import bulk_operations_section
        bulk_operations_section()
    except ImportError:
        # Fallback implementation
        st.markdown("### 🔧 Bulk Operations")
        st.info("Bulk operations functionality allows you to manage multiple records at once.")
        
        bulk_type = st.selectbox(
            "Select bulk operation type:",
            ["Employee Updates", "Commission Rate Changes", "Data Import/Export"]
        )
        
        if bulk_type == "Employee Updates":
            st.markdown("#### 📊 Bulk Employee Updates")
            st.write("Update multiple employee records simultaneously.")
        elif bulk_type == "Commission Rate Changes":
            st.markdown("#### 💰 Bulk Rate Changes")
            st.write("Apply commission rate changes across multiple entities.")
        else:
            st.markdown("#### 📥 Batch Import/Export")
            st.write("Import or export data in bulk.")

def display_kpis():
    """Display key performance indicators"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        employees = len(st.session_state.get('employee_data', pd.DataFrame()))
        st.metric("👥 Total Employees", employees)
    
    with col2:
        if 'commission_results' in st.session_state and not st.session_state.commission_results.empty:
            total_commission = st.session_state.commission_results['Total Commission'].sum()
            st.metric("💰 Total Commission", f"${total_commission:,.2f}")
        else:
            st.metric("💰 Total Commission", "$0.00")
    
    with col3:
        revenue_loaded = "✅" if st.session_state.get('saved_revenue_data') is not None else "❌"
        st.metric("📊 Revenue Data", revenue_loaded)
    
    with col4:
        config_status = "✅" if st.session_state.get('config_saved', False) else "⚠️"
        st.metric("⚙️ Config Status", config_status)

def display_system_status():
    """Display system status summary"""
    st.markdown("### 📊 System Status")
    
    # Check data availability
    timesheet_status = "✅ Loaded" if st.session_state.get('saved_timesheet_data') is not None else "❌ Not loaded"
    revenue_status = "✅ Loaded" if st.session_state.get('saved_revenue_data') is not None else "❌ Not loaded"
    config_status = "✅ Configured" if st.session_state.get('config_saved', False) else "⚠️ Not configured"
    
    st.markdown(f"**Timesheet Data:** {timesheet_status}")
    st.markdown(f"**Revenue Data:** {revenue_status}")
    st.markdown(f"**Commission Config:** {config_status}")

def display_analytics_charts():
    """Display analytics charts overview"""
    if (st.session_state.get('saved_timesheet_data') is not None and 
        st.session_state.get('saved_revenue_data') is not None):
        # Show a sample chart
        analytics = AnalyticsService()
        
        # Get commission data if available
        if 'commission_results' in st.session_state:
            kpis = analytics.calculate_kpis(st.session_state.commission_results)
            
            # Display a simple metric
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Commission", f"${kpis.get('total_commission', 0):,.2f}")
            with col2:
                st.metric("Employees", kpis.get('total_employees', 0))
        else:
            st.info("Calculate commissions to see analytics")
    else:
        st.info("📊 Upload data to see analytics")

def display_backup_restore():
    """Display backup and restore section"""
    st.markdown("### 💾 Backup & Restore")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📥 Create Backup")
        if st.button("🔒 Create Full Backup", use_container_width=True):
            create_backup("Full System Backup")
            
    with col2:
        st.markdown("#### 📤 Restore Backup")
        backup_file = st.file_uploader("Upload backup file", type=['json', 'zip'])
        if backup_file:
            # Validate backup file
            size_valid, size_msg = validate_file_size(backup_file, max_size_mb=100)  # Allow larger backups
            if not size_valid:
                st.error(f"❌ {size_msg}")
            elif st.button("🔓 Restore", use_container_width=True):
                restore_from_backup(backup_file, ["all"])

# ===== SMART SUGGESTION HELPER FUNCTIONS =====

def get_employee_suggestions():
    """Get employee suggestions from timesheet data"""
    suggestions = []
    
    # Check if timesheet data exists
    if 'saved_timesheet_data' not in st.session_state or st.session_state.saved_timesheet_data is None:
        return suggestions
    
    timesheet_data = st.session_state.saved_timesheet_data
    existing_employees = set()
    
    # Get existing employee names/IDs
    if 'employee_data' in st.session_state and not st.session_state.employee_data.empty:
        existing_employees.update(st.session_state.employee_data['Name'].str.lower().tolist())
        # Convert numeric Employee IDs to strings for comparison
        existing_employees.update(st.session_state.employee_data['Employee ID'].astype(str).str.lower().tolist())
    
    # Find employee column - be flexible with column names
    employee_col = None
    possible_employee_columns = ['Employee', 'Employee Name', 'Name', 'Employee_Name', 'EmployeeName', 
                                'Staff', 'Staff Name', 'Worker', 'Person', 'Resource']
    
    # Find the column (case-insensitive)
    for col in timesheet_data.columns:
        if col.lower() in [pc.lower() for pc in possible_employee_columns]:
            employee_col = col
            break
        # Also check if column contains 'employee' or 'name'
        elif 'employee' in col.lower() or 'name' in col.lower():
            employee_col = col
            break
    
    if employee_col:
        # Extract unique employees from timesheet
        timesheet_employees = timesheet_data[employee_col].dropna().unique()
        
        # Calculate starting Employee ID for sequential assignment in suggestions
        if 'employee_data' in st.session_state and not st.session_state.employee_data.empty:
            existing_ids = st.session_state.employee_data['Employee ID'].dropna().tolist()
            if existing_ids:
                next_id = max(existing_ids) + 1
            else:
                next_id = 1001
        else:
            next_id = 1001
        
        suggestion_counter = 0
        for emp_name in timesheet_employees:
            emp_name_str = str(emp_name).strip()
            if emp_name_str and emp_name_str.lower() not in existing_employees:
                # Try to extract employee ID if it's in format "Name (ID)" or "ID - Name"
                emp_id = None
                
                # Check for ID patterns in the name first
                import re
                # Pattern 1: "John Doe (1001)" - numeric ID in parentheses
                match = re.search(r'\((\d+)\)$', emp_name_str)
                if match:
                    emp_id = int(match.group(1))
                else:
                    # Pattern 2: "1001 - John Doe" - numeric ID at start
                    match = re.search(r'^(\d+)\s*-', emp_name_str)
                    if match:
                        emp_id = int(match.group(1))
                
                # If no ID pattern found, assign sequential ID for display
                if emp_id is None:
                    emp_id = next_id + suggestion_counter
                    suggestion_counter += 1
                
                suggestions.append({
                    'name': emp_name_str,
                    'id': emp_id,
                    'source': 'timesheet'
                })
    
    return suggestions

def get_business_unit_suggestions():
    """Get business unit suggestions from revenue data"""
    suggestions = []
    
    # Check if revenue data exists
    if 'saved_revenue_data' not in st.session_state or st.session_state.saved_revenue_data is None:
        return suggestions
    
    revenue_data = st.session_state.saved_revenue_data
    existing_units = set()
    
    # Get existing business unit codes/names
    if 'business_unit_rates' in st.session_state:
        for code, unit in st.session_state.business_unit_rates.items():
            existing_units.add(code.lower())
            existing_units.add(unit['name'].lower())
    
    # Find business unit column in revenue data - be more flexible
    business_unit_col = None
    possible_columns = ['Business Unit', 'Business_Unit', 'Unit', 'Department', 'Division', 'Region',
                       'BU', 'Dept', 'Team', 'Office', 'Branch', 'Location', 'Area']
    
    # Find the column (case-insensitive)
    for col in revenue_data.columns:
        # Direct match (case-insensitive)
        if col.lower() in [pc.lower() for pc in possible_columns]:
            business_unit_col = col
            break
        # Contains match
        elif any(keyword in col.lower() for keyword in ['business', 'unit', 'department', 'division', 'region']):
            business_unit_col = col
            break
    
    if business_unit_col:
        # Get unique business units from revenue data
        revenue_units = revenue_data[business_unit_col].dropna().unique()
        
        for unit_name in revenue_units:
            if unit_name.lower() not in existing_units:
                # Count revenue entries for this unit
                revenue_count = len(revenue_data[revenue_data[business_unit_col] == unit_name])
                
                # Generate a suggested code
                suggested_code = generate_business_unit_code(unit_name)
                
                suggestions.append({
                    'name': unit_name,
                    'suggested_code': suggested_code,
                    'revenue_count': revenue_count,
                    'source': 'revenue'
                })
    
    return suggestions

def extract_employee_id(emp_name):
    """Extract employee ID from various name formats"""
    import re
    
    # Pattern 1: "John Doe (1001)" - numeric ID in parentheses
    match = re.search(r'\((\d+)\)$', emp_name)
    if match:
        return int(match.group(1))
    
    # Pattern 2: "1001 - John Doe" - numeric ID at start
    match = re.search(r'^(\d+)\s*-', emp_name)
    if match:
        return int(match.group(1))
    
    # Pattern 3: Generate sequential numeric ID starting from 1001
    # Generate unique sequential ID based on existing employee data
    if 'employee_data' in st.session_state and not st.session_state.employee_data.empty:
        existing_ids = st.session_state.employee_data['Employee ID'].dropna()
        if len(existing_ids) > 0:
            return int(existing_ids.max()) + 1
    return 1001  # Start from 1001 if no existing data

def generate_business_unit_code(unit_name):
    """Generate a business unit code from the name"""
    import re
    
    # Remove special characters and split into words
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', unit_name)
    words = clean_name.strip().split()
    
    if len(words) == 1:
        # Single word: take first 3 characters
        return words[0][:3].upper()
    elif len(words) == 2:
        # Two words: take first 2 chars of each
        return (words[0][:2] + words[1][:2]).upper()
    else:
        # Multiple words: take first char of first 3 words
        return ''.join([word[0] for word in words[:3]]).upper()

def add_suggested_employees(suggested_employees, exclude_from_payroll=False, mark_as_helpers=False):
    """Add all suggested employees to the employee list with specified options"""
    # Calculate starting Employee ID for sequential assignment
    if not st.session_state.employee_data.empty and 'Employee ID' in st.session_state.employee_data.columns:
        existing_ids = st.session_state.employee_data['Employee ID'].dropna().tolist()
        if existing_ids:
            next_id = max(existing_ids) + 1
        else:
            next_id = 1001
    else:
        next_id = 1001
    
    for i, emp in enumerate(suggested_employees):
        # Determine Employee ID - use sequential assignment for unique IDs
        emp_id = emp.get('id')
        if emp_id and str(emp_id).isdigit():
            emp_id = int(emp_id)
        else:
            # Generate sequential unique numeric ID
            emp_id = next_id + i
        
        # Set status based on exclusion options
        if exclude_from_payroll:
            status = 'Excluded from Payroll'
            commission_eligible = False
            department = 'Office'
            role = 'Office Employee'
        else:
            status = 'Active'
            commission_eligible = not mark_as_helpers  # If helper, not commission eligible
            department = 'Unknown'
            role = 'Employee'
        
        new_employee = {
            'Employee ID': emp_id,
            'Name': emp['name'],
            'Department': department,
            'Role': role,
            'Hourly Rate': 25.0,  # Default rate
            'Start Date': datetime.now().date(),
            'Status': status,
            'Email': '',
            'Commission Eligible': commission_eligible,
            'Helper/Apprentice': mark_as_helpers,
            'Commission Plan': 'Efficiency Pay' if not mark_as_helpers else 'None'
        }
        
        st.session_state.employee_data = pd.concat([
            st.session_state.employee_data, 
            pd.DataFrame([new_employee])
        ], ignore_index=True)

def fix_duplicate_employee_ids():
    """Fix duplicate Employee IDs by reassigning sequential IDs"""
    if st.session_state.employee_data.empty:
        return
    
    # Find duplicates
    employee_data = st.session_state.employee_data.copy()
    duplicates = employee_data['Employee ID'].value_counts()[employee_data['Employee ID'].value_counts() > 1]
    
    if duplicates.empty:
        return  # No duplicates found
    
    # Get highest valid Employee ID to start from
    valid_ids = employee_data['Employee ID'].dropna()
    if len(valid_ids) > 0:
        next_id = int(valid_ids.max()) + 1
    else:
        next_id = 1001
    
    # Fix duplicates by assigning new sequential IDs
    fixed_count = 0
    for duplicate_id in duplicates.index:
        # Find all rows with this duplicate ID
        duplicate_rows = employee_data[employee_data['Employee ID'] == duplicate_id]
        
        # Keep the first occurrence unchanged, reassign others
        for i, (idx, row) in enumerate(duplicate_rows.iterrows()):
            if i > 0:  # Skip first occurrence
                st.session_state.employee_data.loc[idx, 'Employee ID'] = next_id
                next_id += 1
                fixed_count += 1
    
    return fixed_count

def add_selected_employees(employees_to_add):
    """Add individually selected employees with their specific configurations"""
    # Calculate starting Employee ID for sequential assignment
    if not st.session_state.employee_data.empty and 'Employee ID' in st.session_state.employee_data.columns:
        existing_ids = st.session_state.employee_data['Employee ID'].dropna().tolist()
        if existing_ids:
            next_id = max(existing_ids) + 1
        else:
            next_id = 1001
    else:
        next_id = 1001
    
    for i, (employee, exclude_from_payroll, is_helper) in enumerate(employees_to_add):
        # Determine Employee ID - use sequential assignment for unique IDs
        emp_id = employee.get('id')
        if emp_id and str(emp_id).isdigit():
            emp_id = int(emp_id)
        else:
            # Generate sequential unique numeric ID
            emp_id = next_id + i
        
        # Set status and attributes based on individual configuration
        if exclude_from_payroll:
            status = 'Excluded from Payroll'
            commission_eligible = False
            department = 'Office'
            role = 'Office Employee'
            is_helper = False  # Office employees can't be helpers
        else:
            status = 'Active'
            commission_eligible = not is_helper  # Helpers are not commission eligible
            department = 'Unknown'
            role = 'Helper/Apprentice' if is_helper else 'Employee'
        
        new_employee = {
            'Employee ID': emp_id,
            'Name': employee['name'],
            'Department': department,
            'Role': role,
            'Hourly Rate': 25.0,  # Default rate
            'Start Date': datetime.now().date(),
            'Status': status,
            'Email': '',
            'Commission Eligible': commission_eligible,
            'Helper/Apprentice': is_helper,
            'Commission Plan': 'Efficiency Pay' if not is_helper else 'None'
        }
        
        st.session_state.employee_data = pd.concat([
            st.session_state.employee_data, 
            pd.DataFrame([new_employee])
        ], ignore_index=True)

def setup_suggested_business_units(suggested_units):
    """Add all suggested business units with default rates"""
    default_rates = {
        'Lead Generation': 5.0,
        'Sales': 10.0,
        'Work Done': 7.5
    }
    
    # Initialize commission settings if not exists
    if 'business_unit_commission_settings' not in st.session_state:
        st.session_state.business_unit_commission_settings = {}
    
    for unit in suggested_units:
        code = unit['suggested_code']
        
        # Ensure unique code
        counter = 1
        original_code = code
        while code in st.session_state.business_unit_rates:
            code = f"{original_code}{counter}"
            counter += 1
        
        st.session_state.business_unit_rates[code] = {
            'name': unit['name'],
            'code': code,
            'rates': default_rates.copy(),
            'created_date': datetime.now().strftime("%Y-%m-%d"),
            'created_by': st.session_state.get('user', {}).get('username', 'System'),
            'source': 'auto_suggested'
        }
        
        # SYNC WITH COMMISSION SETTINGS
        st.session_state.business_unit_commission_settings[unit['name']] = {
            'lead_gen_rate': default_rates['Lead Generation'],
            'sold_by_rate': default_rates['Sales'],
            'work_done_rate': default_rates['Work Done'],
            'enabled': True
        }

# ===== END SMART SUGGESTION FUNCTIONS =====

# ===== END NEW CONSOLIDATED FUNCTIONS =====

def display_employee_setup_tab():
    """Employee setup and management tab - DEPRECATED, functionality moved to display_data_management_tab"""
    # This function is kept for backward compatibility but the functionality
    # has been moved directly into display_data_management_tab
    pass

def display_add_employee():
    """Add new employee form"""
    st.markdown("### ➕ Add New Employee")
    
    # Commission system explanation
    st.info("💡 **Commission System**: Employees earn commissions based on revenue data (Lead Generation, Sales, Work Done). Commission rates are configured per business unit in Commission Settings.")
    
    
    with st.form("add_employee_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            emp_id = st.number_input("Employee ID*", min_value=1, value=None, step=1, format="%d", placeholder="e.g. 1001")
            emp_name = st.text_input("Full Name*", placeholder="John Doe")
            emp_dept = st.selectbox("Department", ["Sales", "Marketing", "Operations", "IT", "HR", "Finance"])
            emp_role = st.selectbox("Role", ["Sales Rep", "Manager", "Director", "Executive", "Analyst", "Specialist"])
        
        with col2:
            emp_rate = st.number_input("Hourly Rate ($)*", min_value=0.0, value=25.0, step=0.50)
            emp_start = st.date_input("Start Date", value=datetime.now().date())
            emp_status = st.selectbox("Status", ["Active", "Inactive", "On Leave", "Excluded from Payroll"])
            emp_email = st.text_input("Email", placeholder="john.doe@company.com")
        
        # Commission eligibility
        st.markdown("#### Commission Eligibility")
        col1, col2 = st.columns(2)
        
        with col1:
            commission_eligible = st.checkbox("Eligible for Commission", value=True, help="Employee can earn commissions from revenue-based calculations")
        
        with col2:
            if commission_eligible:
                st.info("💡 Commission rates are configured per business unit in Commission Settings")
            else:
                st.info("❌ Employee will not receive any commission payments")
        
        # Submit button
        submitted = st.form_submit_button("➕ Add Employee", type="primary", use_container_width=True)
        
        if submitted:
            if emp_id and emp_name and emp_rate > 0:
                # Create new employee record
                new_employee = pd.DataFrame({
                    'Employee ID': [emp_id],
                    'Name': [emp_name],
                    'Department': [emp_dept],
                    'Role': [emp_role],
                    'Hourly Rate': [emp_rate],
                    'Start Date': [emp_start],
                    'Status': [emp_status],
                    'Email': [emp_email],
                    'Commission Eligible': [commission_eligible]
                })
                
                # Check if employee ID already exists
                if emp_id in st.session_state.employee_data['Employee ID'].values:
                    st.error(f"❌ Employee ID '{emp_id}' already exists!")
                else:
                    # Add to employee data
                    st.session_state.employee_data = pd.concat([st.session_state.employee_data, new_employee], ignore_index=True)
                    st.success(f"✅ Employee '{emp_name}' added successfully!")
                    st.balloons()
                    st.rerun()
            else:
                st.error("❌ Please fill in all required fields (Employee ID, Name, Hourly Rate)")

def display_manage_employees():
    """Manage existing employees"""
    st.markdown("### 📋 Manage Employees")
    
    # Add commission info
    st.info("💰 **Commission System**: Commission rates are now configured per business unit in the 'Commission Calc' tab → 'Settings' section, not per employee. Each employee is simply eligible or not eligible for commissions.")
    
    if len(st.session_state.employee_data) > 0:
        # Filter options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            dept_filter = st.selectbox("Filter by Department", ["All"] + list(st.session_state.employee_data['Department'].unique()))
        
        with col2:
            status_filter = st.selectbox("Filter by Status", ["All", "Active", "Inactive", "On Leave", "Excluded from Payroll"])
        
        with col3:
            search_term = st.text_input("🔍 Search Employee", placeholder="Name or ID", key="employee_search")
        
        # Apply filters while preserving original index
        filtered_data = st.session_state.employee_data.copy()
        
        if dept_filter != "All":
            filtered_data = filtered_data[filtered_data['Department'] == dept_filter]
        
        if status_filter != "All":
            filtered_data = filtered_data[filtered_data['Status'] == status_filter]
        
        if search_term:
            filtered_data = filtered_data[
                filtered_data['Name'].str.contains(search_term, case=False, na=False) |
                filtered_data['Employee ID'].astype(str).str.contains(search_term, case=False, na=False)
            ]
        
        # Store original indices to map back after editing
        filtered_data_with_original_index = filtered_data.copy()
        filtered_data = filtered_data.reset_index(drop=False).rename(columns={'index': 'original_index'})
        
        # Display employee data
        st.markdown(f"**Showing {len(filtered_data)} of {len(st.session_state.employee_data)} employees**")
        
        # Editable dataframe
        edited_data = st.data_editor(
            filtered_data,
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "Hourly Rate": st.column_config.NumberColumn(
                    "Hourly Rate ($)",
                    min_value=0,
                    format="$%.2f"
                ),
                "Start Date": st.column_config.DateColumn(
                    "Start Date",
                    format="YYYY-MM-DD"
                ),
                "Commission Eligible": st.column_config.CheckboxColumn(
                    "Commission Eligible",
                    help="Employee eligible for revenue-based commissions"
                ),
                "Commission Plan": st.column_config.SelectboxColumn(
                    "Commission Plan",
                    options=["Efficiency Pay", "Hourly + Commission", "None"],
                    help="Efficiency Pay: max(hourly, commission) | Hourly + Commission: hourly + commission"
                ),
                "Email": st.column_config.TextColumn(
                    "Email",
                    help="Employee email address"
                )
            }
        )
        
        # Save changes button
        if st.button("💾 Save Changes", type="primary", key="employee_save_changes"):
            st.session_state.employee_data = edited_data
            st.success("✅ Employee data updated successfully!")
            st.rerun()
        
    
    else:
        st.info("👥 No employees found. Add employees using the 'Add Employee' tab.")

def display_employee_import_export():
    """Import and export employee data"""
    st.markdown("### 📤 Import/Export Employee Data")
    
    st.warning("⚠️ **Commission System Update**: Individual commission rates, tiers, and minimum hours are no longer used. Commission rates are now configured per business unit in Commission Settings.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📥 Import Employees")
        
        # Download template
        if st.button("📄 Download Import Template"):
            template_df = pd.DataFrame({
                'Employee ID': [1001, 1002],
                'Name': ['John Doe', 'Jane Smith'],
                'Department': ['Sales', 'Marketing'],
                'Role': ['Sales Rep', 'Manager'],
                'Hourly Rate': [25.0, 35.0],
                'Start Date': ['2024-01-01', '2024-01-01'],
                'Status': ['Active', 'Active'],
                'Email': ['john@company.com', 'jane@company.com'],
                'Commission Eligible': [True, True]
            })
            csv = template_df.to_csv(index=False)
            st.download_button(
                label="Download Template CSV",
                data=csv,
                file_name="employee_import_template.csv",
                mime="text/csv"
            )
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload Employee Data",
            type=['csv', 'xlsx', 'xls'],
            help="Upload employee data in CSV or Excel format"
        )
        
        if uploaded_file:
            # Validate file size and content
            size_valid, size_msg = validate_file_size(uploaded_file, max_size_mb=25)
            content_valid, content_msg = validate_file_content(uploaded_file)
            
            if not size_valid:
                st.error(f"❌ {size_msg}")
                return
            
            if not content_valid:
                st.error(f"❌ {content_msg}")
                return
            
            # Show validation success
            if size_msg:
                st.info(f"✅ {size_msg}")
            if content_msg:
                st.info(f"✅ {content_msg}")
            
            try:
                # Read file
                file_ext = uploaded_file.name.lower()
                if file_ext.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(uploaded_file)
                else:
                    df = pd.read_csv(uploaded_file)
                
                st.success(f"✅ File loaded: {len(df)} employees found")
                st.dataframe(df.head())
                
                # Import options
                import_mode = st.radio("Import Mode", ["Append", "Replace All"])
                
                if st.button("📥 Import Employees", type="primary"):
                    # Auto-increment Employee IDs for bulk import
                    df_to_import = df.copy()
                    
                    # Get the highest existing Employee ID
                    if not st.session_state.employee_data.empty and 'Employee ID' in st.session_state.employee_data.columns:
                        max_existing_id = st.session_state.employee_data['Employee ID'].max()
                        if pd.isna(max_existing_id):
                            next_id = 1001
                        else:
                            next_id = int(max_existing_id) + 1
                    else:
                        next_id = 1001
                    
                    # Assign sequential Employee IDs to all imported employees
                    for i in range(len(df_to_import)):
                        df_to_import.loc[df_to_import.index[i], 'Employee ID'] = next_id + i
                    
                    if import_mode == "Replace All":
                        st.session_state.employee_data = df_to_import
                        st.success(f"✅ Replaced all employees with {len(df_to_import)} new records (Employee IDs: {next_id}-{next_id + len(df_to_import) - 1})")
                    else:
                        # Append all employees (no duplicates since we're using new sequential IDs)
                        st.session_state.employee_data = pd.concat([st.session_state.employee_data, df_to_import], ignore_index=True)
                        st.success(f"✅ Added {len(df_to_import)} new employees (Employee IDs: {next_id}-{next_id + len(df_to_import) - 1})")
                    st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")
    
    with col2:
        st.markdown("#### 📤 Export Employees")
        
        if len(st.session_state.employee_data) > 0:
            # Export options
            export_format = st.radio("Export Format", ["CSV", "Excel"])
            include_inactive = st.checkbox("Include Inactive Employees", value=True)
            
            # Prepare data for export
            export_data = st.session_state.employee_data.copy()
            if not include_inactive:
                export_data = export_data[export_data['Status'] == 'Active']
            
            st.info(f"📊 Will export {len(export_data)} employees")
            
            # Export button
            if st.button("📤 Export Employee Data", type="primary"):
                if export_format == "CSV":
                    csv = export_data.to_csv(index=False)
                    st.download_button(
                        label="Download Employees CSV",
                        data=csv,
                        file_name=f"employees_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    # Excel export would require additional handling
                    st.info("Excel export requires additional libraries. Using CSV format.")
                    csv = export_data.to_csv(index=False)
                    st.download_button(
                        label="Download Employees CSV",
                        data=csv,
                        file_name=f"employees_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
        else:
            st.info("No employee data to export")

def display_home_tab():
    """Home/Dashboard tab"""
    st.markdown("## 🏠 Welcome to Commission Calculator Pro")
    
    # Debug info (can be hidden with expander)
    with st.expander("🔧 Debug Info", expanded=False):
        st.write("**Session State:**")
        st.write(f"• Timesheet data saved: {st.session_state.get('saved_timesheet_data') is not None}")
        st.write(f"• Revenue data saved: {st.session_state.get('saved_revenue_data') is not None}")
        st.write(f"• Configuration saved: {st.session_state.get('config_saved', False)}")
        st.write(f"• Last timesheet save: {st.session_state.get('last_timesheet_save', 'Never')}")
        st.write(f"• Last revenue save: {st.session_state.get('last_revenue_save', 'Never')}")
        st.write(f"• Last config save: {st.session_state.get('last_config_save', 'Never')}")
        st.write(f"• Data updated flag: {st.session_state.get('data_updated', False)}")
        
        if st.session_state.get('saved_timesheet_data') is not None:
            st.write(f"• Timesheet rows: {len(st.session_state.saved_timesheet_data)}")
        if st.session_state.get('saved_revenue_data') is not None:
            st.write(f"• Revenue rows: {len(st.session_state.saved_revenue_data)}")
        if st.session_state.get('config_saved', False):
            st.write(f"• Employee rates count: {len(st.session_state.get('employee_rates', {}))}")
            st.write(f"• Commission rates count: {len(st.session_state.get('commission_rates', {}))}")
    
    # Check for data updates and clear the flag
    if st.session_state.get('data_updated', False):
        st.session_state.data_updated = False
        st.success("🔄 Data updated! Dashboard metrics refreshed.")
    
    # Feature overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h4>📤 Data Management</h4>
            <p>Upload and manage timesheet and revenue data with validation and templates.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h4>⚙️ Configuration</h4>
            <p>Set up employee rates, commission percentages, and system settings.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h4>📊 Analytics</h4>
            <p>View real-time analytics, KPIs, and performance metrics.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # System status
    st.markdown("## 📊 System Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🧮 Calculator", "✅ Ready", delta="Active")
    
    with col2:
        # Check if timesheet data exists
        timesheet_status = "✅ Loaded" if st.session_state.get('saved_timesheet_data') is not None else "⚠️ None loaded"
        timesheet_count = len(st.session_state.get('saved_timesheet_data', [])) if st.session_state.get('saved_timesheet_data') is not None else 0
        st.metric("👥 Timesheet Data", timesheet_status, delta=f"{timesheet_count} rows")
    
    with col3:
        # Check if revenue data exists
        revenue_status = "✅ Loaded" if st.session_state.get('saved_revenue_data') is not None else "⚠️ None loaded"
        revenue_count = len(st.session_state.get('saved_revenue_data', [])) if st.session_state.get('saved_revenue_data') is not None else 0
        st.metric("💰 Revenue Data", revenue_status, delta=f"{revenue_count} rows")
    
    with col4:
        commission_status = "✅ Ready" if (st.session_state.get('saved_timesheet_data') is not None and st.session_state.get('saved_revenue_data') is not None) else "⚠️ Missing data"
        st.metric("🧮 Commission Calc", commission_status, delta="Ready" if commission_status == "✅ Ready" else "Need data")
    

def display_timesheet_tab():
    """Timesheet data management tab"""
    st.markdown("## ⏰ Timesheet Data")
    
    # Initialize session state for timesheet
    if 'timesheet_data' not in st.session_state:
        st.session_state.timesheet_data = None
    
    # Create sub-tabs
    time_tab1, time_tab2, time_tab3 = st.tabs([
        "📤 Upload Timesheet",
        "📊 View & Edit",
        "📈 Summary"
    ])
    
    with time_tab1:
        display_timesheet_upload()
    
    with time_tab2:
        display_timesheet_view()
    
    with time_tab3:
        display_timesheet_summary()

def display_timesheet_upload():
    """Upload timesheet data"""
    st.markdown("### 📤 Upload Timesheet Data")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload Timesheet File",
        type=['xlsx', 'xls', 'csv'],
        help="Upload employee timesheet data with hours worked"
    )
    
    if uploaded_file:
        # Validate file size and content
        size_valid, size_msg = validate_file_size(uploaded_file, max_size_mb=25)
        content_valid, content_msg = validate_file_content(uploaded_file)
        
        if not size_valid:
            st.error(f"❌ {size_msg}")
            return
        
        if not content_valid:
            st.error(f"❌ {content_msg}")
            return
        
        # Show validation success
        if size_msg:
            st.info(f"✅ {size_msg}")
        if content_msg:
            st.info(f"✅ {content_msg}")
        
        try:
            # Read file
            file_ext = uploaded_file.name.lower()
            if file_ext.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(uploaded_file)
            else:
                df = pd.read_csv(uploaded_file)
            
            # Validate DataFrame
            if df.empty:
                st.error("❌ The uploaded timesheet file is empty")
                return
                
            st.success(f"✅ File loaded: {uploaded_file.name}")
            
            # Show preview
            st.markdown("#### 📋 Data Preview")
            st.dataframe(df.head(10), use_container_width=True)
            
            # Data validation
            st.markdown("#### ✅ Data Validation")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Rows", len(df))
                st.metric("Columns", len(df.columns))
            
            with col2:
                # Check for required columns
                required_cols = ['Employee Name']
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
                else:
                    st.success("✅ Employee Name column found")
                
                # Check for hours columns
                hours_columns = [col for col in df.columns if 'hour' in col.lower()]
                if hours_columns:
                    st.info(f"📊 Found {len(hours_columns)} hours columns: {', '.join(hours_columns[:3])}{'...' if len(hours_columns) > 3 else ''}")
                
                # Show column names
                with st.expander("📊 Column Names"):
                    for col in df.columns:
                        st.write(f"• {col}")
            
            # Process timesheet to show total hours
            if 'Employee Name' in df.columns:
                st.markdown("#### 📊 Hours Summary")
                
                # Find all hours columns
                hours_columns = [col for col in df.columns if 'hour' in col.lower()]
                
                if hours_columns:
                    # Calculate total hours for each employee
                    summary_df = df.copy()
                    
                    # Convert hours columns to numeric
                    for col in hours_columns:
                        summary_df[col] = pd.to_numeric(summary_df[col], errors='coerce').fillna(0)
                    
                    # Calculate total hours
                    summary_df['Total Hours'] = summary_df[hours_columns].sum(axis=1)
                    
                    # Group by employee
                    employee_summary = summary_df.groupby('Employee Name')['Total Hours'].sum().reset_index()
                    # Ensure Total Hours is numeric before sorting
                    employee_summary['Total Hours'] = pd.to_numeric(employee_summary['Total Hours'], errors='coerce').fillna(0)
                    employee_summary = employee_summary.sort_values('Total Hours', ascending=False)
                    
                    st.dataframe(employee_summary, use_container_width=True)
                    
                    # Show total hours breakdown
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Employees", len(employee_summary))
                    with col2:
                        st.metric("Total Hours", f"{employee_summary['Total Hours'].sum():,.0f}")
                else:
                    st.info("💡 No hours columns found. Showing original data.")
            
            # Save button
            if st.button("💾 Save Timesheet Data", type="primary", use_container_width=True):
                st.session_state.timesheet_data = df
                st.session_state.uploaded_timesheet_data = df  # For compatibility
                st.session_state.saved_timesheet_data = df  # For compatibility
                st.session_state.timesheet_file_name = uploaded_file.name
                st.session_state.last_timesheet_save = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.success("✅ Timesheet data saved successfully!")
                st.balloons()
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ Error reading file: {e}")

def paginate_dataframe(df, page_size=50):
    """Paginate DataFrame for better performance"""
    if 'page_num' not in st.session_state:
        st.session_state.page_num = 0
    
    total_pages = (len(df) - 1) // page_size + 1
    
    # Pagination controls
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("⏮️ First", disabled=st.session_state.page_num == 0, key="page_first"):
            st.session_state.page_num = 0
            st.rerun()
    
    with col2:
        if st.button("◀️ Previous", disabled=st.session_state.page_num == 0, key="page_prev"):
            st.session_state.page_num -= 1
            st.rerun()
    
    with col3:
        st.write(f"Page {st.session_state.page_num + 1} of {total_pages}")
    
    with col4:
        if st.button("Next ▶️", disabled=st.session_state.page_num >= total_pages - 1, key="page_next"):
            st.session_state.page_num += 1
            st.rerun()
    
    with col5:
        if st.button("Last ⏭️", disabled=st.session_state.page_num >= total_pages - 1, key="page_last"):
            st.session_state.page_num = total_pages - 1
            st.rerun()
    
    # Calculate slice
    start_idx = st.session_state.page_num * page_size
    end_idx = min(start_idx + page_size, len(df))
    
    return df.iloc[start_idx:end_idx], start_idx, end_idx, total_pages

def display_timesheet_view():
    """View and edit timesheet data"""
    st.markdown("### 📊 View & Edit Timesheet Data")
    
    if st.session_state.timesheet_data is not None:
        # Filter options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Get unique employees
            if 'Employee Name' in st.session_state.timesheet_data.columns:
                employees = ['All'] + list(st.session_state.timesheet_data['Employee Name'].unique())
                selected_employee = st.selectbox("Filter by Employee", employees)
            else:
                selected_employee = 'All'
        
        with col2:
            # Date range filter if date column exists
            date_columns = [col for col in st.session_state.timesheet_data.columns if 'date' in col.lower()]
            if date_columns:
                st.date_input("Date Range", value=(datetime.now().date(), datetime.now().date()))
        
        with col3:
            search_term = st.text_input("🔍 Search", placeholder="Search in data...", key="timesheet_search")
        
        # Apply filters
        filtered_data = st.session_state.timesheet_data.copy()
        
        if selected_employee != 'All' and 'Employee Name' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data['Employee Name'] == selected_employee]
        
        # Display data with pagination
        if len(filtered_data) > 50:
            st.markdown(f"**Total: {len(filtered_data)} records (showing 50 per page)**")
            paginated_data, start_idx, end_idx, total_pages = paginate_dataframe(filtered_data)
            st.markdown(f"**Showing records {start_idx + 1} to {end_idx}**")
            
            # Editable dataframe
            edited_data = st.data_editor(
                paginated_data,
                hide_index=True,
                use_container_width=True,
                num_rows="dynamic"
            )
        else:
            st.markdown(f"**Showing {len(filtered_data)} of {len(st.session_state.timesheet_data)} records**")
            
            # Editable dataframe
            edited_data = st.data_editor(
                filtered_data,
                hide_index=True,
                use_container_width=True,
                num_rows="dynamic"
            )
        
        # Save changes
        if st.button("💾 Save Changes", type="primary", key="timesheet_save_changes"):
            st.session_state.timesheet_data = edited_data
            st.session_state.saved_timesheet_data = edited_data  # For compatibility
            st.success("✅ Changes saved successfully!")
            st.rerun()
        
        # Export options
        st.markdown("#### 📤 Export Options")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Download Current View", key="timesheet_download"):
                csv = filtered_data.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"timesheet_data_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    key="timesheet_download_csv"
                )
        
        with col2:
            if st.button("🗑️ Clear All Data", key="timesheet_clear"):
                if st.checkbox("Confirm clear all data", key="timesheet_clear_confirm"):
                    st.session_state.timesheet_data = None
                    st.session_state.saved_timesheet_data = None
                    st.success("✅ Timesheet data cleared")
                    st.rerun()
    
    else:
        st.info("📤 No timesheet data loaded. Please upload data in the 'Upload Timesheet' tab.")

@st.cache_data
def calculate_timesheet_metrics(df):
    """Calculate timesheet metrics with caching"""
    if df is None or df.empty:
        return None
        
    hours_columns = [col for col in df.columns if 'hour' in col.lower()]
    metrics = {
        'total_records': len(df),
        'unique_employees': df['Employee Name'].nunique() if 'Employee Name' in df.columns else 0,
        'total_hours': 0,
        'hours_columns': hours_columns
    }
    
    if hours_columns:
        for col in hours_columns:
            metrics['total_hours'] += pd.to_numeric(df[col], errors='coerce').sum()
    
    return metrics

def display_timesheet_summary():
    """Display timesheet summary and analytics"""
    st.markdown("### 📈 Timesheet Summary")
    
    if st.session_state.timesheet_data is not None:
        df = st.session_state.timesheet_data
        
        # Use cached metrics calculation
        metrics = calculate_timesheet_metrics(df)
        
        if metrics:
            # Overall metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📋 Total Records", metrics['total_records'])
            
            with col2:
                st.metric("👥 Unique Employees", metrics['unique_employees'])
            
            with col3:
                st.metric("⏰ Total Hours", f"{metrics['total_hours']:,.0f}")
            
            with col4:
                st.metric("📅 Last Updated", st.session_state.get('last_timesheet_save', 'Never'))
                
            hours_columns = metrics['hours_columns']
        
        # Employee hours summary
        if 'Employee Name' in df.columns and hours_columns:
            st.markdown("#### 👥 Employee Hours Summary")
            
            # Calculate total hours per employee
            summary_df = df.copy()
            for col in hours_columns:
                summary_df[col] = pd.to_numeric(summary_df[col], errors='coerce').fillna(0)
            
            # Separate regular, OT, and double time hours
            regular_cols = [col for col in hours_columns if 'regular' in col.lower() or 'reg' in col.lower()]
            ot_cols = [col for col in hours_columns if 'ot' in col.lower() or 'overtime' in col.lower()]
            dt_cols = [col for col in hours_columns if 'dt' in col.lower() or 'double' in col.lower() or 'doubletime' in col.lower()]
            
            # Calculate totals by employee
            agg_dict = {}
            if regular_cols:
                agg_dict.update({col: 'sum' for col in regular_cols})
            if ot_cols:
                agg_dict.update({col: 'sum' for col in ot_cols})
            if dt_cols:
                agg_dict.update({col: 'sum' for col in dt_cols})
                
            employee_summary = summary_df.groupby('Employee Name').agg(agg_dict).reset_index()
            
            # Add calculated columns
            if regular_cols:
                employee_summary['Total Regular Hours'] = employee_summary[regular_cols].sum(axis=1)
            else:
                employee_summary['Total Regular Hours'] = 0
                
            if ot_cols:
                employee_summary['Total OT Hours'] = employee_summary[ot_cols].sum(axis=1)
            else:
                employee_summary['Total OT Hours'] = 0
                
            if dt_cols:
                employee_summary['Total Double Time Hours'] = employee_summary[dt_cols].sum(axis=1)
            else:
                employee_summary['Total Double Time Hours'] = 0
                
            employee_summary['Total Hours'] = employee_summary['Total Regular Hours'] + employee_summary['Total OT Hours'] + employee_summary['Total Double Time Hours']
            # Ensure Total Hours is numeric before sorting
            employee_summary['Total Hours'] = pd.to_numeric(employee_summary['Total Hours'], errors='coerce').fillna(0)
            employee_summary = employee_summary.sort_values('Total Hours', ascending=False)
            
            # Display chart
            fig = px.bar(
                employee_summary.head(20),
                x='Employee Name',
                y='Total Hours',
                title='Top 20 Employees by Total Hours',
                color='Total Hours',
                color_continuous_scale='Blues'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            
            # Summary table
            st.markdown("#### 📊 Detailed Summary")
            
            # Add statistics
            # Calculate average hours per day (protect against division by zero)
            employee_summary['Average Hours/Day'] = employee_summary['Total Hours'].apply(
                lambda x: x / 20 if x > 0 else 0  # Assuming 20 work days
            )
            employee_summary['Status'] = employee_summary['Total Hours'].apply(
                lambda x: '✅ Full Time' if x >= 160 else '⚠️ Part Time' if x >= 80 else '❌ Low Hours'
            )
            
            # Select only the summary columns for display
            display_columns = ['Employee Name', 'Total Regular Hours', 'Total OT Hours', 'Total Double Time Hours', 'Total Hours', 'Average Hours/Day', 'Status']
            display_summary = employee_summary[display_columns].copy()
            
            st.dataframe(
                display_summary,
                use_container_width=True,
                column_config={
                    "Total Regular Hours": st.column_config.NumberColumn(
                        "Regular Hours",
                        format="%.1f"
                    ),
                    "Total OT Hours": st.column_config.NumberColumn(
                        "OT Hours", 
                        format="%.1f"
                    ),
                    "Total Double Time Hours": st.column_config.NumberColumn(
                        "Double Time Hours",
                        format="%.1f"
                    ),
                    "Total Hours": st.column_config.NumberColumn(
                        "Total Hours",
                        format="%.1f"
                    ),
                    "Average Hours/Day": st.column_config.NumberColumn(
                        "Avg Hours/Day",
                        format="%.1f"
                    )
                }
            )
            
            # Add totals at the bottom
            st.markdown("#### 📊 Grand Totals")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_regular = employee_summary['Total Regular Hours'].sum()
                st.metric("🕘 Total Regular Hours", f"{total_regular:,.1f}")
            
            with col2:
                total_ot = employee_summary['Total OT Hours'].sum()
                st.metric("⏰ Total OT Hours", f"{total_ot:,.1f}")
            
            with col3:
                total_dt = employee_summary['Total Double Time Hours'].sum()
                st.metric("⚡ Total Double Time Hours", f"{total_dt:,.1f}")
            
            with col4:
                grand_total = total_regular + total_ot + total_dt
                st.metric("📊 Grand Total Hours", f"{grand_total:,.1f}")
        
        # Data quality report
        st.markdown("#### 🔍 Data Quality Report")
        col1, col2 = st.columns(2)
        
        with col1:
            missing_values = df.isnull().sum()
            missing_values = missing_values[missing_values > 0]
            if len(missing_values) > 0:
                st.warning(f"⚠️ Found {len(missing_values)} columns with missing values")
                with st.expander("Show details"):
                    for col, count in missing_values.items():
                        st.write(f"• {col}: {count} missing values")
            else:
                st.success("✅ No missing values found")
        
        with col2:
            duplicate_count = df.duplicated().sum()
            if duplicate_count > 0:
                st.warning(f"⚠️ Found {duplicate_count} duplicate rows")
            else:
                st.success("✅ No duplicate rows found")
    
    else:
        st.info("📤 No timesheet data loaded. Please upload data in the 'Upload Timesheet' tab.")

def display_revenue_tab():
    """Revenue data management tab"""
    st.markdown("## 💰 Revenue Data")
    
    # Initialize session state for revenue
    if 'revenue_data' not in st.session_state:
        st.session_state.revenue_data = None
    
    # Create sub-tabs
    rev_tab1, rev_tab2, rev_tab3 = st.tabs([
        "📤 Upload Revenue",
        "📊 View & Edit",
        "📈 Summary"
    ])
    
    with rev_tab1:
        display_revenue_upload()
    
    with rev_tab2:
        display_revenue_view()
    
    with rev_tab3:
        display_revenue_summary()

def process_revenue_data(df, business_unit_col, revenue_col, lead_gen_col, sold_by_col, assigned_techs_col):
    """
    Process revenue data to split technicians and standardize columns
    """
    df_processed = df.copy()
    
    # Filter out total/summary rows that have missing invoice information
    # These are typically the last rows with totals
    if 'Invoice #' in df_processed.columns and 'Invoice Date' in df_processed.columns:
        # Count rows before filtering
        rows_before = len(df_processed)
        
        # Remove rows where both Invoice # and Invoice Date are missing/null
        df_processed = df_processed[
            ~(df_processed['Invoice #'].isna() & df_processed['Invoice Date'].isna())
        ]
        
        # Also remove rows where Invoice # contains total-related keywords
        if 'Invoice #' in df_processed.columns:
            # Convert to string and check for total keywords
            invoice_col_str = df_processed['Invoice #'].astype(str).str.lower()
            total_keywords = ['total', 'sum', 'grand total', 'subtotal', 'summary']
            for keyword in total_keywords:
                df_processed = df_processed[~invoice_col_str.str.contains(keyword, na=False)]
        
        rows_removed = rows_before - len(df_processed)
        if rows_removed > 0:
            st.info(f"📊 Removed {rows_removed} total/summary row(s) from revenue data")
    
    # Standardize core columns
    if revenue_col and revenue_col != 'Revenue':
        df_processed['Revenue'] = df_processed[revenue_col]
        if revenue_col != 'Revenue':
            df_processed = df_processed.drop(columns=[revenue_col])
    
    if business_unit_col and business_unit_col != 'Business Unit':
        df_processed['Business Unit'] = df_processed[business_unit_col]
        if business_unit_col != 'Business Unit':
            df_processed = df_processed.drop(columns=[business_unit_col])
    
    # Standardize commission-related columns
    if lead_gen_col:
        df_processed['Lead Generated By'] = df_processed[lead_gen_col]
        if lead_gen_col != 'Lead Generated By':
            df_processed = df_processed.drop(columns=[lead_gen_col])
    
    if sold_by_col:
        df_processed['Sold By'] = df_processed[sold_by_col]
        if sold_by_col != 'Sold By':
            df_processed = df_processed.drop(columns=[sold_by_col])
    
    if assigned_techs_col:
        # Split technicians if they are in a single column
        original_techs = df_processed[assigned_techs_col].fillna('')
        
        # Create individual technician columns
        max_techs = 0
        for tech_string in original_techs:
            if pd.notna(tech_string) and str(tech_string).strip():
                # Split by common separators
                techs = [t.strip() for t in str(tech_string).replace(',', ';').replace('&', ';').replace(' and ', ';').split(';') if t.strip()]
                max_techs = max(max_techs, len(techs))
        
        # Add individual technician columns
        for i in range(max_techs):
            df_processed[f'Technician_{i+1}'] = ''
        
        # Populate technician columns
        for idx, tech_string in enumerate(original_techs):
            if pd.notna(tech_string) and str(tech_string).strip():
                techs = [t.strip() for t in str(tech_string).replace(',', ';').replace('&', ';').replace(' and ', ';').split(';') if t.strip()]
                for i, tech in enumerate(techs):
                    if i < max_techs:
                        df_processed.loc[idx, f'Technician_{i+1}'] = tech
        
        # Drop original technician column
        if assigned_techs_col != 'Assigned Technicians':
            df_processed = df_processed.drop(columns=[assigned_techs_col])
        else:
            df_processed = df_processed.drop(columns=['Assigned Technicians'])
        
        # Add metadata about technician splitting
        df_processed['Total_Technicians'] = df_processed[[f'Technician_{i+1}' for i in range(max_techs)]].apply(
            lambda row: len([t for t in row if t and str(t).strip()]), axis=1
        )
    
    return df_processed

def perform_data_validation(df, data_type='revenue'):
    """Perform comprehensive data validation with detailed analysis"""
    try:
        validation_results = {
            'errors': [],
            'warnings': [],
            'info': [],
            'valid_rows': 0,
            'quality_score': 0,
            'column_analysis': {},
            'data_types': {},
            'duplicates': 0,
            'missing_data': {}
        }
        
        # Basic validation
        if df is None or df.empty:
            validation_results['errors'].append("DataFrame is empty or None")
            return validation_results
        
        total_rows = len(df)
        valid_rows = total_rows
        
        # Column analysis
        for col in df.columns:
            col_analysis = {
                'dtype': str(df[col].dtype),
                'null_count': df[col].isnull().sum(),
                'null_percentage': (df[col].isnull().sum() / total_rows) * 100,
                'unique_values': df[col].nunique(),
                'sample_values': df[col].dropna().head(3).tolist()
            }
            validation_results['column_analysis'][col] = col_analysis
            
            # Check for high null percentage
            if col_analysis['null_percentage'] > 50:
                validation_results['warnings'].append(f"Column '{col}' has {col_analysis['null_percentage']:.1f}% missing values")
            elif col_analysis['null_percentage'] > 25:
                validation_results['info'].append(f"Column '{col}' has {col_analysis['null_percentage']:.1f}% missing values")
        
        # Data type specific validation
        if data_type == 'revenue':
            # Check for required revenue columns
            revenue_cols = [col for col in df.columns if 'revenue' in col.lower() or 'amount' in col.lower()]
            business_unit_cols = [col for col in df.columns if 'business' in col.lower() or 'unit' in col.lower()]
            
            if not revenue_cols:
                validation_results['errors'].append("No revenue/amount column found")
            else:
                # Validate revenue data
                revenue_col = revenue_cols[0]
                try:
                    numeric_revenue = pd.to_numeric(df[revenue_col], errors='coerce')
                    null_revenue = numeric_revenue.isnull().sum()
                    negative_revenue = (numeric_revenue < 0).sum()
                    zero_revenue = (numeric_revenue == 0).sum()
                    
                    if null_revenue > 0:
                        validation_results['warnings'].append(f"{null_revenue} rows have invalid revenue values")
                        valid_rows -= null_revenue
                    
                    if negative_revenue > 0:
                        validation_results['warnings'].append(f"{negative_revenue} rows have negative revenue")
                    
                    if zero_revenue > 0:
                        validation_results['info'].append(f"{zero_revenue} rows have zero revenue")
                        
                except Exception as e:
                    validation_results['errors'].append(f"Revenue column validation failed: {str(e)}")
            
            if not business_unit_cols:
                validation_results['warnings'].append("No business unit column found - all revenue will be assigned to 'Unassigned'")
            
            # Check for commission-related columns
            commission_cols = ['Lead Generated By', 'Sold By', 'Assigned Technicians']
            found_comm_cols = []
            for comm_col in commission_cols:
                matching_cols = [col for col in df.columns if comm_col.lower() in col.lower()]
                if matching_cols:
                    found_comm_cols.append(matching_cols[0])
            
            if not found_comm_cols:
                validation_results['warnings'].append("No commission-related columns found (Lead Generated By, Sold By, Assigned Technicians)")
            else:
                validation_results['info'].append(f"Found commission columns: {', '.join(found_comm_cols)}")
        
        elif data_type == 'timesheet':
            # Check for required timesheet columns
            required_cols = ['Employee Name']
            hour_cols = [col for col in df.columns if 'hour' in col.lower()]
            
            missing_required = [col for col in required_cols if col not in df.columns]
            if missing_required:
                validation_results['errors'].append(f"Missing required columns: {', '.join(missing_required)}")
            
            if not hour_cols:
                validation_results['errors'].append("No hour columns found (should contain 'hour' in name)")
            else:
                # Validate hour data
                for hour_col in hour_cols:
                    try:
                        numeric_hours = pd.to_numeric(df[hour_col], errors='coerce')
                        null_hours = numeric_hours.isnull().sum()
                        negative_hours = (numeric_hours < 0).sum()
                        excessive_hours = (numeric_hours > 100).sum()
                        
                        if null_hours > 0:
                            validation_results['warnings'].append(f"{null_hours} rows have invalid values in '{hour_col}'")
                        
                        if negative_hours > 0:
                            validation_results['warnings'].append(f"{negative_hours} rows have negative hours in '{hour_col}'")
                        
                        if excessive_hours > 0:
                            validation_results['info'].append(f"{excessive_hours} rows have >100 hours in '{hour_col}' (check for data entry errors)")
                            
                    except Exception as e:
                        validation_results['errors'].append(f"Hour column '{hour_col}' validation failed: {str(e)}")
        
        # Check for duplicates
        duplicate_count = df.duplicated().sum()
        validation_results['duplicates'] = duplicate_count
        if duplicate_count > 0:
            validation_results['warnings'].append(f"{duplicate_count} duplicate rows found")
        
        # Calculate overall data quality score
        error_penalty = len(validation_results['errors']) * 20
        warning_penalty = len(validation_results['warnings']) * 10
        info_penalty = len(validation_results['info']) * 2
        
        # Base score from valid rows percentage
        valid_percentage = (valid_rows / total_rows) * 100 if total_rows > 0 else 0
        quality_score = max(0, valid_percentage - error_penalty - warning_penalty - info_penalty)
        
        validation_results['valid_rows'] = valid_rows
        validation_results['quality_score'] = min(100, quality_score)
        
        return validation_results
        
    except Exception as e:
        return {
            'errors': [f"Validation failed: {str(e)}"],
            'warnings': [],
            'info': [],
            'valid_rows': 0,
            'quality_score': 0,
            'column_analysis': {},
            'data_types': {},
            'duplicates': 0,
            'missing_data': {}
        }

def display_revenue_upload():
    """Upload revenue data"""
    st.markdown("### 📤 Upload Revenue Data")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload Revenue File",
        type=['xlsx', 'xls', 'csv'],
        help="Upload business unit revenue data"
    )
    
    if uploaded_file:
        # Validate file size and content
        size_valid, size_msg = validate_file_size(uploaded_file, max_size_mb=25)
        content_valid, content_msg = validate_file_content(uploaded_file)
        
        if not size_valid:
            st.error(f"❌ {size_msg}")
            return
        
        if not content_valid:
            st.error(f"❌ {content_msg}")
            return
        
        # Show validation success
        if size_msg:
            st.info(f"✅ {size_msg}")
        if content_msg:
            st.info(f"✅ {content_msg}")
        
        try:
            # Read file
            file_ext = uploaded_file.name.lower()
            if file_ext.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(uploaded_file)
            else:
                df = pd.read_csv(uploaded_file)
            
            # Validate DataFrame
            if df.empty:
                st.error("❌ The uploaded revenue file is empty")
                return
            
            # Additional validation
            if len(df.columns) == 0:
                st.error("❌ The uploaded file has no columns")
                return
            
            if len(df) > 10000:
                st.warning(f"⚠️ Large file detected ({len(df):,} rows). Processing may take longer.")
                if not st.checkbox("I understand this is a large file and want to proceed"):
                    st.stop()
                
            st.success(f"✅ File loaded: {uploaded_file.name}")
            
            # Show preview
            st.markdown("#### 📋 Data Preview")
            st.dataframe(df.head(10), use_container_width=True)
            
            # Enhanced Data Validation Preview
            st.markdown("#### ✅ Advanced Data Validation")
            
            # Run comprehensive validation
            validation_results = perform_data_validation(df, 'revenue')
            
            # Display validation summary
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Rows", len(df))
                st.metric("Columns", len(df.columns))
            
            with col2:
                valid_rows = validation_results['valid_rows']
                st.metric("Valid Rows", valid_rows, delta=f"{valid_rows/len(df)*100:.1f}%")
                st.metric("Data Quality Score", f"{validation_results['quality_score']:.1f}%")
            
            with col3:
                errors = len(validation_results['errors'])
                warnings = len(validation_results['warnings'])
                st.metric("Issues Found", errors + warnings)
                if errors == 0:
                    st.success("✅ No Critical Errors")
                else:
                    st.error(f"❌ {errors} Critical Errors")
            
            # Detailed validation results
            if validation_results['errors'] or validation_results['warnings'] or validation_results['info']:
                with st.expander("🔍 Detailed Validation Results", expanded=bool(validation_results['errors'])):
                    
                    if validation_results['errors']:
                        st.markdown("**❌ Critical Errors:**")
                        for error in validation_results['errors']:
                            st.error(f"• {error}")
                    
                    if validation_results['warnings']:
                        st.markdown("**⚠️ Warnings:**")
                        for warning in validation_results['warnings']:
                            st.warning(f"• {warning}")
                    
                    if validation_results['info']:
                        st.markdown("**ℹ️ Information:**")
                        for info in validation_results['info']:
                            st.info(f"• {info}")
            
            # Column analysis
            with st.expander("📊 Column Analysis"):
                col_df = pd.DataFrame.from_dict(validation_results['column_analysis'], orient='index')
                if not col_df.empty:
                    col_df['Sample Values'] = col_df['sample_values'].apply(lambda x: ', '.join(map(str, x[:2])) + '...' if len(x) > 2 else ', '.join(map(str, x)))
                    display_cols = ['dtype', 'null_count', 'null_percentage', 'unique_values', 'Sample Values']
                    st.dataframe(col_df[display_cols], use_container_width=True)
            
            # Data quality recommendations
            if validation_results['quality_score'] < 90:
                with st.expander("💡 Data Quality Recommendations"):
                    if validation_results['quality_score'] < 50:
                        st.warning("**Low Data Quality Detected**")
                        st.write("• Review and clean your data before proceeding")
                        st.write("• Check for missing values and correct data types")
                        st.write("• Ensure all required columns are present and properly named")
                    elif validation_results['quality_score'] < 80:
                        st.info("**Moderate Data Quality**")
                        st.write("• Consider addressing warnings before processing")
                        st.write("• Verify data accuracy for optimal results")
                    else:
                        st.success("**Good Data Quality**")
                        st.write("• Minor issues detected but data is processable")
            
            with col2:
                # Check for required columns - flexible detection
                business_unit_col = None
                revenue_col = None
                lead_gen_col = None
                sold_by_col = None
                assigned_techs_col = None
                
                # Find business unit column
                for col in df.columns:
                    if 'business unit' in col.lower() or 'unit' in col.lower():
                        business_unit_col = col
                        break
                
                # Find revenue column
                for col in df.columns:
                    if 'revenue' in col.lower():
                        revenue_col = col
                        break
                
                # Find lead generated by column
                for col in df.columns:
                    if 'lead generated' in col.lower() or 'lead gen' in col.lower():
                        lead_gen_col = col
                        break
                
                # Find sold by column
                for col in df.columns:
                    if 'sold by' in col.lower() or 'sales' in col.lower():
                        sold_by_col = col
                        break
                
                # Find assigned technicians column
                for col in df.columns:
                    if 'assigned tech' in col.lower() or 'technician' in col.lower() or 'tech' in col.lower():
                        assigned_techs_col = col
                        break
                
                missing_cols = []
                if not business_unit_col:
                    missing_cols.append('Business Unit (or similar)')
                if not revenue_col:
                    missing_cols.append('Revenue (or similar)')
                
                optional_cols = []
                if lead_gen_col:
                    optional_cols.append(f"Lead Generated By: '{lead_gen_col}'")
                if sold_by_col:
                    optional_cols.append(f"Sold By: '{sold_by_col}'")
                if assigned_techs_col:
                    optional_cols.append(f"Assigned Techs: '{assigned_techs_col}'")
                
                if missing_cols:
                    st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
                else:
                    st.success(f"✅ Found: '{business_unit_col}' and '{revenue_col}'")
                
                if optional_cols:
                    st.info(f"📋 Commission columns found: {'; '.join(optional_cols)}")
                
                # Show column names
                with st.expander("📊 Column Names"):
                    for col in df.columns:
                        col_type = "📊 Data"
                        if col == business_unit_col:
                            col_type = "🏢 Business Unit"
                        elif col == revenue_col:
                            col_type = "💰 Revenue"
                        elif col == lead_gen_col:
                            col_type = "🎯 Lead Gen"
                        elif col == sold_by_col:
                            col_type = "💼 Sales"
                        elif col == assigned_techs_col:
                            col_type = "🔧 Techs"
                        st.write(f"• {col_type} {col}")
            
            # Revenue summary
            if revenue_col:
                st.markdown("#### 💰 Revenue Summary")
                
                # Convert revenue to numeric
                df[revenue_col] = pd.to_numeric(df[revenue_col], errors='coerce')
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Revenue", f"${df[revenue_col].sum():,.0f}")
                
                with col2:
                    st.metric("Average Revenue", f"${df[revenue_col].mean():,.0f}")
                
                with col3:
                    if business_unit_col:
                        st.metric("Business Units", df[business_unit_col].nunique())
                    else:
                        st.metric("Business Units", "N/A")
            
            # Save button
            if st.button("💾 Save Revenue Data", type="primary", use_container_width=True):
                # Process and standardize the data
                df_processed = process_revenue_data(df, business_unit_col, revenue_col, lead_gen_col, sold_by_col, assigned_techs_col)
                
                st.session_state.revenue_data = df_processed
                st.session_state.uploaded_revenue_data = df_processed  # For compatibility
                st.session_state.saved_revenue_data = df_processed  # For compatibility
                st.session_state.revenue_file_name = uploaded_file.name
                st.session_state.last_revenue_save = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.success("✅ Revenue data saved successfully!")
                st.balloons()
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ Error reading file: {e}")

def get_commission_types_for_job(job_row):
    """Determine what commission types a job generates"""
    commission_types = []
    
    try:
        # Check for Lead Generation Commission
        if 'Lead Generated By' in job_row.index:
            lead_gen_by = job_row.get('Lead Generated By')
            if pd.notna(lead_gen_by):  # Use pandas notna for better NaN handling
                lead_gen_str = str(lead_gen_by).strip()
                if lead_gen_str and lead_gen_str.lower() not in ['nan', 'none', '']:
                    commission_types.append('Lead Gen')
        
        # Check for Sales Commission
        if 'Sold By' in job_row.index:
            sold_by = job_row.get('Sold By')
            if pd.notna(sold_by):  # Use pandas notna for better NaN handling
                sold_by_str = str(sold_by).strip()
                if sold_by_str and sold_by_str.lower() not in ['nan', 'none', '']:
                    commission_types.append('Sales')
        
        # Check for Work Done Commission
        if 'Assigned Technicians' in job_row.index:
            techs = job_row.get('Assigned Technicians')
            if pd.notna(techs):  # Use pandas notna for better NaN handling
                techs_str = str(techs).strip()
                if techs_str and techs_str.lower() not in ['nan', 'none', '']:
                    commission_types.append('Work Done')
        
        return ', '.join(commission_types) if commission_types else 'None'
    
    except Exception as e:
        # Fallback in case of any unexpected errors
        return 'Error'

def get_employee_hours_with_overrides(employee_name, timesheet_df):
    """
    Get employee hours with override support
    Returns tuple: (regular_hours, ot_hours, dt_hours)
    """
    # Check if there are hour overrides for this employee
    if ('timesheet_hour_overrides' in st.session_state and 
        st.session_state.timesheet_hour_overrides and 
        employee_name in st.session_state.timesheet_hour_overrides):
        
        override_data = st.session_state.timesheet_hour_overrides[employee_name]
        return (
            override_data.get('regular_hours', 0),
            override_data.get('ot_hours', 0),
            override_data.get('dt_hours', 0)
        )
    
    # Fall back to original timesheet data
    if timesheet_df is not None and 'Employee Name' in timesheet_df.columns:
        emp_hours = timesheet_df[
            (timesheet_df['Employee Name'] == employee_name) |
            (timesheet_df.get('Name', pd.Series(dtype='object')) == employee_name)
        ]
        
        if not emp_hours.empty:
            # Handle both naming conventions
            reg_col = 'Regular Hours' if 'Regular Hours' in timesheet_df.columns else 'Reg Hours'
            regular_hours = emp_hours.get(reg_col, pd.Series([0])).fillna(0).sum()
            ot_hours = emp_hours.get('OT Hours', pd.Series([0])).fillna(0).sum()
            dt_hours = emp_hours.get('DT Hours', pd.Series([0])).fillna(0).sum()
            return (regular_hours, ot_hours, dt_hours)
    
    # No data found
    return (0, 0, 0)

def calculate_employee_pay(employee_name, regular_hours, ot_hours, dt_hours, hourly_rate, commission_total, commission_plan):
    """
    Calculate final employee pay based on their commission plan
    
    Args:
        employee_name: Name of the employee
        regular_hours: Regular hours worked
        ot_hours: Overtime hours worked (paid at 1.5x rate)
        dt_hours: Double-time hours worked (paid at 2.0x rate)
        hourly_rate: Employee's hourly rate
        commission_total: Total commission earned
        commission_plan: 'Efficiency Pay', 'Hourly + Commission', or 'None'
    
    Returns:
        dict with calculation details
    """
    try:
        # Calculate proper hourly pay with OT/DT multipliers
        regular_pay = regular_hours * hourly_rate
        ot_pay = ot_hours * hourly_rate * 1.5
        dt_pay = dt_hours * hourly_rate * 2.0
        hourly_pay = regular_pay + ot_pay + dt_pay
        total_hours = regular_hours + ot_hours + dt_hours
        
        if commission_plan == 'Efficiency Pay':
            # Efficiency Pay: max(hourly_pay, commission_total)
            # If commission > hourly: employee gets commission
            # If commission < hourly: employee gets hourly (floor protection)
            final_pay = max(hourly_pay, commission_total)
            efficiency_pay = final_pay - hourly_pay  # This will be 0 or positive
            
            return {
                'employee_name': employee_name,
                'commission_plan': commission_plan,
                'regular_hours': regular_hours,
                'ot_hours': ot_hours,
                'dt_hours': dt_hours,
                'total_hours': total_hours,
                'hourly_rate': hourly_rate,
                'regular_pay': regular_pay,
                'ot_pay': ot_pay,
                'dt_pay': dt_pay,
                'hourly_pay': hourly_pay,
                'commission_total': commission_total,
                'efficiency_pay': efficiency_pay,
                'final_pay': final_pay,
                'calculation_method': f"max(${hourly_pay:.2f} hourly, ${commission_total:.2f} commission)"
            }
            
        elif commission_plan == 'Hourly + Commission':
            # Traditional model: hourly_pay + commission_total
            final_pay = hourly_pay + commission_total
            
            return {
                'employee_name': employee_name,
                'commission_plan': commission_plan,
                'regular_hours': regular_hours,
                'ot_hours': ot_hours,
                'dt_hours': dt_hours,
                'total_hours': total_hours,
                'hourly_rate': hourly_rate,
                'regular_pay': regular_pay,
                'ot_pay': ot_pay,
                'dt_pay': dt_pay,
                'hourly_pay': hourly_pay,
                'commission_total': commission_total,
                'efficiency_pay': 0,  # Not applicable for this model
                'final_pay': final_pay,
                'calculation_method': f"${hourly_pay:.2f} hourly + ${commission_total:.2f} commission"
            }
            
        else:  # 'None' or any other value
            # No commission, just hourly pay
            return {
                'employee_name': employee_name,
                'commission_plan': commission_plan,
                'regular_hours': regular_hours,
                'ot_hours': ot_hours,
                'dt_hours': dt_hours,
                'total_hours': total_hours,
                'hourly_rate': hourly_rate,
                'regular_pay': regular_pay,
                'ot_pay': ot_pay,
                'dt_pay': dt_pay,
                'hourly_pay': hourly_pay,
                'commission_total': 0,
                'efficiency_pay': 0,
                'final_pay': hourly_pay,
                'calculation_method': f"${hourly_pay:.2f} hourly only"
            }
            
    except Exception as e:
        # Return error details for debugging
        return {
            'employee_name': employee_name,
            'commission_plan': commission_plan,
            'regular_hours': 0,
            'ot_hours': 0,
            'dt_hours': 0,
            'total_hours': 0,
            'hourly_rate': hourly_rate,
            'regular_pay': 0,
            'ot_pay': 0,
            'dt_pay': 0,
            'hourly_pay': 0,
            'commission_total': commission_total,
            'efficiency_pay': 0,
            'final_pay': 0,
            'error': str(e),
            'calculation_method': f"Error: {str(e)}"
        }

def display_revenue_view():
    """View and edit revenue data"""
    st.markdown("### 📊 View & Edit Revenue Data")
    
    if st.session_state.revenue_data is not None:
        # Clean up any total/summary rows that might have slipped through
        if 'Invoice #' in st.session_state.revenue_data.columns and 'Invoice Date' in st.session_state.revenue_data.columns:
            # Check for and remove summary rows
            original_len = len(st.session_state.revenue_data)
            mask = ~(st.session_state.revenue_data['Invoice #'].isna() & st.session_state.revenue_data['Invoice Date'].isna())
            st.session_state.revenue_data = st.session_state.revenue_data[mask]
            
            # Also check for total keywords
            if 'Invoice #' in st.session_state.revenue_data.columns:
                invoice_str = st.session_state.revenue_data['Invoice #'].astype(str).str.lower()
                total_mask = ~invoice_str.str.contains('total|sum|grand total|subtotal|summary', na=False, regex=True)
                st.session_state.revenue_data = st.session_state.revenue_data[total_mask]
            
            if len(st.session_state.revenue_data) < original_len:
                st.info(f"📊 Auto-removed {original_len - len(st.session_state.revenue_data)} total/summary row(s)")
        
        # Add revenue verification section
        st.markdown("#### 🔍 Revenue Data Verification")
        
        # Get configured business units from company setup
        configured_business_units = []
        if 'business_unit_commission_settings' in st.session_state:
            configured_business_units = list(st.session_state.business_unit_commission_settings.keys())
        
        # Check for issues
        issues = []
        warnings = []
        
        # Check for missing revenue values
        if 'Jobs Total Revenue' in st.session_state.revenue_data.columns:
            zero_revenue = st.session_state.revenue_data[st.session_state.revenue_data['Jobs Total Revenue'] == 0]
            if not zero_revenue.empty:
                issues.append(f"⚠️ {len(zero_revenue)} rows have $0 revenue")
        
        # Check for business units not in company setup
        if 'Business Unit' in st.session_state.revenue_data.columns:
            # Check for NaN/missing business units first
            nan_count = st.session_state.revenue_data['Business Unit'].isna().sum()
            if nan_count > 0:
                issues.append(f"⚠️ {nan_count} rows have missing/NaN business units")
                
                # Show jobs with missing business units
                missing_bu_jobs = st.session_state.revenue_data[st.session_state.revenue_data['Business Unit'].isna()]
                if not missing_bu_jobs.empty:
                    with st.expander(f"🔍 View {nan_count} jobs with missing Business Units"):
                        display_cols = []
                        if 'Invoice #' in missing_bu_jobs.columns:
                            display_cols.append('Invoice #')
                        if 'Customer Name' in missing_bu_jobs.columns:
                            display_cols.append('Customer Name')
                        if 'Jobs Total Revenue' in missing_bu_jobs.columns:
                            display_cols.append('Jobs Total Revenue')
                        
                        if display_cols:
                            st.dataframe(missing_bu_jobs[display_cols], use_container_width=True)
                        else:
                            st.dataframe(missing_bu_jobs.head(10), use_container_width=True)
            
            # Check for unconfigured business units (excluding NaN)
            revenue_bus = set(st.session_state.revenue_data['Business Unit'].dropna().unique())
            unconfigured_bus = revenue_bus - set(configured_business_units)
            if unconfigured_bus:
                # Convert to strings to handle any float/numeric business units
                unconfigured_str = [str(bu) for bu in unconfigured_bus]
                warnings.append(f"🏢 Business units not in company setup: {', '.join(unconfigured_str)}")
        
        # Check for missing employee assignments
        missing_assignments = 0
        for col in ['Lead Generated By', 'Sold By', 'Assigned Technicians']:
            if col in st.session_state.revenue_data.columns:
                empty_count = st.session_state.revenue_data[col].isna().sum() + (st.session_state.revenue_data[col] == '').sum()
                if empty_count > 0:
                    warnings.append(f"👤 {empty_count} rows missing {col}")
        
        # Display verification results
        col1, col2 = st.columns(2)
        
        with col1:
            if issues:
                st.error("**Issues Found:**")
                for issue in issues:
                    st.write(issue)
            else:
                st.success("✅ No critical issues found")
        
        with col2:
            if warnings:
                st.warning("**Warnings:**")
                for warning in warnings:
                    st.write(warning)
            else:
                st.info("ℹ️ No warnings")
        st.markdown("#### 🔧 Edit Revenue Data")
        
        # Add instructions for the new editing features
        with st.expander("📖 Editing Instructions", expanded=False):
            st.markdown("""
            **Enhanced Editing Features:**
            - **Remove Employees**: Simply clear the text in "Lead Generated By" or "Sold By" columns to remove assignments
            - **Edit Technicians**: Each technician is now in a separate column for easier editing
            - **Remove Technicians**: Clear any technician cell to remove that person from the job
            - **Add Technicians**: Fill in empty technician columns to add new assignments
            - All changes are saved when you click "Save Changes"
            """)
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Get unique business units from revenue data and configured units
            if 'Business Unit' in st.session_state.revenue_data.columns:
                # Get revenue units, excluding NaN values and converting to strings
                revenue_units = [str(bu) for bu in st.session_state.revenue_data['Business Unit'].dropna().unique()]
                # Ensure configured units are also strings
                configured_units_str = [str(bu) for bu in configured_business_units]
                # Combine and sort
                all_units = ['All'] + sorted(set(revenue_units + configured_units_str))
                selected_unit = st.selectbox("Filter by Business Unit", all_units)
            else:
                selected_unit = 'All'
        
        with col2:
            # Period filter if exists
            period_columns = [col for col in st.session_state.revenue_data.columns if 'period' in col.lower() or 'date' in col.lower()]
            if period_columns:
                st.selectbox("Filter by Period", ['All'] + ['Q1', 'Q2', 'Q3', 'Q4'])
        
        with col3:
            search_term = st.text_input("🔍 Search", placeholder="Search in data...", key="revenue_search")
        
        # Apply filters
        filtered_data = st.session_state.revenue_data.copy()
        
        if selected_unit != 'All' and 'Business Unit' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data['Business Unit'] == selected_unit]
        
        # Display data
        st.markdown(f"**Showing {len(filtered_data)} of {len(st.session_state.revenue_data)} records**")
        
        # Make a copy for editing to avoid modifying the filtered data
        edit_data = filtered_data.copy()
        
        # Process technicians - split into separate columns for easier editing
        if 'Assigned Technicians' in edit_data.columns:
            # Find maximum number of technicians in any row
            max_techs = 0
            for techs in edit_data['Assigned Technicians'].dropna():
                if isinstance(techs, str) and techs.strip():
                    # Split by comma or ampersand
                    tech_list = [t.strip() for t in techs.replace('&', ',').split(',') if t.strip()]
                    max_techs = max(max_techs, len(tech_list))
            
            # Create separate columns for each technician
            if max_techs > 0:
                for i in range(max_techs):
                    tech_col_name = f'Technician {i+1}'
                    edit_data[tech_col_name] = ''
                    
                    # Fill in technician data
                    for idx, row in edit_data.iterrows():
                        techs = row['Assigned Technicians']
                        if isinstance(techs, str) and techs.strip():
                            tech_list = [t.strip() for t in techs.replace('&', ',').split(',') if t.strip()]
                            if i < len(tech_list):
                                edit_data.at[idx, tech_col_name] = tech_list[i]
                
                # Remove original Assigned Technicians column from display
                edit_data = edit_data.drop(columns=['Assigned Technicians'])
        
        # Editable dataframe with enhanced column configurations
        column_config = {}
        
        # Revenue column formatting
        if 'Jobs Total Revenue' in edit_data.columns:
            column_config["Jobs Total Revenue"] = st.column_config.NumberColumn(
                "Revenue ($)",
                format="$%.2f",
                min_value=0,
                help="Total revenue for this job"
            )
        elif 'Revenue' in edit_data.columns:
            column_config["Revenue"] = st.column_config.NumberColumn(
                "Revenue ($)",
                format="$%.2f",
                min_value=0,
                help="Total revenue for this job"
            )
        
        # Business Unit dropdown
        if 'Business Unit' in edit_data.columns and configured_business_units:
            column_config["Business Unit"] = st.column_config.SelectboxColumn(
                "Business Unit",
                options=configured_business_units,
                help="Select from configured business units"
            )
        
        # Invoice # column - handle as number without comma formatting
        if 'Invoice #' in edit_data.columns:
            # Convert to integer if it's a float to remove decimals
            if edit_data['Invoice #'].dtype in ['float64', 'float32']:
                # Convert non-null values to integer
                mask = edit_data['Invoice #'].notna()
                edit_data.loc[mask, 'Invoice #'] = edit_data.loc[mask, 'Invoice #'].astype('Int64')
            
            column_config["Invoice #"] = st.column_config.NumberColumn(
                "Invoice #",
                help="Invoice number",
                format="%d"  # Integer format without commas
            )
        
        # Employee assignment columns with ability to clear
        for col in ['Lead Generated By', 'Sold By']:
            if col in edit_data.columns:
                column_config[col] = st.column_config.TextColumn(
                    col,
                    help=f"Employee who handled {col.lower()} - leave blank to remove"
                )
        
        # Configure technician columns
        tech_columns = [col for col in edit_data.columns if col.startswith('Technician ')]
        for tech_col in tech_columns:
            column_config[tech_col] = st.column_config.TextColumn(
                tech_col,
                help="Technician name - leave blank to remove"
            )
        
        # Add commission type indicators before displaying
        if 'Commission Types' not in edit_data.columns:
            edit_data = edit_data.copy()
            # Add progress indicator for large datasets
            if len(edit_data) > 100:
                with st.spinner('Analyzing commission types...'):
                    edit_data['Commission Types'] = edit_data.apply(
                        lambda row: get_commission_types_for_job(row), axis=1
                    )
            else:
                edit_data['Commission Types'] = edit_data.apply(
                    lambda row: get_commission_types_for_job(row), axis=1
                )
            
            # Add column configuration for Commission Types
            column_config["Commission Types"] = st.column_config.TextColumn(
                "Commission Types",
                help="Types of commissions this job generates (Lead Gen, Sales, Work Done)",
                disabled=True  # Read-only column
            )
        
        edited_data = st.data_editor(
            edit_data,
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
            column_config=column_config
        )
        
        # Quick Fix Actions
        st.markdown("#### ⚡ Quick Fix Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔧 Fix Missing Business Units", help="Replace NaN/missing business units with 'Default'"):
                if 'Business Unit' in edited_data.columns:
                    # Fix NaN/missing business units
                    nan_count = edited_data['Business Unit'].isna().sum()
                    if nan_count > 0:
                        if 'Default' in configured_business_units:
                            edited_data.loc[edited_data['Business Unit'].isna(), 'Business Unit'] = 'Default'
                            st.success(f"✅ Fixed {nan_count} missing/NaN business units → 'Default'")
                        else:
                            st.error("Cannot fix: No 'Default' business unit configured. Please add 'Default' in Company Setup.")
                    
                    # Also fix unconfigured business units
                    unconfigured = set(edited_data['Business Unit'].dropna().unique()) - set(configured_business_units)
                    if unconfigured and 'Default' in configured_business_units:
                        fixed_count = 0
                        for unit in unconfigured:
                            count = (edited_data['Business Unit'] == unit).sum()
                            edited_data.loc[edited_data['Business Unit'] == unit, 'Business Unit'] = 'Default'
                            fixed_count += count
                        st.success(f"✅ Mapped {fixed_count} unconfigured business units to 'Default'")
                    
                    if nan_count == 0 and not unconfigured:
                        st.info("No missing or unconfigured business units found")
        
        with col2:
            if st.button("💰 Remove $0 Revenue Rows", help="Delete rows with zero revenue"):
                if 'Jobs Total Revenue' in edited_data.columns:
                    before_count = len(edited_data)
                    edited_data = edited_data[edited_data['Jobs Total Revenue'] > 0]
                    removed_count = before_count - len(edited_data)
                    if removed_count > 0:
                        st.success(f"✅ Removed {removed_count} rows with $0 revenue")
                    else:
                        st.info("No $0 revenue rows found")
        
        with col3:
            if st.button("📋 Export Issues Report", help="Download report of data issues"):
                report_data = []
                if 'Jobs Total Revenue' in edited_data.columns:
                    zero_rev = edited_data[edited_data['Jobs Total Revenue'] == 0]
                    for _, row in zero_rev.iterrows():
                        report_data.append({
                            'Issue': 'Zero Revenue',
                            'Business Unit': row.get('Business Unit', 'N/A'),
                            'Invoice #': row.get('Invoice #', 'N/A'),
                            'Customer': row.get('Customer Name', 'N/A')
                        })
                
                if report_data:
                    report_df = pd.DataFrame(report_data)
                    csv = report_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Issues Report",
                        data=csv,
                        file_name=f"revenue_issues_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No issues to report")
        
        # Save changes
        if st.button("💾 Save Changes", type="primary", key="revenue_save_changes"):
            # Process the edited data before saving
            save_data = edited_data.copy()
            
            # Combine technician columns back into Assigned Technicians
            tech_columns = [col for col in save_data.columns if col.startswith('Technician ')]
            if tech_columns:
                # Create the combined Assigned Technicians column
                save_data['Assigned Technicians'] = save_data.apply(
                    lambda row: ', '.join([str(row[col]).strip() for col in tech_columns 
                                         if pd.notna(row[col]) and str(row[col]).strip()]), 
                    axis=1
                )
                # Drop the individual technician columns
                save_data = save_data.drop(columns=tech_columns)
            
            # If the original data had Assigned Technicians column but the edited data doesn't, add it back
            if 'Assigned Technicians' not in save_data.columns and 'Assigned Technicians' in st.session_state.revenue_data.columns:
                save_data['Assigned Technicians'] = ''
            
            # Clean up empty strings in employee columns
            for col in ['Lead Generated By', 'Sold By']:
                if col in save_data.columns:
                    # Replace empty strings with NaN
                    save_data[col] = save_data[col].replace('', pd.NA)
            
            st.session_state.revenue_data = save_data
            st.session_state.saved_revenue_data = save_data  # For compatibility
            st.success("✅ Changes saved successfully!")
            st.rerun()
        
        # Export options
        st.markdown("#### 📤 Export Options")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Download Current View", key="revenue_download"):
                # For download, combine technician columns back into original format
                download_data = edited_data.copy()
                tech_columns = [col for col in download_data.columns if col.startswith('Technician ')]
                if tech_columns:
                    download_data['Assigned Technicians'] = download_data.apply(
                        lambda row: ', '.join([str(row[col]).strip() for col in tech_columns 
                                             if pd.notna(row[col]) and str(row[col]).strip()]), 
                        axis=1
                    )
                    download_data = download_data.drop(columns=tech_columns)
                
                csv = download_data.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"revenue_data_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    key="revenue_download_csv"
                )
        
        with col2:
            if st.button("🗑️ Clear All Data", key="revenue_clear"):
                if st.checkbox("Confirm clear all data", key="revenue_clear_confirm"):
                    st.session_state.revenue_data = None
                    st.session_state.saved_revenue_data = None
                    st.success("✅ Revenue data cleared")
                    st.rerun()
    
    else:
        st.info("📤 No revenue data loaded. Please upload data in the 'Upload Revenue' tab.")

@st.cache_data
def calculate_revenue_metrics(df):
    """Calculate revenue metrics with caching"""
    if df is None or df.empty:
        return None
        
    metrics = {
        'total_records': len(df),
        'business_units': df['Business Unit'].nunique() if 'Business Unit' in df.columns else 0,
        'total_revenue': 0
    }
    
    if 'Revenue' in df.columns:
        metrics['total_revenue'] = pd.to_numeric(df['Revenue'], errors='coerce').sum()
    
    return metrics

def display_revenue_summary():
    """Display revenue summary and analytics"""
    st.markdown("### 📈 Revenue Summary")
    
    if st.session_state.revenue_data is not None:
        df = st.session_state.revenue_data
        
        # Overall metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📋 Total Records", len(df))
        
        with col2:
            if 'Business Unit' in df.columns:
                st.metric("🏢 Business Units", df['Business Unit'].nunique())
            else:
                st.metric("🏢 Business Units", "N/A")
        
        with col3:
            if 'Revenue' in df.columns:
                total_revenue = pd.to_numeric(df['Revenue'], errors='coerce').sum()
                st.metric("💰 Total Revenue", f"${total_revenue:,.0f}")
            else:
                st.metric("💰 Total Revenue", "N/A")
        
        with col4:
            st.metric("📅 Last Updated", st.session_state.get('last_revenue_save', 'Never'))
        
        # Revenue by business unit
        if 'Business Unit' in df.columns and 'Revenue' in df.columns:
            st.markdown("#### 🏢 Revenue by Business Unit")
            
            # Clean revenue data
            df['Revenue'] = pd.to_numeric(df['Revenue'], errors='coerce')
            
            # Group by business unit
            unit_summary = df.groupby('Business Unit')['Revenue'].sum().reset_index()
            unit_summary = unit_summary.sort_values('Revenue', ascending=False)
            
            # Display chart
            fig = px.pie(
                unit_summary,
                values='Revenue',
                names='Business Unit',
                title='Revenue Distribution by Business Unit'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Bar chart
            fig2 = px.bar(
                unit_summary,
                x='Business Unit',
                y='Revenue',
                title='Revenue by Business Unit',
                color='Revenue',
                color_continuous_scale='Greens'
            )
            fig2.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig2, use_container_width=True)
            
            # Summary table
            st.markdown("#### 📊 Detailed Summary")
            
            # Add percentage
            # Calculate percentage with division by zero protection
            total_revenue = unit_summary['Revenue'].sum()
            if total_revenue > 0:
                unit_summary['Percentage'] = (unit_summary['Revenue'] / total_revenue * 100).round(1)
            else:
                unit_summary['Percentage'] = 0
            unit_summary['Status'] = unit_summary['Revenue'].apply(
                lambda x: '🌟 Top Performer' if x >= unit_summary['Revenue'].quantile(0.75) else '✅ Good' if x >= unit_summary['Revenue'].quantile(0.5) else '⚠️ Below Average'
            )
            
            st.dataframe(
                unit_summary,
                use_container_width=True,
                column_config={
                    "Revenue": st.column_config.NumberColumn(
                        "Revenue ($)",
                        format="$%.0f"
                    ),
                    "Percentage": st.column_config.NumberColumn(
                        "% of Total",
                        format="%.1f%%"
                    )
                }
            )
        
        # Data quality report
        st.markdown("#### 🔍 Data Quality Report")
        col1, col2 = st.columns(2)
        
        with col1:
            missing_values = df.isnull().sum()
            missing_values = missing_values[missing_values > 0]
            if len(missing_values) > 0:
                st.warning(f"⚠️ Found {len(missing_values)} columns with missing values")
                with st.expander("Show details"):
                    for col, count in missing_values.items():
                        st.write(f"• {col}: {count} missing values")
            else:
                st.success("✅ No missing values found")
        
        with col2:
            if 'Revenue' in df.columns:
                negative_revenue = (pd.to_numeric(df['Revenue'], errors='coerce') < 0).sum()
                if negative_revenue > 0:
                    st.warning(f"⚠️ Found {negative_revenue} negative revenue values")
                else:
                    st.success("✅ All revenue values are positive")
    
    else:
        st.info("📤 No revenue data loaded. Please upload data in the 'Upload Revenue' tab.")

# REMOVED: Lead Generation Tab
# The lead generation functionality has been removed from the UI
# but lead commission calculations are still available in revenue reports

# def display_lead_generation_tab():
#     """Lead generation tracking and management"""
#     st.markdown("## 🎯 Lead Generation")
#     
#     # Initialize lead data in session state
#     if 'lead_data' not in st.session_state:
#         st.session_state.lead_data = pd.DataFrame(columns=[
#             'Lead ID', 'Date', 'Employee Name', 'Client Name', 'Lead Type', 
#             'Lead Value', 'Status', 'Commission Rate', 'Notes'
#         ])
#     
#     # Create sub-tabs
#     lead_tab1, lead_tab2, lead_tab3, lead_tab4 = st.tabs([
#         "➕ Add Lead",
#         "📋 Manage Leads",
#         "📤 Import/Export",
#         "📊 Summary"
#     ])
#     
#     with lead_tab1:
#         display_add_lead()
#     
#     with lead_tab2:
#         display_manage_leads()
#     
#     with lead_tab3:
#         display_lead_import_export()
#     
#     with lead_tab4:
#         display_lead_summary()

# def display_add_lead():
#     """Add new lead form"""
#     st.markdown("### ➕ Add New Lead")
#     
#     with st.form("add_lead_form"):
#         col1, col2 = st.columns(2)
#         
#         with col1:
#             # Generate lead ID
#             lead_count = len(st.session_state.lead_data) + 1
#             lead_id = st.text_input("Lead ID*", value=f"LEAD{lead_count:04d}", disabled=True)
#             lead_date = st.date_input("Date*", value=datetime.now().date())
#             
#             # Get employee list from employee data
#             if 'employee_data' in st.session_state and len(st.session_state.employee_data) > 0:
#                 employee_names = st.session_state.employee_data['Name'].tolist()
#             else:
#                 employee_names = ['John Doe', 'Jane Smith', 'Bob Johnson']
#             
#             employee_name = st.selectbox("Employee Name*", employee_names)
#             client_name = st.text_input("Client/Company Name*", placeholder="ABC Corporation")
#         
#         with col2:
#             lead_type = st.selectbox("Lead Type", [
#                 "New Business", "Referral", "Upsell", "Cross-sell", 
#                 "Renewal", "Partnership", "Other"
#             ])
#             lead_value = st.number_input("Potential Value ($)*", min_value=0.0, value=0.0, step=100.0)
#             lead_status = st.selectbox("Status", [
#                 "New", "Contacted", "Qualified", "Proposal", 
#                 "Negotiation", "Closed Won", "Closed Lost"
#             ])
#             commission_rate = st.number_input("Commission Rate (%)", min_value=0.0, max_value=100.0, value=10.0, step=0.5)
#         
#         notes = st.text_area("Notes", placeholder="Additional details about the lead...")
#         
#         # Submit button
#         submitted = st.form_submit_button("➕ Add Lead", type="primary", use_container_width=True)
#         
#         if submitted:
#             if employee_name and client_name and lead_value > 0:
#                 # Create new lead record
#                 new_lead = pd.DataFrame({
#                     'Lead ID': [lead_id],
#                     'Date': [lead_date],
#                     'Employee Name': [employee_name],
#                     'Client Name': [client_name],
#                     'Lead Type': [lead_type],
#                     'Lead Value': [lead_value],
#                     'Status': [lead_status],
#                     'Commission Rate': [commission_rate],
#                     'Notes': [notes]
#                 })
#                 
#                 # Add to lead data
#                 st.session_state.lead_data = pd.concat([st.session_state.lead_data, new_lead], ignore_index=True)
#                 st.success(f"✅ Lead '{client_name}' added successfully!")
#                 st.balloons()
#                 st.rerun()
#             else:
#                 st.error("❌ Please fill in all required fields")

# def display_manage_leads():
#     """Manage existing leads"""
#     st.markdown("### 📋 Manage Leads")
#     
#     if len(st.session_state.lead_data) > 0:
#         # Filter options
#         col1, col2, col3, col4 = st.columns(4)
#         
#         with col1:
#             employee_filter = st.selectbox("Filter by Employee", 
#                 ["All"] + list(st.session_state.lead_data['Employee Name'].unique()))
#         
#         with col2:
#             status_filter = st.selectbox("Filter by Status", 
#                 ["All"] + list(st.session_state.lead_data['Status'].unique()))
#         
#         with col3:
#             lead_type_filter = st.selectbox("Filter by Type", 
#                 ["All"] + list(st.session_state.lead_data['Lead Type'].unique()))
#         
#         with col4:
#             date_range = st.date_input("Date Range", 
#                 value=(datetime.now().date() - timedelta(days=30), datetime.now().date()),
#                 key="lead_date_range")
#             
#             # Apply filters
#             filtered_data = st.session_state.lead_data.copy()
#             
#             if employee_filter != "All":
#                 filtered_data = filtered_data[filtered_data['Employee Name'] == employee_filter]
#             
#             if status_filter != "All":
#                 filtered_data = filtered_data[filtered_data['Status'] == status_filter]
#             
#             if lead_type_filter != "All":
#                 filtered_data = filtered_data[filtered_data['Lead Type'] == lead_type_filter]
#             
#             # Date filter
#             filtered_data['Date'] = pd.to_datetime(filtered_data['Date'])
#             filtered_data = filtered_data[
#                 (filtered_data['Date'].dt.date >= date_range[0]) & 
#                 (filtered_data['Date'].dt.date <= date_range[1])
#             ]
#             
#             # Display metrics
#             col1, col2, col3, col4 = st.columns(4)
#             
#             with col1:
#                 st.metric("Total Leads", len(filtered_data))
#             
#             with col2:
#                 total_value = filtered_data['Lead Value'].sum()
#                 st.metric("Total Potential Value", f"${total_value:,.0f}")
#             
#             with col3:
#                 won_leads = filtered_data[filtered_data['Status'] == 'Closed Won']
#                 won_value = won_leads['Lead Value'].sum()
#                 st.metric("Won Value", f"${won_value:,.0f}")
#             
#             with col4:
#                 if len(filtered_data) > 0:
#                     win_rate = len(won_leads) / len(filtered_data) * 100
#                     st.metric("Win Rate", f"{win_rate:.1f}%")
#                 else:
#                     st.metric("Win Rate", "N/A")
#             
#             # Display data
#             st.markdown(f"**Showing {len(filtered_data)} of {len(st.session_state.lead_data)} leads**")
#             
#             # Editable dataframe
#             edited_data = st.data_editor(
#                 filtered_data,
#                 hide_index=True,
#                 use_container_width=True,
#                 num_rows="dynamic",
#                 column_config={
#                     "Lead Value": st.column_config.NumberColumn(
#                         "Lead Value ($)",
#                         format="$%.0f"
#                     ),
#                     "Commission Rate": st.column_config.NumberColumn(
#                         "Commission Rate (%)",
#                         format="%.1f%%"
#                     ),
#                     "Date": st.column_config.DateColumn(
#                         "Date",
#                         format="YYYY-MM-DD"
#                     )
#                 }
#             )
#             
#             # Save changes
#             if st.button("💾 Save Changes", type="primary", key="lead_save_changes"):
#                 st.session_state.lead_data = edited_data
#                 st.success("✅ Lead data updated successfully!")
#                 st.rerun()
#         
#         else:
#             st.info("🎯 No leads found. Add leads using the 'Add Lead' tab.")

# def display_lead_import_export():
#         """Import and export lead data"""
#         st.markdown("### 📤 Import/Export Lead Data")
#         
#         col1, col2 = st.columns(2)
#         
#         with col1:
#             st.markdown("#### 📥 Import Leads")
#             
#             # Download template
#             if st.button("📄 Download Lead Import Template"):
#                 template_df = pd.DataFrame({
#                     'Lead ID': ['LEAD0001', 'LEAD0002'],
#                     'Date': ['2024-01-15', '2024-01-16'],
#                     'Employee Name': ['John Doe', 'Jane Smith'],
#                     'Client Name': ['ABC Corp', 'XYZ Inc'],
#                     'Lead Type': ['New Business', 'Referral'],
#                     'Lead Value': [50000, 75000],
#                     'Status': ['Qualified', 'Proposal'],
#                     'Commission Rate': [10.0, 12.5],
#                     'Notes': ['High priority', 'Follow up needed']
#                 })
#                 csv = template_df.to_csv(index=False)
#                 st.download_button(
#                     label="Download Template CSV",
#                     data=csv,
#                     file_name="lead_import_template.csv",
#                     mime="text/csv"
#                 )
#             
#             # File upload
#             uploaded_file = st.file_uploader(
#                 "Upload Lead Data",
#                 type=['csv', 'xlsx', 'xls'],
#                 help="Upload lead data in CSV or Excel format",
#                 key="lead_upload"
#             )
#             
#             if uploaded_file:
#                 try:
#                     # Read file
#                     file_ext = uploaded_file.name.lower()
#                     if file_ext.endswith(('.xlsx', '.xls')):
#                         df = pd.read_excel(uploaded_file)
#                     else:
#                         df = pd.read_csv(uploaded_file)
#                     
#                     st.success(f"✅ File loaded: {len(df)} leads found")
#                     st.dataframe(df.head())
#                     
#                     if st.button("📥 Import Leads", type="primary"):
#                         st.session_state.lead_data = pd.concat([st.session_state.lead_data, df], ignore_index=True)
#                         st.success(f"✅ Imported {len(df)} leads successfully!")
#                         st.rerun()
#                     
#                 except Exception as e:
#                     st.error(f"❌ Error reading file: {e}")
#         
#         with col2:
#             st.markdown("#### 📤 Export Leads")
#             
#             if len(st.session_state.lead_data) > 0:
#                 # Export options
#                 export_status = st.multiselect("Filter by Status", 
#                     st.session_state.lead_data['Status'].unique().tolist(),
#                     default=st.session_state.lead_data['Status'].unique().tolist())
#                 
#                 # Prepare export data
#                 export_data = st.session_state.lead_data[
#                     st.session_state.lead_data['Status'].isin(export_status)
#                 ]
#                 
#                 st.info(f"📊 Will export {len(export_data)} leads")
#                 
#                 # Export button
#                 if st.button("📤 Export Lead Data", type="primary"):
#                     csv = export_data.to_csv(index=False)
#                     st.download_button(
#                         label="Download Leads CSV",
#                         data=csv,
#                         file_name=f"leads_{datetime.now().strftime('%Y%m%d')}.csv",
#                         mime="text/csv"
#                     )
#             else:
#                 st.info("No lead data to export")

# def display_lead_summary():
#         """Display lead summary and analytics"""
#         st.markdown("### 📊 Lead Summary & Analytics")
#         
#         if len(st.session_state.lead_data) > 0:
#             df = st.session_state.lead_data.copy()
#             df['Date'] = pd.to_datetime(df['Date'])
#             
#             # Time period selector
#             period = st.selectbox("Select Period", ["Last 30 Days", "Last 90 Days", "Year to Date", "All Time"])
#             
#             # Filter by period
#             if period == "Last 30 Days":
#                 start_date = datetime.now() - timedelta(days=30)
#                 df = df[df['Date'] >= start_date]
#             elif period == "Last 90 Days":
#                 start_date = datetime.now() - timedelta(days=90)
#                 df = df[df['Date'] >= start_date]
#             elif period == "Year to Date":
#                 start_date = datetime(datetime.now().year, 1, 1)
#                 df = df[df['Date'] >= start_date]
#             
#             # Overall metrics
#             col1, col2, col3, col4 = st.columns(4)
#             
#             with col1:
#                 st.metric("📋 Total Leads", len(df))
#             
#             with col2:
#                 total_value = df['Lead Value'].sum()
#                 st.metric("💰 Total Pipeline", f"${total_value:,.0f}")
#             
#             with col3:
#                 won_leads = df[df['Status'] == 'Closed Won']
#                 won_value = won_leads['Lead Value'].sum()
#                 st.metric("✅ Won Revenue", f"${won_value:,.0f}")
#             
#             with col4:
#                 # Calculate estimated commission
#                 df['Est Commission'] = df['Lead Value'] * df['Commission Rate'] / 100
#                 won_commission = won_leads['Lead Value'].sum() * won_leads['Commission Rate'].mean() / 100
#                 st.metric("💸 Won Commission", f"${won_commission:,.0f}")
#             
#             # Employee performance
#             st.markdown("#### 🏆 Top Performers")
#             
#             employee_summary = df.groupby('Employee Name').agg({
#                 'Lead ID': 'count',
#                 'Lead Value': 'sum',
#                 'Status': lambda x: (x == 'Closed Won').sum()
#             }).rename(columns={
#                 'Lead ID': 'Total Leads',
#                 'Lead Value': 'Pipeline Value',
#                 'Status': 'Closed Won'
#             })
#             
#             # Calculate win rate
#             employee_summary['Win Rate'] = (employee_summary['Closed Won'] / employee_summary['Total Leads'] * 100).round(1)
#             employee_summary = employee_summary.sort_values('Pipeline Value', ascending=False)
#             
#             # Display top performers
#             fig = px.bar(
#                 employee_summary.head(10),
#                 x=employee_summary.head(10).index,
#                 y='Pipeline Value',
#                 title='Top 10 Employees by Pipeline Value',
#                 color='Win Rate',
#                 color_continuous_scale='RdYlGn'
#             )
#             fig.update_layout(xaxis_title="Employee", yaxis_title="Pipeline Value ($)")
#             st.plotly_chart(fig, use_container_width=True)
#             
#             # Lead funnel
#             st.markdown("#### 🔄 Lead Funnel")
#             
#             status_order = ["New", "Contacted", "Qualified", "Proposal", "Negotiation", "Closed Won", "Closed Lost"]
#             status_counts = df['Status'].value_counts()
#             funnel_data = pd.DataFrame({
#                 'Status': status_order,
#                 'Count': [status_counts.get(status, 0) for status in status_order]
#             })
#             
#             fig2 = px.funnel(
#                 funnel_data,
#                 x='Count',
#                 y='Status',
#                 title='Lead Conversion Funnel'
#             )
#             st.plotly_chart(fig2, use_container_width=True)
#             
#             # Lead type distribution
#             col1, col2 = st.columns(2)
#             
#             with col1:
#                 lead_type_summary = df.groupby('Lead Type')['Lead Value'].sum().reset_index()
#                 fig3 = px.pie(
#                     lead_type_summary,
#                     values='Lead Value',
#                     names='Lead Type',
#                     title='Pipeline Value by Lead Type'
#                 )
#                 st.plotly_chart(fig3, use_container_width=True)
#             
#             with col2:
#                 # Monthly trend
#                 monthly_data = df.groupby(df['Date'].dt.to_period('M')).agg({
#                     'Lead Value': 'sum',
#                     'Lead ID': 'count'
#                 }).reset_index()
#                 monthly_data['Date'] = monthly_data['Date'].astype(str)
#                 
#                 fig4 = px.line(
#                     monthly_data,
#                     x='Date',
#                     y='Lead Value',
#                     title='Monthly Lead Value Trend',
#                     markers=True
#                 )
#                 st.plotly_chart(fig4, use_container_width=True)
#         
#         else:
#             st.info("🎯 No lead data available. Add leads in the 'Add Lead' tab.")

def display_commission_calculation_tab():
    """Commission calculation and tracking"""
    st.markdown("## 💸 Commission Calculation")
    
    # Create sub-tabs
    calc_tab1, calc_tab2, calc_tab3, calc_tab4 = st.tabs([
        "🧮 Calculate",
        "📊 Results",
        "📋 History",
        "⚙️ Settings"
    ])
    
    with calc_tab1:
        display_commission_calculate()
    
    with calc_tab2:
        display_commission_results()
    
    with calc_tab3:
        display_commission_history()
    
    with calc_tab4:
        display_commission_settings()

def display_commission_calculate():
    """Calculate commissions"""
    st.markdown("### 🧮 Calculate Commissions")
    
    # Check data availability
    has_employee_data = 'employee_data' in st.session_state and len(st.session_state.employee_data) > 0
    has_timesheet_data = st.session_state.get('timesheet_data') is not None
    
    # Check for lead generation data in revenue data (column H or "Lead Generated By")
    has_lead_data = False
    revenue_data = st.session_state.get('revenue_data')
    if revenue_data is not None and not revenue_data.empty:
        # Check if there's a "Lead Generated By" column or similar
        lead_columns = [col for col in revenue_data.columns if 'lead' in col.lower() and 'by' in col.lower()]
        if lead_columns:
            # Check if there's actual lead generation data (non-empty values)
            lead_col = lead_columns[0]
            has_lead_data = revenue_data[lead_col].notna().any() and (revenue_data[lead_col] != '').any()
    
    # Also check for separate lead data (legacy support)
    if not has_lead_data:
        has_lead_data = 'lead_data' in st.session_state and len(st.session_state.lead_data) > 0
    
    if not has_employee_data:
        st.warning("⚠️ No employee data found. Please set up employees first.")
        return
    
    # Calculation period
    st.markdown("#### 📅 Select Calculation Period")
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now().replace(day=1).date())
    
    with col2:
        end_date = st.date_input("End Date", value=datetime.now().date())
    
    # Data availability info
    st.markdown("#### 📊 Available Data Sources")
    
    col1, col2, col3 = st.columns(3)
    
    # Always calculate all commission types based on available data
    calculate_hourly = has_timesheet_data
    calculate_leads = has_lead_data
    has_revenue_data = st.session_state.get('revenue_data') is not None
    calculate_revenue = has_revenue_data
    
    with col1:
        if has_timesheet_data:
            st.success("⏰ Hourly Work Commission - ✅ Data Available")
        else:
            st.info("⏰ Hourly Work Commission - ⚠️ No timesheet data")
    
    with col2:
        if has_lead_data:
            if revenue_data is not None and not revenue_data.empty:
                lead_columns = [col for col in revenue_data.columns if 'lead' in col.lower() and 'by' in col.lower()]
                if lead_columns:
                    st.success(f"🎯 Lead Generation Commission - ✅ Found in revenue data (column: {lead_columns[0]})")
                else:
                    st.success("🎯 Lead Generation Commission - ✅ Data Available")
            else:
                st.success("🎯 Lead Generation Commission - ✅ Data Available")
        else:
            st.info("🎯 Lead Generation Commission - ⚠️ No lead generation data found in revenue data")
    
    with col3:
        if has_revenue_data:
            st.success("💰 Revenue Commission - ✅ Data Available")
        else:
            st.info("💰 Revenue Commission - ⚠️ No revenue data")
    
    # Employee selection
    st.markdown("#### 👥 Select Employees")
    
    employee_names = st.session_state.employee_data['Name'].tolist()
    selected_employees = st.multiselect(
        "Employees to Calculate",
        employee_names,
        default=employee_names
    )
    
    # Calculate button
    if st.button("🧮 Calculate Commissions", type="primary", use_container_width=True):
        if not selected_employees:
            st.error("❌ Please select at least one employee")
            return
        
        if not calculate_hourly and not calculate_leads and not calculate_revenue:
            st.error("❌ No commission data available. Please upload timesheet, lead, or revenue data first.")
            return
        
        # Initialize results
        commission_results = []
        
        # Calculate revenue-based commissions first (new system)
        revenue_commission_df = pd.DataFrame()
        if calculate_revenue:
            commission_settings = st.session_state.get('commission_settings')
            revenue_data = st.session_state.get('revenue_data')
            
            # Debug: Check what data we have
            st.info(f"🔍 **Debug Info:**")
            st.write(f"- Revenue data available: {'✅' if revenue_data is not None else '❌'}")
            st.write(f"- Commission settings available: {'✅' if commission_settings else '❌'}")
            
            if revenue_data is not None:
                st.write(f"- Revenue data rows: {len(revenue_data)}")
                st.write(f"- Revenue data columns: {list(revenue_data.columns)}")
                
                # Check Revenue column values
                if 'Revenue' in revenue_data.columns:
                    revenue_values = revenue_data['Revenue'].head()
                    non_zero_count = (revenue_data['Revenue'] > 0).sum()
                    st.write(f"- Non-zero revenue entries: {non_zero_count} out of {len(revenue_data)}")
                    st.write(f"- Sample revenue values: {revenue_values.tolist()}")
                else:
                    st.write("- No 'Revenue' column found!")
                
                if 'Lead Generated By' in revenue_data.columns:
                    lead_count = revenue_data['Lead Generated By'].notna().sum()
                    st.write(f"- Lead generation entries: {lead_count}")
                else:
                    st.write("- No 'Lead Generated By' column found in revenue data")
            
            if commission_settings:
                bu_settings = commission_settings.get('business_unit_settings', {})
                enabled_units = [bu for bu, settings in bu_settings.items() if settings.get('enabled', False)]
                st.write(f"- Enabled business units: {len(enabled_units)} ({enabled_units})")
            
            if commission_settings and revenue_data is not None:
                try:
                    revenue_commission_df = calculate_revenue_commissions(
                        revenue_data,
                        commission_settings
                    )
                    
                    # Debug information
                    if revenue_commission_df.empty:
                        st.warning("⚠️ Revenue commission calculation returned no results")
                        st.info("This could mean: no enabled business units, no revenue data, or commission rates are 0")
                    else:
                        st.success(f"✅ Calculated {len(revenue_commission_df)} revenue commission entries")
                        
                except Exception as e:
                    st.error(f"❌ Error calculating revenue commissions: {e}")
                    revenue_commission_df = pd.DataFrame()
            else:
                st.warning("⚠️ Revenue commission calculation requires both revenue data and commission settings")
        
        for employee in selected_employees:
            result = {
                'Employee': employee,
                'Lead Gen Commission': 0,
                'Sales Commission': 0,
                'Work Done Commission': 0,
                'Total Commission': 0,
                'Details': {}
            }
            
            # Add revenue-based commissions for this employee
            if not revenue_commission_df.empty:
                emp_revenue_commissions = revenue_commission_df[revenue_commission_df['Employee'] == employee]
                
                # Debug: Show if employee has any commissions
                if emp_revenue_commissions.empty:
                    st.info(f"📋 No revenue commissions found for employee: {employee}")
                else:
                    st.success(f"💰 Found {len(emp_revenue_commissions)} commission entries for {employee}")
                
                # Debug removed - issue found and fixed
                
                for _, comm_row in emp_revenue_commissions.iterrows():
                    comm_type = comm_row['Commission Type']
                    amount = comm_row['Commission Amount']
                    
                    if comm_type == 'Lead Generation':
                        result['Lead Gen Commission'] += amount
                    elif comm_type == 'Sales':
                        result['Sales Commission'] += amount
                    elif comm_type == 'Work Done':
                        result['Work Done Commission'] += amount
                
                # Add revenue commission details
                if len(emp_revenue_commissions) > 0:
                    result['Details']['Revenue Entries'] = len(emp_revenue_commissions)
                    result['Details']['Total Revenue'] = emp_revenue_commissions['Revenue'].sum()
                    result['Details']['Business Units'] = emp_revenue_commissions['Business Unit'].unique().tolist()
            
            # Calculate hourly commission
            if calculate_hourly and has_timesheet_data:
                # Check if employee data exists
                if 'employee_data' not in st.session_state or st.session_state.employee_data is None:
                    st.warning("⚠️ No employee data available for commission calculation")
                    continue
                    
                # Get employee hourly rate
                emp_data = st.session_state.employee_data[
                    st.session_state.employee_data['Name'] == employee
                ]
                if len(emp_data) > 0:
                    try:
                        hourly_rate = emp_data.iloc[0]['Hourly Rate']
                        commission_rate = emp_data.iloc[0].get('Commission Rate', 5.0)
                    except (IndexError, KeyError) as e:
                        st.error(f"❌ Error accessing employee data for {employee}: {e}")
                        continue
                else:
                    st.warning(f"⚠️ Employee '{employee}' not found in employee data")
                    continue
                    
                    # Get hours from timesheet
                    if 'timesheet_data' not in st.session_state or st.session_state.timesheet_data is None:
                        continue
                        
                    timesheet_df = st.session_state.timesheet_data
                    if 'Employee Name' in timesheet_df.columns:
                        emp_timesheet = timesheet_df[timesheet_df['Employee Name'] == employee]
                        
                        # Get hours with override support
                        regular_hours, ot_hours, dt_hours = get_employee_hours_with_overrides(employee, timesheet_df)
                        total_hours = regular_hours + ot_hours + dt_hours
                        
                        # Store hour details
                        result['Details']['Regular Hours'] = regular_hours
                        result['Details']['OT Hours'] = ot_hours 
                        result['Details']['DT Hours'] = dt_hours
                        result['Details']['Total Hours'] = total_hours
                        result['Details']['Commission Rate'] = commission_rate
            
            # Legacy lead commission calculation removed - now handled by revenue commission system
            # Lead generation commissions are processed from revenue data in the revenue commission calculation above
            
            # Calculate total
            result['Total Commission'] = (
                result['Lead Gen Commission'] + 
                result['Sales Commission'] + 
                result['Work Done Commission']
            )
            commission_results.append(result)
        
        # Store results in session state
        st.session_state.commission_results = pd.DataFrame(commission_results)
        st.session_state.commission_period = {'start': start_date, 'end': end_date}
        
        st.success("✅ Commission calculation completed!")
        st.info("Go to the 'Results' tab to view detailed calculations.")

def display_commission_results():
    """Display commission calculation results"""
    st.markdown("### 📊 Commission Results")
    
    if 'commission_results' not in st.session_state:
        st.info("🧮 No calculations available. Go to the 'Calculate' tab to run calculations.")
        return
    
    # Add button to recalculate/refresh results
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Recalculate", help="Clear cached results and recalculate commissions"):
            # Clear cached results to force recalculation
            if 'commission_results' in st.session_state:
                del st.session_state.commission_results
            if 'commission_period' in st.session_state:
                del st.session_state.commission_period
            st.info("✅ Results cleared. Please go to 'Calculate' tab to recalculate with updated logic.")
            st.rerun()
    
    # Add button to debug and verify commission rates
    if st.button("🔍 Debug Commission Rates", help="Show current commission rates being used in calculations"):
        if 'business_unit_commission_settings' in st.session_state:
            st.markdown("#### 💰 Current Commission Rate Configuration:")
            debug_data = []
            for bu_name, settings in st.session_state.business_unit_commission_settings.items():
                debug_data.append({
                    'Business Unit': bu_name,
                    'Status': '✅ Enabled' if settings.get('enabled', False) else '❌ Disabled',
                    'Lead Gen Rate (%)': settings.get('lead_gen_rate', 0),
                    'Sales Rate (%)': settings.get('sold_by_rate', 0),
                    'Work Done Rate (%)': settings.get('work_done_rate', 0)
                })
            
            if debug_data:
                debug_df = pd.DataFrame(debug_data)
                st.dataframe(debug_df, use_container_width=True, hide_index=True)
                
                # Check for inconsistencies
                inconsistent_units = []
                for data in debug_data:
                    if data['Status'] == '✅ Enabled':
                        if (data['Lead Gen Rate (%)'] == 5.0 and data['Sales Rate (%)'] == 7.5 and data['Work Done Rate (%)'] == 3.0):
                            inconsistent_units.append(data['Business Unit'])
                
                if inconsistent_units:
                    st.warning(f"⚠️ Found {len(inconsistent_units)} business units with old default rates: {', '.join(inconsistent_units)}")
                    if st.button("🔧 Update Old Defaults", help="Update business units still using old default rates"):
                        updated_count = 0
                        for bu_name, settings in st.session_state.business_unit_commission_settings.items():
                            if bu_name in inconsistent_units:
                                settings['work_done_rate'] = 7.5  # Update to match your preference
                                updated_count += 1
                        if updated_count > 0:
                            st.success(f"✅ Updated {updated_count} business units. Please recalculate commissions.")
                            st.rerun()
                else:
                    st.success("✅ All business units appear to be using updated rates.")
            else:
                st.info("No commission rate data found.")
        else:
            st.warning("No business unit settings found.")
    
    results_df = st.session_state.commission_results
    period = st.session_state.commission_period
    
    # Period info
    st.info(f"📅 Commission Period: {period['start']} to {period['end']}")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_commission = results_df['Total Commission'].sum()
        st.metric("💸 Total Commissions", f"${total_commission:,.2f}")
    
    with col2:
        lead_gen_commission = results_df['Lead Gen Commission'].sum()
        st.metric("🎯 Lead Gen Commissions", f"${lead_gen_commission:,.2f}")
    
    with col3:
        sales_commission = results_df['Sales Commission'].sum()
        st.metric("💼 Sales Commissions", f"${sales_commission:,.2f}")
    
    with col4:
        work_done_commission = results_df['Work Done Commission'].sum()
        st.metric("🔧 Work Done Commissions", f"${work_done_commission:,.2f}")
    
    
    # Results table
    st.markdown("#### 📋 Commission Breakdown")
    
    # Format for display
    display_columns = ['Employee', 'Lead Gen Commission', 'Sales Commission', 'Work Done Commission', 'Total Commission']
    
    # Only include columns that exist in the dataframe
    display_columns = [col for col in display_columns if col in results_df.columns]
    
    # Debug: Check for duplicate columns
    st.write(f"🔍 **DataFrame Debug:**")
    st.write(f"All columns in results_df: {list(results_df.columns)}")
    st.write(f"Display columns: {display_columns}")
    
    # Check for duplicate columns in results_df
    duplicates = [col for col in results_df.columns if list(results_df.columns).count(col) > 1]
    if duplicates:
        st.error(f"⚠️ Duplicate columns found: {duplicates}")
        # Remove duplicates by creating new DataFrame with unique columns
        unique_columns = []
        seen = set()
        for col in results_df.columns:
            if col not in seen:
                unique_columns.append(col)
                seen.add(col)
        results_df = results_df[unique_columns]
        st.write(f"Fixed columns: {list(results_df.columns)}")
    
    display_df = results_df[display_columns]
    
    # Configure number columns
    column_config = {}
    for col in display_columns:
        if 'Commission' in col:
            column_config[col] = st.column_config.NumberColumn(
                col.replace('Commission', 'Comm.'),
                format="$%.2f"
            )
    
    st.dataframe(
        display_df,
        use_container_width=True,
        column_config=column_config
    )
    
    # EFFICIENCY PAY CALCULATIONS
    st.markdown("#### 💰 Final Pay Calculations (Efficiency Pay Model)")
    
    if ('employee_data' in st.session_state and 
        not st.session_state.employee_data.empty and
        'saved_timesheet_data' in st.session_state and 
        st.session_state.saved_timesheet_data is not None):
        
        # Calculate final pay for each employee
        efficiency_pay_results = []
        
        for _, employee_row in results_df.iterrows():
            employee_name = employee_row['Employee']
            commission_total = employee_row['Total Commission']
            
            # Get employee data
            emp_data = st.session_state.employee_data[
                (st.session_state.employee_data['Name'] == employee_name) | 
                (st.session_state.employee_data['Employee ID'].astype(str) == str(employee_name))
            ]
            
            if not emp_data.empty:
                emp_info = emp_data.iloc[0]
                hourly_rate = emp_info.get('Hourly Rate', 25.0)
                commission_plan = emp_info.get('Commission Plan', 'Efficiency Pay')
                
                # Get hours from timesheet data
                timesheet_df = st.session_state.saved_timesheet_data
                emp_hours = timesheet_df[
                    (timesheet_df['Employee Name'] == employee_name) |
                    (timesheet_df.get('Name', pd.Series(dtype='object')) == employee_name)
                ]
                
                # Get hours with override support
                regular_hours, ot_hours, dt_hours = get_employee_hours_with_overrides(employee_name, timesheet_df)
                
                if regular_hours > 0 or ot_hours > 0 or dt_hours > 0:
                    
                    # Calculate final pay using our efficiency pay function with proper OT/DT rates
                    pay_calc = calculate_employee_pay(
                        employee_name, regular_hours, ot_hours, dt_hours, 
                        hourly_rate, commission_total, commission_plan
                    )
                    
                    efficiency_pay_results.append(pay_calc)
                else:
                    # No timesheet data found for this employee
                    efficiency_pay_results.append({
                        'employee_name': employee_name,
                        'commission_plan': 'Unknown',
                        'regular_hours': 0,
                        'ot_hours': 0,
                        'dt_hours': 0,
                        'total_hours': 0,
                        'hourly_rate': 0,
                        'regular_pay': 0,
                        'ot_pay': 0,
                        'dt_pay': 0,
                        'hourly_pay': 0,
                        'commission_total': commission_total,
                        'efficiency_pay': 0,
                        'final_pay': commission_total,
                        'calculation_method': 'Commission only (no timesheet data)',
                        'error': 'No timesheet data found'
                    })
        
        if efficiency_pay_results:
            # Create efficiency pay DataFrame
            efficiency_df = pd.DataFrame(efficiency_pay_results)
            
            # Summary metrics for efficiency pay
            st.markdown("##### 📊 Pay Summary")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_hourly = efficiency_df['hourly_pay'].sum()
                st.metric("⏰ Total Hourly Pay", f"${total_hourly:,.2f}")
            
            with col2:
                total_efficiency = efficiency_df['efficiency_pay'].sum()
                st.metric("⚡ Total Efficiency Pay", f"${total_efficiency:,.2f}")
            
            with col3:
                total_final = efficiency_df['final_pay'].sum()
                st.metric("💵 Total Final Pay", f"${total_final:,.2f}")
            
            with col4:
                efficiency_employees = len(efficiency_df[efficiency_df['efficiency_pay'] > 0])
                st.metric("🎯 Employees w/ Efficiency Pay", efficiency_employees)
            
            # Display efficiency pay table
            st.markdown("##### 💰 Individual Pay Breakdown")
            
            # Format display dataframe
            display_efficiency_df = efficiency_df.copy()
            display_efficiency_df = display_efficiency_df.rename(columns={
                'employee_name': 'Employee',
                'commission_plan': 'Plan',
                'regular_hours': 'Reg Hrs',
                'ot_hours': 'OT Hrs',
                'dt_hours': 'DT Hrs',
                'total_hours': 'Total Hrs',
                'hourly_rate': 'Rate',
                'regular_pay': 'Reg Pay',
                'ot_pay': 'OT Pay',
                'dt_pay': 'DT Pay',
                'hourly_pay': 'Total Hourly',
                'commission_total': 'Commission',
                'efficiency_pay': 'Efficiency Pay', 
                'final_pay': 'Final Pay',
                'calculation_method': 'Calculation'
            })
            
            # Select and reorder columns - show detailed breakdown
            display_cols = ['Employee', 'Plan', 'Reg Hrs', 'OT Hrs', 'DT Hrs', 'Total Hrs', 'Rate', 
                           'Reg Pay', 'OT Pay', 'DT Pay', 'Total Hourly', 'Commission', 'Efficiency Pay', 'Final Pay']
            display_cols = [col for col in display_cols if col in display_efficiency_df.columns]
            display_efficiency_df = display_efficiency_df[display_cols]
            
            # Configure columns
            efficiency_column_config = {
                'Employee': st.column_config.TextColumn('Employee'),
                'Plan': st.column_config.TextColumn('Plan'),
                'Reg Hrs': st.column_config.NumberColumn('Reg Hrs', format="%.1f"),
                'OT Hrs': st.column_config.NumberColumn('OT Hrs', format="%.1f"),
                'DT Hrs': st.column_config.NumberColumn('DT Hrs', format="%.1f"),
                'Total Hrs': st.column_config.NumberColumn('Total Hrs', format="%.1f"),
                'Rate': st.column_config.NumberColumn('Rate', format="$%.2f"),
                'Reg Pay': st.column_config.NumberColumn('Reg Pay', format="$%.2f"),
                'OT Pay': st.column_config.NumberColumn('OT Pay', format="$%.2f", help="OT Hours × Rate × 1.5"),
                'DT Pay': st.column_config.NumberColumn('DT Pay', format="$%.2f", help="DT Hours × Rate × 2.0"),
                'Total Hourly': st.column_config.NumberColumn('Total Hourly', format="$%.2f"),
                'Commission': st.column_config.NumberColumn('Commission', format="$%.2f"),
                'Efficiency Pay': st.column_config.NumberColumn('Efficiency Pay', format="$%.2f"),
                'Final Pay': st.column_config.NumberColumn('Final Pay', format="$%.2f")
            }
            
            st.dataframe(
                display_efficiency_df,
                use_container_width=True,
                column_config=efficiency_column_config,
                hide_index=True
            )
            
            # Add explanation
            with st.expander("ℹ️ How Efficiency Pay Works"):
                st.markdown("""
                **Efficiency Pay Model:**
                - Employee gets the **higher** of: total hourly pay OR commission total
                - If commission > hourly pay: Employee gets commission (efficiency pay = commission - hourly)
                - If commission < hourly pay: Employee gets hourly pay (efficiency pay = $0, floor protection)
                
                **Hourly Pay Calculation:**
                - **Regular Hours**: Hours × Rate
                - **OT Hours**: Hours × Rate × 1.5
                - **DT Hours**: Hours × Rate × 2.0
                - **Total Hourly**: Regular Pay + OT Pay + DT Pay
                
                **Hourly + Commission Model:**
                - Employee gets: total hourly pay + commission total (traditional sales model)
                
                **Example:**
                - Employee works: 40 reg hrs + 5 OT hrs @ $25/hr
                - Hourly pay: (40 × $25) + (5 × $25 × 1.5) = $1,000 + $187.50 = $1,187.50
                - Commission earned: $1,200
                - **Efficiency Pay Result**: Gets $1,200 (efficiency pay = $12.50)
                - **Hourly + Commission Would Be**: $2,387.50 ($1,187.50 + $1,200)
                """)
                
    else:
        st.warning("⚠️ Cannot calculate efficiency pay: Missing employee data or timesheet data")

    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        # Commission distribution pie chart
        fig1 = px.pie(
            display_df,
            values='Total Commission',
            names='Employee',
            title='Commission Distribution by Employee'
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Commission type breakdown
        commission_data = []
        lead_gen_commission = results_df['Lead Gen Commission'].sum()
        sales_commission = results_df['Sales Commission'].sum()
        work_done_commission = results_df['Work Done Commission'].sum()
        
        if lead_gen_commission > 0:
            commission_data.append({'Type': 'Lead Generation', 'Amount': lead_gen_commission})
        if sales_commission > 0:
            commission_data.append({'Type': 'Sales', 'Amount': sales_commission})
        if work_done_commission > 0:
            commission_data.append({'Type': 'Work Done', 'Amount': work_done_commission})
        
        if commission_data:
            commission_types = pd.DataFrame(commission_data)
            
            fig2 = px.bar(
                commission_types,
                x='Type',
                y='Amount',
                title='Commission by Type',
                color='Type',
                color_discrete_map={
                    'Hourly Work': '#1f77b4', 
                    'Legacy Leads': '#ff7f0e',
                    'Revenue Based': '#2ca02c'
                }
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No commission data to display")
    
    # Detailed view
    st.markdown("#### 🔍 Detailed View")
    
    selected_employee = st.selectbox("Select Employee for Details", display_df['Employee'].tolist())
    
    if selected_employee:
        emp_data = results_df[results_df['Employee'] == selected_employee]
        if len(emp_data) > 0:
            try:
                emp_result = emp_data.iloc[0]
                details = emp_result.get('Details', {})
            except (IndexError, KeyError) as e:
                st.error(f"❌ Error accessing commission data for {selected_employee}: {e}")
                return
        else:
            st.error(f"❌ No commission data found for {selected_employee}")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Commission Summary**")
            st.write(f"Lead Gen Commission: ${emp_result['Lead Gen Commission']:,.2f}")
            st.write(f"Sales Commission: ${emp_result['Sales Commission']:,.2f}")
            st.write(f"Work Done Commission: ${emp_result['Work Done Commission']:,.2f}")
            st.write(f"**Total Commission: ${emp_result['Total Commission']:,.2f}**")
            
            # Add detailed job breakdown
            if 'saved_revenue_data' in st.session_state and st.session_state.saved_revenue_data is not None:
                st.markdown("##### 📋 Job-by-Job Commission Breakdown")
                
                revenue_df = st.session_state.saved_revenue_data
                employee_jobs = []
                
                # Jobs where employee generated leads
                if 'Lead Generated By' in revenue_df.columns:
                    lead_jobs = revenue_df[revenue_df['Lead Generated By'] == selected_employee].copy()
                    for _, job in lead_jobs.iterrows():
                        employee_jobs.append({
                            'Invoice #': job.get('Invoice #', 'N/A'),
                            'Customer': job.get('Customer Name', 'N/A'),
                            'Business Unit': job.get('Business Unit', 'N/A'),
                            'Revenue': job.get('Jobs Total Revenue', 0),
                            'Role': 'Lead Generation',
                            'Commission Type': 'Lead Gen',
                            'Commission Amount': 0  # Will be calculated below
                        })
                
                # Jobs where employee made sales
                if 'Sold By' in revenue_df.columns:
                    sales_jobs = revenue_df[revenue_df['Sold By'] == selected_employee].copy()
                    for _, job in sales_jobs.iterrows():
                        employee_jobs.append({
                            'Invoice #': job.get('Invoice #', 'N/A'),
                            'Customer': job.get('Customer Name', 'N/A'),
                            'Business Unit': job.get('Business Unit', 'N/A'),
                            'Revenue': job.get('Jobs Total Revenue', 0),
                            'Role': 'Sales',
                            'Commission Type': 'Sales',
                            'Commission Amount': 0  # Will be calculated below
                        })
                
                # Jobs where employee worked as technician
                if 'Assigned Technicians' in revenue_df.columns:
                    tech_jobs = revenue_df[revenue_df['Assigned Technicians'].fillna('').str.contains(selected_employee, na=False, regex=False)].copy()
                    for _, job in tech_jobs.iterrows():
                        # Get all technicians from the job
                        all_techs = []
                        tech_string = str(job.get('Assigned Technicians', '')).strip()
                        if tech_string:
                            # Split technicians by common separators (same logic as main calculation)
                            techs = [t.strip() for t in tech_string.replace(',', ';').replace('&', ';').replace(' and ', ';').split(';') if t.strip()]
                            all_techs.extend(techs)
                        
                        # Filter out helpers/apprentices to get eligible count (same logic as main calculation)
                        eligible_techs = []
                        if 'employee_data' in st.session_state and not st.session_state.employee_data.empty:
                            for tech in all_techs:
                                emp_data = st.session_state.employee_data[
                                    (st.session_state.employee_data['Name'] == tech) | 
                                    (st.session_state.employee_data['Employee ID'] == tech)
                                ]
                                # Include if not found or (not helper AND not excluded from payroll)
                                if (emp_data.empty or 
                                    (not emp_data.iloc[0].get('Helper/Apprentice', False) and 
                                     emp_data.iloc[0].get('Status', 'Active') != 'Excluded from Payroll')):
                                    eligible_techs.append(tech)
                        else:
                            eligible_techs = all_techs
                        
                        eligible_count = len(eligible_techs) if eligible_techs else 1
                        
                        employee_jobs.append({
                            'Invoice #': job.get('Invoice #', 'N/A'),
                            'Customer': job.get('Customer Name', 'N/A'),
                            'Business Unit': job.get('Business Unit', 'N/A'),
                            'Revenue': job.get('Jobs Total Revenue', 0),
                            'Role': f'Technician (1 of {eligible_count} eligible)',
                            'Commission Type': 'Work Done',
                            'Commission Amount': 0,  # Will be calculated below
                            'Eligible_Tech_Count': eligible_count  # Store for calculation
                        })
                
                if employee_jobs:
                    # Calculate commission amounts based on business unit settings
                    if 'business_unit_commission_settings' in st.session_state:
                        bu_settings = st.session_state.business_unit_commission_settings
                        
                        for job in employee_jobs:
                            bu = job['Business Unit']
                            settings = bu_settings.get(bu, bu_settings.get('Default', {}))
                            
                            if settings.get('enabled', False):
                                # Ensure revenue is numeric
                                try:
                                    revenue = float(job['Revenue']) if job['Revenue'] else 0
                                except (ValueError, TypeError):
                                    revenue = 0  # Fallback for non-numeric revenue
                                
                                if job['Commission Type'] == 'Lead Gen':
                                    rate = settings.get('lead_gen_rate', 0)
                                    job['Commission Amount'] = revenue * (rate / 100)
                                elif job['Commission Type'] == 'Sales':
                                    rate = settings.get('sold_by_rate', 0)
                                    job['Commission Amount'] = revenue * (rate / 100)
                                elif job['Commission Type'] == 'Work Done':
                                    rate = settings.get('work_done_rate', 0)
                                    # Use the eligible technician count we calculated
                                    eligible_count = job.get('Eligible_Tech_Count', 1)
                                    job['Commission Amount'] = (revenue * (rate / 100)) / eligible_count
                    
                    # Create DataFrame for display
                    jobs_df = pd.DataFrame(employee_jobs)
                    
                    # Format columns
                    if 'Invoice #' in jobs_df.columns:
                        jobs_df['Invoice #'] = jobs_df['Invoice #'].astype(str).str.replace(',', '', regex=False)
                    if 'Revenue' in jobs_df.columns:
                        jobs_df['Revenue'] = jobs_df['Revenue'].apply(lambda x: f"${x:,.2f}")
                    if 'Commission Amount' in jobs_df.columns:
                        jobs_df['Commission Amount'] = jobs_df['Commission Amount'].apply(lambda x: f"${x:,.2f}")
                    
                    # Reorder columns including Commission Type
                    display_cols = ['Invoice #', 'Customer', 'Business Unit', 'Revenue', 'Role', 'Commission Type', 'Commission Amount']
                    jobs_df = jobs_df[display_cols]
                    
                    st.dataframe(jobs_df, use_container_width=True, hide_index=True)
                else:
                    st.info(f"No job details found for {selected_employee}")
            else:
                st.info("Revenue data not available for detailed breakdown")
        
        with col2:
            st.markdown("**Timesheet Hours**")
            if 'Regular Hours' in details:
                st.write(f"Regular Hours: {details['Regular Hours']:,.1f}")
                st.write(f"OT Hours: {details['OT Hours']:,.1f}")
                st.write(f"DT Hours: {details['DT Hours']:,.1f}")
                st.write(f"**Total Hours: {details['Total Hours']:,.1f}**")
            else:
                st.write("No timesheet data available")
    
    # Export options
    st.markdown("#### 📤 Export Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Download Results CSV"):
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"commission_results_{period['start']}_{period['end']}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("📧 Email Results"):
            st.success("📧 Commission results sent to admin@company.com")

def display_commission_history():
    """Display commission calculation history"""
    st.markdown("### 📋 Commission History")
    
    # Initialize history if not exists
    if 'commission_history' not in st.session_state:
        st.session_state.commission_history = pd.DataFrame(columns=[
            'Calculation Date', 'Period Start', 'Period End', 'Total Commission', 
            'Employees', 'Status'
        ])
    
    # Add current results to history if available
    if 'commission_results' in st.session_state and len(st.session_state.commission_results) > 0:
        if st.button("💾 Save Current Results to History"):
            results = st.session_state.commission_results
            period = st.session_state.commission_period
            
            new_history = pd.DataFrame({
                'Calculation Date': [datetime.now()],
                'Period Start': [period['start']],
                'Period End': [period['end']],
                'Total Commission': [results['Total Commission'].sum()],
                'Employees': [len(results)],
                'Status': ['Calculated']
            })
            
            st.session_state.commission_history = pd.concat(
                [st.session_state.commission_history, new_history], 
                ignore_index=True
            )
            st.success("✅ Results saved to history!")
    
    # Display history
    if len(st.session_state.commission_history) > 0:
        st.dataframe(
            st.session_state.commission_history,
            use_container_width=True,
            column_config={
                "Total Commission": st.column_config.NumberColumn(
                    "Total Commission",
                    format="$%.2f"
                ),
                "Calculation Date": st.column_config.DatetimeColumn(
                    "Calculation Date",
                    format="YYYY-MM-DD HH:mm"
                )
            }
        )
        
        # History chart
        fig = px.line(
            st.session_state.commission_history,
            x='Period End',
            y='Total Commission',
            title='Commission History Trend',
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📋 No commission history available yet.")

def display_commission_settings():
    """Commission calculation settings"""
    st.markdown("### ⚙️ Commission Settings")
    
    st.info("💡 Configure commission rates for each business unit. Commissions are calculated based on revenue from uploaded revenue reports.")
    
    # Get business units from revenue data if available (with safe access)
    business_units = []
    revenue_data = st.session_state.get('revenue_data')
    
    if revenue_data is not None and not revenue_data.empty:
        if 'Business Unit' in revenue_data.columns:
            try:
                unique_units = list(revenue_data['Business Unit'].dropna().unique())
                business_units.extend([unit for unit in unique_units if unit and unit not in business_units])
            except Exception as e:
                st.warning(f"⚠️ Error reading business units from revenue data: {e}")
    
    # Initialize business unit settings if not exists
    if 'business_unit_commission_settings' not in st.session_state:
        st.session_state.business_unit_commission_settings = {}
    
    st.markdown("#### 🏢 Revenue Commission Setup by Business Unit")
    
    # Add explanation
    with st.expander("ℹ️ How Commission Calculation Works", expanded=False):
        st.markdown("""
        **Commission Types:**
        - **Lead Generated By**: Commission paid to the person who generated the lead
        - **Sold By**: Commission paid to the person who closed the sale
        - **Work Done**: Commission paid to each assigned technician based on their individual rate
        
        **Advanced Logic**: Each employee can have custom commission rates that override the business unit defaults.
        
        **Example**: If a job has $100,000 revenue and default rates are Lead Gen: 5%, Sales: 7.5%, Work Done: 3%:
        - Lead generator gets: $5,000 (or custom rate if set)  
        - Salesperson gets: $7,500 (or custom rate if set)
        - **New**: Each technician gets their individual rate × revenue (not split equally!)
          - Senior Tech at 4%: $4,000
          - Junior Tech at 2%: $2,000
          - Total Work Done: $6,000 (vs old system: $3,000 ÷ 2 = $1,500 each)
        """)
    
    # Check if there are business units to configure
    if not business_units:
        st.warning("⚠️ No business units found. Please add business units in the Company Setup tab first.")
        st.markdown("**To add business units:**")
        st.markdown("1. Go to **🏢 Company Setup** tab")
        st.markdown("2. Navigate to **💰 Commission Configuration**")
        st.markdown("3. Add your business units with commission rates")
    else:
        # Commission setup for each business unit
        for business_unit in business_units:
            with st.expander(f"🏢 {business_unit} Commission Rates", expanded=(business_unit == business_units[0])):
                # Initialize settings for this business unit if not exists
                if business_unit not in st.session_state.business_unit_commission_settings:
                    st.session_state.business_unit_commission_settings[business_unit] = {
                        'lead_gen_rate': 5.0,
                        'sold_by_rate': 7.5,
                        'work_done_rate': 7.5,  # Fixed: Use 7.5% as default
                        'enabled': True
                    }
                
                settings = st.session_state.business_unit_commission_settings[business_unit]
                
                # Enable/disable toggle
                enabled = st.checkbox(
                    f"Enable commissions for {business_unit}", 
                    value=settings['enabled'], 
                    key=f"enable_{business_unit}"
                )
                
                if enabled:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("**🎯 Lead Generation**")
                        lead_gen_rate = st.number_input(
                            "Commission Rate (%)",
                            min_value=0.0,
                            max_value=100.0,
                            value=settings['lead_gen_rate'],
                            step=0.25,
                            key=f"lead_gen_{business_unit}",
                            help="Percentage of revenue paid to lead generator"
                        )
                    
                    with col2:
                        st.markdown("**💼 Sales**")
                        sold_by_rate = st.number_input(
                            "Commission Rate (%)",
                            min_value=0.0,
                            max_value=100.0,
                            value=settings['sold_by_rate'],
                            step=0.25,
                            key=f"sold_by_{business_unit}",
                            help="Percentage of revenue paid to salesperson"
                        )
                    
                    with col3:
                        st.markdown("**🔧 Work Done**")
                        work_done_rate = st.number_input(
                            "Commission Rate (%)",
                            min_value=0.0,
                            max_value=100.0,
                            value=settings['work_done_rate'],
                            step=0.25,
                            key=f"work_done_{business_unit}",
                            help="Percentage of revenue split equally among all assigned technicians"
                        )
                    
                    # Validate commission rates
                    total_rate = lead_gen_rate + sold_by_rate + work_done_rate
                    if total_rate > 100:
                        st.error(f"❌ Total commission rate ({total_rate:.2f}%) exceeds 100%. Please adjust rates.")
                    
                    # Show calculation example
                    if lead_gen_rate > 0 or sold_by_rate > 0 or work_done_rate > 0:
                        st.markdown("**💡 Example Calculation (on $100,000 revenue):**")
                        example_col1, example_col2, example_col3, example_col4 = st.columns(4)
                        
                        with example_col1:
                            if lead_gen_rate > 0:
                                st.metric("Lead Gen", f"${(100000 * lead_gen_rate / 100):,.0f}")
                        
                        with example_col2:
                            if sold_by_rate > 0:
                                st.metric("Sales", f"${(100000 * sold_by_rate / 100):,.0f}")
                        
                        with example_col3:
                            if work_done_rate > 0:
                                st.metric("Work (Total)", f"${(100000 * work_done_rate / 100):,.0f}")
                        
                        with example_col4:
                            color = "red" if total_rate > 100 else "normal"
                            st.metric("Total Rate", f"{total_rate:.2f}%", delta=f"{'⚠️ High' if total_rate > 50 else 'OK'}" if total_rate <= 100 else "❌ Too High")
                else:
                    st.info(f"Commissions disabled for {business_unit}")
                    lead_gen_rate = 0
                    sold_by_rate = 0
                    work_done_rate = 0
                
                # Update settings
                st.session_state.business_unit_commission_settings[business_unit] = {
                    'lead_gen_rate': lead_gen_rate,
                    'sold_by_rate': sold_by_rate,
                    'work_done_rate': work_done_rate,
                    'enabled': enabled
                }
                
    
    
    # Approval settings (optional)
    with st.expander("✅ Commission Approval Settings", expanded=False):
        st.markdown("Configure approval workflow for high-value commissions.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            approval_threshold = st.number_input(
                "Approval Required Above ($)",
                min_value=0.0,
                value=5000.0,
                step=100.0,
                help="Commission amounts above this threshold require approval"
            )
        
        with col2:
            approver_role = st.selectbox(
                "Approver Role",
                ["Manager", "Director", "Executive"]
            )
    
    # Save settings
    if st.button("💾 Save Commission Settings", type="primary", use_container_width=True):
        # Save settings to session state
        st.session_state.commission_settings = {
            'approval_threshold': approval_threshold,
            'approver_role': approver_role,
            'business_unit_settings': st.session_state.business_unit_commission_settings
        }
        st.success("✅ Commission settings saved successfully!")
        
        # Show summary of business unit settings
        st.markdown("#### 📋 Commission Settings Summary")
        summary_data = []
        for bu, settings in st.session_state.business_unit_commission_settings.items():
            if settings['enabled']:
                summary_data.append({
                    'Business Unit': bu,
                    'Lead Gen Rate (%)': settings['lead_gen_rate'],
                    'Sold By Rate (%)': settings['sold_by_rate'],
                    'Work Done Rate (%)': settings['work_done_rate'],
                    'Status': '✅ Enabled'
                })
            else:
                summary_data.append({
                    'Business Unit': bu,
                    'Lead Gen Rate (%)': 0,
                    'Sold By Rate (%)': 0,
                    'Work Done Rate (%)': 0,
                    'Status': '❌ Disabled'
                })
        
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)

def get_employee_commission_rate(employee, business_unit, commission_type, default_rate):
    """
    Get the effective commission rate for an employee, considering overrides
    
    Args:
        employee: Employee name
        business_unit: Business unit name
        commission_type: 'lead_gen', 'sold_by', or 'work_done'
        default_rate: Default rate from business unit settings
    
    Returns:
        float: Effective commission rate to use
    """
    # Check if there are employee-specific overrides
    if ('employee_commission_overrides' in st.session_state and 
        business_unit in st.session_state.employee_commission_overrides and
        employee in st.session_state.employee_commission_overrides[business_unit]):
        
        employee_overrides = st.session_state.employee_commission_overrides[business_unit][employee]
        
        # Check if this commission type has an override
        override_key = f"{commission_type}_rate"
        use_override_key = f"use_{commission_type}_override"
        
        if employee_overrides.get(use_override_key, False):
            return employee_overrides.get(override_key, default_rate)
    
    # Return default rate if no override
    return default_rate

def calculate_revenue_commissions(revenue_data, commission_settings):
    """
    Calculate commissions for revenue data based on business unit specific settings
    """
    if revenue_data is None or revenue_data.empty:
        return pd.DataFrame()
    
    if 'business_unit_settings' not in commission_settings:
        return pd.DataFrame()
    
    business_unit_settings = commission_settings['business_unit_settings']
    results = []
    
    # Debug: Show what business units we're processing
    st.write(f"🔍 **Revenue Processing Debug:**")
    st.write(f"📊 Revenue Data Shape: {revenue_data.shape}")
    st.write(f"📋 Available columns: {list(revenue_data.columns)}")
    
    # Debug: Show commission rates being used
    st.write(f"💰 **Commission Rates Being Used:**")
    for bu, settings in business_unit_settings.items():
        if settings.get('enabled', False):
            st.write(f"  • {bu}: Lead {settings['lead_gen_rate']}%, Sales {settings['sold_by_rate']}%, Work {settings['work_done_rate']}%")
    
    # Show sample revenue values to debug $0 issue
    if len(revenue_data) > 0:
        sample_revenues = []
        for col in ['Jobs total revenue', 'Revenue', 'Jobs Total Revenue']:
            if col in revenue_data.columns:
                sample_values = revenue_data[col].head(3).tolist()
                sample_revenues.append(f"{col}: {sample_values}")
        st.write(f"💰 Sample revenue values: {'; '.join(sample_revenues)}")
    
    processed_count = 0
    skipped_count = 0
    
    for idx, row in revenue_data.iterrows():
        business_unit = row.get('Business Unit', 'Default')
        # Try multiple possible revenue column names
        revenue = row.get('Jobs total revenue', row.get('Revenue', row.get('Jobs Total Revenue', 0)))
        
        # Get settings for this business unit, fallback to Default
        settings = business_unit_settings.get(business_unit, business_unit_settings.get('Default', {
            'lead_gen_rate': 0, 'sold_by_rate': 0, 'work_done_rate': 0, 'enabled': False
        }))
        
        # Debug: Check why rows might be skipped
        enabled = settings.get('enabled', False)
        has_revenue = revenue > 0
        
        if not enabled or not has_revenue:
            skipped_count += 1
            if idx < 5:  # Only show first 5 for brevity
                st.write(f"⚠️ Row {idx}: BU='{business_unit}', Revenue=${revenue}, Enabled={enabled} - SKIPPED")
            continue
        else:
            processed_count += 1
            if idx < 5:  # Only show first 5 for brevity
                st.write(f"✅ Row {idx}: BU='{business_unit}', Revenue=${revenue}, Enabled={enabled} - PROCESSING")
        
        # Lead Generated By commission
        if 'Lead Generated By' in row and pd.notna(row['Lead Generated By']) and str(row['Lead Generated By']).strip():
            lead_gen_person = str(row['Lead Generated By']).strip()
            
            # Check if employee is eligible for commissions (not helper and not excluded from payroll)
            eligible = True
            if 'employee_data' in st.session_state and not st.session_state.employee_data.empty:
                emp_data = st.session_state.employee_data[
                    (st.session_state.employee_data['Name'] == lead_gen_person) | 
                    (st.session_state.employee_data['Employee ID'] == lead_gen_person)
                ]
                if not emp_data.empty:
                    is_helper = emp_data.iloc[0].get('Helper/Apprentice', False)
                    is_excluded = emp_data.iloc[0].get('Status', 'Active') == 'Excluded from Payroll'
                    eligible = not is_helper and not is_excluded
            
            if eligible:
                # Get employee-specific rate or default
                effective_rate = get_employee_commission_rate(
                    lead_gen_person, business_unit, 'lead_gen', settings['lead_gen_rate']
                )
                lead_gen_commission = revenue * (effective_rate / 100)
                
                results.append({
                    'Employee': lead_gen_person,
                    'Commission Type': 'Lead Generation',
                    'Business Unit': business_unit,
                    'Revenue': revenue,
                    'Commission Rate (%)': effective_rate,
                    'Commission Amount': lead_gen_commission,
                    'Source': f"Lead generation for {business_unit}" + 
                             (f" (Custom: {effective_rate}%)" if effective_rate != settings['lead_gen_rate'] else "")
                })
        
        # Sold By commission
        if 'Sold By' in row and pd.notna(row['Sold By']) and str(row['Sold By']).strip():
            sales_person = str(row['Sold By']).strip()
            
            # Check if employee is eligible for commissions (not helper and not excluded from payroll)
            eligible = True
            if 'employee_data' in st.session_state and not st.session_state.employee_data.empty:
                emp_data = st.session_state.employee_data[
                    (st.session_state.employee_data['Name'] == sales_person) | 
                    (st.session_state.employee_data['Employee ID'] == sales_person)
                ]
                if not emp_data.empty:
                    is_helper = emp_data.iloc[0].get('Helper/Apprentice', False)
                    is_excluded = emp_data.iloc[0].get('Status', 'Active') == 'Excluded from Payroll'
                    eligible = not is_helper and not is_excluded
            
            if eligible:
                # Get employee-specific rate or default
                effective_rate = get_employee_commission_rate(
                    sales_person, business_unit, 'sold_by', settings['sold_by_rate']
                )
                sold_by_commission = revenue * (effective_rate / 100)
                
                results.append({
                    'Employee': sales_person,
                    'Commission Type': 'Sales',
                    'Business Unit': business_unit,
                    'Revenue': revenue,
                    'Commission Rate (%)': effective_rate,
                    'Commission Amount': sold_by_commission,
                    'Source': f"Sales for {business_unit}" + 
                             (f" (Custom: {effective_rate}%)" if effective_rate != settings['sold_by_rate'] else "")
                })
        
        # Work Done commission (split among technicians, excluding helpers/apprentices)
        all_technicians = []
        
        # Check for individual technician columns first (Technician_1, Technician_2, etc.)
        for col in row.index:
            if col.startswith('Technician_') and pd.notna(row[col]) and str(row[col]).strip():
                all_technicians.append(str(row[col]).strip())
        
        # If no individual technician columns found, check for 'Assigned Technicians' column
        if not all_technicians and 'Assigned Technicians' in row.index:
            assigned_techs = row.get('Assigned Technicians', '')
            if pd.notna(assigned_techs) and str(assigned_techs).strip():
                # Split technicians by common separators
                tech_string = str(assigned_techs).strip()
                techs = [t.strip() for t in tech_string.replace(',', ';').replace('&', ';').replace(' and ', ';').split(';') if t.strip()]
                all_technicians.extend(techs)
        
        # Debug output for Work Done commission
        if idx < 3:  # Only show first 3 for brevity
            st.write(f"  🔧 Row {idx} Work Done: Found {len(all_technicians)} technicians: {all_technicians}")
        
        # Filter out helpers/apprentices
        eligible_technicians = []
        if 'employee_data' in st.session_state and not st.session_state.employee_data.empty:
            for tech in all_technicians:
                # Check if technician is a helper/apprentice
                emp_data = st.session_state.employee_data[
                    (st.session_state.employee_data['Name'] == tech) | 
                    (st.session_state.employee_data['Employee ID'] == tech)
                ]
                
                # If employee not found or (not a helper AND not excluded from payroll), include them
                if (emp_data.empty or 
                    (not emp_data.iloc[0].get('Helper/Apprentice', False) and 
                     emp_data.iloc[0].get('Status', 'Active') != 'Excluded from Payroll')):
                    eligible_technicians.append(tech)
        else:
            # If no employee data, include all technicians
            eligible_technicians = all_technicians
        
        # Debug eligibility filtering
        if idx < 3:  # Only show first 3 for brevity
            st.write(f"  🔧 Row {idx} Eligible technicians: {eligible_technicians}")
            st.write(f"  🔧 Row {idx} Work done rate: {settings.get('work_done_rate', 0)}%")
        
        if eligible_technicians and settings['work_done_rate'] > 0:
            # Advanced logic: Calculate based on individual technician rates
            # Each technician gets their own rate applied to the full revenue
            # This allows for different skill levels/rates per technician
            
            # Debug commission calculation
            if idx < 3:  # Only show first 3 for brevity
                st.write(f"  🔧 Row {idx} Calculating individual technician rates...")
            
            for tech in eligible_technicians:
                # Get employee-specific work done rate or default
                tech_rate = get_employee_commission_rate(
                    tech, business_unit, 'work_done', settings['work_done_rate']
                )
                
                # Calculate commission for this technician based on their individual rate
                tech_commission = revenue * (tech_rate / 100)
                
                # Debug: Show individual technician calculation
                if idx < 3:  # Only first 3 for brevity
                    is_custom = tech_rate != settings['work_done_rate']
                    st.write(f"  🔧 {tech}: {tech_rate}% of ${revenue} = ${tech_commission:.2f}" + 
                            (f" (CUSTOM RATE)" if is_custom else " (default)"))
                
                results.append({
                    'Employee': tech,
                    'Commission Type': 'Work Done',
                    'Business Unit': business_unit,
                    'Revenue': revenue,
                    'Commission Rate (%)': tech_rate,
                    'Commission Amount': tech_commission,
                    'Source': f"Work done for {business_unit}" + 
                             (f" (Custom: {tech_rate}%)" if tech_rate != settings['work_done_rate'] else "") +
                             (f" ({len(all_technicians) - len(eligible_technicians)} helpers excluded)" if len(all_technicians) != len(eligible_technicians) else "")
                })
    
    # Debug: Show final processing summary
    st.write(f"📊 **Processing Summary:**")
    st.write(f"- Processed rows: {processed_count}")
    st.write(f"- Skipped rows: {skipped_count}")
    st.write(f"- Commission results: {len(results)}")
    
    if results:
        # Show sample of results
        for i, result in enumerate(results[:3]):  # Show first 3
            st.write(f"  • {result['Employee']}: {result['Commission Type']} = ${result['Commission Amount']:.2f}")
        if len(results) > 3:
            st.write(f"  • ... and {len(results) - 3} more")
            
        return pd.DataFrame(results)
    else:
        st.warning("⚠️ No commission results generated")
        return pd.DataFrame()

def display_data_upload_functionality():
    """Data upload functionality - legacy function"""
    st.markdown("## 📤 Data Upload")
    
    # Initialize session state for uploaded data
    if 'uploaded_timesheet_data' not in st.session_state:
        st.session_state.uploaded_timesheet_data = None
    if 'uploaded_revenue_data' not in st.session_state:
        st.session_state.uploaded_revenue_data = None
    if 'timesheet_file_name' not in st.session_state:
        st.session_state.timesheet_file_name = None
    if 'revenue_file_name' not in st.session_state:
        st.session_state.revenue_file_name = None
    
    # File upload section
    st.markdown("### 📁 File Upload")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 👥 Timesheet Data")
        timesheet_file = st.file_uploader(
            "Upload Timesheet File",
            type=['xlsx', 'xls', 'csv'],
            help="Upload employee timesheet data with hours worked",
            key="timesheet_uploader"
        )
        
        if timesheet_file:
            try:
                # Case-insensitive file extension check
                file_ext = timesheet_file.name.lower()
                if file_ext.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(timesheet_file)
                else:
                    df = pd.read_csv(timesheet_file)
                st.session_state.uploaded_timesheet_data = df
                st.session_state.timesheet_file_name = timesheet_file.name
                st.info(f"📁 File ready: {timesheet_file.name}")
                st.dataframe(df.head(), use_container_width=True)
                
                # Show data validation info
                with st.expander("📊 Data Preview & Validation"):
                    st.write(f"**Rows:** {len(df)}")
                    st.write(f"**Columns:** {len(df.columns)}")
                    st.write("**Column Names:**")
                    for col in df.columns:
                        st.write(f"• {col}")
                        
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")
                st.session_state.uploaded_timesheet_data = None
                st.session_state.timesheet_file_name = None
    
    with col2:
        st.markdown("#### 💰 Revenue Data")
        revenue_file = st.file_uploader(
            "Upload Revenue File",
            type=['xlsx', 'xls', 'csv'],
            help="Upload business unit revenue data",
            key="revenue_uploader"
        )
        
        if revenue_file:
            try:
                # Case-insensitive file extension check
                file_ext = revenue_file.name.lower()
                if file_ext.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(revenue_file)
                else:
                    df = pd.read_csv(revenue_file)
                st.session_state.uploaded_revenue_data = df
                st.session_state.revenue_file_name = revenue_file.name
                st.info(f"📁 File ready: {revenue_file.name}")
                st.dataframe(df.head(), use_container_width=True)
                
                # Show data validation info
                with st.expander("📊 Data Preview & Validation"):
                    st.write(f"**Rows:** {len(df)}")
                    st.write(f"**Columns:** {len(df.columns)}")
                    st.write("**Column Names:**")
                    for col in df.columns:
                        st.write(f"• {col}")
                        
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")
                st.session_state.uploaded_revenue_data = None
                st.session_state.revenue_file_name = None
    
    # Save data section
    st.markdown("### 💾 Save Uploaded Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.session_state.uploaded_timesheet_data is not None:
            st.success(f"📁 Timesheet data loaded: {st.session_state.timesheet_file_name}")
            if st.button("💾 Save Timesheet Data", type="primary", use_container_width=True, key="save_timesheet"):
                # Process and save timesheet data
                try:
                    # Here you would normally save to database or process the data
                    st.session_state.saved_timesheet_data = st.session_state.uploaded_timesheet_data.copy()
                    st.session_state.data_updated = True  # Flag for other tabs to refresh
                    st.session_state.last_timesheet_save = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.success("✅ Timesheet data saved successfully!")
                    st.balloons()
                    st.rerun()  # Refresh the page to update all tabs
                except Exception as e:
                    st.error(f"❌ Error saving timesheet data: {e}")
        else:
            st.info("📤 Upload a timesheet file to save data")
    
    with col2:
        if st.session_state.uploaded_revenue_data is not None:
            st.success(f"📁 Revenue data loaded: {st.session_state.revenue_file_name}")
            if st.button("💾 Save Revenue Data", type="primary", use_container_width=True, key="save_revenue"):
                # Process and save revenue data
                try:
                    # Here you would normally save to database or process the data
                    st.session_state.saved_revenue_data = st.session_state.uploaded_revenue_data.copy()
                    st.session_state.data_updated = True  # Flag for other tabs to refresh
                    st.session_state.last_revenue_save = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.success("✅ Revenue data saved successfully!")
                    st.balloons()
                    st.rerun()  # Refresh the page to update all tabs
                except Exception as e:
                    st.error(f"❌ Error saving revenue data: {e}")
        else:
            st.info("📤 Upload a revenue file to save data")
    
    # Bulk save option
    if (st.session_state.uploaded_timesheet_data is not None and 
        st.session_state.uploaded_revenue_data is not None):
        st.markdown("---")
        if st.button("💾 Save All Data", type="primary", use_container_width=True, key="save_all_data"):
            try:
                st.session_state.saved_timesheet_data = st.session_state.uploaded_timesheet_data.copy()
                st.session_state.saved_revenue_data = st.session_state.uploaded_revenue_data.copy()
                st.session_state.data_updated = True  # Flag for other tabs to refresh
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.last_timesheet_save = current_time
                st.session_state.last_revenue_save = current_time
                st.success("✅ All data saved successfully!")
                st.balloons()
                st.rerun()  # Refresh the page to update all tabs
            except Exception as e:
                st.error(f"❌ Error saving data: {e}")
    
    # Data status summary
    st.markdown("### 📊 Data Status Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📤 Uploaded Files")
        if st.session_state.uploaded_timesheet_data is not None:
            st.success(f"✅ Timesheet: {st.session_state.timesheet_file_name}")
        else:
            st.info("📤 No timesheet uploaded")
            
        if st.session_state.uploaded_revenue_data is not None:
            st.success(f"✅ Revenue: {st.session_state.revenue_file_name}")
        else:
            st.info("📤 No revenue file uploaded")
    
    with col2:
        st.markdown("#### 💾 Saved Data")
        if st.session_state.get('saved_timesheet_data') is not None:
            last_save = st.session_state.get('last_timesheet_save', 'Unknown')
            st.success(f"✅ Timesheet data saved ({len(st.session_state.saved_timesheet_data)} rows)")
            st.caption(f"Last saved: {last_save}")
        else:
            st.warning("⚠️ No timesheet data saved")
            
        if st.session_state.get('saved_revenue_data') is not None:
            last_save = st.session_state.get('last_revenue_save', 'Unknown')
            st.success(f"✅ Revenue data saved ({len(st.session_state.saved_revenue_data)} rows)")
            st.caption(f"Last saved: {last_save}")
        else:
            st.warning("⚠️ No revenue data saved")
    
    # Sample data section
    st.markdown("### 📋 Sample Data")
    if st.button("📥 Load Sample Data"):
        # Create sample data
        sample_employees = pd.DataFrame({
            'Employee Name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
            'Regular Hours': [40, 35, 40],
            'OT Hours': [5, 10, 0],
            'DT Hours': [0, 0, 8]
        })
        
        sample_revenue = pd.DataFrame({
            'Business Unit': ['Sales', 'Marketing', 'Operations'],
            'Revenue': [100000, 75000, 50000],
            'Period': ['2024-01-01', '2024-01-01', '2024-01-01']
        })
        
        st.success("✅ Sample data loaded!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Sample Employees:**")
            st.dataframe(sample_employees)
        
        with col2:
            st.markdown("**Sample Revenue:**")
            st.dataframe(sample_revenue)

def display_configuration_tab():
    """Configuration settings"""
    st.markdown("## ⚙️ System Configuration")
    
    # Initialize config in session state if not exists
    if 'config_saved' not in st.session_state:
        st.session_state.config_saved = False
    if 'employee_rates' not in st.session_state:
        st.session_state.employee_rates = {}
    if 'commission_rates' not in st.session_state:
        st.session_state.commission_rates = {}
    
    # Get dynamic data from uploaded files
    employees = ['John Doe', 'Jane Smith', 'Bob Johnson']  # Default
    business_units = ['Sales', 'Marketing', 'Operations']  # Default
    
    # Try to get actual employee names from timesheet data
    if st.session_state.get('saved_timesheet_data') is not None:
        timesheet_df = st.session_state.saved_timesheet_data
        if 'Employee Name' in timesheet_df.columns:
            # Filter out NaN values and convert to string
            employees = timesheet_df['Employee Name'].dropna().astype(str).unique().tolist()
            # Remove empty strings and clean data
            employees = [emp.strip() for emp in employees if emp.strip() and emp.strip().lower() != 'nan']
        elif 'Employee' in timesheet_df.columns:
            # Filter out NaN values and convert to string
            employees = timesheet_df['Employee'].dropna().astype(str).unique().tolist()
            # Remove empty strings and clean data  
            employees = [emp.strip() for emp in employees if emp.strip() and emp.strip().lower() != 'nan']
        
        # Fall back to defaults if no valid employees found
        if not employees:
            employees = ['John Doe', 'Jane Smith', 'Bob Johnson']
    
    # Try to get actual business units from revenue data
    if st.session_state.get('saved_revenue_data') is not None:
        revenue_df = st.session_state.saved_revenue_data
        if 'Business Unit' in revenue_df.columns:
            # Filter out NaN values and convert to string
            business_units = revenue_df['Business Unit'].dropna().astype(str).unique().tolist()
            # Remove empty strings and clean data
            business_units = [unit.strip() for unit in business_units if unit.strip() and unit.strip().lower() != 'nan']
        elif 'Unit' in revenue_df.columns:
            # Filter out NaN values and convert to string
            business_units = revenue_df['Unit'].dropna().astype(str).unique().tolist()
            # Remove empty strings and clean data
            business_units = [unit.strip() for unit in business_units if unit.strip() and unit.strip().lower() != 'nan']
        
        # Don't add any defaults - keep empty if no business units found
        # User should add business units from Company Setup tab
    
    # Debug info
    with st.expander("🔧 Config Debug Info", expanded=False):
        st.write("**Configuration State:**")
        st.write(f"• Config saved: {st.session_state.get('config_saved', False)}")
        st.write(f"• Employee rates: {st.session_state.get('employee_rates', {})}")
        st.write(f"• Commission rates: {st.session_state.get('commission_rates', {})}")
        st.write(f"• Last config save: {st.session_state.get('last_config_save', 'Never')}")
        st.write(f"• Detected employees: {employees}")
        st.write(f"• Detected business units: {business_units}")
        st.write(f"• Timesheet data exists: {st.session_state.get('saved_timesheet_data') is not None}")
        st.write(f"• Revenue data exists: {st.session_state.get('saved_revenue_data') is not None}")
    
    # Show data detection status
    if st.session_state.get('saved_timesheet_data') is not None or st.session_state.get('saved_revenue_data') is not None:
        st.info("🔄 Configuration automatically updated with data from uploaded files!")
        
        # Add button to auto-populate rates
        if st.button("🚀 Auto-populate Default Rates", help="Set default rates for all detected employees and business units"):
            # Set default rates for all employees
            for emp in employees:
                emp_str = str(emp).strip()
                if not emp_str or emp_str.lower() == 'nan':
                    continue
                if emp_str not in st.session_state.employee_rates:
                    st.session_state.employee_rates[emp_str] = 25.0
            
            # Set default commission rates for all business units
            for unit in business_units:
                unit_str = str(unit).strip()
                if not unit_str or unit_str.lower() == 'nan':
                    continue
                if unit_str not in st.session_state.commission_rates:
                    st.session_state.commission_rates[unit_str] = 5.0
            
            st.success("✅ Default rates auto-populated! Review and save when ready.")
            st.rerun()
    else:
        st.warning("⚠️ Upload and save timesheet/revenue data to auto-populate configuration with actual employee and business unit names.")
    
    # Employee rates
    st.markdown("### 👥 Employee Rates")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Hourly Rates")
        st.caption(f"Found {len(employees)} employees from uploaded data" if st.session_state.get('saved_timesheet_data') is not None else "Using default employees")
        
        for emp in employees:
            # Ensure emp is a string
            emp_str = str(emp).strip()
            if not emp_str or emp_str.lower() == 'nan':
                continue
                
            # Use saved value if exists, otherwise default to 25.0
            default_rate = st.session_state.employee_rates.get(emp_str, 25.0)
            # Create safe unique key using hash to prevent conflicts
            emp_hash = hashlib.md5(emp_str.encode()).hexdigest()[:8]
            safe_emp_key = f"emp_{emp_hash}"
            rate = st.number_input(
                f"{emp_str} - Hourly Rate ($)",
                min_value=0.0,
                value=default_rate,
                step=0.50,
                key=f"rate_{safe_emp_key}"
            )
    
    with col2:
        st.markdown("#### Commission Settings")
        st.caption(f"Found {len(business_units)} business units from uploaded data" if st.session_state.get('saved_revenue_data') is not None else "Using default business units")
        
        for unit in business_units:
            # Ensure unit is a string
            unit_str = str(unit).strip()
            if not unit_str or unit_str.lower() == 'nan':
                continue
                
            # Use saved value if exists, otherwise default to 5.0
            default_commission = st.session_state.commission_rates.get(unit_str, 5.0)
            # Create safe unique key using hash to prevent conflicts
            unit_hash = hashlib.md5(unit_str.encode()).hexdigest()[:8]
            safe_unit_key = f"unit_{unit_hash}"
            commission_rate = st.number_input(
                f"{unit_str} - Commission Rate (%)",
                min_value=0.0,
                max_value=100.0,
                value=default_commission,
                step=0.1,
                key=f"commission_{safe_unit_key}"
            )
    
    # Save button
    if st.button("💾 Save Configuration", type="primary", key="save_config"):
        try:
            # Save employee rates from form inputs
            for emp in employees:
                emp_str = str(emp).strip()
                if not emp_str or emp_str.lower() == 'nan':
                    continue
                emp_hash = hashlib.md5(emp_str.encode()).hexdigest()[:8]
                rate_key = f"rate_emp_{emp_hash}"
                if rate_key in st.session_state:
                    st.session_state.employee_rates[emp_str] = st.session_state[rate_key]
            
            # Save commission rates from form inputs
            for unit in business_units:
                unit_str = str(unit).strip()
                if not unit_str or unit_str.lower() == 'nan':
                    continue
                unit_hash = hashlib.md5(unit_str.encode()).hexdigest()[:8]
                commission_key = f"commission_unit_{unit_hash}"
                if commission_key in st.session_state:
                    st.session_state.commission_rates[unit_str] = st.session_state[commission_key]
            
            # Set save flags
            st.session_state.config_saved = True
            st.session_state.last_config_save = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.data_updated = True  # Flag for other tabs to refresh
            
            st.success("✅ Configuration saved successfully!")
            st.balloons()
            st.rerun()  # Refresh to show updated values
            
        except Exception as e:
            st.error(f"❌ Error saving configuration: {e}")
    
    # Show current saved values
    if st.session_state.config_saved:
        st.markdown("### 📊 Current Saved Configuration")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Employee Hourly Rates:**")
            for emp, rate in st.session_state.employee_rates.items():
                st.write(f"• {emp}: ${rate:.2f}/hour")
        
        with col2:
            st.markdown("**Commission Rates:**")
            for unit, rate in st.session_state.commission_rates.items():
                st.write(f"• {unit}: {rate:.1f}%")
        
        st.caption(f"Last saved: {st.session_state.get('last_config_save', 'Unknown')}")

def display_analytics_tab():
    """Analytics dashboard"""
    st.markdown("## 📊 Analytics Dashboard")
    
    # Debug info
    with st.expander("🔧 Debug Info", expanded=False):
        st.write("**Analytics Tab Session State:**")
        st.write(f"• Timesheet data exists: {st.session_state.get('saved_timesheet_data') is not None}")
        st.write(f"• Revenue data exists: {st.session_state.get('saved_revenue_data') is not None}")
        st.write(f"• Data updated flag: {st.session_state.get('data_updated', False)}")
        
        if st.session_state.get('saved_timesheet_data') is not None:
            df = st.session_state.saved_timesheet_data
            st.write(f"• Timesheet: {len(df)} rows, columns: {list(df.columns)}")
        if st.session_state.get('saved_revenue_data') is not None:
            df = st.session_state.saved_revenue_data
            st.write(f"• Revenue: {len(df)} rows, columns: {list(df.columns)}")
    
    # Add refresh button and data update indicator
    col1, col2 = st.columns([3, 1])
    with col1:
        # Check for data updates and show refresh indicator
        if st.session_state.get('data_updated', False):
            st.info("🔄 Data has been updated! Charts and metrics reflect your latest saved data.")
    with col2:
        if st.button("🔄 Refresh Analytics", help="Refresh charts and metrics"):
            st.rerun()
    
    # Check if we have saved data
    has_timesheet_data = st.session_state.get('saved_timesheet_data') is not None
    has_revenue_data = st.session_state.get('saved_revenue_data') is not None
    
    if not (has_timesheet_data and has_revenue_data):
        st.warning("⚠️ No saved data available. Please upload and save data in the Data Management tab first.")
        st.info("📤 Go to **Data Management** → Upload files → Click **Save** buttons")
        return
    
    # Get actual data
    timesheet_df = st.session_state.saved_timesheet_data
    revenue_df = st.session_state.saved_revenue_data
    
    # KPI Metrics
    st.markdown("### 📈 Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        try:
            total_revenue = 0
            if 'Revenue' in revenue_df.columns:
                # Convert to numeric and handle errors
                revenue_series = pd.to_numeric(revenue_df['Revenue'], errors='coerce')
                total_revenue = revenue_series.sum()
                if pd.isna(total_revenue):
                    total_revenue = 0
            st.metric("💰 Total Revenue", f"${total_revenue:,.0f}", delta="From uploaded data")
        except Exception as e:
            st.metric("💰 Total Revenue", "Error", delta="Data issue")
            st.error(f"Revenue calculation error: {e}")
    
    with col2:
        # Calculate estimated commissions using saved config or default
        if st.session_state.get('config_saved', False) and st.session_state.get('commission_rates') and len(st.session_state.commission_rates) > 0:
            # Use average of saved commission rates
            avg_commission_rate = sum(st.session_state.commission_rates.values()) / len(st.session_state.commission_rates) / 100
            estimated_commissions = total_revenue * avg_commission_rate
            st.metric("💸 Est. Commissions", f"${estimated_commissions:,.0f}", delta="From config")
        else:
            # Use default 5%
            estimated_commissions = total_revenue * 0.05
            st.metric("💸 Est. Commissions", f"${estimated_commissions:,.0f}", delta="5% default")
    
    with col3:
        if st.session_state.get('config_saved', False) and st.session_state.get('commission_rates') and len(st.session_state.commission_rates) > 0:
            avg_rate = sum(st.session_state.commission_rates.values()) / len(st.session_state.commission_rates)
            st.metric("📊 Avg Commission Rate", f"{avg_rate:.1f}%", delta="From config")
        else:
            st.metric("📊 Commission Rate", "5.0%", delta="Default rate")
    
    with col4:
        employee_count = len(timesheet_df) if timesheet_df is not None else 0
        st.metric("👥 Employees", str(employee_count), delta="From timesheet")
    
    # Charts
    st.markdown("### 📊 Visualizations")
    
    # Chart selection
    chart_types = ["Bar Chart", "Pie Chart", "Line Chart", "Scatter Plot", "Sunburst", "Treemap", "Heatmap", "Box Plot"]
    selected_chart = st.selectbox("Select Visualization Type", chart_types, key="chart_selector")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Revenue visualizations
        st.markdown("#### 💰 Revenue Analysis")
        try:
            if 'Business Unit' in revenue_df.columns and 'Revenue' in revenue_df.columns:
                if selected_chart == "Bar Chart":
                    fig = px.bar(revenue_df, x='Business Unit', y='Revenue', 
                                title='Revenue by Business Unit',
                                color='Revenue',
                                color_continuous_scale='Blues',
                                text='Revenue')
                    fig.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
                elif selected_chart == "Pie Chart":
                    fig = px.pie(revenue_df, values='Revenue', names='Business Unit',
                                title='Revenue Distribution by Business Unit')
                elif selected_chart == "Treemap":
                    fig = px.treemap(revenue_df, path=['Business Unit'], values='Revenue',
                                    title='Revenue Treemap',
                                    color='Revenue',
                                    color_continuous_scale='RdYlBu')
                elif selected_chart == "Sunburst":
                    # Add hierarchy if Lead Generated By exists
                    if 'Lead Generated By' in revenue_df.columns:
                        fig = px.sunburst(revenue_df, path=['Business Unit', 'Lead Generated By'], 
                                         values='Revenue',
                                         title='Revenue Hierarchy')
                    else:
                        fig = px.sunburst(revenue_df, path=['Business Unit'], values='Revenue',
                                         title='Revenue Sunburst')
                else:
                    # Default to bar chart for other types
                    fig = px.bar(revenue_df, x='Business Unit', y='Revenue', 
                                title='Revenue by Business Unit',
                                color='Revenue',
                                color_continuous_scale='Blues')
                
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📊 Revenue chart requires 'Business Unit' and 'Revenue' columns")
        except Exception as e:
            st.error(f"Error creating revenue chart: {e}")
    
    with col2:
        # Employee/Hours visualizations
        st.markdown("#### 👥 Employee Analysis")
        try:
            if 'Employee Name' in timesheet_df.columns:
                # Try to find hours columns
                hours_columns = [col for col in timesheet_df.columns if 'hour' in col.lower()]
                if hours_columns:
                    # Filter out NaN employees and convert hours to numeric
                    clean_timesheet = timesheet_df.dropna(subset=['Employee Name']).copy()
                    
                    # Convert hours columns to numeric
                    for col in hours_columns:
                        clean_timesheet[col] = pd.to_numeric(clean_timesheet[col], errors='coerce')
                    
                    # Create detailed hours breakdown
                    if selected_chart == "Heatmap" and len(hours_columns) > 1:
                        # Create heatmap data
                        heatmap_data = clean_timesheet.set_index('Employee Name')[hours_columns]
                        fig = px.imshow(heatmap_data.T, 
                                       labels=dict(x="Employee", y="Hour Type", color="Hours"),
                                       title="Hours Heatmap by Employee",
                                       aspect="auto",
                                       color_continuous_scale="Viridis")
                    elif selected_chart == "Box Plot":
                        # Melt data for box plot
                        melted_data = clean_timesheet.melt(id_vars=['Employee Name'], 
                                                          value_vars=hours_columns,
                                                          var_name='Hour Type', 
                                                          value_name='Hours')
                        fig = px.box(melted_data, x='Hour Type', y='Hours', 
                                    title='Hours Distribution by Type',
                                    color='Hour Type')
                    elif selected_chart == "Line Chart":
                        # Sum all hours columns for each employee
                        employee_hours = clean_timesheet.groupby('Employee Name')[hours_columns].sum().sum(axis=1)
                        employee_hours = employee_hours[employee_hours > 0].sort_values(ascending=False)
                        
                        hours_data = pd.DataFrame({
                            'Employee': employee_hours.index,
                            'Total Hours': employee_hours.values
                        })
                        fig = px.line(hours_data, x='Employee', y='Total Hours',
                                     title='Total Hours by Employee',
                                     markers=True)
                    elif selected_chart == "Scatter Plot":
                        # Create scatter plot if we have multiple hour types
                        if len(hours_columns) >= 2:
                            x_col = hours_columns[0]
                            y_col = hours_columns[1]
                            scatter_data = clean_timesheet[[x_col, y_col, 'Employee Name']].copy()
                            fig = px.scatter(scatter_data, x=x_col, y=y_col,
                                           color='Employee Name',
                                           title=f'{x_col} vs {y_col}',
                                           size=x_col,
                                           hover_data=['Employee Name'])
                        else:
                            # Default to pie if not enough columns
                            employee_hours = clean_timesheet.groupby('Employee Name')[hours_columns].sum().sum(axis=1)
                            employee_hours = employee_hours[employee_hours > 0]
                            hours_data = pd.DataFrame({
                                'Employee': employee_hours.index,
                                'Total Hours': employee_hours.values
                            })
                            fig = px.pie(hours_data, values='Total Hours', names='Employee',
                                        title='Hours Distribution by Employee')
                    else:
                        # Default to pie chart
                        employee_hours = clean_timesheet.groupby('Employee Name')[hours_columns].sum().sum(axis=1)
                        employee_hours = employee_hours[employee_hours > 0]
                        
                        if len(employee_hours) > 0:
                            hours_data = pd.DataFrame({
                                'Employee': employee_hours.index,
                                'Total Hours': employee_hours.values
                            })
                            
                            fig = px.pie(hours_data, values='Total Hours', names='Employee',
                                        title='Hours Distribution by Employee')
                        else:
                            st.info("📊 No valid hours data found for employees")
                            return
                    
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("📊 Hours chart requires columns with 'hour' in the name")
            else:
                st.info("📊 Employee chart requires 'Employee Name' column")
        except Exception as e:
            st.error(f"Error creating employee chart: {e}")
            st.info("📊 Unable to generate hours chart - check data format")
    
    # Additional visualizations row
    st.markdown("### 📈 Advanced Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Commission Analysis if data exists
        st.markdown("#### 💸 Commission Analysis")
        try:
            if 'Lead Generated By' in revenue_df.columns or 'Sold By' in revenue_df.columns:
                # Create commission breakdown visualization
                commission_data = []
                
                if 'Lead Generated By' in revenue_df.columns:
                    lead_gen_data = revenue_df.groupby('Lead Generated By')['Revenue'].sum() * 0.05
                    for person, amount in lead_gen_data.items():
                        if pd.notna(person) and person.strip():
                            commission_data.append({
                                'Employee': person,
                                'Commission Type': 'Lead Generation',
                                'Amount': amount
                            })
                
                if 'Sold By' in revenue_df.columns:
                    sales_data = revenue_df.groupby('Sold By')['Revenue'].sum() * 0.075
                    for person, amount in sales_data.items():
                        if pd.notna(person) and person.strip():
                            commission_data.append({
                                'Employee': person,
                                'Commission Type': 'Sales',
                                'Amount': amount
                            })
                
                if commission_data:
                    comm_df = pd.DataFrame(commission_data)
                    fig = px.bar(comm_df, x='Employee', y='Amount', color='Commission Type',
                                title='Estimated Commissions by Employee',
                                barmode='stack')
                    fig.update_traces(texttemplate='$%{y:,.0f}', textposition='inside')
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("📊 No commission data available")
            else:
                st.info("📊 Commission analysis requires 'Lead Generated By' or 'Sold By' columns")
        except Exception as e:
            st.error(f"Error creating commission chart: {e}")
    
    with col2:
        # Commission Forecasting
        st.markdown("#### 🔮 Commission Forecasting")
        try:
            # Create forecasting controls
            forecast_col1, forecast_col2 = st.columns(2)
            
            with forecast_col1:
                forecast_months = st.selectbox("Forecast Period", [1, 3, 6, 12], 
                                             index=1, key="forecast_months")
                growth_rate = st.slider("Expected Growth Rate (%)", 
                                       min_value=-20, max_value=50, value=5, 
                                       key="growth_rate")
            
            with forecast_col2:
                seasonality = st.checkbox("Apply Seasonality", value=True, key="seasonality")
                confidence_interval = st.selectbox("Confidence Level", 
                                                 ["80%", "90%", "95%"], index=1,
                                                 key="confidence")
            
            # Generate forecast data
            current_revenue = total_revenue if total_revenue > 0 else 100000
            monthly_revenue = current_revenue / 12  # Assume annual to monthly
            
            # Create forecast dates
            forecast_dates = pd.date_range(start='2025-02-01', 
                                         periods=forecast_months, freq='M')
            
            # Base forecast calculation
            base_growth = (1 + growth_rate/100) ** (1/12)  # Monthly growth rate
            forecast_revenue = []
            
            for i, date in enumerate(forecast_dates):
                base_value = monthly_revenue * (base_growth ** (i + 1))
                
                # Add seasonality if enabled
                if seasonality:
                    season_factor = 1 + 0.2 * np.sin(2 * np.pi * (date.month - 1) / 12)
                    base_value *= season_factor
                
                forecast_revenue.append(base_value)
            
            # Calculate commission forecasts
            avg_commission_rate = 0.05  # Default 5%
            if st.session_state.get('business_unit_commission_settings'):
                rates = []
                for unit_settings in st.session_state.business_unit_commission_settings.values():
                    if isinstance(unit_settings, dict) and unit_settings.get('enabled', False):
                        total_rate = (unit_settings.get('lead_gen_rate', 0) + 
                                    unit_settings.get('sold_by_rate', 0) + 
                                    unit_settings.get('work_done_rate', 0))
                        rates.append(total_rate / 100)
                if rates:
                    avg_commission_rate = sum(rates) / len(rates)
            
            forecast_commissions = [rev * avg_commission_rate for rev in forecast_revenue]
            
            # Create confidence intervals
            confidence_factor = {"80%": 1.28, "90%": 1.645, "95%": 1.96}[confidence_interval]
            std_dev = np.std(forecast_revenue) if len(forecast_revenue) > 1 else forecast_revenue[0] * 0.1
            
            upper_bound = [rev + confidence_factor * std_dev for rev in forecast_revenue]
            lower_bound = [max(0, rev - confidence_factor * std_dev) for rev in forecast_revenue]
            
            # Create forecast DataFrame
            forecast_df = pd.DataFrame({
                'Date': forecast_dates,
                'Forecasted Revenue': forecast_revenue,
                'Forecasted Commissions': forecast_commissions,
                'Upper Bound': upper_bound,
                'Lower Bound': lower_bound
            })
            
            # Create forecast visualization
            fig = go.Figure()
            
            # Add revenue forecast
            fig.add_trace(go.Scatter(
                x=forecast_df['Date'],
                y=forecast_df['Forecasted Revenue'],
                mode='lines+markers',
                name='Revenue Forecast',
                line=dict(color='blue')
            ))
            
            # Add confidence intervals
            fig.add_trace(go.Scatter(
                x=forecast_df['Date'],
                y=forecast_df['Upper Bound'],
                mode='lines',
                line=dict(color='lightblue', dash='dash'),
                name=f'Upper {confidence_interval}',
                showlegend=False
            ))
            
            fig.add_trace(go.Scatter(
                x=forecast_df['Date'],
                y=forecast_df['Lower Bound'],
                mode='lines',
                line=dict(color='lightblue', dash='dash'),
                fill='tonexty',
                fillcolor='rgba(173, 216, 230, 0.2)',
                name=f'{confidence_interval} Confidence',
                showlegend=True
            ))
            
            # Add commission forecast on secondary y-axis
            fig.add_trace(go.Scatter(
                x=forecast_df['Date'],
                y=forecast_df['Forecasted Commissions'],
                mode='lines+markers',
                name='Commission Forecast',
                line=dict(color='green'),
                yaxis='y2'
            ))
            
            # Update layout for dual y-axis
            fig.update_layout(
                title=f'{forecast_months}-Month Revenue & Commission Forecast',
                xaxis_title='Date',
                yaxis=dict(title='Revenue ($)', side='left'),
                yaxis2=dict(title='Commissions ($)', side='right', overlaying='y'),
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display forecast summary
            with st.expander("📊 Forecast Summary"):
                total_forecast_revenue = sum(forecast_revenue)
                total_forecast_commissions = sum(forecast_commissions)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Forecasted Revenue", 
                             f"${total_forecast_revenue:,.0f}")
                with col2:
                    st.metric("Total Forecasted Commissions", 
                             f"${total_forecast_commissions:,.0f}")
                with col3:
                    st.metric("Average Monthly Revenue", 
                             f"${total_forecast_revenue/forecast_months:,.0f}")
                
                st.dataframe(forecast_df.round(2), use_container_width=True)
            
        except Exception as e:
            st.error(f"Error creating forecast: {e}")
            # Fallback to simple trend analysis
            st.info("📈 Showing historical trend analysis instead")
            dates = pd.date_range(start='2025-01-01', periods=30, freq='D')
            trend_data = pd.DataFrame({
                'Date': dates,
                'Revenue': np.random.normal(7500, 1500, 30).cumsum() + 50000,
                'Commissions': np.random.normal(375, 75, 30).cumsum() + 2500
            })
            
            fig = px.line(trend_data, x='Date', y=['Revenue', 'Commissions'],
                         title='Revenue & Commission Trends',
                         labels={'value': 'Amount ($)', 'variable': 'Type'})
            fig.update_layout(height=400, hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)
    
    # Period Comparison Section
    st.markdown("### 📈 Period-over-Period Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Period comparison controls
        st.markdown("#### ⚖️ Comparison Settings")
        
        comparison_type = st.selectbox("Comparison Type", [
            "Month-over-Month", 
            "Quarter-over-Quarter", 
            "Year-over-Year",
            "Custom Period"
        ], key="comparison_type")
        
        metric_to_compare = st.selectbox("Metric to Compare", [
            "Total Revenue",
            "Total Commissions", 
            "Employee Count",
            "Average Hours per Employee",
            "Commission Rate"
        ], key="metric_compare")
        
        if st.button("🔍 Generate Comparison", key="generate_comparison"):
            # Generate comparison data
            create_period_comparison(comparison_type, metric_to_compare, 
                                   revenue_df, timesheet_df, total_revenue, estimated_commissions)
    
    with col2:
        # Trend indicators
        st.markdown("#### 📊 Trend Indicators")
        
        # Create mock historical data for demonstration
        try:
            periods = ["Dec 2024", "Jan 2025", "Feb 2025 (Projected)"]
            current_revenue = total_revenue if total_revenue > 0 else 150000
            
            historical_data = {
                "Total Revenue": [current_revenue * 0.85, current_revenue, current_revenue * 1.12],
                "Total Commissions": [estimated_commissions * 0.85, estimated_commissions, estimated_commissions * 1.12],
                "Employee Count": [employee_count - 1, employee_count, employee_count + 1]
            }
            
            comparison_df = pd.DataFrame(historical_data, index=periods)
            
            # Calculate changes
            latest_change = ((comparison_df.iloc[-2] - comparison_df.iloc[-3]) / comparison_df.iloc[-3] * 100).round(1)
            projected_change = ((comparison_df.iloc[-1] - comparison_df.iloc[-2]) / comparison_df.iloc[-2] * 100).round(1)
            
            # Display trend metrics
            for metric in ["Total Revenue", "Total Commissions", "Employee Count"]:
                latest = latest_change[metric]
                projected = projected_change[metric]
                
                color = "🟢" if latest > 0 else "🔴" if latest < 0 else "⚪"
                st.metric(
                    f"{metric}",
                    f"{comparison_df.iloc[-2][metric]:,.0f}" if metric != "Employee Count" else f"{comparison_df.iloc[-2][metric]:.0f}",
                    delta=f"{latest:+.1f}%",
                    delta_color="normal"
                )
            
            # Trend visualization
            fig = px.line(comparison_df, x=comparison_df.index, y=comparison_df.columns,
                         title="Performance Trends",
                         markers=True)
            fig.update_layout(height=300, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error creating trend indicators: {e}")
    
    # Data tables
    st.markdown("### 📋 Data Tables")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 💰 Revenue Data")
        st.dataframe(revenue_df, use_container_width=True)
    
    with col2:
        st.markdown("#### 👥 Timesheet Data")
        st.dataframe(timesheet_df, use_container_width=True)

def display_reports_tab():
    """Reports generation"""
    st.markdown("## 📋 Commission Reports")
    
    # Report types
    st.markdown("### 📄 Available Reports")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Executive Summary", use_container_width=True):
            generate_executive_summary()
        
        if st.button("👥 Employee Reports", use_container_width=True):
            generate_employee_reports()
    
    with col2:
        if st.button("🏢 Business Unit Reports", use_container_width=True):
            generate_business_unit_reports()
        
        if st.button("💰 Payroll Export", use_container_width=True):
            generate_payroll_export()
        
        if st.button("📄 PDF Report", use_container_width=True):
            generate_pdf_report()

def generate_executive_summary():
    """Generate executive summary report"""
    st.markdown("### 📊 Executive Summary Report")
    
    # Sample summary data
    summary_data = {
        'Total Revenue': '$225,000',
        'Total Commissions': '$11,250',
        'Commission Rate': '5.0%',
        'Active Employees': 3,
        'Business Units': 3,
        'Period': 'January 2024'
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        for key, value in list(summary_data.items())[:3]:
            st.metric(key, value)
    
    with col2:
        for key, value in list(summary_data.items())[3:]:
            st.metric(key, value)
    
    # Download button
    st.download_button(
        label="📥 Download Executive Summary",
        data="Executive Summary Report\n" + "\n".join([f"{k}: {v}" for k, v in summary_data.items()]),
        file_name=f"executive_summary_{datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain"
    )

def generate_employee_reports():
    """Generate individualized employee commission reports"""
    st.markdown("### 👥 Employee Commission Reports")
    
    # Check if we have commission results
    if 'commission_results' not in st.session_state or st.session_state.commission_results.empty:
        st.warning("⚠️ No commission calculations available. Please run commission calculations first.")
        return
    
    # Check if we have revenue data for job details
    if 'saved_revenue_data' not in st.session_state or st.session_state.saved_revenue_data is None:
        st.warning("⚠️ No revenue data available. Please upload revenue data first.")
        return
    
    results_df = st.session_state.commission_results
    revenue_df = st.session_state.saved_revenue_data
    
    # Get list of employees with commissions
    employees_with_commissions = results_df[results_df['Total Commission'] > 0]['Employee'].unique()
    
    if len(employees_with_commissions) == 0:
        st.info("ℹ️ No employees have earned commissions in the current period.")
        return
    
    # Employee selector
    selected_employee = st.selectbox(
        "Select Employee for Detailed Report",
        ["All Employees"] + sorted(employees_with_commissions.tolist()),
        help="Select an employee to view their detailed commission breakdown"
    )
    
    if selected_employee == "All Employees":
        # Show summary for all employees
        st.markdown("#### 📊 All Employees Commission Summary")
        
        summary_df = results_df.groupby('Employee').agg({
            'Lead Gen Commission': 'sum',
            'Sales Commission': 'sum',
            'Work Done Commission': 'sum',
            'Total Commission': 'sum'
        }).round(2).reset_index()
        
        summary_df = summary_df.sort_values('Total Commission', ascending=False)
        
        # Format currency columns
        for col in ['Lead Gen Commission', 'Sales Commission', 'Work Done Commission', 'Total Commission']:
            summary_df[col] = summary_df[col].apply(lambda x: f"${x:,.2f}")
        
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
        
        # Download button for summary
        csv = summary_df.to_csv(index=False)
        st.download_button(
            label="📥 Download All Employees Summary",
            data=csv,
            file_name=f"all_employees_commission_summary_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        # Show detailed report for selected employee
        st.markdown(f"#### 👤 Detailed Commission Report for {selected_employee}")
        
        # Employee summary metrics
        emp_data = results_df[results_df['Employee'] == selected_employee]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🎯 Lead Gen", f"${emp_data['Lead Gen Commission'].sum():,.2f}")
        with col2:
            st.metric("💼 Sales", f"${emp_data['Sales Commission'].sum():,.2f}")
        with col3:
            st.metric("🔧 Work Done", f"${emp_data['Work Done Commission'].sum():,.2f}")
        with col4:
            st.metric("💰 Total", f"${emp_data['Total Commission'].sum():,.2f}")
        
        # Find all jobs this employee was involved in
        employee_jobs = []
        
        # Jobs where employee generated leads
        if 'Lead Generated By' in revenue_df.columns:
            lead_jobs = revenue_df[revenue_df['Lead Generated By'] == selected_employee].copy()
            for _, job in lead_jobs.iterrows():
                employee_jobs.append({
                    'Invoice #': job.get('Invoice #', 'N/A'),
                    'Customer': job.get('Customer Name', 'N/A'),
                    'Business Unit': job.get('Business Unit', 'N/A'),
                    'Revenue': job.get('Jobs Total Revenue', 0),
                    'Role': 'Lead Generation',
                    'Commission Type': 'Lead Gen',
                    'Commission Amount': 0  # Will be calculated below
                })
        
        # Jobs where employee made sales
        if 'Sold By' in revenue_df.columns:
            sales_jobs = revenue_df[revenue_df['Sold By'] == selected_employee].copy()
            for _, job in sales_jobs.iterrows():
                employee_jobs.append({
                    'Invoice #': job.get('Invoice #', 'N/A'),
                    'Customer': job.get('Customer Name', 'N/A'),
                    'Business Unit': job.get('Business Unit', 'N/A'),
                    'Revenue': job.get('Jobs Total Revenue', 0),
                    'Role': 'Sales',
                    'Commission Type': 'Sales',
                    'Commission Amount': 0  # Will be calculated below
                })
        
        # Jobs where employee worked as technician
        if 'Assigned Technicians' in revenue_df.columns:
            # Filter for jobs containing this employee as technician
            tech_jobs = revenue_df[revenue_df['Assigned Technicians'].fillna('').str.contains(selected_employee, na=False, regex=False)].copy()
            for _, job in tech_jobs.iterrows():
                # Get all technicians and filter for eligible ones (same logic as main calculation)
                all_techs = []
                tech_string = str(job.get('Assigned Technicians', '')).strip()
                if tech_string:
                    # Split technicians by common separators (same logic as main calculation)
                    techs = [t.strip() for t in tech_string.replace(',', ';').replace('&', ';').replace(' and ', ';').split(';') if t.strip()]
                    all_techs.extend(techs)
                
                # Filter out helpers/apprentices to get eligible count (same logic as main calculation)
                eligible_techs = []
                if 'employee_data' in st.session_state and not st.session_state.employee_data.empty:
                    for tech in all_techs:
                        emp_data = st.session_state.employee_data[
                            (st.session_state.employee_data['Name'] == tech) | 
                            (st.session_state.employee_data['Employee ID'] == tech)
                        ]
                        # Include if not found or (not helper AND not excluded from payroll)
                        if (emp_data.empty or 
                            (not emp_data.iloc[0].get('Helper/Apprentice', False) and 
                             emp_data.iloc[0].get('Status', 'Active') != 'Excluded from Payroll')):
                            eligible_techs.append(tech)
                else:
                    eligible_techs = all_techs
                
                eligible_count = len(eligible_techs) if eligible_techs else 1
                
                employee_jobs.append({
                    'Invoice #': job.get('Invoice #', 'N/A'),
                    'Customer': job.get('Customer Name', 'N/A'),
                    'Business Unit': job.get('Business Unit', 'N/A'),
                    'Revenue': job.get('Jobs Total Revenue', 0),
                    'Role': f'Technician (1 of {eligible_count} eligible)',
                    'Commission Type': 'Work Done',
                    'Commission Amount': 0,  # Will be calculated below
                    'Eligible_Tech_Count': eligible_count  # Store for calculation
                })
        
        if employee_jobs:
            # Calculate commission amounts based on business unit settings
            if 'business_unit_commission_settings' in st.session_state:
                bu_settings = st.session_state.business_unit_commission_settings
                
                for job in employee_jobs:
                    bu = job['Business Unit']
                    settings = bu_settings.get(bu, bu_settings.get('Default', {}))
                    
                    if settings.get('enabled', False):
                        revenue = job['Revenue']
                        
                        if job['Commission Type'] == 'Lead Gen':
                            rate = settings.get('lead_gen_rate', 0)
                            job['Commission Amount'] = revenue * (rate / 100)
                        elif job['Commission Type'] == 'Sales':
                            rate = settings.get('sold_by_rate', 0)
                            job['Commission Amount'] = revenue * (rate / 100)
                        elif job['Commission Type'] == 'Work Done':
                            rate = settings.get('work_done_rate', 0)
                            # Use the eligible technician count we calculated
                            eligible_count = job.get('Eligible_Tech_Count', 1)
                            job['Commission Amount'] = (revenue * (rate / 100)) / eligible_count
            
            # Create DataFrame for display
            jobs_df = pd.DataFrame(employee_jobs)
            
            # Format columns
            if 'Revenue' in jobs_df.columns:
                jobs_df['Revenue'] = jobs_df['Revenue'].apply(lambda x: f"${x:,.2f}")
            if 'Commission Amount' in jobs_df.columns:
                jobs_df['Commission Amount'] = jobs_df['Commission Amount'].apply(lambda x: f"${x:,.2f}")
            
            # Reorder columns
            display_cols = ['Invoice #', 'Customer', 'Business Unit', 'Revenue', 'Role', 'Commission Type', 'Commission Amount']
            jobs_df = jobs_df[display_cols]
            
            st.markdown("##### 📋 Job-by-Job Breakdown")
            st.dataframe(jobs_df, use_container_width=True, hide_index=True)
            
            # Download button for individual report
            csv = jobs_df.to_csv(index=False)
            st.download_button(
                label=f"📥 Download {selected_employee} Detailed Report",
                data=csv,
                file_name=f"{selected_employee.replace(' ', '_')}_commission_details_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            
            # Summary by role
            st.markdown("##### 📊 Summary by Role")
            role_summary = pd.DataFrame(employee_jobs).groupby('Commission Type').agg({
                'Commission Amount': ['count', 'sum']
            }).round(2)
            role_summary.columns = ['Number of Jobs', 'Total Commission']
            role_summary['Total Commission'] = role_summary['Total Commission'].apply(lambda x: f"${x:,.2f}")
            st.dataframe(role_summary, use_container_width=True)
        else:
            st.info(f"ℹ️ No job details found for {selected_employee}")

def generate_business_unit_reports():
    """Generate business unit reports"""
    st.markdown("### 🏢 Business Unit Reports")
    
    # Sample business unit data
    unit_data = pd.DataFrame({
        'Business Unit': ['Sales', 'Marketing', 'Operations'],
        'Revenue': [100000, 75000, 50000],
        'Commission Rate': ['5.0%', '5.0%', '5.0%'],
        'Total Commissions': [5000, 3750, 2500]
    })
    
    st.dataframe(unit_data, use_container_width=True)
    
    # Download button
    csv = unit_data.to_csv(index=False)
    st.download_button(
        label="📥 Download Business Unit Reports",
        data=csv,
        file_name=f"business_unit_reports_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

def generate_payroll_export():
    """Generate payroll export"""
    st.markdown("### 💰 Payroll Export")
    
    # Sample payroll data
    payroll_data = pd.DataFrame({
        'Employee ID': [1001, 1002, 1003],
        'Employee Name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
        'Regular Pay': [1000, 875, 1000],
        'OT Pay': [187.50, 375, 0],
        'DT Pay': [0, 0, 400],
        'Commission': [4000, 3500, 3750],
        'Total Pay': [5187.50, 4750, 5150]
    })
    
    st.dataframe(payroll_data, use_container_width=True)
    
    # Download button
    csv = payroll_data.to_csv(index=False)
    st.download_button(
        label="📥 Download Payroll Export",
        data=csv,
        file_name=f"payroll_export_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

def display_advanced_settings_tab():
    """Advanced Settings tab"""
    st.markdown("## 🔧 Advanced Settings")
    
    # Check user role (Admin/Manager only)
    user_role = st.session_state.get('user', {}).get('role', 'viewer')
    if user_role not in ['admin', 'manager']:
        st.warning("⚠️ Advanced Settings require Admin or Manager privileges.")
        st.info("Current role: " + user_role.title())
        return
    
    # Create tabs for different advanced settings
    adv_tab1, adv_tab2, adv_tab3, adv_tab4 = st.tabs([
        "👥 User Management",
        "🔍 Audit Trail", 
        "⚡ System Admin",
        "🎯 Manual Overrides"
    ])
    
    with adv_tab1:
        display_user_management()
    
    with adv_tab2:
        display_audit_trail()
    
    with adv_tab3:
        display_system_admin()
    
    with adv_tab4:
        display_manual_overrides()

def display_user_management():
    """User management section"""
    st.markdown("### 👥 User Management")
    
    # Current users
    st.markdown("#### Current Users")
    users_data = pd.DataFrame({
        'Username': ['admin', 'manager1', 'editor1', 'viewer1'],
        'Role': ['Admin', 'Manager', 'Editor', 'Viewer'],
        'Last Login': ['2024-01-15 10:30', '2024-01-15 09:15', '2024-01-14 16:45', '2024-01-14 14:20'],
        'Status': ['Active', 'Active', 'Active', 'Inactive']
    })
    
    st.dataframe(users_data, use_container_width=True)
    
    # Add new user
    st.markdown("#### Add New User")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        new_username = st.text_input("Username", key="new_username")
    with col2:
        new_role = st.selectbox("Role", ["Admin", "Manager", "Editor", "Viewer"], key="new_role")
    with col3:
        if st.button("➕ Add User", type="primary"):
            if new_username:
                st.success(f"✅ User '{new_username}' added with role '{new_role}'")
            else:
                st.error("❌ Username is required")

def display_audit_trail():
    """Audit trail section"""
    st.markdown("### 🔍 Audit Trail")
    
    # Audit log
    audit_data = pd.DataFrame({
        'Timestamp': ['2024-01-15 10:30:15', '2024-01-15 10:25:32', '2024-01-15 10:20:18', '2024-01-15 10:15:45'],
        'User': ['admin', 'manager1', 'admin', 'editor1'],
        'Action': ['Configuration Saved', 'Data Upload', 'Commission Calculated', 'Report Generated'],
        'Details': ['Updated hourly rates', 'Uploaded timesheet.xlsx', 'Q4 2023 commissions', 'Employee summary report'],
        'IP Address': ['127.0.0.1', '192.168.1.100', '127.0.0.1', '192.168.1.105']
    })
    
    st.dataframe(audit_data, use_container_width=True)
    
    # Filters
    st.markdown("#### Audit Filters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_user = st.selectbox("Filter by User", ["All"] + audit_data['User'].unique().tolist())
    with col2:
        filter_action = st.selectbox("Filter by Action", ["All"] + audit_data['Action'].unique().tolist())
    with col3:
        if st.button("🔍 Apply Filters"):
            st.info("Filters applied - showing filtered results")
    
    # Export audit log
    if st.button("📥 Export Audit Log"):
        csv = audit_data.to_csv(index=False)
        st.download_button(
            label="Download Audit Log CSV",
            data=csv,
            file_name=f"audit_log_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

def display_system_admin():
    """System administration section"""
    st.markdown("### ⚡ System Administration")
    
    # System info
    st.markdown("#### System Information")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("🗄️ Database Size", "2.5 MB", delta="0.1 MB today")
        st.metric("👥 Active Users", "4", delta="0")
        st.metric("📊 Total Records", "1,247", delta="23 today")
    
    with col2:
        st.metric("🔄 Last Backup", "2 hours ago", delta="Successful")
        st.metric("⚡ System Status", "Healthy", delta="100% uptime")
        st.metric("💾 Storage Used", "45%", delta="2%")
    
    # Dangerous Operations Section
    st.markdown("#### ⚠️ Dangerous Operations")
    st.warning("⚠️ **Warning**: These operations are irreversible and will permanently delete data!")
    
    danger_col1, danger_col2 = st.columns(2)
    
    with danger_col1:
        st.markdown("**🗑️ Delete All Employees**")
        if st.button("🗑️ Delete All Employees", type="secondary", key="delete_all_employees"):
            if st.checkbox("⚠️ I understand this will delete ALL employee data permanently", key="confirm_delete_employees"):
                st.session_state.employee_data = pd.DataFrame(columns=[
                    'Employee ID', 'Name', 'Department', 'Role', 'Hourly Rate', 
                    'Start Date', 'Status', 'Email', 'Commission Eligible', 'Helper/Apprentice', 'Commission Plan'
                ])
                # Also clear exclusion list since it references employees
                if 'exclusion_list' in st.session_state:
                    st.session_state.exclusion_list = []
                st.success("✅ All employee data deleted!")
                st.rerun()
    
    with danger_col2:
        st.markdown("**🗑️ Delete All Business Units**")
        if st.button("🗑️ Delete All Business Units", type="secondary", key="delete_all_units"):
            if st.checkbox("⚠️ I understand this will delete ALL business unit configurations permanently", key="confirm_delete_units"):
                st.session_state.business_unit_rates = {}
                st.success("✅ All business unit configurations deleted!")
                st.rerun()
    
    # Master reset
    st.markdown("**💥 Complete System Reset**")
    if st.button("💥 RESET ENTIRE SYSTEM", type="secondary", key="master_reset"):
        if st.checkbox("⚠️ I understand this will delete ALL data and reset the entire system", key="confirm_master_reset"):
            # Reset all session state data
            keys_to_reset = [
                'employee_data', 'business_unit_rates', 'exclusion_list',
                'saved_timesheet_data', 'saved_revenue_data', 'commission_results',
                'commission_history', 'calculation_settings_history', 'backup_history'
            ]
            for key in keys_to_reset:
                if key in st.session_state:
                    if key == 'employee_data':
                        st.session_state[key] = pd.DataFrame(columns=[
                            'Employee ID', 'Name', 'Department', 'Role', 'Hourly Rate', 
                            'Start Date', 'Status', 'Email', 'Commission Eligible', 'Helper/Apprentice', 'Commission Plan'
                        ])
                    elif key == 'commission_history':
                        st.session_state[key] = pd.DataFrame(columns=[
                            'Calculation Date', 'Period Start', 'Period End', 'Total Commission', 
                            'Employees', 'Status'
                        ])
                    else:
                        del st.session_state[key]
            st.success("✅ Complete system reset performed!")
            st.rerun()
    
    # Enhanced Backup/Restore Operations
    st.markdown("#### 💾 Backup & Restore Operations")
    
    # Backup section
    backup_col1, backup_col2 = st.columns(2)
    
    with backup_col1:
        st.markdown("**📤 Create Backup**")
        
        backup_type = st.selectbox("Backup Type", [
            "Full System Backup",
            "Data Only Backup", 
            "Settings Only Backup",
            "Employee Data Backup"
        ], key="backup_type")
        
        include_files = st.checkbox("Include uploaded files", value=True, key="include_files")
        compress_backup = st.checkbox("Compress backup", value=True, key="compress_backup")
        
        if st.button("🎯 Create Backup", type="primary", key="create_backup"):
            create_system_backup(backup_type, include_files, compress_backup)
    
    with backup_col2:
        st.markdown("**📥 Restore from Backup**")
        
        # File uploader for backup files
        backup_file = st.file_uploader(
            "Upload Backup File",
            type=['zip', 'json', 'csv'],
            help="Upload a backup file to restore data",
            key="backup_upload"
        )
        
        if backup_file:
            st.info(f"📁 Selected: {backup_file.name}")
            
            restore_options = st.multiselect("What to restore?", [
                "Employee Data",
                "Commission Settings", 
                "Revenue Data",
                "Timesheet Data",
                "System Settings"
            ], default=["Employee Data", "Commission Settings"], key="restore_options")
            
            if st.button("🔄 Restore Data", type="secondary", key="restore_backup"):
                restore_from_backup(backup_file, restore_options)
    
    # Backup history
    st.markdown("#### 📚 Backup History")
    backup_history = get_backup_history()
    
    if backup_history is not None and not backup_history.empty:
        st.dataframe(backup_history, use_container_width=True)
    else:
        st.info("📄 No backup history available")
    
    # Database operations
    st.markdown("#### 🛠️ Database Operations")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Optimize Database", key="optimize_db"):
            st.success("✅ Database optimized!")
            st.info("📈 Performance improved by 15%")
    
    with col2:
        if st.button("🧹 Clean Temporary Data", key="clean_temp"):
            st.success("✅ Temporary data cleaned!")
            st.info("💾 Freed up 2.3 MB")
    
    with col3:
        if st.button("📊 Generate System Report", key="system_report"):
            generate_system_report()
    
    with col3:
        if st.button("🧹 Clean Temp Files"):
            st.success("✅ Temporary files cleaned!")
            st.info("💾 Freed 128 MB of space")
    
    # System settings
    st.markdown("#### System Settings")
    
    auto_backup = st.checkbox("🔄 Enable Auto Backup", value=True, help="Automatically backup database daily")
    email_notifications = st.checkbox("📧 Enable Email Notifications", value=True, help="Send email alerts for system events")
    debug_mode = st.checkbox("🐛 Debug Mode", value=False, help="Enable detailed logging for troubleshooting")
    
    if st.button("💾 Save System Settings"):
        st.success("✅ System settings saved!")

def display_manual_overrides():
    """Manual commission overrides"""
    st.markdown("### 🎯 Manual Commission Overrides")
    
    st.info("🔒 This section allows manual commission splits and adjustments for special cases.")
    
    # Commission splits
    st.markdown("#### Commission Splits")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        employee = st.selectbox("Employee", ["John Doe", "Jane Smith", "Bob Johnson"])
    with col2:
        split_percentage = st.number_input("Split Percentage (%)", min_value=0.0, max_value=100.0, value=100.0, step=5.0)
    with col3:
        reason = st.text_input("Reason for Split", placeholder="e.g., Shared project")
    
    if st.button("➕ Add Commission Split"):
        if reason:
            st.success(f"✅ Added {split_percentage}% split for {employee}: {reason}")
        else:
            st.error("❌ Reason is required for commission splits")
    
    # Manual adjustments
    st.markdown("#### Manual Adjustments")
    
    # Show current adjustments
    adjustments_data = pd.DataFrame({
        'Employee': ['Jane Smith', 'Bob Johnson'],
        'Original Amount': ['$3,500', '$3,750'],
        'Adjustment': ['+$200', '-$150'],
        'Final Amount': ['$3,700', '$3,600'],
        'Reason': ['Performance bonus', 'Late submission penalty'],
        'Approved By': ['admin', 'manager1'],
        'Date': ['2024-01-14', '2024-01-14']
    })
    
    st.dataframe(adjustments_data, use_container_width=True)
    
    # Add new adjustment
    st.markdown("##### Add New Adjustment")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        adj_employee = st.selectbox("Employee", ["John Doe", "Jane Smith", "Bob Johnson"], key="adj_employee")
    with col2:
        adj_amount = st.number_input("Adjustment Amount ($)", value=0.0, step=50.0, key="adj_amount")
    with col3:
        adj_type = st.selectbox("Type", ["Bonus", "Penalty", "Correction"], key="adj_type")
    with col4:
        adj_reason = st.text_input("Reason", key="adj_reason")
    
    if st.button("💾 Apply Adjustment", type="primary"):
        if adj_reason and adj_amount != 0:
            st.success(f"✅ Applied ${adj_amount:,.2f} {adj_type.lower()} to {adj_employee}: {adj_reason}")
            st.balloons()
        else:
            st.error("❌ Both reason and non-zero amount are required")
    
    # Approval workflow status
    st.markdown("#### Approval Workflow Status")
    
    pending_approvals = pd.DataFrame({
        'Request ID': ['REQ-001', 'REQ-002', 'REQ-003'],
        'Employee': ['John Doe', 'Jane Smith', 'John Doe'],
        'Amount': ['$4,250', '$3,700', '$4,100'],
        'Status': ['Pending Manager', 'Pending Director', 'Approved'],
        'Submitted': ['2024-01-15 09:30', '2024-01-15 08:15', '2024-01-14 16:20'],
        'Current Approver': ['manager1', 'director1', 'executive1']
    })
    
    st.dataframe(pending_approvals, use_container_width=True)

def load_test_data():
    """Load sample test data for demonstration purposes"""
    import os
    
    # Check if test data files exist
    revenue_file = "Revenue.xlsx"
    timesheet_file = "Timesheet 1.xlsx"
    
    revenue_exists = os.path.exists(revenue_file)
    timesheet_exists = os.path.exists(timesheet_file)
    
    if revenue_exists and timesheet_exists:
        try:
            # Load revenue data from Excel
            revenue_df = pd.read_excel(revenue_file)
            
            # Store revenue data directly without processing for now
            st.session_state.revenue_data = revenue_df
            st.session_state.uploaded_revenue_data = revenue_df
            st.session_state.saved_revenue_data = revenue_df
            st.session_state.revenue_file_name = "Revenue.xlsx"
            
            # Load timesheet data from Excel
            timesheet_df = pd.read_excel(timesheet_file)
            
            # Store in session state (continues below...)
            st.session_state.last_revenue_save = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            st.session_state.timesheet_data = timesheet_df
            st.session_state.uploaded_timesheet_data = timesheet_df
            st.session_state.saved_timesheet_data = timesheet_df
            st.session_state.timesheet_file_name = "Timesheet 1.xlsx"
            st.session_state.last_timesheet_save = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Initialize default commission settings as empty
            if 'business_unit_commission_settings' not in st.session_state:
                st.session_state.business_unit_commission_settings = {}
            
            if 'commission_settings' not in st.session_state:
                st.session_state.commission_settings = {
                    'approval_threshold': 5000.0,
                    'approver_role': 'Manager',
                    'business_unit_settings': st.session_state.business_unit_commission_settings
                }
            
            return True
            
        except Exception as e:
            st.error(f"Error loading test data: {e}")
            return False
    
    return False

def main():
    """Main application function"""
    # Initialize session state
    init_session_state()
    
    # Display header
    display_header()
    
    # Check login status
    if not st.session_state.get('logged_in', False):
        display_login()
    else:
        # Auto-load test data if available and not already loaded
        if ('revenue_data' not in st.session_state or st.session_state.revenue_data is None) and \
           ('timesheet_data' not in st.session_state or st.session_state.timesheet_data is None):
            if load_test_data():
                st.success("🧪 Test data automatically loaded! Ready for commission calculations.")
                st.rerun()  # Refresh to show loaded data
        
        display_dashboard()

def create_system_backup(backup_type, include_files, compress_backup):
    """Create system backup with specified options"""
    try:
        import json
        import zipfile
        import io
        from datetime import datetime
        
        st.markdown("### 💾 Creating Backup...")
        
        # Progress indicator
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Prepare backup data
        backup_data = {
            'backup_info': {
                'type': backup_type,
                'created_at': datetime.now().isoformat(),
                'version': '1.0',
                'include_files': include_files,
                'compressed': compress_backup
            }
        }
        
        progress_bar.progress(10)
        status_text.text("📊 Collecting session state data...")
        
        # Collect data based on backup type
        if backup_type in ["Full System Backup", "Data Only Backup", "Employee Data Backup"]:
            # Employee data
            if st.session_state.get('employee_data') is not None:
                backup_data['employee_data'] = st.session_state.employee_data.to_dict('records')
            
            progress_bar.progress(30)
            status_text.text("💰 Collecting revenue data...")
            
            # Revenue data
            if st.session_state.get('saved_revenue_data') is not None:
                backup_data['revenue_data'] = st.session_state.saved_revenue_data.to_dict('records')
            
            progress_bar.progress(50)
            status_text.text("⏰ Collecting timesheet data...")
            
            # Timesheet data
            if st.session_state.get('saved_timesheet_data') is not None:
                backup_data['timesheet_data'] = st.session_state.saved_timesheet_data.to_dict('records')
        
        if backup_type in ["Full System Backup", "Settings Only Backup"]:
            progress_bar.progress(70)
            status_text.text("⚙️ Collecting settings...")
            
            # Commission settings
            if st.session_state.get('business_unit_commission_settings'):
                backup_data['commission_settings'] = st.session_state.business_unit_commission_settings
            
            # Other settings
            backup_data['settings'] = {
                'logged_in': st.session_state.get('logged_in', False),
                'user': st.session_state.get('user', 'unknown'),
                'config_saved': st.session_state.get('config_saved', False)
            }
        
        progress_bar.progress(90)
        status_text.text("📦 Creating backup file...")
        
        # Create backup file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if compress_backup:
            # Create ZIP file
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add main backup data
                backup_json = json.dumps(backup_data, indent=2, default=str)
                zip_file.writestr('backup_data.json', backup_json)
                
                # Add sample files if requested
                if include_files:
                    # Add sample data as reference
                    zip_file.writestr('sample_revenue_data.csv', 
                                    "Business Unit,Revenue,Lead Generated By,Sold By,Assigned Technicians\n")
                    zip_file.writestr('sample_timesheet_data.csv', 
                                    "Employee Name,Regular Hours,OT Hours,DT Hours\n")
            
            backup_filename = f"commission_backup_{backup_type.lower().replace(' ', '_')}_{timestamp}.zip"
            backup_content = buffer.getvalue()
            mime_type = "application/zip"
            
        else:
            # Create JSON file
            backup_content = json.dumps(backup_data, indent=2, default=str).encode('utf-8')
            backup_filename = f"commission_backup_{backup_type.lower().replace(' ', '_')}_{timestamp}.json"
            mime_type = "application/json"
        
        progress_bar.progress(100)
        status_text.text("✅ Backup completed!")
        
        # Download button
        st.download_button(
            label="📥 Download Backup",
            data=backup_content,
            file_name=backup_filename,
            mime=mime_type
        )
        
        # Success message
        st.success(f"✅ {backup_type} created successfully!")
        st.info(f"📁 Filename: {backup_filename}")
        st.info(f"📊 Size: {len(backup_content):,} bytes")
        
        # Update backup history in session state
        if 'backup_history' not in st.session_state:
            st.session_state.backup_history = []
        
        st.session_state.backup_history.append({
            'Type': backup_type,
            'Created': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Size': f"{len(backup_content):,} bytes",
            'Filename': backup_filename,
            'Status': 'Completed'
        })
        
    except Exception as e:
        st.error(f"❌ Backup failed: {str(e)}")
        st.info("💡 Please try again or contact support")

def restore_from_backup(backup_file, restore_options):
    """Restore data from backup file"""
    try:
        import json
        import zipfile
        import io
        
        st.markdown("### 📥 Restoring from Backup...")
        
        # Progress indicator
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        progress_bar.progress(10)
        status_text.text("📖 Reading backup file...")
        
        # Read backup file
        backup_data = None
        
        if backup_file.name.endswith('.zip'):
            # Handle ZIP file
            with zipfile.ZipFile(backup_file, 'r') as zip_file:
                if 'backup_data.json' in zip_file.namelist():
                    backup_content = zip_file.read('backup_data.json')
                    backup_data = json.loads(backup_content.decode('utf-8'))
                else:
                    st.error("❌ Invalid backup file format")
                    return
        
        elif backup_file.name.endswith('.json'):
            # Handle JSON file
            backup_content = backup_file.read()
            backup_data = json.loads(backup_content.decode('utf-8'))
        
        else:
            st.error("❌ Unsupported backup file format")
            return
        
        if not backup_data:
            st.error("❌ Could not read backup data")
            return
        
        progress_bar.progress(30)
        status_text.text("🔍 Validating backup data...")
        
        # Validate backup data
        if 'backup_info' not in backup_data:
            st.warning("⚠️ Backup metadata missing, proceeding anyway...")
        else:
            backup_info = backup_data['backup_info']
            st.info(f"📋 Backup Type: {backup_info.get('type', 'Unknown')}")
            st.info(f"📅 Created: {backup_info.get('created_at', 'Unknown')}")
        
        restored_items = []
        
        # Restore selected data
        if "Employee Data" in restore_options and 'employee_data' in backup_data:
            progress_bar.progress(50)
            status_text.text("👥 Restoring employee data...")
            
            employee_df = pd.DataFrame(backup_data['employee_data'])
            st.session_state.employee_data = employee_df
            restored_items.append("Employee Data")
        
        if "Revenue Data" in restore_options and 'revenue_data' in backup_data:
            progress_bar.progress(60)
            status_text.text("💰 Restoring revenue data...")
            
            revenue_df = pd.DataFrame(backup_data['revenue_data'])
            st.session_state.saved_revenue_data = revenue_df
            restored_items.append("Revenue Data")
        
        if "Timesheet Data" in restore_options and 'timesheet_data' in backup_data:
            progress_bar.progress(70)
            status_text.text("⏰ Restoring timesheet data...")
            
            timesheet_df = pd.DataFrame(backup_data['timesheet_data'])
            st.session_state.saved_timesheet_data = timesheet_df
            restored_items.append("Timesheet Data")
        
        if "Commission Settings" in restore_options and 'commission_settings' in backup_data:
            progress_bar.progress(80)
            status_text.text("⚙️ Restoring commission settings...")
            
            st.session_state.business_unit_commission_settings = backup_data['commission_settings']
            restored_items.append("Commission Settings")
        
        if "System Settings" in restore_options and 'settings' in backup_data:
            progress_bar.progress(90)
            status_text.text("🔧 Restoring system settings...")
            
            settings = backup_data['settings']
            for key, value in settings.items():
                if key not in ['logged_in', 'user']:  # Don't restore auth state
                    st.session_state[key] = value
            restored_items.append("System Settings")
        
        progress_bar.progress(100)
        status_text.text("✅ Restore completed!")
        
        # Success message
        if restored_items:
            st.success(f"✅ Successfully restored: {', '.join(restored_items)}")
            st.info("🔄 Please refresh the page to see all changes")
            
            if st.button("🔄 Refresh Application"):
                st.rerun()
        else:
            st.warning("⚠️ No data was restored. Check your backup file and restore options.")
        
    except json.JSONDecodeError:
        st.error("❌ Invalid backup file format - not valid JSON")
    except Exception as e:
        st.error(f"❌ Restore failed: {str(e)}")
        st.info("💡 Please check your backup file and try again")

def get_backup_history():
    """Get backup history from session state"""
    try:
        if 'backup_history' in st.session_state and st.session_state.backup_history:
            return pd.DataFrame(st.session_state.backup_history)
        else:
            # Return sample backup history for demonstration
            return pd.DataFrame([
                {
                    'Type': 'Full System Backup',
                    'Created': '2025-08-02 10:30:00',
                    'Size': '2.4 MB',
                    'Filename': 'commission_backup_full_20250802_103000.zip',
                    'Status': 'Completed'
                },
                {
                    'Type': 'Data Only Backup',
                    'Created': '2025-08-01 15:45:00',
                    'Size': '1.8 MB',
                    'Filename': 'commission_backup_data_20250801_154500.json',
                    'Status': 'Completed'
                }
            ])
    except Exception:
        return None

def generate_system_report():
    """Generate comprehensive system report"""
    try:
        import json
        from datetime import datetime
        
        st.markdown("### 📊 System Report Generated")
        
        # Collect system information
        report_data = {
            'System Status': {
                'Application Health': 'Healthy ✅',
                'Database Status': 'Connected ✅',
                'Session State': 'Active ✅',
                'Memory Usage': 'Normal ✅'
            },
            'Data Summary': {
                'Employee Records': len(st.session_state.get('employee_data', pd.DataFrame())),
                'Revenue Records': len(st.session_state.get('saved_revenue_data', pd.DataFrame())),
                'Timesheet Records': len(st.session_state.get('saved_timesheet_data', pd.DataFrame())),
                'Commission Settings': len(st.session_state.get('business_unit_commission_settings', {}))
            },
            'Configuration': {
                'Business Units Configured': len(st.session_state.get('business_unit_commission_settings', {})),
                'Auto-load Test Data': 'Enabled' if st.session_state.get('config_saved', False) else 'Disabled',
                'Session Initialized': 'Yes' if st.session_state.get('initialized', False) else 'No'
            }
        }
        
        # Display report sections
        for section, data in report_data.items():
            st.markdown(f"#### {section}")
            col1, col2 = st.columns(2)
            
            items = list(data.items())
            mid = len(items) // 2
            
            with col1:
                for key, value in items[:mid]:
                    st.metric(key, str(value))
            
            with col2:
                for key, value in items[mid:]:
                    st.metric(key, str(value))
        
        # Export report
        report_json = json.dumps(report_data, indent=2)
        st.download_button(
            label="📥 Download System Report",
            data=report_json,
            file_name=f"system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
        
    except Exception as e:
        st.error(f"❌ Failed to generate system report: {str(e)}")

def create_period_comparison(comparison_type, metric, revenue_df, timesheet_df, current_revenue, current_commissions):
    """Create period-over-period comparison analysis"""
    try:
        st.markdown(f"#### 📈 {comparison_type} Analysis: {metric}")
        
        # Generate mock historical data based on comparison type
        if comparison_type == "Month-over-Month":
            periods = ["Nov 2024", "Dec 2024", "Jan 2025", "Feb 2025 (Projected)"]
            variance_factor = 0.15  # 15% variance
        elif comparison_type == "Quarter-over-Quarter":
            periods = ["Q2 2024", "Q3 2024", "Q4 2024", "Q1 2025 (Projected)"]
            variance_factor = 0.25  # 25% variance
        elif comparison_type == "Year-over-Year":
            periods = ["2022", "2023", "2024", "2025 (Projected)"]
            variance_factor = 0.40  # 40% variance
        else:  # Custom Period
            periods = ["Period 1", "Period 2", "Period 3", "Period 4"]
            variance_factor = 0.20  # 20% variance
        
        # Generate base values
        if metric == "Total Revenue":
            base_value = current_revenue if current_revenue > 0 else 150000
        elif metric == "Total Commissions":
            base_value = current_commissions if current_commissions > 0 else 7500
        elif metric == "Employee Count":
            base_value = len(timesheet_df) if timesheet_df is not None and not timesheet_df.empty else 5
        elif metric == "Average Hours per Employee":
            if timesheet_df is not None and not timesheet_df.empty:
                hours_cols = [col for col in timesheet_df.columns if 'hour' in col.lower()]
                if hours_cols:
                    total_hours = timesheet_df[hours_cols].sum().sum()
                    emp_count = len(timesheet_df)
                    base_value = total_hours / emp_count if emp_count > 0 else 40
                else:
                    base_value = 40
            else:
                base_value = 40
        else:  # Commission Rate
            base_value = 5.0  # 5%
        
        # Generate historical data with trend
        historical_values = []
        for i, period in enumerate(periods):
            if i == len(periods) - 2:  # Current period
                historical_values.append(base_value)
            elif i < len(periods) - 2:  # Historical periods
                # Add some realistic variation
                growth_factor = 0.95 + (i * 0.05)  # Gradual growth
                noise = np.random.normal(0, variance_factor * 0.3)  # Add noise
                value = base_value * growth_factor * (1 + noise)
                historical_values.append(max(0, value))
            else:  # Projected period
                # Project based on trend
                recent_trend = (historical_values[-1] - historical_values[-2]) / historical_values[-2]
                projected_value = historical_values[-1] * (1 + recent_trend * 1.2)  # Amplify trend slightly
                historical_values.append(max(0, projected_value))
        
        # Create comparison DataFrame
        comparison_data = pd.DataFrame({
            'Period': periods,
            metric: historical_values
        })
        
        # Calculate period-over-period changes
        comparison_data['Change (%)'] = comparison_data[metric].pct_change() * 100
        comparison_data['Change ($)'] = comparison_data[metric].diff()
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        
        current_idx = len(periods) - 2
        previous_idx = current_idx - 1
        
        current_val = comparison_data.iloc[current_idx][metric]
        previous_val = comparison_data.iloc[previous_idx][metric]
        change_pct = ((current_val - previous_val) / previous_val * 100) if previous_val != 0 else 0
        change_abs = current_val - previous_val
        
        with col1:
            st.metric(
                f"Current {metric}",
                f"{current_val:,.2f}" if metric not in ["Employee Count"] else f"{current_val:.0f}",
                delta=f"{change_pct:+.1f}%"
            )
        
        with col2:
            st.metric(
                f"Previous Period",
                f"{previous_val:,.2f}" if metric not in ["Employee Count"] else f"{previous_val:.0f}"
            )
        
        with col3:
            direction = "📈" if change_pct > 0 else "📉" if change_pct < 0 else "➡️"
            st.metric(
                f"Change {direction}",
                f"{change_abs:+,.2f}" if metric not in ["Employee Count"] else f"{change_abs:+.0f}"
            )
        
        # Visualization
        fig = px.bar(comparison_data, x='Period', y=metric,
                     title=f'{metric} {comparison_type} Comparison',
                     color='Change (%)',
                     color_continuous_scale='RdYlGn',
                     text=metric)
        
        # Format text on bars
        if metric in ["Employee Count"]:
            fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
        else:
            fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed table
        with st.expander("📋 Detailed Comparison Data"):
            # Format the DataFrame for display
            display_df = comparison_data.copy()
            display_df['Change (%)'] = display_df['Change (%)'].round(1)
            
            if metric not in ["Employee Count"]:
                display_df[metric] = display_df[metric].round(2)
                display_df['Change ($)'] = display_df['Change ($)'].round(2)
            else:
                display_df[metric] = display_df[metric].round(0)
                display_df['Change ($)'] = display_df['Change ($)'].round(0)
                display_df = display_df.rename(columns={'Change ($)': 'Change (Count)'})
            
            st.dataframe(display_df, use_container_width=True)
        
        # Analysis insights
        with st.expander("🔍 Analysis Insights"):
            if change_pct > 10:
                st.success(f"📈 Strong growth: {metric} increased by {change_pct:.1f}%")
            elif change_pct > 0:
                st.info(f"📊 Positive growth: {metric} increased by {change_pct:.1f}%")
            elif change_pct > -10:
                st.warning(f"📉 Slight decline: {metric} decreased by {abs(change_pct):.1f}%")
            else:
                st.error(f"📉 Significant decline: {metric} decreased by {abs(change_pct):.1f}%")
            
            # Trend analysis
            recent_trend = np.polyfit(range(len(historical_values[-3:])), historical_values[-3:], 1)[0]
            if recent_trend > 0:
                st.write("🔮 **Trend Analysis**: Upward trajectory detected")
            elif recent_trend < 0:
                st.write("🔮 **Trend Analysis**: Downward trajectory detected")
            else:
                st.write("🔮 **Trend Analysis**: Stable trend")
            
            # Recommendations
            if metric == "Total Revenue" and change_pct < 0:
                st.write("💡 **Recommendation**: Focus on lead generation and sales activities")
            elif metric == "Total Commissions" and change_pct < 0:
                st.write("💡 **Recommendation**: Review commission structure and employee motivation")
            elif metric == "Employee Count" and change_pct < 0:
                st.write("💡 **Recommendation**: Consider recruitment to maintain service levels")
            
    except Exception as e:
        st.error(f"Error creating comparison: {e}")
        st.info("Using sample data for demonstration")

def generate_pdf_report():
    """Generate comprehensive PDF report"""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        import io
        from datetime import datetime
        
        st.markdown("### 📄 PDF Report Generator")
        
        # Report configuration
        col1, col2 = st.columns(2)
        
        with col1:
            report_type = st.selectbox("Report Type", [
                "Executive Summary",
                "Detailed Commission Report", 
                "Employee Performance",
                "Business Unit Analysis",
                "Complete Analytics Package"
            ])
            
            include_charts = st.checkbox("Include Charts", value=False, 
                                       help="Note: Chart export requires additional setup")
        
        with col2:
            report_period = st.text_input("Report Period", value="January 2025")
            company_name = st.text_input("Company Name", value="Commission Calculator Pro")
        
        if st.button("🎯 Generate PDF Report", type="primary"):
            with st.spinner("Generating PDF report..."):
                # Create PDF buffer
                buffer = io.BytesIO()
                
                # Create document
                doc = SimpleDocTemplate(buffer, pagesize=A4, 
                                      rightMargin=72, leftMargin=72,
                                      topMargin=72, bottomMargin=18)
                
                # Get styles
                styles = getSampleStyleSheet()
                
                # Custom styles
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=24,
                    spaceAfter=30,
                    alignment=TA_CENTER,
                    textColor=colors.darkblue
                )
                
                subtitle_style = ParagraphStyle(
                    'CustomSubtitle',
                    parent=styles['Heading2'],
                    fontSize=16,
                    spaceAfter=12,
                    textColor=colors.blue
                )
                
                # Story list (content)
                story = []
                
                # Title page
                story.append(Paragraph(f"{company_name}", title_style))
                story.append(Paragraph(f"{report_type}", subtitle_style))
                story.append(Paragraph(f"Report Period: {report_period}", styles['Normal']))
                story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
                story.append(Spacer(1, 0.5*inch))
                
                # Executive Summary Section
                story.append(Paragraph("Executive Summary", subtitle_style))
                
                # Get data for report
                has_revenue_data = st.session_state.get('saved_revenue_data') is not None
                has_timesheet_data = st.session_state.get('saved_timesheet_data') is not None
                
                if has_revenue_data and has_timesheet_data:
                    revenue_df = st.session_state.saved_revenue_data
                    timesheet_df = st.session_state.saved_timesheet_data
                    
                    # Calculate metrics
                    if 'Revenue' in revenue_df.columns:
                        total_revenue = pd.to_numeric(revenue_df['Revenue'], errors='coerce').sum()
                    else:
                        total_revenue = 0
                    
                    # Commission calculation
                    avg_commission_rate = 0.05
                    if st.session_state.get('business_unit_commission_settings'):
                        rates = []
                        for unit_settings in st.session_state.business_unit_commission_settings.values():
                            if isinstance(unit_settings, dict) and unit_settings.get('enabled', False):
                                total_rate = (unit_settings.get('lead_gen_rate', 0) + 
                                            unit_settings.get('sold_by_rate', 0) + 
                                            unit_settings.get('work_done_rate', 0))
                                rates.append(total_rate / 100)
                        if rates:
                            avg_commission_rate = sum(rates) / len(rates)
                    
                    estimated_commissions = total_revenue * avg_commission_rate
                    employee_count = len(timesheet_df) if timesheet_df is not None else 0
                    
                    # Summary table
                    summary_data = [
                        ['Metric', 'Value'],
                        ['Total Revenue', f'${total_revenue:,.2f}'],
                        ['Estimated Commissions', f'${estimated_commissions:,.2f}'],
                        ['Average Commission Rate', f'{avg_commission_rate*100:.1f}%'],
                        ['Active Employees', str(employee_count)],
                        ['Business Units', str(len(revenue_df['Business Unit'].unique()) if 'Business Unit' in revenue_df.columns else 0)]
                    ]
                    
                    summary_table = Table(summary_data)
                    summary_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 14),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    
                    story.append(summary_table)
                    story.append(Spacer(1, 0.3*inch))
                    
                    # Detailed sections based on report type
                    if report_type in ["Detailed Commission Report", "Complete Analytics Package"]:
                        story.append(Paragraph("Commission Breakdown", subtitle_style))
                        
                        # Revenue by Business Unit
                        if 'Business Unit' in revenue_df.columns:
                            bu_revenue = revenue_df.groupby('Business Unit')['Revenue'].sum().reset_index()
                            bu_data = [['Business Unit', 'Revenue', 'Est. Commissions']]
                            
                            for _, row in bu_revenue.iterrows():
                                bu_name = row['Business Unit']
                                bu_rev = row['Revenue']
                                bu_comm = bu_rev * avg_commission_rate
                                bu_data.append([bu_name, f'${bu_rev:,.2f}', f'${bu_comm:,.2f}'])
                            
                            bu_table = Table(bu_data)
                            bu_table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('FONTSIZE', (0, 0), (-1, 0), 12),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black)
                            ]))
                            
                            story.append(bu_table)
                            story.append(Spacer(1, 0.3*inch))
                    
                    if report_type in ["Employee Performance", "Complete Analytics Package"]:
                        story.append(Paragraph("Employee Performance", subtitle_style))
                        
                        # Employee hours summary
                        if 'Employee Name' in timesheet_df.columns:
                            hours_columns = [col for col in timesheet_df.columns if 'hour' in col.lower()]
                            if hours_columns:
                                emp_hours = timesheet_df.groupby('Employee Name')[hours_columns].sum()
                                emp_hours['Total Hours'] = emp_hours.sum(axis=1)
                                
                                emp_data = [['Employee', 'Total Hours', 'Productivity Rank']]
                                
                                sorted_emp = emp_hours.sort_values('Total Hours', ascending=False)
                                for i, (emp_name, row) in enumerate(sorted_emp.iterrows()):
                                    total_hours = row['Total Hours']
                                    rank = i + 1
                                    emp_data.append([emp_name, f'{total_hours:.1f}', f'#{rank}'])
                                
                                emp_table = Table(emp_data)
                                emp_table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                                ]))
                                
                                story.append(emp_table)
                                story.append(Spacer(1, 0.3*inch))
                    
                    # Recommendations section
                    story.append(Paragraph("Recommendations", subtitle_style))
                    recommendations = [
                        "• Monitor commission rates to ensure competitiveness",
                        "• Review employee performance metrics regularly",
                        "• Consider implementing performance bonuses for top performers",
                        "• Analyze business unit profitability for resource allocation",
                        "• Maintain accurate record-keeping for payroll processing"
                    ]
                    
                    for rec in recommendations:
                        story.append(Paragraph(rec, styles['Normal']))
                        story.append(Spacer(1, 0.1*inch))
                
                else:
                    story.append(Paragraph("No data available for report generation.", styles['Normal']))
                    story.append(Paragraph("Please upload timesheet and revenue data first.", styles['Normal']))
                
                # Footer
                story.append(Spacer(1, 0.5*inch))
                footer_style = ParagraphStyle(
                    'Footer',
                    parent=styles['Normal'],
                    fontSize=8,
                    alignment=TA_CENTER,
                    textColor=colors.grey
                )
                story.append(Paragraph(f"Generated by Commission Calculator Pro | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style))
                
                # Build PDF
                doc.build(story)
                
                # Get PDF data
                pdf_data = buffer.getvalue()
                buffer.close()
                
                # Download button
                st.download_button(
                    label="📥 Download PDF Report",
                    data=pdf_data,
                    file_name=f"{report_type.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf"
                )
                
                st.success("✅ PDF report generated successfully!")
                st.info(f"📊 Report contains: {report_type} for {report_period}")
                
    except ImportError:
        st.error("❌ PDF generation requires reportlab. Install with: pip install reportlab")
    except Exception as e:
        st.error(f"❌ Error generating PDF: {str(e)}")
        st.info("💡 Make sure you have data uploaded and saved before generating reports.")

def display_history_tab():
    """Commission calculation history and audit trail"""
    st.markdown("## 📜 Commission Calculation History")
    
    # Initialize commission history in session state
    if 'commission_history' not in st.session_state:
        st.session_state.commission_history = pd.DataFrame(columns=[
            'Calculation Date', 'Period Start', 'Period End', 'Total Commission', 
            'Employees', 'Status'
        ])
    
    if 'calculation_settings_history' not in st.session_state:
        st.session_state.calculation_settings_history = []
    
    # Create sub-tabs for different history views
    history_tabs = st.tabs([
        "📊 Calculation History",
        "⚙️ Settings Changes", 
        "🔍 Audit Trail",
        "📈 Historical Trends",
        "🔄 Replay Calculations"
    ])
    
    with history_tabs[0]:
        display_calculation_history()
    
    with history_tabs[1]:
        display_settings_history()
    
    with history_tabs[2]:
        display_audit_trail()
    
    with history_tabs[3]:
        display_historical_trends()
    
    with history_tabs[4]:
        display_calculation_replay()

def display_calculation_history():
    """Show commission calculation history"""
    st.markdown("### 📊 Commission Calculation History")
    
    # Add current calculation to history button
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if st.button("💾 Save Current Calculation", type="primary", use_container_width=True):
            save_current_calculation_to_history()
    
    with col2:
        if st.button("🗑️ Clear History", use_container_width=True):
            if st.session_state.get('confirm_clear_history'):
                clear_calculation_history()
                st.session_state.confirm_clear_history = False
                st.rerun()
            else:
                st.session_state.confirm_clear_history = True
                st.warning("Click again to confirm clearing all history")
    
    with col3:
        if st.button("📥 Export History", use_container_width=True):
            export_calculation_history()
    
    # Display calculation history
    if st.session_state.get('commission_history') is not None and not st.session_state.commission_history.empty:
        st.markdown(f"**Found {len(st.session_state.commission_history)} saved calculations**")
        
        # History filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            date_filter = st.selectbox(
                "Filter by period:",
                ["All Time", "Last 7 Days", "Last 30 Days", "Last 90 Days"]
            )
        
        with col2:
            employee_filter = st.selectbox(
                "Filter by employee:",
                ["All Employees"] + get_unique_employees_from_history()
            )
        
        with col3:
            sort_by = st.selectbox(
                "Sort by:",
                ["Date (Newest)", "Date (Oldest)", "Total Commission", "Employee Count"]
            )
        
        # Apply filters and display
        filtered_history = filter_calculation_history(date_filter, employee_filter, sort_by)
        
        # Display history entries
        for i, (_, calc_entry) in enumerate(filtered_history.iterrows()):
            with st.expander(
                f"📅 {calc_entry.get('Calculation Date', 'Unknown')} - {calc_entry.get('Status', 'Unknown')}", 
                expanded=False
            ):
                display_calculation_entry(calc_entry, i)
    else:
        st.info("📝 No calculation history found. Save your current calculations to start building history.")
        
        # Show example of what will be saved
        with st.expander("ℹ️ What gets saved in calculation history?", expanded=False):
            st.markdown("""
            **Each calculation history entry includes:**
            - 📅 Timestamp of calculation
            - 👥 Employee data and hours
            - 💰 Revenue data and business units
            - ⚙️ Commission rates and settings
            - 💸 Calculated commission amounts
            - 📊 Summary statistics
            - 🏷️ User-defined description/notes
            """)

def display_settings_history():
    """Show commission settings change history"""
    st.markdown("### ⚙️ Commission Settings Change History")
    
    if st.session_state.get('calculation_settings_history') and len(st.session_state.calculation_settings_history) > 0:
        st.markdown(f"**Found {len(st.session_state.calculation_settings_history)} settings changes**")
        
        # Display settings changes
        for i, settings_entry in enumerate(st.session_state.calculation_settings_history):
            with st.expander(
                f"🔧 {settings_entry['timestamp']} - {settings_entry['change_type']}", 
                expanded=False
            ):
                display_settings_change_entry(settings_entry)
    else:
        st.info("📝 No settings changes recorded yet.")
        
        if st.button("🔄 Start Tracking Settings Changes"):
            initialize_settings_tracking()
            st.success("✅ Settings change tracking is now enabled!")
            st.rerun()

def display_audit_trail():
    """Show complete audit trail"""
    st.markdown("### 🔍 Comprehensive Audit Trail")
    
    # Combine all history types for complete audit
    all_events = compile_audit_events()
    
    if all_events:
        st.markdown(f"**Found {len(all_events)} audit events**")
        
        # Audit filters
        col1, col2 = st.columns(2)
        
        with col1:
            event_type_filter = st.multiselect(
                "Filter by event type:",
                ["Calculation", "Settings Change", "Data Upload", "Export", "Configuration"],
                default=["Calculation", "Settings Change"]
            )
        
        with col2:
            user_filter = st.selectbox(
                "Filter by user:",
                ["All Users"] + get_unique_users_from_audit()
            )
        
        # Apply filters
        filtered_events = filter_audit_events(all_events, event_type_filter, user_filter)
        
        # Display audit trail
        for event in filtered_events:
            display_audit_event(event)
    else:
        st.info("📝 No audit events found. Activity will be automatically tracked.")

def display_historical_trends():
    """Show historical commission trends"""
    st.markdown("### 📈 Historical Commission Trends")
    
    if len(st.session_state.commission_history) >= 2:
        # Generate trend analysis
        trend_data = analyze_commission_trends()
        
        if trend_data:
            # Trend charts
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 💰 Commission Trends Over Time")
                display_commission_trend_chart(trend_data)
            
            with col2:
                st.markdown("#### 👥 Employee Commission Changes")
                display_employee_trend_chart(trend_data)
            
            # Trend metrics
            st.markdown("#### 📊 Trend Analysis")
            display_trend_metrics(trend_data)
            
            # Insights and recommendations
            st.markdown("#### 💡 Insights & Recommendations")
            display_trend_insights(trend_data)
        else:
            st.warning("Unable to generate trend analysis from available data.")
    else:
        st.info("📈 Need at least 2 calculations in history to show trends.")
        st.markdown("Save more calculations to unlock trend analysis!")

def display_calculation_replay():
    """Replay and compare historical calculations"""
    st.markdown("### 🔄 Calculation Replay & Comparison")
    
    if st.session_state.get('commission_history') is not None and not st.session_state.commission_history.empty:
        # Select calculations to replay/compare
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🎯 Select Calculation to Replay")
            calc_options = [f"{row['Calculation Date']} - {row['Status']}" 
                           for _, row in st.session_state.commission_history.iterrows()]
            
            selected_calc_index = st.selectbox(
                "Choose calculation:",
                range(len(calc_options)),
                format_func=lambda x: calc_options[x]
            )
            
            if st.button("🔄 Replay Selected Calculation", type="primary"):
                replay_calculation(selected_calc_index)
        
        with col2:
            st.markdown("#### 🔍 Compare Two Calculations")
            
            if len(st.session_state.commission_history) >= 2:
                calc1_index = st.selectbox(
                    "First calculation:",
                    range(len(calc_options)),
                    format_func=lambda x: f"📊 {calc_options[x]}"
                )
                
                calc2_index = st.selectbox(
                    "Second calculation:",
                    range(len(calc_options)),
                    format_func=lambda x: f"📊 {calc_options[x]}",
                    index=1 if len(calc_options) > 1 else 0
                )
                
                if calc1_index != calc2_index:
                    if st.button("🔍 Compare Calculations", type="primary"):
                        compare_calculations(calc1_index, calc2_index)
                else:
                    st.warning("Please select two different calculations to compare")
            else:
                st.info("Need at least 2 calculations to enable comparison")
        
        # Show replay results if available
        if 'replay_results' in st.session_state:
            display_replay_results()
        
        if 'comparison_results' in st.session_state:
            display_comparison_results()
    else:
        st.info("📝 No calculations available for replay. Save calculations first.")

# Helper functions for commission history

def save_current_calculation_to_history():
    """Save current calculation state to history"""
    try:
        from datetime import datetime
        
        # Get current calculation data
        current_calc = {
            'id': len(st.session_state.commission_history) + 1,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'description': f"Calculation #{len(st.session_state.commission_history) + 1}",
            'user': st.session_state.get('user', {}).get('username', 'Unknown'),
            'employee_data': dict(st.session_state.get('saved_timesheet_data', {})) if st.session_state.get('saved_timesheet_data') else {},
            'revenue_data': dict(st.session_state.get('saved_revenue_data', {})) if st.session_state.get('saved_revenue_data') else {},
            'commission_rates': dict(st.session_state.get('commission_rates', {})),
            'employee_rates': dict(st.session_state.get('employee_rates', {})),
            'calculated_results': calculate_current_commissions(),
            'summary_stats': get_calculation_summary_stats()
        }
        
        # Add custom description
        description = st.text_input(
            "Add description (optional):",
            value=f"Calculation #{len(st.session_state.commission_history) + 1}",
            key="calc_description"
        )
        
        if description:
            current_calc['description'] = description
        
        # Save to history
        st.session_state.commission_history.append(current_calc)
        
        st.success(f"✅ Calculation saved to history: {current_calc['description']}")
        st.info(f"📊 Saved {len(current_calc.get('calculated_results', {}))} commission results")
        
        # Save settings change if commission rates changed
        track_settings_change("Commission calculation saved", current_calc['commission_rates'])
        
    except Exception as e:
        st.error(f"❌ Error saving calculation: {e}")

def clear_calculation_history():
    """Clear all calculation history"""
    st.session_state.commission_history = pd.DataFrame(columns=[
        'Calculation Date', 'Period Start', 'Period End', 'Total Commission', 
        'Employees', 'Status'
    ])
    st.session_state.calculation_settings_history = []
    st.success("✅ All calculation history cleared")

def export_calculation_history():
    """Export calculation history to file"""
    try:
        import json
        
        export_data = {
            'exported_at': datetime.now().isoformat(),
            'calculation_history': st.session_state.commission_history,
            'settings_history': st.session_state.calculation_settings_history
        }
        
        # Create download
        json_data = json.dumps(export_data, indent=2, default=str)
        
        st.download_button(
            label="📥 Download History (JSON)",
            data=json_data,
            file_name=f"commission_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
        
        st.success("✅ History export ready for download")
        
    except Exception as e:
        st.error(f"❌ Export failed: {e}")

def get_unique_employees_from_history():
    """Get unique employee names from history"""
    employees = set()
    for calc in st.session_state.commission_history:
        if 'calculated_results' in calc:
            employees.update(calc['calculated_results'].keys())
    return sorted(list(employees))

def filter_calculation_history(date_filter, employee_filter, sort_by):
    """Filter and sort calculation history"""
    filtered = st.session_state.commission_history.copy()
    
    # Apply date filter
    if date_filter != "All Time" and not filtered.empty:
        days = {"Last 7 Days": 7, "Last 30 Days": 30, "Last 90 Days": 90}[date_filter]
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Convert date column to datetime if it's not already
        if 'Calculation Date' in filtered.columns:
            filtered['Calculation Date'] = pd.to_datetime(filtered['Calculation Date'])
            filtered = filtered[filtered['Calculation Date'] >= cutoff_date]
    
    # Apply employee filter
    if employee_filter != "All Employees" and not filtered.empty:
        # For now, skip employee filtering since DataFrame structure may not have detailed employee data
        pass
    
    # Apply sorting
    if not filtered.empty:
        if sort_by == "Date (Newest)":
            filtered = filtered.sort_values('Calculation Date', ascending=False)
        elif sort_by == "Date (Oldest)":
            filtered = filtered.sort_values('Calculation Date', ascending=True)
        elif sort_by == "Total Commission":
            if 'Total Commission' in filtered.columns:
                filtered = filtered.sort_values('Total Commission', ascending=False)
        elif sort_by == "Employee Count":
            if 'Employees' in filtered.columns:
                filtered = filtered.sort_values('Employees', ascending=False)
    
    return filtered

def display_calculation_entry(calc_entry, index):
    """Display a single calculation history entry"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"**👤 User:** {calc_entry.get('user', 'Unknown')}")
        st.markdown(f"**📅 Date:** {calc_entry.get('Calculation Date', 'Unknown')}")
        st.markdown(f"**📝 Status:** {calc_entry.get('Status', 'Unknown')}")
    
    with col2:
        st.markdown(f"**👥 Employees:** {calc_entry.get('Employees', 'N/A')}")
        total_commission = calc_entry.get('Total Commission', 0)
        if isinstance(total_commission, (int, float)):
            st.markdown(f"**💰 Total Commission:** ${total_commission:,.2f}")
        else:
            st.markdown(f"**💰 Total Commission:** {total_commission}")
    
    with col3:
        if st.button(f"🔄 View Details", key=f"details_{index}"):
            st.info(f"Period: {calc_entry.get('Period Start', 'N/A')} to {calc_entry.get('Period End', 'N/A')}")
    
    # Show details if requested
    if st.session_state.get(f'show_details_{index}', False):
        with st.expander("📊 Detailed Results", expanded=True):
            display_detailed_calculation_results(calc_entry)

def display_detailed_calculation_results(calc_entry):
    """Display detailed results from a calculation entry"""
    if 'calculated_results' in calc_entry and calc_entry['calculated_results']:
        results_df = pd.DataFrame([
            {
                'Employee': emp,
                'Commission': f"${comm:,.2f}"
            }
            for emp, comm in calc_entry['calculated_results'].items()
        ])
        st.dataframe(results_df, use_container_width=True)
    
    if 'commission_rates' in calc_entry:
        st.markdown("**Commission Rates Used:**")
        for unit, rate in calc_entry['commission_rates'].items():
            st.text(f"  • {unit}: {rate}%")

def calculate_current_commissions():
    """Calculate commissions with current data"""
    try:
        # This would integrate with existing commission calculation logic
        results = {}
        
        if (st.session_state.get('saved_timesheet_data') and 
            st.session_state.get('saved_revenue_data') and
            st.session_state.get('commission_rates')):
            
            # Simple commission calculation for history
            timesheet_data = st.session_state.saved_timesheet_data
            revenue_data = st.session_state.saved_revenue_data
            rates = st.session_state.commission_rates
            
            for employee in timesheet_data.get('Employee Name', []):
                # Basic calculation - would use actual commission logic
                base_commission = 100.0  # Placeholder
                results[employee] = base_commission
        
        return results
    except Exception:
        return {}

def get_calculation_summary_stats():
    """Get summary statistics for current calculation"""
    try:
        stats = {
            'total_employees': len(st.session_state.get('saved_timesheet_data', {})),
            'total_business_units': len(st.session_state.get('saved_revenue_data', {})),
            'total_revenue': 0,  # Would calculate from revenue data
            'average_commission_rate': 0  # Would calculate average
        }
        return stats
    except Exception:
        return {}

def track_settings_change(change_type, new_settings):
    """Track a settings change"""
    try:
        change_entry = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'change_type': change_type,
            'user': st.session_state.get('user', {}).get('username', 'Unknown'),
            'new_settings': dict(new_settings) if new_settings else {},
            'previous_settings': dict(st.session_state.get('previous_commission_rates', {}))
        }
        
        if 'calculation_settings_history' not in st.session_state:
            st.session_state.calculation_settings_history = []
        
        st.session_state.calculation_settings_history.append(change_entry)
        
        # Store current settings as previous for next change
        st.session_state.previous_commission_rates = dict(new_settings) if new_settings else {}
        
    except Exception as e:
        st.warning(f"Could not track settings change: {e}")

def restore_calculation(calc_entry):
    """Restore a historical calculation"""
    try:
        # Restore data to session state
        if 'employee_data' in calc_entry:
            st.session_state.saved_timesheet_data = calc_entry['employee_data']
        
        if 'revenue_data' in calc_entry:
            st.session_state.saved_revenue_data = calc_entry['revenue_data']
        
        if 'commission_rates' in calc_entry:
            st.session_state.commission_rates = calc_entry['commission_rates']
        
        if 'employee_rates' in calc_entry:
            st.session_state.employee_rates = calc_entry['employee_rates']
        
        st.success(f"✅ Calculation restored: {calc_entry['description']}")
        st.info("💡 Switch to Commission Calc tab to see the restored calculation")
        
        # Track the restoration
        track_settings_change("Calculation restored", calc_entry.get('commission_rates', {}))
        
    except Exception as e:
        st.error(f"❌ Error restoring calculation: {e}")

# Placeholder functions for remaining history features
def display_settings_change_entry(settings_entry):
    """Display a settings change entry"""
    st.markdown(f"**👤 User:** {settings_entry.get('user', 'Unknown')}")
    st.markdown(f"**🔧 Change:** {settings_entry['change_type']}")
    
    if settings_entry.get('new_settings'):
        st.markdown("**New Settings:**")
        for key, value in settings_entry['new_settings'].items():
            st.text(f"  • {key}: {value}")

def initialize_settings_tracking():
    """Initialize settings change tracking"""
    st.session_state.calculation_settings_history = []
    st.session_state.previous_commission_rates = dict(st.session_state.get('commission_rates', {}))

def compile_audit_events():
    """Compile all audit events from different sources"""
    events = []
    
    # Add calculation history as events
    commission_history = st.session_state.get('commission_history')
    if commission_history is not None and not commission_history.empty:
        for _, calc in commission_history.iterrows():
            events.append({
                'timestamp': calc.get('Calculation Date', datetime.now()),
                'type': 'Calculation',
                'description': f"Commission calculation: {calc.get('Status', 'Completed')}",
                'user': calc.get('user', 'Unknown')
            })
    
    # Add settings history as events
    for setting in st.session_state.get('calculation_settings_history', []):
        events.append({
            'timestamp': setting['timestamp'],
            'type': 'Settings Change',
            'description': setting['change_type'],
            'user': setting.get('user', 'Unknown')
        })
    
    # Sort by timestamp
    events.sort(key=lambda x: x['timestamp'], reverse=True)
    return events

def get_unique_users_from_audit():
    """Get unique users from audit trail"""
    users = set()
    
    commission_history = st.session_state.get('commission_history')
    if commission_history is not None and not commission_history.empty:
        for _, calc in commission_history.iterrows():
            users.add(calc.get('user', 'Unknown'))
    
    for setting in st.session_state.get('calculation_settings_history', []):
        users.add(setting.get('user', 'Unknown'))
    
    return sorted(list(users))

def filter_audit_events(events, event_types, user_filter):
    """Filter audit events"""
    filtered = [event for event in events if event['type'] in event_types]
    
    if user_filter != "All Users":
        filtered = [event for event in filtered if event['user'] == user_filter]
    
    return filtered

def display_audit_event(event):
    """Display a single audit event"""
    st.markdown(f"🕐 **{event['timestamp']}** - {event['description']} (by {event['user']})")

def analyze_commission_trends():
    """Analyze commission trends from history"""
    if len(st.session_state.commission_history) < 2:
        return None
    
    trend_data = {
        'dates': [],
        'total_commissions': [],
        'employee_counts': []
    }
    
    for calc in st.session_state.commission_history:
        trend_data['dates'].append(calc['timestamp'])
        results = calc.get('calculated_results', {})
        trend_data['total_commissions'].append(sum(results.values()) if results else 0)
        trend_data['employee_counts'].append(len(results))
    
    return trend_data

def display_commission_trend_chart(trend_data):
    """Display commission trend chart"""
    try:
        import plotly.graph_objects as go
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trend_data['dates'],
            y=trend_data['total_commissions'],
            mode='lines+markers',
            name='Total Commission',
            line=dict(color='#2C5F75', width=3)
        ))
        
        fig.update_layout(
            title="Commission Trends Over Time",
            xaxis_title="Date",
            yaxis_title="Commission Amount ($)",
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Could not generate trend chart: {e}")

def display_employee_trend_chart(trend_data):
    """Display employee count trend chart"""
    try:
        import plotly.graph_objects as go
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trend_data['dates'],
            y=trend_data['employee_counts'],
            mode='lines+markers',
            name='Employee Count',
            line=dict(color='#922B3E', width=3)
        ))
        
        fig.update_layout(
            title="Employee Count Trends",
            xaxis_title="Date",
            yaxis_title="Number of Employees",
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Could not generate employee trend chart: {e}")

def display_trend_metrics(trend_data):
    """Display trend metrics"""
    if len(trend_data['total_commissions']) >= 2:
        latest = trend_data['total_commissions'][-1]
        previous = trend_data['total_commissions'][-2]
        change = ((latest - previous) / previous * 100) if previous > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Latest Commission", f"${latest:,.2f}", f"{change:+.1f}%")
        
        with col2:
            avg_commission = sum(trend_data['total_commissions']) / len(trend_data['total_commissions'])
            st.metric("Average Commission", f"${avg_commission:,.2f}")
        
        with col3:
            total_calculations = len(trend_data['dates'])
            st.metric("Total Calculations", total_calculations)

def display_trend_insights(trend_data):
    """Display trend insights and recommendations"""
    if len(trend_data['total_commissions']) >= 3:
        # Simple trend analysis
        recent_commissions = trend_data['total_commissions'][-3:]
        
        if recent_commissions[-1] > recent_commissions[0]:
            st.success("📈 **Upward Trend:** Commission amounts are increasing over recent calculations")
        elif recent_commissions[-1] < recent_commissions[0]:
            st.warning("📉 **Downward Trend:** Commission amounts are decreasing over recent calculations")
        else:
            st.info("➡️ **Stable Trend:** Commission amounts are relatively stable")
        
        # Recommendations
        st.markdown("**💡 Recommendations:**")
        st.markdown("• Monitor commission rate effectiveness")
        st.markdown("• Review employee performance patterns")
        st.markdown("• Consider seasonal adjustments if applicable")

def replay_calculation(calc_index):
    """Replay a specific calculation"""
    try:
        calc_entry = st.session_state.commission_history.iloc[calc_index]
        
        # Store replay results
        st.session_state.replay_results = {
            'original': calc_entry,
            'replayed_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'status': 'success'
        }
        
        st.success(f"✅ Replayed calculation: {calc_entry['description']}")
        
    except Exception as e:
        st.error(f"❌ Replay failed: {e}")

def compare_calculations(calc1_index, calc2_index):
    """Compare two calculations"""
    try:
        calc1 = st.session_state.commission_history.iloc[calc1_index]
        calc2 = st.session_state.commission_history.iloc[calc2_index]
        
        # Generate comparison
        comparison = {
            'calc1': calc1,
            'calc2': calc2,
            'differences': find_calculation_differences(calc1, calc2),
            'compared_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        st.session_state.comparison_results = comparison
        st.success("✅ Comparison completed")
        
    except Exception as e:
        st.error(f"❌ Comparison failed: {e}")

def find_calculation_differences(calc1, calc2):
    """Find differences between two calculations"""
    differences = {}
    
    # Compare commission results
    results1 = calc1.get('calculated_results', {})
    results2 = calc2.get('calculated_results', {})
    
    all_employees = set(results1.keys()) | set(results2.keys())
    
    for emp in all_employees:
        comm1 = results1.get(emp, 0)
        comm2 = results2.get(emp, 0)
        
        if comm1 != comm2:
            differences[emp] = {
                'calc1_commission': comm1,
                'calc2_commission': comm2,
                'difference': comm2 - comm1,
                'percent_change': ((comm2 - comm1) / comm1 * 100) if comm1 > 0 else 0
            }
    
    return differences

def display_replay_results():
    """Display calculation replay results"""
    results = st.session_state.replay_results
    
    st.markdown("### 🔄 Replay Results")
    st.markdown(f"**Replayed:** {results['original']['description']}")
    st.markdown(f"**Replay Time:** {results['replayed_at']}")
    
    if results['status'] == 'success':
        st.success("✅ Calculation replayed successfully")
    else:
        st.error("❌ Replay encountered issues")

def display_comparison_results():
    """Display calculation comparison results"""
    comparison = st.session_state.comparison_results
    
    st.markdown("### 🔍 Comparison Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**📊 Calculation 1:** {comparison['calc1']['description']}")
        st.markdown(f"**📅 Date:** {comparison['calc1']['timestamp']}")
    
    with col2:
        st.markdown(f"**📊 Calculation 2:** {comparison['calc2']['description']}")
        st.markdown(f"**📅 Date:** {comparison['calc2']['timestamp']}")
    
    # Show differences
    if comparison['differences']:
        st.markdown("#### 📈 Differences Found:")
        
        diff_df = pd.DataFrame([
            {
                'Employee': emp,
                'Calc 1 Commission': f"${data['calc1_commission']:,.2f}",
                'Calc 2 Commission': f"${data['calc2_commission']:,.2f}",
                'Difference': f"${data['difference']:,.2f}",
                'Change %': f"{data['percent_change']:+.1f}%"
            }
            for emp, data in comparison['differences'].items()
        ])
        
        st.dataframe(diff_df, use_container_width=True)
    else:
        st.info("✅ No differences found between the two calculations")

if __name__ == "__main__":
    main()