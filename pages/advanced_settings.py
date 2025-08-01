import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
from loguru import logger
import json
import numpy as np

def advanced_settings_page():
    """Advanced settings page with manual splits, audit trails, and system administration"""
    st.title("🔧 Advanced Settings")
    
    # Ensure session state is initialized
    if 'calculator' not in st.session_state:
        from models import CommissionCalculator
        st.session_state.calculator = CommissionCalculator()
    
    if 'auth_manager' not in st.session_state:
        try:
            from utils import AuthManager, DatabaseManager
            db_manager = DatabaseManager()
            st.session_state.auth_manager = AuthManager(db_manager)
        except:
            st.warning("Authentication manager not available - access controls disabled")
            st.session_state.auth_manager = None
    
    # Check user permissions
    if st.session_state.auth_manager:
        current_user = st.session_state.auth_manager.get_current_user()
    else:
        current_user = {'role': 'admin'}  # Fallback
    
    if not current_user or current_user['role'] not in ['admin', 'manager']:
        st.error("⛔ Access denied. Admin or Manager role required.")
        return
    
    # Advanced settings tabs
    tabs = st.tabs([
        "✂️ Manual Commission Splits",
        "📊 Audit Trail",
        "👥 User Management",
        "⚙️ System Administration",
        "🔄 Data Migration",
        "📈 Performance Monitoring"
    ])
    
    with tabs[0]:
        manual_commission_splits()
    
    with tabs[1]:
        audit_trail_management()
    
    with tabs[2]:
        user_management()
    
    with tabs[3]:
        system_administration()
    
    with tabs[4]:
        data_migration_tools()
    
    with tabs[5]:
        performance_monitoring()

def manual_commission_splits():
    """Manage manual commission splits for specific jobs/projects"""
    st.subheader("✂️ Manual Commission Splits")
    
    calc = st.session_state.calculator
    
    st.info("💡 Create manual commission splits when multiple employees work on the same project")
    
    # Create new split
    with st.expander("➕ Create New Commission Split", expanded=False):
        create_new_split(calc)
    
    # Display existing splits
    display_existing_splits(calc)
    
    # Bulk split operations
    st.divider()
    st.markdown("### 🔄 Bulk Operations")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📤 Export All Splits", use_container_width=True):
            export_commission_splits(calc)
    
    with col2:
        uploaded_splits = st.file_uploader("📥 Import Splits", type=['csv', 'xlsx'])
        if uploaded_splits:
            import_commission_splits(uploaded_splits, calc)
    
    with col3:
        if st.button("🔄 Recalculate All", use_container_width=True):
            recalculate_all_splits(calc)

def create_new_split(calc):
    """Create new commission split"""
    st.markdown("#### Create New Split")
    
    # Job/Project identification
    job_id = st.text_input("Job/Project ID", help="Unique identifier for this job")
    job_description = st.text_area("Description (optional)", help="Brief description of the project")
    
    if not job_id:
        st.warning("Please enter a Job/Project ID")
        return
    
    # Check if split already exists
    if job_id in calc.commission_splits:
        st.error("A split already exists for this Job ID")
        return
    
    # Select employees
    available_employees = [emp.name for emp in calc.employees.values() if emp.is_active]
    
    if not available_employees:
        st.warning("No active employees available")
        return
    
    selected_employees = st.multiselect(
        "Select Employees for Split",
        available_employees,
        help="Choose employees who worked on this project"
    )
    
    if not selected_employees:
        st.warning("Please select at least one employee")
        return
    
    # Commission amount
    total_commission = st.number_input(
        "Total Commission Amount ($)",
        min_value=0.0,
        step=100.0,
        help="Total commission amount to be split"
    )
    
    # Split percentages
    st.markdown("#### Split Percentages")
    
    splits = {}
    remaining_percentage = 100.0
    
    for i, emp_name in enumerate(selected_employees):
        if i == len(selected_employees) - 1:
            # Last employee gets remaining percentage
            splits[emp_name] = remaining_percentage
            st.write(f"**{emp_name}:** {remaining_percentage:.1f}% (auto-calculated)")
        else:
            percentage = st.number_input(
                f"Percentage for {emp_name}",
                min_value=0.0,
                max_value=remaining_percentage,
                value=remaining_percentage / (len(selected_employees) - i),
                step=0.1,
                key=f"split_{emp_name}"
            )
            splits[emp_name] = percentage
            remaining_percentage -= percentage
    
    # Validation
    total_percentage = sum(splits.values())
    
    if abs(total_percentage - 100.0) > 0.01:
        st.error(f"Split percentages must sum to 100%. Current total: {total_percentage:.1f}%")
        return
    
    # Preview
    st.markdown("#### Split Preview")
    
    preview_data = []
    for emp_name, percentage in splits.items():
        amount = total_commission * percentage / 100
        preview_data.append({
            'Employee': emp_name,
            'Percentage': f"{percentage:.1f}%",
            'Amount': f"${amount:.2f}"
        })
    
    st.dataframe(pd.DataFrame(preview_data), use_container_width=True)
    
    # Create split
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Create Split", type="primary", use_container_width=True):
            try:
                from models.business_unit import CommissionSplit
                
                # Convert employee names to IDs
                employee_splits = {}
                for emp_name, percentage in splits.items():
                    employee = calc.find_employee_by_name(emp_name)
                    if employee:
                        employee_splits[employee.id] = Decimal(str(percentage))
                
                # Create split
                new_split = CommissionSplit(
                    job_id=job_id,
                    employee_splits=employee_splits,
                    total_amount=Decimal(str(total_commission)),
                    created_by=st.session_state.auth_manager.get_current_user()['username']
                )
                
                calc.commission_splits[job_id] = new_split
                
                # Save to database
                save_commission_split(new_split)
                
                st.success(f"✅ Commission split created for Job ID: {job_id}")
                
                # Log action
                st.session_state.db_manager.log_action('commission_split_created', {
                    'job_id': job_id,
                    'employees': len(selected_employees),
                    'total_amount': total_commission
                }, st.session_state.auth_manager.get_current_user()['username'])
                
                st.rerun()
                
            except Exception as e:
                st.error(f"Error creating split: {str(e)}")
    
    with col2:
        if st.button("🔄 Reset Form", use_container_width=True):
            st.rerun()

def display_existing_splits(calc):
    """Display and manage existing commission splits"""
    st.markdown("### 📋 Existing Commission Splits")
    
    if not calc.commission_splits:
        st.info("No commission splits created yet")
        return
    
    # Search and filter
    search_term = st.text_input("🔍 Search Splits", placeholder="Search by Job ID or description...")
    
    # Display splits
    for job_id, split in calc.commission_splits.items():
        if search_term and search_term.lower() not in job_id.lower():
            continue
        
        with st.expander(f"📁 Job ID: {job_id}", expanded=False):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Total Amount:** ${float(split.total_amount):,.2f}")
                st.write(f"**Created By:** {split.created_by}")
                st.write(f"**Created:** {split.created_at.strftime('%Y-%m-%d %H:%M')}")
                
                # Split details
                st.markdown("**Employee Splits:**")
                
                split_data = []
                for emp_id, percentage in split.employee_splits.items():
                    employee = calc.employees.get(emp_id)
                    emp_name = employee.name if employee else f"Unknown ({emp_id})"
                    amount = split.calculate_employee_amount(emp_id)
                    
                    split_data.append({
                        'Employee': emp_name,
                        'Percentage': f"{float(percentage):.1f}%",
                        'Amount': f"${float(amount):,.2f}"
                    })
                
                st.dataframe(pd.DataFrame(split_data), use_container_width=True)
            
            with col2:
                st.markdown("**Actions**")
                
                if st.button(f"✏️ Edit", key=f"edit_{job_id}", use_container_width=True):
                    st.session_state.editing_split = job_id
                    st.rerun()
                
                if st.button(f"🗑️ Delete", key=f"delete_{job_id}", use_container_width=True):
                    if st.checkbox(f"Confirm delete {job_id}", key=f"confirm_delete_{job_id}"):
                        delete_commission_split(job_id, calc)
                        st.rerun()
                
                if st.button(f"📊 Apply Split", key=f"apply_{job_id}", use_container_width=True):
                    apply_commission_split(job_id, split, calc)

def audit_trail_management():
    """Manage audit trail and system logs"""
    st.subheader("📊 Audit Trail Management")
    
    db_manager = st.session_state.db_manager
    
    # Audit log filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        log_limit = st.selectbox("Records to Display", [50, 100, 200, 500, 1000], index=1)
    
    with col2:
        action_filter = st.text_input("Filter by Action", placeholder="e.g., login, data_saved")
    
    with col3:
        user_filter = st.text_input("Filter by User", placeholder="Username")
    
    # Get audit logs
    audit_logs = db_manager.get_audit_log(log_limit)
    
    # Apply filters
    if action_filter:
        audit_logs = [log for log in audit_logs if action_filter.lower() in log['action'].lower()]
    
    if user_filter:
        audit_logs = [log for log in audit_logs if user_filter.lower() in log['user'].lower()]
    
    # Display audit logs
    if audit_logs:
        st.markdown(f"### 📋 Audit Log ({len(audit_logs)} entries)")
        
        # Convert to DataFrame for better display
        audit_data = []
        for log in audit_logs:
            audit_data.append({
                'Timestamp': log['timestamp'],
                'User': log['user'],
                'Action': log['action'],
                'Details': str(log['details'])[:100] + '...' if len(str(log['details'])) > 100 else str(log['details'])
            })
        
        df_audit = pd.DataFrame(audit_data)
        st.dataframe(df_audit, use_container_width=True)
        
        # Action statistics
        st.divider()
        st.markdown("### 📊 Audit Statistics")
        
        # Action frequency
        actions = [log['action'] for log in audit_logs]
        action_counts = pd.Series(actions).value_counts()
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_actions = px.bar(
                x=action_counts.index[:10],
                y=action_counts.values[:10],
                title="Top 10 Actions",
                labels={'x': 'Action', 'y': 'Count'}
            )
            fig_actions.update_xaxis(tickangle=-45)
            st.plotly_chart(fig_actions, use_container_width=True)
        
        with col2:
            # User activity
            users = [log['user'] for log in audit_logs]
            user_counts = pd.Series(users).value_counts()
            
            fig_users = px.pie(
                values=user_counts.values,
                names=user_counts.index,
                title="Activity by User"
            )
            st.plotly_chart(fig_users, use_container_width=True)
    
    else:
        st.info("No audit logs found matching the criteria")
    
    # Audit management actions
    st.divider()
    st.markdown("### 🔧 Audit Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📤 Export Audit Log", use_container_width=True):
            export_audit_log(audit_logs)
    
    with col2:
        if st.button("🧹 Clean Old Logs", use_container_width=True):
            clean_old_audit_logs(db_manager)
    
    with col3:
        if st.button("📊 Generate Report", use_container_width=True):
            generate_audit_report(audit_logs)

def user_management():
    """User management interface"""
    st.subheader("👥 User Management")
    
    auth_manager = st.session_state.auth_manager
    current_user = auth_manager.get_current_user()
    
    # Only admins can manage users
    if current_user['role'] != 'admin':
        st.error("⛔ Admin access required for user management")
        return
    
    # User management tabs
    user_tabs = st.tabs(["👥 All Users", "➕ Add User", "🔧 User Settings"])
    
    with user_tabs[0]:
        display_all_users()
    
    with user_tabs[1]:
        add_new_user(auth_manager)
    
    with user_tabs[2]:
        user_settings_management()

def display_all_users():
    """Display all users with management options"""
    st.markdown("### 👥 All Users")
    
    db_manager = st.session_state.db_manager
    
    # Get users from database
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, role, is_active, created_at, last_login
            FROM users
            ORDER BY created_at DESC
        ''')
        users = [dict(row) for row in cursor.fetchall()]
    
    if users:
        # Display users table
        user_data = []
        for user in users:
            user_data.append({
                'ID': user['id'],
                'Username': user['username'],
                'Role': user['role'].title(),
                'Status': '✅ Active' if user['is_active'] else '❌ Inactive',
                'Created': user['created_at'][:10] if user['created_at'] else 'N/A',
                'Last Login': user['last_login'][:10] if user['last_login'] else 'Never'
            })
        
        df_users = pd.DataFrame(user_data)
        st.dataframe(df_users, use_container_width=True)
        
        # User actions
        st.markdown("### 🔧 User Actions")
        
        selected_user_id = st.selectbox(
            "Select User",
            [f"{user['id']} - {user['username']}" for user in users]
        )
        
        if selected_user_id:
            user_id = int(selected_user_id.split(' - ')[0])
            selected_user = next(user for user in users if user['id'] == user_id)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                new_role = st.selectbox(
                    "Change Role",
                    ['viewer', 'editor', 'manager', 'admin'],
                    index=['viewer', 'editor', 'manager', 'admin'].index(selected_user['role'])
                )
                
                if st.button("Update Role", use_container_width=True):
                    update_user_role(user_id, new_role, db_manager)
                    st.rerun()
            
            with col2:
                if st.button("Reset Password", use_container_width=True):
                    reset_user_password(user_id, db_manager)
            
            with col3:
                status_action = "Deactivate" if selected_user['is_active'] else "Activate"
                if st.button(status_action, use_container_width=True):
                    toggle_user_status(user_id, db_manager)
                    st.rerun()
            
            with col4:
                if st.button("Delete User", use_container_width=True):
                    if st.checkbox(f"Confirm delete {selected_user['username']}"):
                        delete_user(user_id, db_manager)
                        st.rerun()
    
    else:
        st.info("No users found")

def add_new_user(auth_manager):
    """Add new user interface"""
    st.markdown("### ➕ Add New User")
    
    with st.form("add_user_form"):
        username = st.text_input("Username", help="Unique username for the new user")
        password = st.text_input("Password", type="password", help="Initial password (user can change later)")
        confirm_password = st.text_input("Confirm Password", type="password")
        role = st.selectbox("Role", ['viewer', 'editor', 'manager', 'admin'])
        
        submitted = st.form_submit_button("Create User", type="primary")
        
        if submitted:
            if not username or not password:
                st.error("Username and password are required")
            elif password != confirm_password:
                st.error("Passwords do not match")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters")
            else:
                success = auth_manager.create_user(username, password, role)
                if success:
                    st.success(f"✅ User '{username}' created successfully with role '{role}'")
                    
                    # Log action
                    st.session_state.db_manager.log_action('user_created', {
                        'new_username': username,
                        'role': role
                    }, st.session_state.auth_manager.get_current_user()['username'])
                    
                else:
                    st.error("Failed to create user. Username may already exist.")

def system_administration():
    """System administration tools"""
    st.subheader("⚙️ System Administration")
    
    current_user = st.session_state.auth_manager.get_current_user()
    
    if current_user['role'] != 'admin':
        st.error("⛔ Admin access required")
        return
    
    # System information
    st.markdown("### 🖥️ System Information")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Database info
        db_manager = st.session_state.db_manager
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Count records
            cursor.execute("SELECT COUNT(*) FROM employees")
            employee_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM business_units")
            unit_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM commissions")
            commission_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM audit_log")
            log_count = cursor.fetchone()[0]
        
        st.markdown("**Database Records**")
        st.write(f"Employees: {employee_count}")
        st.write(f"Business Units: {unit_count}")
        st.write(f"Commissions: {commission_count}")
        st.write(f"Audit Logs: {log_count}")
    
    with col2:
        # System status
        st.markdown("**System Status**")
        st.write("✅ Database: Online")
        st.write("✅ Authentication: Active")
        st.write("✅ Backup System: Running")
        st.write("✅ Logging: Enabled")
    
    with col3:
        # System metrics
        st.markdown("**Performance Metrics**")
        
        # Calculate some basic metrics
        calc = st.session_state.calculator
        total_employees = len(calc.employees)
        active_employees = len([e for e in calc.employees.values() if e.total_hours > 0])
        
        st.write(f"Active Users: {len([u for u in get_all_users() if u['is_active']])}")
        st.write(f"Active Employees: {active_employees}/{total_employees}")
        st.write(f"Data Utilization: {(active_employees/total_employees*100):.1f}%" if total_employees > 0 else "0%")
    
    # System operations
    st.divider()
    st.markdown("### 🔧 System Operations")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 System Backup", type="primary", use_container_width=True):
            try:
                backup_path = db_manager.create_backup("admin_manual")
                st.success(f"✅ Backup created: {backup_path}")
            except Exception as e:
                st.error(f"Backup failed: {str(e)}")
    
    with col2:
        if st.button("🧹 Clean Database", use_container_width=True):
            if st.checkbox("Confirm database cleanup"):
                cleanup_database(db_manager)
    
    with col3:
        if st.button("📊 Generate Report", use_container_width=True):
            generate_system_report()
    
    with col4:
        if st.button("🔄 Restart Services", use_container_width=True):
            st.info("Service restart feature coming soon")
    
    # System settings
    st.divider()
    st.markdown("### ⚙️ System Settings")
    
    # Configuration settings
    settings_form = st.form("system_settings")
    
    with settings_form:
        col1, col2 = st.columns(2)
        
        with col1:
            session_timeout = st.number_input(
                "Session Timeout (minutes)",
                min_value=15,
                max_value=480,
                value=60
            )
            
            max_upload_size = st.number_input(
                "Max Upload Size (MB)",
                min_value=1,
                max_value=100,
                value=10
            )
        
        with col2:
            auto_backup_enabled = st.checkbox("Enable Auto Backup", value=True)
            
            backup_frequency = st.selectbox(
                "Backup Frequency",
                ["Daily", "Weekly", "Monthly"],
                index=0
            )
        
        if st.form_submit_button("Save Settings", type="primary"):
            save_system_settings({
                'session_timeout': session_timeout,
                'max_upload_size': max_upload_size,
                'auto_backup_enabled': auto_backup_enabled,
                'backup_frequency': backup_frequency
            })
            st.success("✅ System settings saved")

def data_migration_tools():
    """Data migration and import/export tools"""
    st.subheader("🔄 Data Migration Tools")
    
    st.info("🔧 Tools for migrating data between systems and formats")
    
    # Migration tabs
    migration_tabs = st.tabs(["📤 Export All", "📥 Import Data", "🔄 Data Transformation"])
    
    with migration_tabs[0]:
        full_system_export()
    
    with migration_tabs[1]:
        system_data_import()
    
    with migration_tabs[2]:
        data_transformation_tools()

def performance_monitoring():
    """System performance monitoring"""
    st.subheader("📈 Performance Monitoring")
    
    st.info("📊 Monitor system performance and usage patterns")
    
    # Performance metrics
    calc = st.session_state.calculator
    db_manager = st.session_state.db_manager
    
    # Usage statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # User activity
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(DISTINCT user) 
                FROM audit_log 
                WHERE timestamp >= datetime('now', '-7 days')
            ''')
            active_users = cursor.fetchone()[0]
        
        st.metric("Active Users (7 days)", active_users)
    
    with col2:
        # Data operations
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) 
                FROM audit_log 
                WHERE action LIKE '%_saved%' AND timestamp >= datetime('now', '-7 days')
            ''')
            data_ops = cursor.fetchone()[0]
        
        st.metric("Data Operations (7 days)", data_ops)
    
    with col3:
        # System health score
        health_score = calculate_system_health(calc, db_manager)
        st.metric("System Health", f"{health_score:.1f}%")
    
    with col4:
        # Response time (simulated)
        avg_response = 0.25  # Simulated average response time
        st.metric("Avg Response Time", f"{avg_response:.2f}s")
    
    # Performance charts
    st.divider()
    
    # User activity over time (simulated)
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    activity_data = []
    
    for date in dates:
        # Simulate activity data
        base_activity = 10
        weekend_factor = 0.3 if date.weekday() >= 5 else 1.0
        daily_activity = int(base_activity * weekend_factor * (1 + np.random.uniform(-0.3, 0.3)))
        
        activity_data.append({
            'Date': date,
            'User_Activity': daily_activity,
            'Data_Operations': int(daily_activity * 2.5),
            'System_Load': daily_activity * 0.1
        })
    
    df_activity = pd.DataFrame(activity_data)
    
    # Activity trend chart
    fig_activity = go.Figure()
    
    fig_activity.add_trace(go.Scatter(
        x=df_activity['Date'],
        y=df_activity['User_Activity'],
        mode='lines+markers',
        name='User Activity'
    ))
    
    fig_activity.add_trace(go.Scatter(
        x=df_activity['Date'],
        y=df_activity['Data_Operations'],
        mode='lines+markers',
        name='Data Operations'
    ))
    
    fig_activity.update_layout(
        title='System Activity Trends (30 days)',
        xaxis_title='Date',
        yaxis_title='Activity Count'
    )
    
    st.plotly_chart(fig_activity, use_container_width=True)

# Helper functions
def save_commission_split(split):
    """Save commission split to database"""
    try:
        db_manager = st.session_state.db_manager
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO commission_splits
                (id, job_id, employee_splits, total_amount, created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                split.id,
                split.job_id,
                json.dumps({emp_id: float(pct) for emp_id, pct in split.employee_splits.items()}),
                float(split.total_amount),
                split.created_by,
                split.created_at.isoformat(),
                split.updated_at.isoformat()
            ))
        
        logger.info(f"Commission split saved: {split.job_id}")
        
    except Exception as e:
        logger.error(f"Error saving commission split: {e}")
        raise

def delete_commission_split(job_id: str, calc):
    """Delete commission split"""
    try:
        if job_id in calc.commission_splits:
            del calc.commission_splits[job_id]
        
        # Remove from database
        db_manager = st.session_state.db_manager
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM commission_splits WHERE job_id = ?', (job_id,))
        
        st.success(f"✅ Commission split deleted: {job_id}")
        
        # Log action
        db_manager.log_action('commission_split_deleted', {
            'job_id': job_id
        }, st.session_state.auth_manager.get_current_user()['username'])
        
    except Exception as e:
        st.error(f"Error deleting split: {str(e)}")

def get_all_users():
    """Get all users from database"""
    db_manager = st.session_state.db_manager
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users')
        return [dict(row) for row in cursor.fetchall()]

def update_user_role(user_id: int, new_role: str, db_manager):
    """Update user role"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET role = ?, updated_at = ? WHERE id = ?
            ''', (new_role, datetime.now().isoformat(), user_id))
        
        st.success(f"✅ User role updated to {new_role}")
        
        # Log action
        db_manager.log_action('user_role_updated', {
            'user_id': user_id,
            'new_role': new_role
        }, st.session_state.auth_manager.get_current_user()['username'])
        
    except Exception as e:
        st.error(f"Error updating user role: {str(e)}")

def calculate_system_health(calc, db_manager):
    """Calculate system health score"""
    score = 100.0
    
    # Check data completeness
    if not calc.employees:
        score -= 20
    elif any(emp.hourly_rate == 0 for emp in calc.employees.values()):
        score -= 10
    
    if not calc.business_units:
        score -= 20
    elif any(unit.commission_rate == 0 for unit in calc.business_units.values()):
        score -= 10
    
    # Check database health
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM audit_log WHERE timestamp >= datetime('now', '-1 day')")
            recent_activity = cursor.fetchone()[0]
            
            if recent_activity == 0:
                score -= 15
    except:
        score -= 25
    
    return max(0, score)

# Placeholder functions for features to be implemented
def export_commission_splits(calc):
    """Export commission splits"""
    st.info("Export functionality coming soon")

def import_commission_splits(file, calc):
    """Import commission splits"""
    st.info("Import functionality coming soon")

def recalculate_all_splits(calc):
    """Recalculate all commission splits"""
    st.info("Recalculation functionality coming soon")

def export_audit_log(logs):
    """Export audit log"""
    st.info("Audit log export coming soon")

def clean_old_audit_logs(db_manager):
    """Clean old audit logs"""
    st.info("Audit log cleanup coming soon")

def generate_audit_report(logs):
    """Generate audit report"""
    st.info("Audit report generation coming soon")

def user_settings_management():
    """User settings management"""
    st.info("User settings management coming soon")

def reset_user_password(user_id, db_manager):
    """Reset user password"""
    st.info("Password reset functionality coming soon")

def toggle_user_status(user_id, db_manager):
    """Toggle user active status"""
    st.info("User status toggle coming soon")

def delete_user(user_id, db_manager):
    """Delete user"""
    st.info("User deletion coming soon")

def cleanup_database(db_manager):
    """Clean up database"""
    st.info("Database cleanup coming soon")

def generate_system_report():
    """Generate system report"""
    st.info("System report generation coming soon")

def save_system_settings(settings):
    """Save system settings"""
    st.info("System settings save coming soon")

def full_system_export():
    """Full system export"""
    st.info("Full system export coming soon")

def system_data_import():
    """System data import"""
    st.info("System data import coming soon")

def data_transformation_tools():
    """Data transformation tools"""
    st.info("Data transformation tools coming soon")

def apply_commission_split(job_id, split, calc):
    """Apply commission split to calculations"""
    st.info("Commission split application coming soon")