import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from decimal import Decimal
import io
from typing import Dict, List, Any

# Import email service
try:
    from utils.email_service import EmailService, display_email_configuration, display_email_scheduler, send_test_email
except ImportError:
    EmailService = None

def commission_reports_page():
    """Enhanced commission reports with multiple formats and advanced features"""
    st.title("📋 Commission Reports")
    
    # Ensure session state is initialized
    if 'calculator' not in st.session_state:
        from models import CommissionCalculator
        st.session_state.calculator = CommissionCalculator()
    
    if 'export_manager' not in st.session_state:
        try:
            from utils import ExportManager
            st.session_state.export_manager = ExportManager()
        except:
            st.warning("Export manager not available - some export features may be limited")
            st.session_state.export_manager = None
    
    calc = st.session_state.calculator
    export_mgr = st.session_state.export_manager
    
    # Check if calculations exist
    if not calc.commissions:
        st.warning("⚠️ No commission data available. Calculate commissions first.")
        if st.button("Go to System Configuration"):
            st.session_state.selected_page = "⚙️ System Configuration"
            st.rerun()
        return
    
    # Report generation tabs
    tabs = st.tabs([
        "📊 Executive Summary",
        "👥 Employee Reports", 
        "🏢 Business Unit Reports",
        "📈 Commission Breakdown",
        "💰 Payroll Export",
        "📄 Custom Reports",
        "📧 Email Reports"
    ])
    
    with tabs[0]:
        executive_summary_report(calc, export_mgr)
    
    with tabs[1]:
        employee_reports(calc, export_mgr)
    
    with tabs[2]:
        business_unit_reports(calc, export_mgr)
    
    with tabs[3]:
        commission_breakdown_report(calc, export_mgr)
    
    with tabs[4]:
        payroll_export(calc, export_mgr)
    
    with tabs[5]:
        custom_reports(calc, export_mgr)
    
    with tabs[6]:
        email_reports_management(calc, export_mgr)

def executive_summary_report(calc, export_mgr):
    """Generate executive summary report"""
    st.subheader("📊 Executive Summary Report")
    
    # Get analytics data
    analytics = calc.get_analytics_data()
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Revenue", f"${analytics['kpis']['total_revenue']:,.2f}")
    
    with col2:
        st.metric("Total Commissions", f"${analytics['kpis']['total_commissions']:,.2f}")
    
    with col3:
        st.metric("Gross Profit", f"${analytics['kpis']['gross_profit']:,.2f}")
    
    with col4:
        st.metric("Profit Margin", f"{analytics['kpis']['profit_margin']:.1f}%")
    
    # Generate markdown report
    report_text = export_mgr.generate_executive_summary(analytics)
    
    st.markdown("### 📄 Executive Summary")
    st.markdown(report_text)
    
    # Commission distribution chart
    if calc.business_units:
        unit_data = []
        for unit in calc.business_units.values():
            unit_data.append({
                'Business Unit': unit.name,
                'Revenue': float(unit.revenue),
                'Commission': float(unit.commission_amount)
            })
        
        df = pd.DataFrame(unit_data)
        
        fig = px.bar(
            df,
            x='Business Unit',
            y=['Revenue', 'Commission'],
            title='Revenue vs Commission by Business Unit',
            barmode='group',
            color_discrete_map={
                'Revenue': '#2C5F75',
                'Commission': '#922B3E'
            }
        )
        fig.update_xaxis(tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    # Export options
    st.divider()
    st.markdown("### 📤 Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Export PDF Report", use_container_width=True):
            st.info("PDF export coming soon!")
    
    with col2:
        if st.button("📊 Export Excel", use_container_width=True):
            export_executive_excel(analytics, export_mgr)
    
    with col3:
        if st.button("📋 Copy Summary", use_container_width=True):
            st.code(report_text)
            st.success("Summary copied to clipboard area above")

def employee_reports(calc, export_mgr):
    """Generate detailed employee reports"""
    st.subheader("👥 Employee Commission Reports")
    
    # Employee selection
    employees = list(calc.employees.values())
    employee_names = [emp.name for emp in employees]
    
    # Multi-select for employees
    selected_employees = st.multiselect(
        "Select Employees (leave empty for all)",
        employee_names,
        help="Select specific employees or leave empty to include all"
    )
    
    if not selected_employees:
        selected_employees = employee_names
    
    # Report type selection
    report_type = st.selectbox(
        "Report Type",
        ["Detailed Report", "Summary Only", "Hours Breakdown", "Commission Analysis"]
    )
    
    # Generate employee data
    employee_data = []
    for emp in employees:
        if emp.name in selected_employees:
            emp_summary = calc.get_employee_summary(emp.id)
            employee_data.append(emp_summary)
    
    if not employee_data:
        st.warning("No employee data to display")
        return
    
    # Display based on report type
    if report_type == "Detailed Report":
        display_detailed_employee_report(employee_data, export_mgr)
    elif report_type == "Summary Only":
        display_employee_summary(employee_data, export_mgr)
    elif report_type == "Hours Breakdown":
        display_hours_breakdown(employee_data, export_mgr)
    else:
        display_commission_analysis(employee_data, export_mgr)

def display_detailed_employee_report(employee_data, export_mgr):
    """Display detailed employee report"""
    st.markdown("### 📋 Detailed Employee Report")
    
    for emp_data in employee_data:
        emp = emp_data['employee']
        
        with st.expander(f"👤 {emp['name']}", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Employee Info**")
                st.write(f"ID: {emp.get('employee_id', 'N/A')}")
                st.write(f"Department: {emp.get('department', 'N/A')}")
                st.write(f"Hourly Rate: ${emp['hourly_rate']:.2f}")
            
            with col2:
                st.markdown("**Hours Worked**")
                st.write(f"Regular: {emp['regular_hours']:.2f}")
                st.write(f"Overtime: {emp['ot_hours']:.2f}")
                st.write(f"Double Time: {emp['dt_hours']:.2f}")
                st.write(f"**Total: {emp_data['total_hours']:.2f}**")
            
            with col3:
                st.markdown("**Earnings**")
                st.write(f"Labor Cost: ${emp_data['labor_cost']:,.2f}")
                st.write(f"Commission: ${emp_data['total_commission']:,.2f}")
                st.write(f"**Total: ${emp_data['total_earnings']:,.2f}**")
            
            # Commission breakdown by business unit
            if emp_data['commissions_by_unit']:
                st.markdown("**Commission Breakdown**")
                
                comm_df = pd.DataFrame(emp_data['commissions_by_unit'])
                
                fig = px.pie(
                    comm_df,
                    values='amount',
                    names='business_unit',
                    title=f"Commission Distribution - {emp['name']}"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # Export button
    if st.button("📤 Export Detailed Report", type="primary", use_container_width=True):
        export_detailed_employee_report(employee_data, export_mgr)

def display_employee_summary(employee_data, export_mgr):
    """Display employee summary table"""
    st.markdown("### 📊 Employee Summary")
    
    # Create summary dataframe
    summary_data = []
    for emp_data in employee_data:
        emp = emp_data['employee']
        summary_data.append({
            'Employee': emp['name'],
            'Department': emp.get('department', 'N/A'),
            'Total Hours': emp_data['total_hours'],
            'Hourly Rate': emp['hourly_rate'],
            'Labor Cost': emp_data['labor_cost'],
            'Commission': emp_data['total_commission'],
            'Total Earnings': emp_data['total_earnings']
        })
    
    df = pd.DataFrame(summary_data)
    
    # Format for display
    display_df = df.copy()
    display_df['Hourly Rate'] = display_df['Hourly Rate'].apply(lambda x: f'${x:.2f}')
    display_df['Labor Cost'] = display_df['Labor Cost'].apply(lambda x: f'${x:,.2f}')
    display_df['Commission'] = display_df['Commission'].apply(lambda x: f'${x:,.2f}')
    display_df['Total Earnings'] = display_df['Total Earnings'].apply(lambda x: f'${x:,.2f}')
    
    st.dataframe(display_df, use_container_width=True)
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Employees", len(df))
    
    with col2:
        st.metric("Total Hours", f"{df['Total Hours'].sum():,.1f}")
    
    with col3:
        st.metric("Total Labor Cost", f"${df['Labor Cost'].sum():,.2f}")
    
    with col4:
        st.metric("Total Commissions", f"${df['Commission'].sum():,.2f}")
    
    # Export button
    if st.button("📤 Export Summary", type="primary", use_container_width=True):
        export_employee_summary(df, export_mgr)

def display_hours_breakdown(employee_data, export_mgr):
    """Display hours breakdown analysis"""
    st.markdown("### ⏰ Hours Breakdown Analysis")
    
    # Prepare hours data
    hours_data = []
    for emp_data in employee_data:
        emp = emp_data['employee']
        hours_data.append({
            'Employee': emp['name'],
            'Regular Hours': emp['regular_hours'],
            'Overtime Hours': emp['ot_hours'],
            'Double Time Hours': emp['dt_hours'],
            'Total Hours': emp_data['total_hours']
        })
    
    df = pd.DataFrame(hours_data)
    
    # Hours distribution chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Regular Hours',
        x=df['Employee'],
        y=df['Regular Hours'],
        marker_color='#2C5F75'
    ))
    
    fig.add_trace(go.Bar(
        name='Overtime Hours',
        x=df['Employee'],
        y=df['Overtime Hours'],
        marker_color='#FFA500'
    ))
    
    fig.add_trace(go.Bar(
        name='Double Time Hours',
        x=df['Employee'],
        y=df['Double Time Hours'],
        marker_color='#922B3E'
    ))
    
    fig.update_layout(
        title='Hours Breakdown by Employee',
        barmode='stack',
        xaxis_tickangle=-45,
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Hours statistics
    total_regular = df['Regular Hours'].sum()
    total_ot = df['Overtime Hours'].sum()
    total_dt = df['Double Time Hours'].sum()
    total_all = total_regular + total_ot + total_dt
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Regular Hours", f"{total_regular:,.1f}")
    
    with col2:
        st.metric("Overtime Hours", f"{total_ot:,.1f}", f"{(total_ot/total_all*100):.1f}%")
    
    with col3:
        st.metric("Double Time Hours", f"{total_dt:,.1f}", f"{(total_dt/total_all*100):.1f}%")
    
    with col4:
        st.metric("Premium Hours %", f"{((total_ot+total_dt)/total_all*100):.1f}%")
    
    # Detailed table
    st.dataframe(df, use_container_width=True)
    
    # Export button
    if st.button("📤 Export Hours Report", type="primary", use_container_width=True):
        export_hours_breakdown(df, export_mgr)

def business_unit_reports(calc, export_mgr):
    """Generate business unit reports"""
    st.subheader("🏢 Business Unit Reports")
    
    # Business unit selection
    units = list(calc.business_units.values())
    unit_names = [unit.name for unit in units]
    
    selected_units = st.multiselect(
        "Select Business Units (leave empty for all)",
        unit_names,
        help="Select specific business units or leave empty to include all"
    )
    
    if not selected_units:
        selected_units = unit_names
    
    # Generate unit data
    unit_data = []
    for unit in units:
        if unit.name in selected_units:
            unit_summary = calc.get_business_unit_summary(unit.id)
            unit_data.append(unit_summary)
    
    if not unit_data:
        st.warning("No business unit data to display")
        return
    
    # Business unit analysis
    st.markdown("### 📊 Business Unit Performance")
    
    # Create comparison chart
    chart_data = []
    for unit_summary in unit_data:
        unit = unit_summary['business_unit']
        chart_data.append({
            'Business Unit': unit['name'],
            'Revenue': unit_summary['revenue'],
            'Commission': unit_summary['total_commission'],
            'Profit': unit_summary['profit_after_commission'],
            'Employees': unit_summary['employees_paid']
        })
    
    df = pd.DataFrame(chart_data)
    
    # Revenue vs Commission chart
    fig = px.bar(
        df,
        x='Business Unit',
        y=['Revenue', 'Commission'],
        title='Revenue vs Commission by Business Unit',
        barmode='group',
        color_discrete_map={
            'Revenue': '#2C5F75',
            'Commission': '#922B3E'
        }
    )
    fig.update_xaxis(tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    
    # Profit margin analysis
    df['Profit Margin'] = (df['Profit'] / df['Revenue'] * 100).round(1)
    
    fig_margin = px.bar(
        df.sort_values('Profit Margin', ascending=False),
        x='Business Unit',
        y='Profit Margin',
        title='Profit Margin by Business Unit',
        color='Profit Margin',
        color_continuous_scale='RdYlGn'
    )
    fig_margin.update_xaxis(tickangle=-45)
    st.plotly_chart(fig_margin, use_container_width=True)
    
    # Detailed business unit table
    st.markdown("### 📋 Detailed Business Unit Analysis")
    
    detailed_data = []
    for unit_summary in unit_data:
        unit = unit_summary['business_unit']
        detailed_data.append({
            'Business Unit': unit['name'],
            'Category': unit.get('category', 'N/A'),
            'Revenue': unit_summary['revenue'],
            'Commission Rate': unit['commission_rate'],
            'Commission Amount': unit_summary['total_commission'],
            'Employees Paid': unit_summary['employees_paid'],
            'Profit After Commission': unit_summary['profit_after_commission'],
            'Profit Margin': f"{(unit_summary['profit_after_commission'] / unit_summary['revenue'] * 100):.1f}%"
        })
    
    detail_df = pd.DataFrame(detailed_data)
    
    # Format for display
    display_detail_df = detail_df.copy()
    currency_cols = ['Revenue', 'Commission Amount', 'Profit After Commission']
    for col in currency_cols:
        display_detail_df[col] = display_detail_df[col].apply(lambda x: f'${x:,.2f}')
    
    display_detail_df['Commission Rate'] = display_detail_df['Commission Rate'].apply(lambda x: f'{x:.1f}%')
    
    st.dataframe(display_detail_df, use_container_width=True)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Units", len(detail_df))
    
    with col2:
        st.metric("Total Revenue", f"${detail_df['Revenue'].sum():,.2f}")
    
    with col3:
        st.metric("Total Commission", f"${detail_df['Commission Amount'].sum():,.2f}")
    
    with col4:
        avg_margin = (detail_df['Profit After Commission'].sum() / detail_df['Revenue'].sum() * 100)
        st.metric("Average Margin", f"{avg_margin:.1f}%")
    
    # Export button
    if st.button("📤 Export Business Unit Report", type="primary", use_container_width=True):
        export_business_unit_report(detail_df, export_mgr)

def commission_breakdown_report(calc, export_mgr):
    """Generate detailed commission breakdown report"""
    st.subheader("📈 Commission Breakdown Report")
    
    if not calc.commissions:
        st.warning("No commission data available")
        return
    
    # Commission details
    commission_data = []
    for commission in calc.commissions:
        employee = calc.employees.get(commission.employee_id)
        unit = calc.business_units.get(commission.business_unit_id)
        
        commission_data.append({
            'Commission ID': commission.id,
            'Employee': employee.name if employee else 'Unknown',
            'Business Unit': unit.name if unit else 'Unknown',
            'Base Amount': float(commission.amount),
            'Split %': float(commission.percentage),
            'Adjusted Amount': float(commission.adjusted_amount),
            'Status': commission.status,
            'Period Start': commission.period_start.strftime('%Y-%m-%d'),
            'Period End': commission.period_end.strftime('%Y-%m-%d')
        })
    
    df = pd.DataFrame(commission_data)
    
    # Commission summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Commissions", len(df))
    
    with col2:
        st.metric("Total Amount", f"${df['Adjusted Amount'].sum():,.2f}")
    
    with col3:
        st.metric("Average Commission", f"${df['Adjusted Amount'].mean():,.2f}")
    
    with col4:
        pending_count = len(df[df['Status'] == 'pending'])
        st.metric("Pending Commissions", pending_count)
    
    # Commission distribution by employee
    emp_summary = df.groupby('Employee')['Adjusted Amount'].sum().sort_values(ascending=False)
    
    fig_emp = px.bar(
        x=emp_summary.index,
        y=emp_summary.values,
        title='Commission Distribution by Employee',
        labels={'x': 'Employee', 'y': 'Commission Amount ($)'},
        color=emp_summary.values,
        color_continuous_scale='Blues'
    )
    fig_emp.update_xaxis(tickangle=-45)
    st.plotly_chart(fig_emp, use_container_width=True)
    
    # Commission distribution by business unit
    unit_summary = df.groupby('Business Unit')['Adjusted Amount'].sum().sort_values(ascending=False)
    
    fig_unit = px.pie(
        values=unit_summary.values,
        names=unit_summary.index,
        title='Commission Distribution by Business Unit'
    )
    st.plotly_chart(fig_unit, use_container_width=True)
    
    # Detailed commission table
    st.markdown("### 📋 Detailed Commission Records")
    
    # Format for display
    display_df = df.copy()
    display_df['Base Amount'] = display_df['Base Amount'].apply(lambda x: f'${x:,.2f}')
    display_df['Adjusted Amount'] = display_df['Adjusted Amount'].apply(lambda x: f'${x:,.2f}')
    display_df['Split %'] = display_df['Split %'].apply(lambda x: f'{x:.1f}%')
    
    st.dataframe(display_df, use_container_width=True)
    
    # Commission status analysis
    status_counts = df['Status'].value_counts()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Pending", status_counts.get('pending', 0))
    
    with col2:
        st.metric("Approved", status_counts.get('approved', 0))
    
    with col3:
        st.metric("Paid", status_counts.get('paid', 0))
    
    # Export button
    if st.button("📤 Export Commission Breakdown", type="primary", use_container_width=True):
        export_commission_breakdown(df, export_mgr)

def payroll_export(calc, export_mgr):
    """Generate payroll-ready export"""
    st.subheader("💰 Payroll Export")
    
    st.info("📋 Generate payroll-ready files for your payroll system")
    
    # Period selection
    col1, col2 = st.columns(2)
    
    with col1:
        pay_period_start = st.date_input(
            "Pay Period Start",
            value=calc.period_start.date() if calc.period_start else datetime.now().date()
        )
    
    with col2:
        pay_period_end = st.date_input(
            "Pay Period End",
            value=calc.period_end.date() if calc.period_end else datetime.now().date()
        )
    
    # Payroll format selection
    payroll_format = st.selectbox(
        "Payroll System Format",
        ["Standard CSV", "ADP", "QuickBooks", "Paychex", "Custom"]
    )
    
    # Include options
    st.markdown("### 📋 Include in Payroll Export")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        include_labor = st.checkbox("Labor Costs", value=True)
        include_commission = st.checkbox("Commissions", value=True)
    
    with col2:
        include_hours = st.checkbox("Hour Details", value=True)
        include_rates = st.checkbox("Rate Information", value=True)
    
    with col3:
        include_departments = st.checkbox("Department Codes", value=True)
        include_employee_ids = st.checkbox("Employee IDs", value=True)
    
    # Generate payroll data
    if st.button("🔄 Generate Payroll Data", type="primary", use_container_width=True):
        payroll_data = []
        
        for emp in calc.employees.values():
            if emp.total_hours > 0:  # Only include employees with hours
                emp_summary = calc.get_employee_summary(emp.id)
                
                record = {
                    'Employee Name': emp.name,
                    'Pay Period Start': pay_period_start.strftime('%Y-%m-%d'),
                    'Pay Period End': pay_period_end.strftime('%Y-%m-%d')
                }
                
                if include_employee_ids:
                    record['Employee ID'] = emp.employee_id or ''
                
                if include_departments:
                    record['Department'] = emp.department or ''
                
                if include_hours:
                    record['Regular Hours'] = float(emp.regular_hours)
                    record['OT Hours'] = float(emp.ot_hours)
                    record['DT Hours'] = float(emp.dt_hours)
                    record['Total Hours'] = emp_summary['total_hours']
                
                if include_rates:
                    record['Hourly Rate'] = float(emp.hourly_rate)
                
                if include_labor:
                    record['Regular Pay'] = float(emp.regular_hours * emp.hourly_rate)
                    record['OT Pay'] = float(emp.ot_hours * emp.hourly_rate * Decimal('1.5'))
                    record['DT Pay'] = float(emp.dt_hours * emp.hourly_rate * Decimal('2.0'))
                    record['Total Labor Cost'] = emp_summary['labor_cost']
                
                if include_commission:
                    record['Commission'] = emp_summary['total_commission']
                
                record['Total Earnings'] = emp_summary['total_earnings']
                record['Status'] = 'Ready for Payroll'
                
                payroll_data.append(record)
        
        if payroll_data:
            df_payroll = pd.DataFrame(payroll_data)
            
            # Display preview
            st.markdown("### 👀 Payroll Data Preview")
            st.dataframe(df_payroll, use_container_width=True)
            
            # Summary
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Employees", len(df_payroll))
            
            with col2:
                if include_labor:
                    st.metric("Total Labor", f"${df_payroll['Total Labor Cost'].sum():,.2f}")
            
            with col3:
                if include_commission:
                    st.metric("Total Commission", f"${df_payroll['Commission'].sum():,.2f}")
            
            # Export options
            st.markdown("### 📤 Export Payroll Data")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                csv_data = export_mgr.export_to_csv(df_payroll.to_dict('records'))
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_data,
                    file_name=f"payroll_{pay_period_start}_{pay_period_end}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                excel_data = export_mgr.export_to_excel({'Payroll': df_payroll})
                st.download_button(
                    label="📊 Download Excel",
                    data=excel_data,
                    file_name=f"payroll_{pay_period_start}_{pay_period_end}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            with col3:
                if st.button("📋 Copy to Clipboard", use_container_width=True):
                    st.code(csv_data)
                    st.success("Data ready to copy from above")
        
        else:
            st.warning("No payroll data to export")

def custom_reports(calc, export_mgr):
    """Generate custom reports with user-defined parameters"""
    st.subheader("📄 Custom Report Builder")
    
    st.info("🛠️ Build custom reports by selecting data fields and filters")
    
    # Report configuration
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Data Sources")
        
        include_employees = st.checkbox("Employee Data", value=True)
        include_business_units = st.checkbox("Business Unit Data", value=True)
        include_commissions = st.checkbox("Commission Details", value=True)
        include_hours = st.checkbox("Hours Breakdown", value=True)
        include_analytics = st.checkbox("Analytics & KPIs", value=False)
    
    with col2:
        st.markdown("### 🎯 Filters")
        
        # Employee filters
        if include_employees:
            dept_filter = st.multiselect(
                "Filter by Department",
                list(set(emp.department for emp in calc.employees.values() if emp.department))
            )
            
            min_hours = st.number_input("Minimum Hours", min_value=0.0, value=0.0)
        
        # Commission filters
        if include_commissions:
            status_filter = st.multiselect(
                "Commission Status",
                ['pending', 'approved', 'paid'],
                default=['pending', 'approved']
            )
    
    # Report format
    report_format = st.selectbox(
        "Report Format",
        ["Excel Workbook", "CSV Files", "JSON Export", "Summary Report"]
    )
    
    # Generate custom report
    if st.button("🔄 Generate Custom Report", type="primary", use_container_width=True):
        datasets = {}
        
        # Employee data
        if include_employees:
            emp_data = []
            for emp in calc.employees.values():
                # Apply filters
                if dept_filter and emp.department not in dept_filter:
                    continue
                if emp.total_hours < min_hours:
                    continue
                
                emp_summary = calc.get_employee_summary(emp.id)
                emp_record = emp_summary['employee'].copy()
                emp_record.update({
                    'total_hours': emp_summary['total_hours'],
                    'labor_cost': emp_summary['labor_cost'],
                    'total_commission': emp_summary['total_commission'],
                    'total_earnings': emp_summary['total_earnings']
                })
                emp_data.append(emp_record)
            
            if emp_data:
                datasets['Employees'] = pd.DataFrame(emp_data)
        
        # Business unit data
        if include_business_units:
            unit_data = []
            for unit in calc.business_units.values():
                unit_summary = calc.get_business_unit_summary(unit.id)
                unit_data.append({
                    'name': unit.name,
                    'category': unit.category,
                    'revenue': unit_summary['revenue'],
                    'commission_rate': unit_summary['business_unit']['commission_rate'],
                    'total_commission': unit_summary['total_commission'],
                    'employees_paid': unit_summary['employees_paid'],
                    'profit_after_commission': unit_summary['profit_after_commission']
                })
            
            if unit_data:
                datasets['Business_Units'] = pd.DataFrame(unit_data)
        
        # Commission data
        if include_commissions:
            comm_data = []
            for commission in calc.commissions:
                # Apply status filter
                if status_filter and commission.status not in status_filter:
                    continue
                
                employee = calc.employees.get(commission.employee_id)
                unit = calc.business_units.get(commission.business_unit_id)
                
                comm_data.append({
                    'commission_id': commission.id,
                    'employee_name': employee.name if employee else 'Unknown',
                    'business_unit': unit.name if unit else 'Unknown',
                    'base_amount': float(commission.amount),
                    'percentage': float(commission.percentage),
                    'adjusted_amount': float(commission.adjusted_amount),
                    'status': commission.status,
                    'period_start': commission.period_start.strftime('%Y-%m-%d'),
                    'period_end': commission.period_end.strftime('%Y-%m-%d')
                })
            
            if comm_data:
                datasets['Commissions'] = pd.DataFrame(comm_data)
        
        # Analytics data
        if include_analytics:
            analytics = calc.get_analytics_data()
            datasets['Analytics'] = pd.DataFrame([analytics['kpis']])
        
        # Export based on format
        if datasets:
            if report_format == "Excel Workbook":
                excel_data = export_mgr.export_to_excel(datasets)
                st.download_button(
                    label="📊 Download Custom Report",
                    data=excel_data,
                    file_name=f"custom_report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            elif report_format == "JSON Export":
                json_data = export_mgr.export_to_json(datasets)
                st.download_button(
                    label="📄 Download JSON",
                    data=json_data,
                    file_name=f"custom_report_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json"
                )
            
            elif report_format == "Summary Report":
                # Display summary
                st.markdown("### 📊 Custom Report Summary")
                
                for sheet_name, df in datasets.items():
                    st.markdown(f"#### {sheet_name}")
                    st.dataframe(df, use_container_width=True)
                    st.markdown(f"*{len(df)} records*")
            
            st.success(f"✅ Custom report generated with {len(datasets)} data sections")
        
        else:
            st.warning("No data matches the selected filters")

# Helper functions for exports
def export_executive_excel(analytics, export_mgr):
    """Export executive summary to Excel"""
    datasets = {
        'Executive_Summary': pd.DataFrame([analytics['kpis']]),
        'KPIs': pd.DataFrame([{
            'Metric': k.replace('_', ' ').title(),
            'Value': v
        } for k, v in analytics['kpis'].items()])
    }
    
    excel_data = export_mgr.export_to_excel(datasets)
    
    st.download_button(
        label="📊 Download Executive Summary",
        data=excel_data,
        file_name=f"executive_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def export_detailed_employee_report(employee_data, export_mgr):
    """Export detailed employee report"""
    # Flatten employee data
    flat_data = []
    for emp_data in employee_data:
        emp = emp_data['employee']
        record = emp.copy()
        record.update({
            'total_hours': emp_data['total_hours'],
            'labor_cost': emp_data['labor_cost'],
            'total_commission': emp_data['total_commission'],
            'total_earnings': emp_data['total_earnings']
        })
        flat_data.append(record)
    
    df = pd.DataFrame(flat_data)
    
    excel_data = export_mgr.export_to_excel({'Employee_Details': df})
    
    st.download_button(
        label="📊 Download Employee Report",
        data=excel_data,
        file_name=f"employee_report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def export_employee_summary(df, export_mgr):
    """Export employee summary"""
    excel_data = export_mgr.export_to_excel({'Employee_Summary': df})
    
    st.download_button(
        label="📊 Download Summary",
        data=excel_data,
        file_name=f"employee_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def export_hours_breakdown(df, export_mgr):
    """Export hours breakdown"""
    excel_data = export_mgr.export_to_excel({'Hours_Breakdown': df})
    
    st.download_button(
        label="📊 Download Hours Report",
        data=excel_data,
        file_name=f"hours_breakdown_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def export_business_unit_report(df, export_mgr):
    """Export business unit report"""
    excel_data = export_mgr.export_to_excel({'Business_Unit_Report': df})
    
    st.download_button(
        label="📊 Download Business Unit Report",
        data=excel_data,
        file_name=f"business_unit_report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def export_commission_breakdown(df, export_mgr):
    """Export commission breakdown"""
    excel_data = export_mgr.export_to_excel({'Commission_Breakdown': df})
    
    st.download_button(
        label="📊 Download Commission Breakdown",
        data=excel_data,
        file_name=f"commission_breakdown_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def email_reports_management(calc, export_mgr):
    """Email reports management interface"""
    st.subheader("📧 Email Reports")
    
    if not EmailService:
        st.warning("Email service not available. Please install required dependencies.")
        return
    
    email_service = EmailService()
    
    # Create sub-tabs for email functionality
    email_tabs = st.tabs([
        "📤 Send Reports",
        "⚙️ Email Settings", 
        "📅 Scheduled Reports",
        "🧪 Test Email"
    ])
    
    with email_tabs[0]:
        send_commission_reports(calc, email_service)
    
    with email_tabs[1]:
        display_email_configuration()
    
    with email_tabs[2]:
        display_email_scheduler()
    
    with email_tabs[3]:
        send_test_email()

def send_commission_reports(calc, email_service):
    """Interface for sending commission reports via email"""
    st.subheader("📤 Send Commission Reports")
    
    if not email_service.config.is_configured():
        st.warning("Please configure email settings first")
        return
    
    # Report type selection
    report_type = st.selectbox(
        "Report Type",
        ["Individual Commission Report", "Executive Summary", "Business Unit Summary"]
    )
    
    if report_type == "Individual Commission Report":
        # Individual employee reports
        st.markdown("### Send Individual Commission Reports")
        
        # Get employees with commissions
        employees_with_commissions = {}
        for commission in calc.commissions:
            emp = calc.employees.get(commission.employee_id)
            if emp:
                if emp.id not in employees_with_commissions:
                    employees_with_commissions[emp.id] = {
                        'name': emp.name,
                        'email': emp.email if hasattr(emp, 'email') else '',
                        'commissions': []
                    }
                employees_with_commissions[emp.id]['commissions'].append(commission)
        
        if not employees_with_commissions:
            st.info("No employees with commissions found")
            return
        
        # Employee selection
        selected_employees = st.multiselect(
            "Select Employees",
            options=list(employees_with_commissions.keys()),
            format_func=lambda x: employees_with_commissions[x]['name']
        )
        
        # Email addresses input
        email_addresses = {}
        for emp_id in selected_employees:
            emp_data = employees_with_commissions[emp_id]
            default_email = emp_data['email']
            email_addresses[emp_id] = st.text_input(
                f"Email for {emp_data['name']}",
                value=default_email,
                key=f"email_{emp_id}"
            )
        
        # Send options
        col1, col2 = st.columns(2)
        with col1:
            include_pdf = st.checkbox("Include PDF attachment", value=True)
        with col2:
            send_copy_to_manager = st.checkbox("Send copy to manager")
        
        manager_email = ""
        if send_copy_to_manager:
            manager_email = st.text_input("Manager email address")
        
        # Send button
        if st.button("📧 Send Commission Reports", type="primary", use_container_width=True):
            if not selected_employees:
                st.error("Please select at least one employee")
                return
            
            success_count = 0
            error_count = 0
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, emp_id in enumerate(selected_employees):
                emp_data = employees_with_commissions[emp_id]
                email = email_addresses.get(emp_id)
                
                if not email:
                    st.warning(f"No email address for {emp_data['name']}")
                    error_count += 1
                    continue
                
                status_text.text(f"Sending report to {emp_data['name']}...")
                
                # Prepare commission data for this employee
                commission_data = prepare_employee_commission_data(emp_data, calc)
                
                # Send email
                recipients = [email]
                if send_copy_to_manager and manager_email:
                    recipients.append(manager_email)
                
                success, message = email_service.send_commission_report(
                    recipient_email=email,
                    recipient_name=emp_data['name'],
                    commission_data=commission_data
                )
                
                if success:
                    success_count += 1
                    st.success(f"✅ Sent to {emp_data['name']}")
                else:
                    error_count += 1
                    st.error(f"❌ Failed to send to {emp_data['name']}: {message}")
                
                progress_bar.progress((i + 1) / len(selected_employees))
            
            progress_bar.empty()
            status_text.empty()
            
            # Summary
            if success_count > 0:
                st.success(f"Successfully sent {success_count} reports")
            if error_count > 0:
                st.error(f"Failed to send {error_count} reports")
    
    elif report_type == "Executive Summary":
        # Executive summary report
        st.markdown("### Send Executive Summary Report")
        
        recipients = st.text_area(
            "Recipient Email Addresses (one per line)",
            help="Enter email addresses of executives/managers"
        )
        
        recipient_list = [email.strip() for email in recipients.split('\n') if email.strip()]
        
        if recipient_list and st.button("📧 Send Executive Summary", type="primary"):
            # Prepare summary data
            summary_data = prepare_executive_summary_data(calc)
            
            success, message = email_service.send_summary_report(
                recipients=recipient_list,
                summary_data=summary_data
            )
            
            if success:
                st.success(f"Executive summary sent to {len(recipient_list)} recipients")
            else:
                st.error(f"Failed to send executive summary: {message}")
    
    else:  # Business Unit Summary
        st.markdown("### Send Business Unit Summary Reports")
        st.info("Business unit summary reports coming soon")

def prepare_employee_commission_data(emp_data, calc):
    """Prepare commission data for email template"""
    commissions = emp_data['commissions']
    
    total_commission = sum(float(c.amount) for c in commissions)
    
    # Get employee object for hours
    emp = calc.employees.get(commissions[0].employee_id)
    total_hours = float(emp.total_hours) if emp else 0
    
    effective_rate = total_commission / total_hours if total_hours > 0 else 0
    
    # Prepare details
    details = []
    for comm in commissions:
        business_unit = calc.business_units.get(comm.business_unit_id)
        if business_unit:
            details.append({
                'business_unit': business_unit.name,
                'hours': float(emp.regular_hours + emp.ot_hours + emp.dt_hours) if emp else 0,
                'revenue': float(business_unit.revenue),
                'rate': float(business_unit.commission_rate),
                'amount': float(comm.amount)
            })
    
    return {
        'period': f"{commissions[0].period_start.date()} to {commissions[0].period_end.date()}",
        'period_start': commissions[0].period_start.strftime('%Y-%m-%d'),
        'period_end': commissions[0].period_end.strftime('%Y-%m-%d'),
        'total_commission': total_commission,
        'total_hours': total_hours,
        'effective_rate': effective_rate,
        'details': details
    }

def prepare_executive_summary_data(calc):
    """Prepare executive summary data for email"""
    total_revenue = sum(float(unit.revenue) for unit in calc.business_units.values())
    total_commissions = sum(float(c.amount) for c in calc.commissions)
    commission_rate = (total_commissions / total_revenue * 100) if total_revenue > 0 else 0
    employee_count = len([emp for emp in calc.employees.values() if emp.total_hours > 0])
    
    # Get period from first commission
    period = "Current Period"
    if calc.commissions:
        first_comm = calc.commissions[0]
        period = f"{first_comm.period_start.date()} to {first_comm.period_end.date()}"
    
    return {
        'period': period,
        'total_revenue': total_revenue,
        'total_commissions': total_commissions,
        'commission_rate': commission_rate,
        'employee_count': employee_count,
        'additional_content': '<p>For detailed breakdowns, please access the Commission Calculator Pro dashboard.</p>'
    }