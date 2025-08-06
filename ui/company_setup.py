"""
Company Setup UI Module
Handles employee management, data uploads, and system configuration
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from .utils import (
    safe_session_get,
    safe_session_check,
    safe_session_init,
    validate_file_size,
    validate_file_content,
    format_currency,
    get_project_root
)

def display_company_setup_tab():
    """Main company setup interface"""
    st.markdown("## ⚙️ Company Setup")
    st.markdown("Configure your company settings, employees, pay periods, and commission structure")
    
    # Create tabs for different setup sections
    setup_tabs = st.tabs([
        "📅 Pay Period Setup",
        "👥 Employee Management",
        "💰 Commission Configuration",
        "🗂️ Backup & Restore"
    ])
    
    with setup_tabs[0]:
        display_pay_period_setup()
    
    with setup_tabs[1]:
        display_employee_management()
    
    with setup_tabs[2]:
        display_commission_configuration()
    
    with setup_tabs[3]:
        display_backup_restore()

def display_pay_period_setup():
    """Pay period configuration and management"""
    st.markdown("### 📅 Pay Period Setup")
    st.markdown("Configure your company's pay schedule and manage pay periods")
    
    # Initialize pay period settings
    safe_session_init('pay_period_settings', {
        'schedule': 'Bi-weekly',
        'start_date': None,
        'configured': False
    })
    
    pay_settings = safe_session_get('pay_period_settings', {})
    
    # Check if pay periods are configured
    if not pay_settings.get('configured', False):
        display_pay_period_configuration()
    else:
        display_pay_period_management()

def display_pay_period_configuration():
    """Initial pay period configuration"""
    st.info("🚀 **Welcome!** Let's set up your pay period schedule. This is a one-time setup that will automate all your payroll date calculations.")
    
    with st.form("pay_period_config"):
        col1, col2 = st.columns(2)
        
        with col1:
            schedule = st.selectbox(
                "Pay Schedule Type*",
                ["Weekly", "Bi-weekly", "Semi-monthly", "Monthly"],
                index=1,  # Default to Bi-weekly
                help="How often do you run payroll?"
            )
            
            # Show schedule details
            schedule_info = {
                "Weekly": "52 pay periods per year (every 7 days)",
                "Bi-weekly": "26 pay periods per year (every 14 days)",
                "Semi-monthly": "24 pay periods per year (1st & 15th or 15th & last day)",
                "Monthly": "12 pay periods per year"
            }
            st.info(f"ℹ️ {schedule_info[schedule]}")
        
        with col2:
            if schedule == "Semi-monthly":
                # For semi-monthly, offer common options
                semi_option = st.radio(
                    "Semi-monthly Schedule",
                    ["1st and 15th", "15th and Last Day"],
                    help="Choose your semi-monthly pay dates"
                )
                # Use the 1st as the reference start date
                start_date = st.date_input(
                    "Reference Start Date*",
                    value=datetime.now().replace(day=1).date(),
                    help="Pick the 1st or 15th of any month to start"
                )
            else:
                start_date = st.date_input(
                    "First Pay Period Start Date*",
                    value=datetime.now().date() - timedelta(days=datetime.now().weekday()),  # Last Monday
                    help="When does your first pay period begin?"
                )
            
            # Show pay period end date
            if schedule == "Weekly":
                end_date = start_date + timedelta(days=6)
            elif schedule == "Bi-weekly":
                end_date = start_date + timedelta(days=13)
            elif schedule == "Semi-monthly":
                if semi_option == "1st and 15th":
                    if start_date.day == 1:
                        end_date = start_date.replace(day=14)
                    else:
                        end_date = start_date.replace(day=1) + timedelta(days=30)
                        end_date = end_date.replace(day=1) - timedelta(days=1)
                else:  # 15th and Last Day
                    if start_date.day == 15:
                        # Get last day of month
                        next_month = start_date.replace(day=1) + timedelta(days=32)
                        end_date = next_month - timedelta(days=next_month.day)
                    else:
                        end_date = start_date.replace(day=14)
            else:  # Monthly
                next_month = start_date.replace(day=1) + timedelta(days=32)
                end_date = next_month - timedelta(days=next_month.day)
            
            st.info(f"📆 First pay period: {start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}")
        
        # Generate preview of upcoming pay periods
        st.markdown("#### 📅 Preview of Upcoming Pay Periods")
        preview_periods = generate_pay_periods(start_date, schedule, 6)  # Show next 6 periods
        
        preview_df = pd.DataFrame(preview_periods)
        preview_df['Period'] = preview_df.index + 1
        preview_df = preview_df[['Period', 'start_date', 'end_date', 'pay_date']]
        preview_df.columns = ['Period #', 'Start Date', 'End Date', 'Pay Date']
        
        # Format dates
        for col in ['Start Date', 'End Date', 'Pay Date']:
            preview_df[col] = pd.to_datetime(preview_df[col]).dt.strftime('%b %d, %Y')
        
        st.dataframe(preview_df, hide_index=True, use_container_width=True)
        
        if st.form_submit_button("🚀 Configure Pay Periods", type="primary"):
            # Save pay period configuration
            st.session_state.pay_period_settings = {
                'schedule': schedule,
                'start_date': start_date,
                'configured': True,
                'semi_option': semi_option if schedule == "Semi-monthly" else None,
                'created_at': datetime.now().isoformat()
            }
            
            # Generate and store pay periods for the current year
            current_periods = generate_pay_periods(start_date, schedule, 26 if schedule == "Bi-weekly" else 52)
            st.session_state.pay_periods = current_periods
            
            st.success("✅ Pay period configuration saved successfully!")
            st.rerun()

def display_pay_period_management():
    """Manage configured pay periods"""
    pay_settings = safe_session_get('pay_period_settings', {})
    
    # Display current configuration
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Pay Schedule", pay_settings.get('schedule', 'Not Set'))
        
    with col2:
        start_date = pay_settings.get('start_date')
        if start_date:
            st.metric("First Pay Period", start_date.strftime('%b %d, %Y') if isinstance(start_date, datetime) else str(start_date))
        else:
            st.metric("First Pay Period", "Not Set")
    
    with col3:
        # Get current pay period
        current_period = get_current_pay_period()
        if current_period:
            st.metric("Current Pay Period", f"{current_period['number']} of {current_period['total_year']}")
        else:
            st.metric("Current Pay Period", "Not Available")
    
    # Pay period selector and viewer
    st.markdown("---")
    st.markdown("#### 📅 Pay Period Viewer")
    
    # Generate pay periods for the year
    if not safe_session_check('pay_periods'):
        start_date = pay_settings.get('start_date')
        schedule = pay_settings.get('schedule')
        if start_date and schedule:
            periods_to_generate = {
                'Weekly': 52,
                'Bi-weekly': 26,
                'Semi-monthly': 24,
                'Monthly': 12
            }.get(schedule, 26)
            
            current_periods = generate_pay_periods(start_date, schedule, periods_to_generate)
            st.session_state.pay_periods = current_periods
    
    pay_periods = safe_session_get('pay_periods', [])
    
    if pay_periods:
        # Current pay period highlight
        current_period = get_current_pay_period()
        if current_period:
            st.success(f"📍 **Current Pay Period:** Period {current_period['number']} ({current_period['start_date'].strftime('%b %d')} - {current_period['end_date'].strftime('%b %d, %Y')})")
        
        # Pay period selector
        period_options = [f"Period {p['number']}: {p['start_date'].strftime('%b %d')} - {p['end_date'].strftime('%b %d, %Y')}" 
                         for p in pay_periods]
        
        selected_period_idx = st.selectbox(
            "Select Pay Period to View",
            range(len(period_options)),
            format_func=lambda x: period_options[x],
            index=current_period['number'] - 1 if current_period else 0
        )
        
        selected_period = pay_periods[selected_period_idx]
        
        # Display selected pay period details
        st.markdown("##### 📋 Pay Period Details")
        detail_col1, detail_col2, detail_col3 = st.columns(3)
        
        with detail_col1:
            st.info(f"**Start Date:** {selected_period['start_date'].strftime('%B %d, %Y')}")
        
        with detail_col2:
            st.info(f"**End Date:** {selected_period['end_date'].strftime('%B %d, %Y')}")
        
        with detail_col3:
            st.info(f"**Pay Date:** {selected_period['pay_date'].strftime('%B %d, %Y')}")
        
        # Store selected pay period in session for use across the app
        st.session_state.selected_pay_period = selected_period
    
    # Advanced options
    with st.expander("⚙️ Advanced Pay Period Options", expanded=False):
        st.markdown("#### 🔧 Modify Pay Period Configuration")
        st.warning("⚠️ **Caution:** Changing pay period settings will affect all calculations. Only modify if necessary.")
        
        if st.button("🔄 Reset Pay Period Configuration", type="secondary"):
            if st.button("⚠️ Confirm Reset", type="primary"):
                st.session_state.pay_period_settings = {
                    'schedule': 'Bi-weekly',
                    'start_date': None,
                    'configured': False
                }
                if 'pay_periods' in st.session_state:
                    del st.session_state.pay_periods
                if 'selected_pay_period' in st.session_state:
                    del st.session_state.selected_pay_period
                st.rerun()

def generate_pay_periods(start_date, schedule, num_periods=26):
    """Generate pay periods based on schedule"""
    periods = []
    current_start = start_date
    
    for i in range(num_periods):
        if schedule == "Weekly":
            current_end = current_start + timedelta(days=6)
            pay_date = current_end + timedelta(days=4)  # Pay on Thursday after period ends
        
        elif schedule == "Bi-weekly":
            current_end = current_start + timedelta(days=13)
            pay_date = current_end + timedelta(days=4)  # Pay on Thursday after period ends
        
        elif schedule == "Semi-monthly":
            if current_start.day == 1:
                current_end = current_start.replace(day=14)
                pay_date = current_start.replace(day=15)
            elif current_start.day == 15:
                # Get last day of month
                next_month = current_start.replace(day=1) + timedelta(days=32)
                current_end = next_month - timedelta(days=next_month.day)
                pay_date = next_month.replace(day=1)
            else:
                # Handle edge cases
                if current_start.day < 15:
                    current_end = current_start.replace(day=14)
                    pay_date = current_start.replace(day=15)
                else:
                    next_month = current_start.replace(day=1) + timedelta(days=32)
                    current_end = next_month - timedelta(days=next_month.day)
                    pay_date = next_month.replace(day=1)
        
        else:  # Monthly
            # Get last day of current month
            next_month = current_start.replace(day=1) + timedelta(days=32)
            current_end = next_month - timedelta(days=next_month.day)
            pay_date = next_month + timedelta(days=4)  # Pay on the 5th of next month
        
        periods.append({
            'number': i + 1,
            'start_date': current_start,
            'end_date': current_end,
            'pay_date': pay_date,
            'year': current_start.year,
            'total_year': num_periods
        })
        
        # Calculate next period start
        if schedule == "Semi-monthly":
            if current_start.day == 1:
                current_start = current_start.replace(day=15)
            else:
                current_start = (current_start.replace(day=1) + timedelta(days=32)).replace(day=1)
        else:
            current_start = current_end + timedelta(days=1)
    
    return periods

def get_current_pay_period():
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

def display_employee_management():
    """Employee management interface"""
    st.markdown("### 👥 Employee Management")
    
    # Smart Auto-Add Features
    display_smart_auto_add_section()
    
    # Add/Edit Employee Form
    with st.expander("➕ Add New Employee", expanded=False):
        display_add_employee_form()
    
    # Display existing employees
    display_employee_list()

def display_smart_auto_add_section():
    """Smart auto-add functionality for employees and business units"""
    st.markdown("#### 🤖 Smart Auto-Add")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Auto-Add Employees from Timesheet**")
        timesheet_data = safe_session_get('saved_timesheet_data')
        if timesheet_data is not None and not timesheet_data.empty:
            # Check for Employee Name column
            if 'Employee Name' in timesheet_data.columns:
                unique_employees = timesheet_data['Employee Name'].dropna().unique()
                existing_employees = safe_session_get('employee_data', pd.DataFrame())
                
                if not existing_employees.empty:
                    existing_names = existing_employees['Name'].tolist()
                    new_employees = [emp for emp in unique_employees if emp not in existing_names]
                else:
                    new_employees = unique_employees.tolist()
                
                if new_employees:
                    st.success(f"📋 Found {len(new_employees)} new employees in timesheet data")
                    
                    # Individual employee configuration
                    st.markdown("**👤 Configure Each Employee Individually**")
                    st.markdown("Set the status, department, rates, and commission plan for each employee found in your timesheet data.")
                    
                    # Initialize session state for employee configurations if not exists
                    if 'employee_configs' not in st.session_state:
                        st.session_state.employee_configs = {}
                    
                    # Ensure all new employees have default configurations
                    for emp_name in new_employees:
                        if emp_name not in st.session_state.employee_configs:
                            st.session_state.employee_configs[emp_name] = {
                                'status': 'Active',
                                'department': 'Operations',
                                'hourly_rate': 25.0,
                                'commission_plan': 'Efficiency Pay',
                                'include': True  # Whether to include this employee in the add
                            }
                    
                    # Display configuration for each employee
                    configured_employees = []
                    
                    for i, emp_name in enumerate(new_employees):
                        with st.container():
                            st.markdown(f"#### 👤 {emp_name}")
                            
                            # Use columns for compact layout with smaller hourly rate column
                            config_col1, config_col2, config_col3, config_col4, config_col5 = st.columns([0.7, 1.2, 1.2, 0.8, 1.1])
                            
                            with config_col1:
                                include_employee = st.checkbox(
                                    "Add",
                                    value=st.session_state.employee_configs[emp_name]['include'],
                                    key=f"include_{emp_name}",
                                    help=f"Include {emp_name} in the auto-add process"
                                )
                                st.session_state.employee_configs[emp_name]['include'] = include_employee
                            
                            with config_col2:
                                status = st.selectbox(
                                    "Status",
                                    ["Active", "Helper/Apprentice", "Inactive", "Excluded from Payroll"],
                                    index=["Active", "Helper/Apprentice", "Inactive", "Excluded from Payroll"].index(
                                        st.session_state.employee_configs[emp_name]['status']
                                    ),
                                    key=f"status_{emp_name}",
                                    disabled=not include_employee
                                )
                                st.session_state.employee_configs[emp_name]['status'] = status
                            
                            with config_col3:
                                department = st.selectbox(
                                    "Department",
                                    ["Operations", "Sales", "Management", "Administration", "Technical"],
                                    index=["Operations", "Sales", "Management", "Administration", "Technical"].index(
                                        st.session_state.employee_configs[emp_name]['department']
                                    ),
                                    key=f"dept_{emp_name}",
                                    disabled=not include_employee
                                )
                                st.session_state.employee_configs[emp_name]['department'] = department
                            
                            with config_col4:
                                hourly_rate = st.number_input(
                                    "Hourly Rate ($)",
                                    min_value=0.0,
                                    value=st.session_state.employee_configs[emp_name]['hourly_rate'],
                                    step=0.50,
                                    key=f"rate_{emp_name}",
                                    disabled=not include_employee
                                )
                                st.session_state.employee_configs[emp_name]['hourly_rate'] = hourly_rate
                            
                            with config_col5:
                                commission_plan = st.selectbox(
                                    "Plan",
                                    ["Efficiency Pay", "Hourly + Commission"],
                                    index=["Efficiency Pay", "Hourly + Commission"].index(
                                        st.session_state.employee_configs[emp_name]['commission_plan']
                                    ),
                                    key=f"plan_{emp_name}",
                                    disabled=not include_employee
                                )
                                st.session_state.employee_configs[emp_name]['commission_plan'] = commission_plan
                            
                            # Show status-specific info
                            if include_employee:
                                if status == "Helper/Apprentice":
                                    st.info("👷 Helper/Apprentice: Will be tracked with potential different commission rules.")
                                elif status == "Excluded from Payroll":
                                    st.warning("🚫 Excluded: Will NOT appear in commission calculations or payroll reports.")
                                elif status == "Inactive":
                                    st.info("😴 Inactive: In system but not included in active calculations.")
                            
                            if include_employee:
                                configured_employees.append({
                                    'name': emp_name,
                                    'config': st.session_state.employee_configs[emp_name]
                                })
                            
                            st.divider()
                    
                    # Summary and action buttons
                    if configured_employees:
                        selected_count = len(configured_employees)
                        st.markdown(f"### 📋 Summary: {selected_count} employee(s) selected for adding")
                        
                        # Quick actions
                        action_col1, action_col2, action_col3 = st.columns(3)
                        
                        with action_col1:
                            if st.button("✅ Select All", key="select_all_employees"):
                                for emp_name in new_employees:
                                    st.session_state.employee_configs[emp_name]['include'] = True
                                st.rerun()
                        
                        with action_col2:
                            if st.button("❌ Deselect All", key="deselect_all_employees"):
                                for emp_name in new_employees:
                                    st.session_state.employee_configs[emp_name]['include'] = False
                                st.rerun()
                        
                        with action_col3:
                            if st.button("🔄 Reset to Defaults", key="reset_employee_configs"):
                                st.session_state.employee_configs = {}
                                st.rerun()
                        
                        # Add selected employees button
                        if st.button(f"🚀 Add {selected_count} Selected Employee(s)", type="primary", key="auto_add_selected_employees"):
                            auto_add_configured_employees_from_timesheet(configured_employees)
                    
                    else:
                        st.info("ℹ️ No employees selected for adding. Use the checkboxes above to select employees.")
                else:
                    st.info("✅ All timesheet employees already exist in the system")
            else:
                st.warning("⚠️ No 'Employee Name' column found in timesheet data")
        else:
            st.info("📤 Upload timesheet data to auto-detect employees")
    
    with col2:
        st.markdown("**Auto-Add Business Units from Revenue**")
        revenue_data = safe_session_get('saved_revenue_data')
        if revenue_data is not None and not revenue_data.empty:
            # Check for Business Unit column
            if 'Business Unit' in revenue_data.columns:
                unique_units = revenue_data['Business Unit'].dropna().unique()
                existing_settings = safe_session_get('business_unit_commission_settings', {})
                
                new_units = [unit for unit in unique_units if unit not in existing_settings.keys()]
                
                if new_units:
                    st.success(f"🏢 Found {len(new_units)} new business units in revenue data")
                    
                    # Show preview of business units to be added
                    with st.expander(f"Preview {len(new_units)} business units to add", expanded=False):
                        preview_df = pd.DataFrame({
                            'Business Unit': new_units,
                            'Lead Gen Rate': [2.0] * len(new_units),
                            'Sales Rate': [3.0] * len(new_units),
                            'Work Done Rate': [2.5] * len(new_units)
                        })
                        st.dataframe(preview_df, hide_index=True, use_container_width=True)
                    
                    if st.button("🏢 Auto-Add All Business Units", type="primary", key="auto_add_units"):
                        auto_add_business_units_from_revenue(new_units)
                else:
                    st.info("✅ All revenue business units already configured")
            else:
                st.warning("⚠️ No 'Business Unit' column found in revenue data")
        else:
            st.info("📤 Upload revenue data to auto-detect business units")

def auto_add_configured_employees_from_timesheet(configured_employees):
    """Auto-add employees from timesheet data with individual configurations"""
    try:
        employee_data = safe_session_get('employee_data', pd.DataFrame())
        
        new_employees = []
        status_summary = {}
        
        for i, emp_config in enumerate(configured_employees):
            emp_name = emp_config['name']
            config = emp_config['config']
            
            emp_id = f"AUTO{str(i+1).zfill(3)}"
            
            # Generate unique employee ID
            while not employee_data.empty and emp_id in employee_data['Employee ID'].values:
                i += 1
                emp_id = f"AUTO{str(i+1).zfill(3)}"
            
            # Determine commission eligibility based on status
            commission_eligible = config['status'] not in ["Excluded from Payroll"]
            
            new_employee = {
                'Employee ID': emp_id,
                'Name': emp_name,
                'Department': config['department'],
                'Hourly Rate': config['hourly_rate'],
                'Status': config['status'],
                'Commission Eligible': commission_eligible,
                'Commission Plan': config['commission_plan'],
                'Hire Date': datetime.now().date()
            }
            new_employees.append(new_employee)
            
            # Track status for summary
            status = config['status']
            if status not in status_summary:
                status_summary[status] = 0
            status_summary[status] += 1
        
        # Add to existing employee data
        new_df = pd.DataFrame(new_employees)
        if employee_data.empty:
            st.session_state.employee_data = new_df
        else:
            st.session_state.employee_data = pd.concat([employee_data, new_df], ignore_index=True)
        
        st.success(f"✅ Successfully added {len(new_employees)} employees from timesheet data!")
        
        # Show detailed summary of what was added by status
        st.markdown("**📊 Employee Addition Summary:**")
        for status, count in status_summary.items():
            if status == "Helper/Apprentice":
                st.info(f"👷 **{count} Helper/Apprentice(s):** Added with potential different commission rules.")
            elif status == "Excluded from Payroll":
                st.warning(f"🚫 **{count} Excluded from Payroll:** These employees will NOT appear in commission calculations.")
            elif status == "Inactive":
                st.info(f"😴 **{count} Inactive:** Added to system but not included in active calculations.")
            else:
                st.info(f"✨ **{count} Active:** Normal commission-eligible employees ready for payroll.")
        
        # Clear the configurations after successful add
        if 'employee_configs' in st.session_state:
            del st.session_state.employee_configs
        
        st.info("💡 **Tip:** Review and edit the added employees in the Employee Management section below.")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error auto-adding employees: {str(e)}")

# Legacy function kept for backwards compatibility
def auto_add_employees_from_timesheet(employee_names, default_status="Active", 
                                     default_hourly_rate=25.0, default_commission_plan="Efficiency Pay",
                                     default_department="Operations", default_commission_eligible=True):
    """Legacy function - now redirects to individual configuration approach"""
    # Convert to new format
    configured_employees = []
    for name in employee_names:
        configured_employees.append({
            'name': name,
            'config': {
                'status': default_status,
                'department': default_department,
                'hourly_rate': default_hourly_rate,
                'commission_plan': default_commission_plan
            }
        })
    
    # Use the new function
    auto_add_configured_employees_from_timesheet(configured_employees)

def auto_add_business_units_from_revenue(business_units):
    """Auto-add business units from revenue data with default commission settings"""
    try:
        business_unit_settings = safe_session_get('business_unit_commission_settings', {})
        
        for unit in business_units:
            business_unit_settings[unit] = {
                'enabled': True,
                'lead_gen_rate': 2.0,  # Default 2%
                'sold_by_rate': 3.0,   # Default 3%
                'work_done_rate': 2.5, # Default 2.5%
                'auto_added': True,
                'date_added': datetime.now().isoformat()
            }
        
        st.session_state.business_unit_commission_settings = business_unit_settings
        
        st.success(f"✅ Successfully added {len(business_units)} business units with default commission rates!")
        st.info("💡 **Tip:** Review and adjust the commission rates in the Commission Configuration tab.")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error auto-adding business units: {str(e)}")

def display_add_employee_form():
    """Form to add new employees"""
    with st.form("add_employee_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            emp_id = st.text_input("Employee ID*", placeholder="EMP001")
            name = st.text_input("Full Name*", placeholder="John Doe")
            department = st.selectbox("Department", [
                "Sales", "Operations", "Management", "Administration", "Technical"
            ])
            hourly_rate = st.number_input("Hourly Rate ($)", min_value=0.0, value=25.0, step=0.50)
        
        with col2:
            status = st.selectbox("Status", [
                "Active", 
                "Inactive", 
                "Helper/Apprentice",
                "Excluded from Payroll"
            ])
            commission_eligible = st.checkbox("Commission Eligible", value=True)
            commission_plan = st.selectbox("Commission Plan", [
                "Efficiency Pay", "Hourly + Commission"
            ])
            hire_date = st.date_input("Hire Date", value=datetime.now().date())
        
        if st.form_submit_button("Add Employee", type="primary"):
            if emp_id and name:
                add_employee_to_database(
                    emp_id, name, department, hourly_rate, 
                    status, commission_eligible, commission_plan, hire_date
                )
            else:
                st.error("Please fill in Employee ID and Name")

def add_employee_to_database(emp_id: str, name: str, department: str, hourly_rate: float,
                           status: str, commission_eligible: bool, commission_plan: str, hire_date):
    """Add employee to the database"""
    
    # Initialize employee data if not exists
    employee_data = safe_session_get('employee_data', pd.DataFrame())
    
    # Check if employee ID already exists
    if not employee_data.empty and emp_id in employee_data['Employee ID'].values:
        st.error(f"Employee ID {emp_id} already exists")
        return
    
    # Create new employee record
    new_employee = {
        'Employee ID': emp_id,
        'Name': name,
        'Department': department,
        'Hourly Rate': hourly_rate,
        'Status': status,
        'Commission Eligible': commission_eligible,
        'Commission Plan': commission_plan,
        'Hire Date': hire_date,
        'Created Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Add to DataFrame
    if employee_data.empty:
        employee_data = pd.DataFrame([new_employee])
    else:
        employee_data = pd.concat([employee_data, pd.DataFrame([new_employee])], ignore_index=True)
    
    # Save to session state
    st.session_state.employee_data = employee_data
    
    st.success(f"✅ Employee {name} added successfully!")
    st.rerun()

def display_employee_list():
    """Display and manage existing employees"""
    st.markdown("#### 📋 Current Employees")
    
    employee_data = safe_session_get('employee_data', pd.DataFrame())
    
    if not employee_data.empty:
        # Add search/filter
        search = st.text_input("🔍 Search employees", placeholder="Search by name, ID, or department...")
        
        # Filter employees - exclude those marked as "Excluded from Payroll" 
        # but include Helper/Apprentice for visibility
        if not employee_data.empty:
            active_employees = employee_data[
                employee_data['Status'] != 'Excluded from Payroll'
            ].copy()
        else:
            active_employees = pd.DataFrame()
        
        if search and not active_employees.empty:
            mask = active_employees.apply(
                lambda row: search.lower() in str(row).lower(), axis=1
            )
            filtered_data = active_employees[mask].copy()
        else:
            filtered_data = active_employees.copy()
        
        if not filtered_data.empty:
            # Add original index for mapping back after edits
            filtered_data['_original_index'] = filtered_data.index
            
            # Configure editable columns
            column_config = {
                "Employee ID": st.column_config.TextColumn("Employee ID", disabled=True),
                "Name": st.column_config.TextColumn("Name"),
                "Department": st.column_config.SelectboxColumn(
                    "Department",
                    options=["Sales", "Operations", "Management", "Administration", "Technical"]
                ),
                "Hourly Rate": st.column_config.NumberColumn(
                    "Hourly Rate",
                    format="$%.2f",
                    min_value=0
                ),
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["Active", "Inactive", "Helper/Apprentice", "Excluded from Payroll"]
                ),
                "Commission Eligible": st.column_config.CheckboxColumn("Commission Eligible"),
                "Commission Plan": st.column_config.SelectboxColumn(
                    "Commission Plan",
                    options=["Efficiency Pay", "Hourly + Commission"]
                ),
                "Hire Date": st.column_config.DateColumn("Hire Date"),
                "_original_index": st.column_config.Column("_original_index", disabled=True)
            }
            
            # Hide internal index column
            edited_data = st.data_editor(
                filtered_data,
                hide_index=True,
                use_container_width=True,
                column_config=column_config,
                disabled=["Employee ID", "_original_index"]
            )
            
            # Save changes button
            if st.button("💾 Save Changes", type="primary"):
                try:
                    # Map changes back to original data using the original index
                    for _, row in edited_data.iterrows():
                        orig_idx = row['_original_index']
                        if orig_idx < len(st.session_state.employee_data):
                            # Update each field
                            st.session_state.employee_data.loc[orig_idx, 'Name'] = row['Name']
                            st.session_state.employee_data.loc[orig_idx, 'Department'] = row['Department']
                            st.session_state.employee_data.loc[orig_idx, 'Hourly Rate'] = row['Hourly Rate']
                            st.session_state.employee_data.loc[orig_idx, 'Status'] = row['Status']
                            st.session_state.employee_data.loc[orig_idx, 'Commission Eligible'] = row['Commission Eligible']
                            st.session_state.employee_data.loc[orig_idx, 'Commission Plan'] = row['Commission Plan']
                            st.session_state.employee_data.loc[orig_idx, 'Hire Date'] = row['Hire Date']
                    
                    st.success("✅ Employee changes saved successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error saving changes: {str(e)}")
        
        # Quick stats
        col1, col2, col3, col4 = st.columns(4)
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
                helpers = len(employee_data[employee_data['Status'] == 'Helper/Apprentice'])
            else:
                helpers = 0
            st.metric("Helpers/Apprentices", helpers)
        with col4:
            if not employee_data.empty:
                eligible = len(employee_data[employee_data['Commission Eligible'] == True])
            else:
                eligible = 0
            st.metric("Commission Eligible", eligible)
        
        # Show excluded employees section if any exist
        if not employee_data.empty:
            excluded_employees = employee_data[employee_data['Status'] == 'Excluded from Payroll']
            if not excluded_employees.empty:
                st.markdown("---")
                st.markdown("#### 🚫 Excluded from Payroll")
                st.info(f"Found {len(excluded_employees)} employees excluded from payroll calculations")
                
                with st.expander(f"View {len(excluded_employees)} excluded employees", expanded=False):
                    # Show excluded employees (read-only)
                    excluded_display = excluded_employees[['Employee ID', 'Name', 'Department', 'Status', 'Hire Date']].copy()
                    st.dataframe(excluded_display, hide_index=True, use_container_width=True)
                    
                    st.markdown("**📝 Note:** These employees are excluded from all commission calculations and payroll reports.")
    else:
        st.info("No employees added yet. Use the form above to add your first employee.")


def display_commission_auto_add_status():
    """Display auto-add status for business units in commission configuration"""
    business_unit_settings = safe_session_get('business_unit_commission_settings', {})
    
    if business_unit_settings:
        auto_added_units = [unit for unit, settings in business_unit_settings.items() if settings.get('auto_added', False)]
        
        if auto_added_units:
            st.info(f"🤖 **Smart Auto-Add Active:** {len(auto_added_units)} business units were automatically detected and added with default rates. Review and adjust rates as needed.")
            
            with st.expander(f"View {len(auto_added_units)} auto-added business units", expanded=False):
                auto_df = pd.DataFrame([
                    {
                        'Business Unit': unit,
                        'Lead Gen Rate': f"{settings.get('lead_gen_rate', 0):.1f}%",
                        'Sales Rate': f"{settings.get('sold_by_rate', 0):.1f}%", 
                        'Work Done Rate': f"{settings.get('work_done_rate', 0):.1f}%",
                        'Date Added': settings.get('date_added', 'Unknown')[:10]
                    }
                    for unit, settings in business_unit_settings.items() 
                    if settings.get('auto_added', False)
                ])
                
                st.dataframe(auto_df, hide_index=True, use_container_width=True)

def display_commission_configuration():
    """Configure commission rates by business unit"""
    st.markdown("### 💰 Commission Configuration")
    st.markdown("Set commission percentages by business unit and commission type")
    
    # Show smart auto-add status
    display_commission_auto_add_status()
    
    # Initialize commission rates
    safe_session_init('business_unit_rates', {})
    
    # SYNC FROM COMMISSION SETTINGS ON LOAD
    business_unit_rates = safe_session_get('business_unit_rates', {})
    business_unit_commission_settings = safe_session_get('business_unit_commission_settings', {})
    
    if (not business_unit_rates and business_unit_commission_settings):
        for unit_name, settings in business_unit_commission_settings.items():
            # Generate a code from the name
            code = ''.join([word[0].upper() for word in unit_name.split()][:3])
            if not code:
                code = unit_name[:3].upper()
            
            # Ensure unique code
            counter = 1
            original_code = code
            while code in business_unit_rates:
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
                        'created_by': safe_session_get('user', {}).get('username', 'Unknown')
                    }
                    
                    # SYNC WITH COMMISSION SETTINGS
                    safe_session_init('business_unit_commission_settings', {})
                    
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
        
        business_unit_rates = safe_session_get('business_unit_rates', {})
        if business_unit_rates:
            # Create a DataFrame for display
            units_data = []
            for code, unit in business_unit_rates.items():
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
                    "Code": st.column_config.TextColumn("Code", disabled=True),
                    "Name": st.column_config.TextColumn("Name"),
                    "Lead Gen %": st.column_config.NumberColumn(
                        "Lead Gen %", min_value=0, max_value=100, step=0.5, format="%.1f%%"
                    ),
                    "Sales %": st.column_config.NumberColumn(
                        "Sales %", min_value=0, max_value=100, step=0.5, format="%.1f%%"
                    ),
                    "Work Done %": st.column_config.NumberColumn(
                        "Work Done %", min_value=0, max_value=100, step=0.5, format="%.1f%%"
                    ),
                    "Created": st.column_config.DateColumn("Created", disabled=True),
                    "Delete": st.column_config.CheckboxColumn("Delete")
                },
                hide_index=True,
                use_container_width=True,
                key="business_units_editor"
            )
            
            # Save button
            if st.button("💾 Save All Changes", type="primary", use_container_width=True):
                # Handle updates and deletions
                update_business_units(edited_df)
        else:
            st.info("No business units configured yet. Add your first business unit to get started.")
    
    # Advanced Commission Settings Section
    display_advanced_commission_settings()

def update_business_units(edited_df: pd.DataFrame):
    """Update business units based on edited data"""
    # First, handle deletions
    codes_to_delete = []
    for _, row in edited_df.iterrows():
        if row['Delete']:
            codes_to_delete.append(row['Code'])
    
    # Delete marked units
    business_unit_rates = safe_session_get('business_unit_rates', {})
    for code in codes_to_delete:
        if code in business_unit_rates:
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
    
    # SYNC WITH COMMISSION SETTINGS
    safe_session_init('business_unit_commission_settings', {})
    
    # Sync all business unit rates to commission settings
    for code, unit_data in st.session_state.business_unit_rates.items():
        unit_name = unit_data['name']
        rates = unit_data['rates']
        
        st.session_state.business_unit_commission_settings[unit_name] = {
            'lead_gen_rate': rates['Lead Generation'],
            'sold_by_rate': rates['Sales'],
            'work_done_rate': rates['Work Done'],
            'enabled': True
        }
    
    # Also remove deleted units from commission settings
    for code in codes_to_delete:
        if code in business_unit_rates:
            unit_name = business_unit_rates[code]['name']
            if unit_name in st.session_state.business_unit_commission_settings:
                del st.session_state.business_unit_commission_settings[unit_name]
    
    if codes_to_delete:
        st.success(f"✅ Deleted {len(codes_to_delete)} business unit(s) and saved changes!")
    else:
        st.success("✅ Changes saved successfully!")
    st.rerun()

def display_advanced_commission_settings():
    """Display streamlined advanced commission settings"""
    st.markdown("---")
    st.markdown("### 🎯 Employee Commission Overrides")
    st.markdown("Set custom commission rates for specific employees that override business unit defaults.")
    
    business_unit_rates = safe_session_get('business_unit_rates', {})
    if not business_unit_rates:
        st.info("⚠️ Please configure business units first before setting up employee overrides.")
        return
    
    # Initialize advanced settings
    safe_session_init('employee_commission_overrides', {})
    
    # Get all employees
    employee_data = safe_session_get('employee_data', pd.DataFrame())
    if employee_data.empty:
        st.warning("⚠️ No employees found. Please add employees first.")
        return
    
    # Two-column layout for better organization
    col1, col2 = st.columns([1, 1])
    
    with col1:
        display_employee_override_manager()
    
    with col2:
        display_override_summary_table()

def display_employee_override_manager():
    """Simplified employee override manager"""
    st.markdown("#### 👤 Set Employee Override")
    
    # Get data
    employee_data = safe_session_get('employee_data', pd.DataFrame())
    business_unit_rates = safe_session_get('business_unit_rates', {})
    employee_overrides = safe_session_get('employee_commission_overrides', {})
    
    employees = employee_data['Name'].tolist()
    business_units = [(code, data['name']) for code, data in business_unit_rates.items()]
    
    with st.form("employee_override_form"):
        # Employee selection
        selected_employee = st.selectbox("Select Employee", [""] + employees)
        
        # Business Unit selection
        business_unit_options = [""] + [name for code, name in business_units]
        selected_business_unit = st.selectbox("Business Unit", business_unit_options)
        
        if selected_employee and selected_business_unit:
            # Get default rates for selected business unit
            selected_unit_code = next((code for code, name in business_units if name == selected_business_unit), None)
            default_rates = business_unit_rates[selected_unit_code]['rates'] if selected_unit_code else {}
            
            # Get current overrides
            current_override = employee_overrides.get(selected_business_unit, {}).get(selected_employee, {})
            
            st.markdown("**Commission Rates (%)**")
            st.markdown(f"*Default rates for {selected_business_unit}: Lead Gen: {default_rates.get('Lead Generation', 0)}%, Sales: {default_rates.get('Sales', 0)}%, Work Done: {default_rates.get('Work Done', 0)}%*")
            
            # Rate inputs with cleaner layout
            rate_col1, rate_col2, rate_col3 = st.columns(3)
            
            with rate_col1:
                lead_gen_enabled = st.checkbox("Override Lead Gen", value=current_override.get('use_lead_override', False))
                lead_gen_rate = st.number_input(
                    "Lead Gen Rate (%)", 
                    min_value=0.0, 
                    max_value=100.0, 
                    value=current_override.get('lead_gen_rate', default_rates.get('Lead Generation', 5.0)),
                    step=0.25,
                    disabled=not lead_gen_enabled
                )
            
            with rate_col2:
                sales_enabled = st.checkbox("Override Sales", value=current_override.get('use_sales_override', False))
                sales_rate = st.number_input(
                    "Sales Rate (%)", 
                    min_value=0.0, 
                    max_value=100.0, 
                    value=current_override.get('sold_by_rate', default_rates.get('Sales', 10.0)),
                    step=0.25,
                    disabled=not sales_enabled
                )
            
            with rate_col3:
                work_enabled = st.checkbox("Override Work Done", value=current_override.get('use_work_override', False))
                work_rate = st.number_input(
                    "Work Done Rate (%)", 
                    min_value=0.0, 
                    max_value=100.0, 
                    value=current_override.get('work_done_rate', default_rates.get('Work Done', 7.5)),
                    step=0.25,
                    disabled=not work_enabled
                )
            
        
        # Submit button (always present but disabled if form isn't ready)
        form_ready = bool(selected_employee and selected_business_unit)
        submitted = st.form_submit_button(
            "💾 Save Override", 
            type="primary", 
            use_container_width=True,
            disabled=not form_ready
        )
        
        if submitted and form_ready:
            # Save the override
            if selected_business_unit not in employee_overrides:
                st.session_state.employee_commission_overrides[selected_business_unit] = {}
            
            # Only save if at least one override is enabled
            if lead_gen_enabled or sales_enabled or work_enabled:
                st.session_state.employee_commission_overrides[selected_business_unit][selected_employee] = {
                    'lead_gen_rate': lead_gen_rate,
                    'sold_by_rate': sales_rate, 
                    'work_done_rate': work_rate,
                    'use_lead_override': lead_gen_enabled,
                    'use_sales_override': sales_enabled,
                    'use_work_override': work_enabled,
                    'last_updated': datetime.now().isoformat()
                }
                st.success(f"✅ Override saved for {selected_employee}")
            else:
                # Remove override if all are disabled
                if selected_employee in st.session_state.employee_commission_overrides.get(selected_business_unit, {}):
                    del st.session_state.employee_commission_overrides[selected_business_unit][selected_employee]
                    st.success(f"✅ Override removed for {selected_employee}")
            
            st.rerun()

def display_override_summary_table():
    """Display summary of all employee overrides in a clean table"""
    st.markdown("#### 📋 Current Overrides")
    
    employee_overrides = safe_session_get('employee_commission_overrides', {})
    
    if not employee_overrides:
        st.info("No employee overrides configured yet.")
        return
    
    # Build summary data
    override_data = []
    for business_unit, employees in employee_overrides.items():
        for employee, rates in employees.items():
            active_overrides = []
            if rates.get('use_lead_override'):
                active_overrides.append(f"Lead: {rates['lead_gen_rate']:.1f}%")
            if rates.get('use_sales_override'):
                active_overrides.append(f"Sales: {rates['sold_by_rate']:.1f}%")
            if rates.get('use_work_override'):
                active_overrides.append(f"Work: {rates['work_done_rate']:.1f}%")
            
            if active_overrides:
                override_data.append({
                    'Employee': employee,
                    'Business Unit': business_unit,
                    'Overrides': ' | '.join(active_overrides),
                    'Updated': rates.get('last_updated', '')[:10] if rates.get('last_updated') else ''
                })
    
    if override_data:
        override_df = pd.DataFrame(override_data)
        st.dataframe(override_df, use_container_width=True, hide_index=True)
        
        # Quick delete option
        st.markdown("**Quick Actions:**")
        delete_col1, delete_col2 = st.columns(2)
        
        with delete_col1:
            if st.button("🗑️ Clear All Overrides", type="secondary"):
                st.session_state.employee_commission_overrides = {}
                st.success("✅ All overrides cleared")
                st.rerun()
        
        with delete_col2:
            # Export overrides
            if st.button("📥 Export Overrides", type="secondary"):
                import json
                override_json = json.dumps(employee_overrides, indent=2)
                st.download_button(
                    label="Download Override Config",
                    data=override_json,
                    file_name=f"commission_overrides_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
    else:
        st.info("No active overrides to display.")

# Legacy functions have been removed and replaced with simplified version above

def display_backup_restore():
    """Backup and restore interface"""
    st.markdown("### 🗂️ Backup & Restore")
    st.markdown("Create backups of your data and restore from previous backups")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 💾 Create Backup")
        if st.button("📦 Create Full Backup", use_container_width=True):
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

def create_backup(backup_name: str):
    """Create a system backup"""
    
    try:
        # Create backup data
        backup_data = {
            'backup_name': backup_name,
            'created_date': datetime.now().isoformat(),
            'employee_data': safe_session_get('employee_data', pd.DataFrame()).to_dict('records') if not safe_session_get('employee_data', pd.DataFrame()).empty else [],
            'business_unit_rates': safe_session_get('business_unit_rates', {}),
            'business_unit_commission_settings': safe_session_get('business_unit_commission_settings', {}),
            'employee_commission_overrides': safe_session_get('employee_commission_overrides', {}),
            'timesheet_hour_overrides': safe_session_get('timesheet_hour_overrides', {}),
            'exclusion_list': safe_session_get('exclusion_list', [])
        }
        
        # Convert to JSON for download
        import json
        backup_json = json.dumps(backup_data, indent=2, default=str)
        
        st.download_button(
            label="📥 Download Backup",
            data=backup_json,
            file_name=f"commission_calc_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
        
        st.success("✅ Backup created successfully!")
        
    except Exception as e:
        st.error(f"❌ Error creating backup: {str(e)}")

def restore_from_backup(backup_file, restore_options: list):
    """Restore from backup file"""
    
    try:
        import json
        
        # Read backup data
        backup_content = backup_file.getvalue().decode('utf-8')
        backup_data = json.loads(backup_content)
        
        # Restore data based on options
        if "all" in restore_options:
            # Restore employee data
            if 'employee_data' in backup_data and backup_data['employee_data']:
                st.session_state.employee_data = pd.DataFrame(backup_data['employee_data'])
            
            # Restore business unit data
            if 'business_unit_rates' in backup_data:
                st.session_state.business_unit_rates = backup_data['business_unit_rates']
            
            if 'business_unit_commission_settings' in backup_data:
                st.session_state.business_unit_commission_settings = backup_data['business_unit_commission_settings']
            
            # Restore overrides
            if 'employee_commission_overrides' in backup_data:
                st.session_state.employee_commission_overrides = backup_data['employee_commission_overrides']
            
            if 'timesheet_hour_overrides' in backup_data:
                st.session_state.timesheet_hour_overrides = backup_data['timesheet_hour_overrides']
            
            if 'exclusion_list' in backup_data:
                st.session_state.exclusion_list = backup_data['exclusion_list']
        
        backup_date = backup_data.get('created_date', 'Unknown')
        st.success(f"✅ Backup restored successfully! (Created: {backup_date})")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error restoring backup: {str(e)}")
