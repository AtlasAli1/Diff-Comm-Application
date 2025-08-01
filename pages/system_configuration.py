import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any
from loguru import logger

def system_configuration_page():
    """Enhanced system configuration page with auto-save and validation"""
    st.title("⚙️ System Configuration")
    
    # Ensure session state is initialized
    if 'calculator' not in st.session_state:
        from models import CommissionCalculator
        st.session_state.calculator = CommissionCalculator()
    
    calc = st.session_state.calculator
    
    # Check if data is loaded
    if not calc.employees and not calc.business_units:
        st.warning("⚠️ Please upload data first in the Data Management page")
        if st.button("Go to Data Management"):
            st.session_state.selected_page = "📤 Data Management"
            st.rerun()
        return
    
    # Configuration tabs
    tabs = st.tabs([
        "💰 Hourly Rates",
        "📊 Commission Rates",
        "⏰ Period Settings",
        "🔧 Advanced Config",
        "📋 Configuration Summary"
    ])
    
    with tabs[0]:
        configure_hourly_rates()
    
    with tabs[1]:
        configure_commission_rates()
    
    with tabs[2]:
        configure_period_settings()
    
    with tabs[3]:
        advanced_configuration()
    
    with tabs[4]:
        configuration_summary()

def configure_hourly_rates():
    """Configure employee hourly rates with bulk operations"""
    st.subheader("💰 Employee Hourly Rates")
    
    calc = st.session_state.calculator
    
    if not calc.employees:
        st.info("No employees loaded. Please upload timesheet data.")
        return
    
    # Bulk operations
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        bulk_rate = st.number_input(
            "Bulk Rate ($)",
            min_value=0.0,
            step=0.50,
            help="Apply this rate to selected employees"
        )
    
    with col2:
        if st.button("Apply to All", use_container_width=True):
            if bulk_rate > 0:
                for emp in calc.employees.values():
                    emp.hourly_rate = Decimal(str(bulk_rate))
                st.success(f"Applied ${bulk_rate:.2f} to all employees")
                save_configuration()
                st.rerun()
    
    with col3:
        percentage_increase = st.number_input(
            "Increase %",
            min_value=-50.0,
            max_value=100.0,
            value=0.0,
            step=1.0
        )
    
    with col4:
        if st.button("Apply % Increase", use_container_width=True):
            if percentage_increase != 0:
                for emp in calc.employees.values():
                    new_rate = float(emp.hourly_rate) * (1 + percentage_increase / 100)
                    emp.hourly_rate = Decimal(str(round(new_rate, 2)))
                st.success(f"Applied {percentage_increase:+.1f}% increase to all rates")
                save_configuration()
                st.rerun()
    
    st.divider()
    
    # Department-based rates
    departments = list(set(emp.department for emp in calc.employees.values() if emp.department))
    
    if departments:
        st.markdown("### 🏢 Department-Based Rates")
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            selected_dept = st.selectbox("Select Department", ["All"] + sorted(departments))
        
        with col2:
            dept_rate = st.number_input(
                "Department Rate ($)",
                min_value=0.0,
                step=0.50,
                key="dept_rate"
            )
        
        with col3:
            if st.button("Apply to Dept", use_container_width=True):
                if dept_rate > 0:
                    count = 0
                    for emp in calc.employees.values():
                        if selected_dept == "All" or emp.department == selected_dept:
                            emp.hourly_rate = Decimal(str(dept_rate))
                            count += 1
                    st.success(f"Applied ${dept_rate:.2f} to {count} employees")
                    save_configuration()
                    st.rerun()
    
    st.divider()
    
    # Individual rate configuration
    st.markdown("### 👤 Individual Employee Rates")
    
    # Search and filter
    search_term = st.text_input("🔍 Search Employee", placeholder="Type to search...")
    
    # Sort options
    col1, col2 = st.columns([3, 1])
    with col1:
        sort_by = st.selectbox(
            "Sort by",
            ["Name", "Current Rate", "Department", "Total Hours"],
            label_visibility="collapsed"
        )
    with col2:
        sort_order = st.selectbox(
            "Order",
            ["Ascending", "Descending"],
            label_visibility="collapsed"
        )
    
    # Filter and sort employees
    employees = list(calc.employees.values())
    
    if search_term:
        employees = [emp for emp in employees if search_term.lower() in emp.name.lower()]
    
    # Sort employees
    if sort_by == "Name":
        employees.sort(key=lambda x: x.name, reverse=(sort_order == "Descending"))
    elif sort_by == "Current Rate":
        employees.sort(key=lambda x: x.hourly_rate, reverse=(sort_order == "Descending"))
    elif sort_by == "Department":
        employees.sort(key=lambda x: x.department or "", reverse=(sort_order == "Descending"))
    elif sort_by == "Total Hours":
        employees.sort(key=lambda x: x.total_hours, reverse=(sort_order == "Descending"))
    
    # Display employees with rates
    if employees:
        # Create columns for better layout
        for i in range(0, len(employees), 2):
            cols = st.columns(2)
            
            for j, col in enumerate(cols):
                if i + j < len(employees):
                    emp = employees[i + j]
                    
                    with col:
                        with st.container():
                            col1, col2, col3 = st.columns([3, 2, 1])
                            
                            with col1:
                                st.markdown(f"**{emp.name}**")
                                if emp.department:
                                    st.caption(f"Dept: {emp.department}")
                            
                            with col2:
                                new_rate = st.number_input(
                                    "Rate",
                                    min_value=0.0,
                                    value=float(emp.hourly_rate),
                                    step=0.50,
                                    key=f"rate_{emp.id}",
                                    label_visibility="collapsed",
                                    on_change=lambda emp_id=emp.id: update_employee_rate(emp_id)
                                )
                            
                            with col3:
                                labor_cost = float(emp.total_labor_cost)
                                st.metric("Labor", f"${labor_cost:.0f}", label_visibility="collapsed")
        
        # Summary statistics
        st.divider()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_rate = sum(float(emp.hourly_rate) for emp in employees) / len(employees)
            st.metric("Average Rate", f"${avg_rate:.2f}")
        
        with col2:
            min_rate = min(float(emp.hourly_rate) for emp in employees)
            st.metric("Minimum Rate", f"${min_rate:.2f}")
        
        with col3:
            max_rate = max(float(emp.hourly_rate) for emp in employees)
            st.metric("Maximum Rate", f"${max_rate:.2f}")
        
        with col4:
            zero_rate_count = sum(1 for emp in employees if emp.hourly_rate == 0)
            st.metric("Zero Rates", zero_rate_count)
        
        # Rate distribution chart
        if st.checkbox("Show Rate Distribution"):
            rate_data = [float(emp.hourly_rate) for emp in employees]
            fig = px.histogram(
                rate_data,
                nbins=20,
                title="Hourly Rate Distribution",
                labels={'value': 'Hourly Rate ($)', 'count': 'Number of Employees'}
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

def configure_commission_rates():
    """Configure business unit commission rates"""
    st.subheader("📊 Business Unit Commission Rates")
    
    calc = st.session_state.calculator
    
    if not calc.business_units:
        st.info("No business units loaded. Please upload revenue data.")
        return
    
    # Bulk operations
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        bulk_commission_rate = st.number_input(
            "Bulk Rate (%)",
            min_value=0.0,
            max_value=100.0,
            step=0.1,
            help="Apply this commission rate to all units"
        )
    
    with col2:
        if st.button("Apply to All Units", use_container_width=True):
            if bulk_commission_rate > 0:
                for unit in calc.business_units.values():
                    unit.commission_rate = Decimal(str(bulk_commission_rate))
                st.success(f"Applied {bulk_commission_rate:.1f}% to all business units")
                save_configuration()
                st.rerun()
    
    with col3:
        category_rate = st.number_input(
            "Category Rate (%)",
            min_value=0.0,
            max_value=100.0,
            step=0.1,
            key="cat_rate"
        )
    
    with col4:
        categories = list(set(unit.category for unit in calc.business_units.values() if unit.category))
        if categories:
            selected_category = st.selectbox("Category", ["All"] + sorted(categories), key="cat_select")
            
            if st.button("Apply to Category", use_container_width=True):
                if category_rate > 0:
                    count = 0
                    for unit in calc.business_units.values():
                        if selected_category == "All" or unit.category == selected_category:
                            unit.commission_rate = Decimal(str(category_rate))
                            count += 1
                    st.success(f"Applied {category_rate:.1f}% to {count} units")
                    save_configuration()
                    st.rerun()
    
    st.divider()
    
    # Individual unit configuration
    st.markdown("### 🏢 Individual Business Unit Rates")
    
    # Display units in a grid
    units = sorted(calc.business_units.values(), key=lambda x: x.revenue, reverse=True)
    
    for i, unit in enumerate(units):
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 2])
            
            with col1:
                st.markdown(f"**{unit.name}**")
                if unit.category:
                    st.caption(f"Category: {unit.category}")
            
            with col2:
                st.metric("Revenue", f"${float(unit.revenue):,.0f}", label_visibility="collapsed")
            
            with col3:
                new_rate = st.number_input(
                    "Commission %",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(unit.commission_rate),
                    step=0.1,
                    key=f"comm_rate_{unit.id}",
                    label_visibility="collapsed",
                    on_change=lambda unit_id=unit.id: update_commission_rate(unit_id)
                )
            
            with col4:
                commission_amount = float(unit.revenue) * new_rate / 100
                st.metric("Commission", f"${commission_amount:,.0f}", label_visibility="collapsed")
            
            with col5:
                net_revenue = float(unit.revenue) - commission_amount
                st.metric("Net", f"${net_revenue:,.0f}", label_visibility="collapsed")
    
    # Summary and analytics
    st.divider()
    
    total_revenue = sum(float(unit.revenue) for unit in units)
    total_commission = sum(float(unit.commission_amount) for unit in units)
    avg_rate = sum(float(unit.commission_rate) for unit in units) / len(units) if units else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Revenue", f"${total_revenue:,.2f}")
    
    with col2:
        st.metric("Total Commission", f"${total_commission:,.2f}")
    
    with col3:
        st.metric("Average Rate", f"{avg_rate:.1f}%")
    
    with col4:
        effective_rate = (total_commission / total_revenue * 100) if total_revenue > 0 else 0
        st.metric("Effective Rate", f"{effective_rate:.1f}%")
    
    # Commission analysis chart
    if st.checkbox("Show Commission Analysis"):
        chart_data = []
        for unit in units:
            chart_data.append({
                'Business Unit': unit.name,
                'Revenue': float(unit.revenue),
                'Commission': float(unit.commission_amount),
                'Rate': float(unit.commission_rate)
            })
        
        df = pd.DataFrame(chart_data)
        
        # Create subplot with revenue and commission
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Revenue',
            x=df['Business Unit'],
            y=df['Revenue'],
            marker_color='#2C5F75'
        ))
        
        fig.add_trace(go.Bar(
            name='Commission',
            x=df['Business Unit'],
            y=df['Commission'],
            marker_color='#922B3E'
        ))
        
        fig.update_layout(
            title="Revenue vs Commission by Business Unit",
            barmode='group',
            xaxis_tickangle=-45,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

def configure_period_settings():
    """Configure commission period settings"""
    st.subheader("⏰ Commission Period Settings")
    
    calc = st.session_state.calculator
    
    # Period selection
    col1, col2 = st.columns(2)
    
    with col1:
        period_start = st.date_input(
            "Period Start Date",
            value=datetime.now().replace(day=1),
            help="Start date for commission calculations"
        )
    
    with col2:
        period_end = st.date_input(
            "Period End Date",
            value=datetime.now(),
            help="End date for commission calculations"
        )
    
    # Validate dates
    if period_start >= period_end:
        st.error("End date must be after start date")
    else:
        days_in_period = (period_end - period_start).days + 1
        st.info(f"Period: {days_in_period} days")
    
    st.divider()
    
    # Period presets
    st.markdown("### 📅 Quick Period Selection")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Current Month", use_container_width=True):
            st.session_state.period_start = datetime.now().replace(day=1)
            st.session_state.period_end = datetime.now()
            st.rerun()
    
    with col2:
        if st.button("Last Month", use_container_width=True):
            last_month = datetime.now().replace(day=1) - timedelta(days=1)
            st.session_state.period_start = last_month.replace(day=1)
            st.session_state.period_end = last_month
            st.rerun()
    
    with col3:
        if st.button("Current Quarter", use_container_width=True):
            current_month = datetime.now().month
            quarter_start_month = ((current_month - 1) // 3) * 3 + 1
            st.session_state.period_start = datetime.now().replace(month=quarter_start_month, day=1)
            st.session_state.period_end = datetime.now()
            st.rerun()
    
    with col4:
        if st.button("Current Year", use_container_width=True):
            st.session_state.period_start = datetime.now().replace(month=1, day=1)
            st.session_state.period_end = datetime.now()
            st.rerun()
    
    st.divider()
    
    # Payment schedule
    st.markdown("### 💳 Payment Schedule")
    
    payment_frequency = st.selectbox(
        "Payment Frequency",
        ["Weekly", "Bi-Weekly", "Semi-Monthly", "Monthly", "Quarterly"],
        help="How often commissions are paid out"
    )
    
    payment_delay = st.number_input(
        "Payment Delay (days)",
        min_value=0,
        max_value=60,
        value=15,
        help="Days after period end before payment is made"
    )
    
    # Calculate next payment date
    if period_end:
        next_payment = period_end + timedelta(days=payment_delay)
        st.info(f"Next payment date: {next_payment.strftime('%Y-%m-%d')}")
    
    # Save period settings
    if st.button("💾 Save Period Settings", type="primary", use_container_width=True):
        calc.period_start = datetime.combine(period_start, datetime.min.time())
        calc.period_end = datetime.combine(period_end, datetime.max.time())
        
        # Save to configuration
        db = st.session_state.db_manager
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO configuration (key, value, updated_at)
                VALUES (?, ?, ?)
            ''', ('period_start', period_start.isoformat(), datetime.now().isoformat()))
            
            cursor.execute('''
                INSERT OR REPLACE INTO configuration (key, value, updated_at)
                VALUES (?, ?, ?)
            ''', ('period_end', period_end.isoformat(), datetime.now().isoformat()))
            
            cursor.execute('''
                INSERT OR REPLACE INTO configuration (key, value, updated_at)
                VALUES (?, ?, ?)
            ''', ('payment_frequency', payment_frequency, datetime.now().isoformat()))
            
            cursor.execute('''
                INSERT OR REPLACE INTO configuration (key, value, updated_at)
                VALUES (?, ?, ?)
            ''', ('payment_delay', str(payment_delay), datetime.now().isoformat()))
        
        st.success("✅ Period settings saved")
        
        # Log action
        current_user = st.session_state.auth_manager.get_current_user()
        db.log_action('period_settings_updated', {
            'period_start': period_start.isoformat(),
            'period_end': period_end.isoformat(),
            'payment_frequency': payment_frequency,
            'payment_delay': payment_delay
        }, current_user['username'] if current_user else 'system')

def advanced_configuration():
    """Advanced system configuration options"""
    st.subheader("🔧 Advanced Configuration")
    
    # Labor cost multipliers
    st.markdown("### ⚙️ Labor Cost Multipliers")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        regular_multiplier = st.number_input(
            "Regular Hours Multiplier",
            min_value=0.5,
            max_value=2.0,
            value=1.0,
            step=0.1,
            help="Multiplier for regular hours (default: 1.0)"
        )
    
    with col2:
        ot_multiplier = st.number_input(
            "Overtime Multiplier",
            min_value=1.0,
            max_value=3.0,
            value=1.5,
            step=0.1,
            help="Multiplier for overtime hours (default: 1.5)"
        )
    
    with col3:
        dt_multiplier = st.number_input(
            "Double Time Multiplier",
            min_value=1.5,
            max_value=4.0,
            value=2.0,
            step=0.1,
            help="Multiplier for double time hours (default: 2.0)"
        )
    
    st.divider()
    
    # Commission calculation method
    st.markdown("### 📊 Commission Calculation Method")
    
    calc_method = st.radio(
        "Distribution Method",
        [
            "Labor-Based (Proportional to labor cost)",
            "Hours-Based (Proportional to hours worked)",
            "Equal Distribution (Same amount for all)",
            "Custom Formula"
        ],
        help="How commissions are distributed among employees"
    )
    
    if calc_method == "Custom Formula":
        st.text_area(
            "Custom Formula (Python expression)",
            value="commission_pool * (employee_labor_cost / total_labor_cost)",
            help="Variables: commission_pool, employee_labor_cost, total_labor_cost, employee_hours, total_hours"
        )
    
    st.divider()
    
    # Rounding rules
    st.markdown("### 🔢 Rounding Rules")
    
    col1, col2 = st.columns(2)
    
    with col1:
        hours_rounding = st.selectbox(
            "Hours Rounding",
            ["No rounding", "Round to 0.25", "Round to 0.5", "Round to 1.0"],
            help="How to round hours for calculations"
        )
    
    with col2:
        currency_rounding = st.selectbox(
            "Currency Rounding",
            ["No rounding", "Round to cent", "Round to dollar", "Round to $5", "Round to $10"],
            help="How to round currency amounts"
        )
    
    st.divider()
    
    # Data retention
    st.markdown("### 📁 Data Retention")
    
    retention_days = st.number_input(
        "Audit Log Retention (days)",
        min_value=30,
        max_value=3650,
        value=365,
        help="How long to keep audit log entries"
    )
    
    backup_retention = st.number_input(
        "Backup Retention (count)",
        min_value=5,
        max_value=100,
        value=10,
        help="Number of backups to keep"
    )
    
    # Save advanced settings
    if st.button("💾 Save Advanced Settings", type="primary", use_container_width=True):
        db = st.session_state.db_manager
        
        settings = {
            'regular_multiplier': regular_multiplier,
            'ot_multiplier': ot_multiplier,
            'dt_multiplier': dt_multiplier,
            'calc_method': calc_method,
            'hours_rounding': hours_rounding,
            'currency_rounding': currency_rounding,
            'retention_days': retention_days,
            'backup_retention': backup_retention
        }
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            for key, value in settings.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO configuration (key, value, updated_at)
                    VALUES (?, ?, ?)
                ''', (key, str(value), datetime.now().isoformat()))
        
        st.success("✅ Advanced settings saved")
        
        # Log action
        current_user = st.session_state.auth_manager.get_current_user()
        db.log_action('advanced_settings_updated', settings, 
                     current_user['username'] if current_user else 'system')

def configuration_summary():
    """Display configuration summary and validation"""
    st.subheader("📋 Configuration Summary")
    
    calc = st.session_state.calculator
    db = st.session_state.db_manager
    
    # Load configuration from database
    config = {}
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT key, value FROM configuration')
        for row in cursor.fetchall():
            config[row['key']] = row['value']
    
    # Validation checks
    st.markdown("### ✅ Configuration Validation")
    
    checks = []
    
    # Check employees have rates
    if calc.employees:
        zero_rate_employees = [emp.name for emp in calc.employees.values() if emp.hourly_rate == 0]
        if zero_rate_employees:
            checks.append({
                'status': '⚠️',
                'message': f"{len(zero_rate_employees)} employees have zero hourly rate",
                'details': ', '.join(zero_rate_employees[:5]) + ('...' if len(zero_rate_employees) > 5 else '')
            })
        else:
            checks.append({
                'status': '✅',
                'message': "All employees have hourly rates configured",
                'details': f"{len(calc.employees)} employees"
            })
    else:
        checks.append({
            'status': '❌',
            'message': "No employees loaded",
            'details': "Upload timesheet data"
        })
    
    # Check business units have rates
    if calc.business_units:
        zero_rate_units = [unit.name for unit in calc.business_units.values() if unit.commission_rate == 0]
        if zero_rate_units:
            checks.append({
                'status': '⚠️',
                'message': f"{len(zero_rate_units)} business units have zero commission rate",
                'details': ', '.join(zero_rate_units[:5]) + ('...' if len(zero_rate_units) > 5 else '')
            })
        else:
            checks.append({
                'status': '✅',
                'message': "All business units have commission rates configured",
                'details': f"{len(calc.business_units)} units"
            })
    else:
        checks.append({
            'status': '❌',
            'message': "No business units loaded",
            'details': "Upload revenue data"
        })
    
    # Check period settings
    if 'period_start' in config and 'period_end' in config:
        checks.append({
            'status': '✅',
            'message': "Commission period configured",
            'details': f"{config['period_start']} to {config['period_end']}"
        })
    else:
        checks.append({
            'status': '❌',
            'message': "Commission period not configured",
            'details': "Set period in Period Settings tab"
        })
    
    # Display validation results
    for check in checks:
        col1, col2 = st.columns([1, 4])
        with col1:
            st.write(check['status'])
        with col2:
            st.write(f"**{check['message']}**")
            st.caption(check['details'])
    
    st.divider()
    
    # Configuration export/import
    st.markdown("### 💾 Configuration Backup")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 Export Configuration", use_container_width=True):
            export_configuration()
    
    with col2:
        uploaded_config = st.file_uploader("📥 Import Configuration", type=['json'])
        if uploaded_config:
            import_configuration(uploaded_config)
    
    st.divider()
    
    # Ready to calculate check
    all_checks_passed = all(check['status'] == '✅' for check in checks[:3])  # First 3 are critical
    
    if all_checks_passed:
        st.success("✅ System is ready to calculate commissions!")
        
        if st.button("🚀 Calculate Commissions Now", type="primary", use_container_width=True):
            with st.spinner("Calculating commissions..."):
                # Perform calculation
                period_start = datetime.fromisoformat(config.get('period_start', datetime.now().isoformat()))
                period_end = datetime.fromisoformat(config.get('period_end', datetime.now().isoformat()))
                
                commissions = calc.calculate_commissions(period_start, period_end)
                
                if commissions:
                    st.success(f"✅ Calculated {len(commissions)} commission entries")
                    
                    # Save to database
                    for commission in commissions:
                        db.save_commission(commission.to_dict())
                    
                    # Show summary
                    total_commission = sum(c.adjusted_amount for c in commissions)
                    st.metric("Total Commission", f"${float(total_commission):,.2f}")
                    
                    if st.button("View Commission Reports"):
                        st.session_state.selected_page = "📋 Commission Reports"
                        st.rerun()
                else:
                    st.warning("No commissions calculated. Check your data and configuration.")
    else:
        st.warning("⚠️ Please complete all configuration steps before calculating commissions")

# Helper functions
def update_employee_rate(employee_id: str):
    """Update employee hourly rate"""
    calc = st.session_state.calculator
    employee = calc.employees.get(employee_id)
    
    if employee:
        rate_key = f"rate_{employee_id}"
        if rate_key in st.session_state:
            new_rate = st.session_state[rate_key]
            employee.hourly_rate = Decimal(str(new_rate))
            employee.updated_at = datetime.now()
            save_configuration()

def update_commission_rate(unit_id: str):
    """Update business unit commission rate"""
    calc = st.session_state.calculator
    unit = calc.business_units.get(unit_id)
    
    if unit:
        rate_key = f"comm_rate_{unit_id}"
        if rate_key in st.session_state:
            new_rate = st.session_state[rate_key]
            unit.commission_rate = Decimal(str(new_rate))
            unit.updated_at = datetime.now()
            save_configuration()

def save_configuration():
    """Save configuration to database"""
    try:
        calc = st.session_state.calculator
        db = st.session_state.db_manager
        
        # Save all employees
        for employee in calc.employees.values():
            db.save_employee(employee.to_dict())
        
        # Save all business units
        for unit in calc.business_units.values():
            db.save_business_unit(unit.to_dict())
        
        # Log action
        current_user = st.session_state.auth_manager.get_current_user()
        db.log_action('configuration_saved', {
            'employees_updated': len(calc.employees),
            'units_updated': len(calc.business_units)
        }, current_user['username'] if current_user else 'system')
        
        logger.info("Configuration saved")
        
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        st.error(f"Error saving configuration: {str(e)}")

def export_configuration():
    """Export configuration to JSON"""
    try:
        calc = st.session_state.calculator
        db = st.session_state.db_manager
        
        # Get all configuration
        config_data = {
            'employees': {id: emp.to_dict() for id, emp in calc.employees.items()},
            'business_units': {id: unit.to_dict() for id, unit in calc.business_units.items()},
            'settings': {}
        }
        
        # Get settings from database
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT key, value FROM configuration')
            for row in cursor.fetchall():
                config_data['settings'][row['key']] = row['value']
        
        # Export
        json_str = st.session_state.export_manager.export_to_json(config_data)
        
        st.download_button(
            label="📥 Download Configuration",
            data=json_str,
            file_name=f"commission_config_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json"
        )
        
    except Exception as e:
        st.error(f"Error exporting configuration: {str(e)}")

def import_configuration(uploaded_file):
    """Import configuration from JSON"""
    try:
        import json
        config_data = json.load(uploaded_file)
        
        calc = st.session_state.calculator
        db = st.session_state.db_manager
        
        # Import employees
        if 'employees' in config_data:
            for emp_data in config_data['employees'].values():
                employee = Employee(**emp_data)
                calc.add_employee(employee)
                db.save_employee(emp_data)
        
        # Import business units
        if 'business_units' in config_data:
            for unit_data in config_data['business_units'].values():
                unit = BusinessUnit(**unit_data)
                calc.add_business_unit(unit)
                db.save_business_unit(unit_data)
        
        # Import settings
        if 'settings' in config_data:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                for key, value in config_data['settings'].items():
                    cursor.execute('''
                        INSERT OR REPLACE INTO configuration (key, value, updated_at)
                        VALUES (?, ?, ?)
                    ''', (key, value, datetime.now().isoformat()))
        
        st.success("✅ Configuration imported successfully")
        st.rerun()
        
    except Exception as e:
        st.error(f"Error importing configuration: {str(e)}")