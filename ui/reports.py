"""
Reports and Analytics UI Module
Handles report generation, analytics, and data export
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from .utils import (
    safe_session_get,
    safe_session_check,
    format_currency,
    format_percentage,
    get_revenue_column,
    get_safe_revenue_data,
    get_current_pay_period,
    get_selected_pay_period,
    format_pay_period,
    is_pay_period_configured,
    get_employee_hours_with_overrides
)

def display_reports_tab():
    """Main reports interface"""
    st.markdown("## 📊 Reports & Analytics")
    st.markdown("Generate comprehensive reports and analyze your commission data")
    
    # Create tabs for different report types
    report_tabs = st.tabs([
        "💰 Enhanced Commission Reports",
        "👥 Employee Performance", 
        "🏢 Business Unit Analysis",
        "📊 Advanced Analytics",
        "📥 Export Center"
    ])
    
    with report_tabs[0]:
        display_enhanced_commission_reports()
    
    with report_tabs[1]:
        display_employee_performance()
    
    with report_tabs[2]:
        display_business_unit_analysis()
    
    with report_tabs[3]:
        display_advanced_analytics()
    
    with report_tabs[4]:
        display_export_center()

def display_enhanced_commission_reports():
    """Enhanced commission reports with detailed pay breakdowns"""
    st.markdown("### 💰 Enhanced Commission Reports")
    st.markdown("**Detailed pay calculations showing exactly how each employee gets paid**")
    
    # Check if pay periods are configured
    if not is_pay_period_configured():
        st.error("❌ Pay periods are not configured. Please go to Company Setup → Pay Period Setup to configure your pay schedule.")
        return
    
    # Pay period selection
    pay_periods = safe_session_get('pay_periods', [])
    if not pay_periods:
        st.error("❌ No pay periods available. Please check your pay period configuration.")
        return
    
    col1, col2 = st.columns([2, 1])
    with col1:
        # Pay period selector
        current_period = get_current_pay_period()
        period_options = [format_pay_period(p) for p in pay_periods]
        
        selected_period_idx = st.selectbox(
            "Select Pay Period",
            range(len(period_options)),
            format_func=lambda x: period_options[x],
            index=current_period['number'] - 1 if current_period else 0,
            help="Select the pay period to generate reports for"
        )
        
        selected_period = pay_periods[selected_period_idx]
        
    with col2:
        # Employee filter
        employee_data = safe_session_get('employee_data', pd.DataFrame())
        if not employee_data.empty:
            employee_options = ["All Employees"] + employee_data['Name'].tolist()
            selected_employee = st.selectbox("Filter by Employee", employee_options)
        else:
            selected_employee = "All Employees"
    
    # Display pay period details
    st.info(f"📅 **Pay Period:** {selected_period['start_date'].strftime('%B %d')} - {selected_period['end_date'].strftime('%B %d, %Y')} | **Pay Date:** {selected_period['pay_date'].strftime('%B %d, %Y')}")
    
    # Get data
    revenue_data = safe_session_get('saved_revenue_data')
    timesheet_data = safe_session_get('saved_timesheet_data')
    
    if revenue_data is None or revenue_data.empty:
        st.info("📤 No revenue data available. Please upload revenue data to generate commission reports.")
        return
    
    if employee_data.empty:
        st.info("👥 No employee data available. Please add employees in Company Setup.")
        return
    
    # Calculate comprehensive pay data
    if st.button("🧮 Generate Detailed Pay Report", type="primary", use_container_width=True):
        with st.spinner("Calculating detailed pay information..."):
            pay_details = calculate_comprehensive_pay_details(
                revenue_data, timesheet_data, employee_data, 
                selected_period['start_date'], selected_period['end_date'], selected_employee
            )
            
            if pay_details:
                display_comprehensive_pay_report(pay_details, selected_period)
            else:
                st.warning("No pay data found for the selected criteria.")

def display_commission_reports():
    """Commission-specific reports"""
    st.markdown("### 💰 Commission Reports")
    
    # Date range selection
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now().replace(day=1).date())
    with col2:
        end_date = st.date_input("End Date", value=datetime.now().date())
    
    # Get commission data
    revenue_data = safe_session_get('saved_revenue_data')
    employee_data = safe_session_get('employee_data', pd.DataFrame())
    
    if revenue_data is None or revenue_data.empty:
        st.info("📤 No revenue data available. Please upload revenue data to generate commission reports.")
        return
    
    # Commission Summary
    st.markdown("#### 💰 Commission Summary")
    display_commission_summary_metrics(revenue_data, start_date, end_date)
    
    # Commission by Type Chart
    st.markdown("#### 📊 Commission Breakdown by Type")
    display_commission_breakdown_chart(revenue_data)
    
    # Top Performers
    st.markdown("#### 🏆 Top Performers")
    display_top_performers(revenue_data)

def display_commission_summary_metrics(revenue_data: pd.DataFrame, start_date, end_date):
    """Display commission summary metrics"""
    
    # Filter data by date if possible
    filtered_data = filter_data_by_date(revenue_data, start_date, end_date)
    
    # Get business unit settings for rate calculations
    business_unit_settings = safe_session_get('business_unit_commission_settings', {})
    
    # Calculate estimated commissions
    total_revenue = 0
    lead_gen_commission = 0
    sales_commission = 0
    work_done_commission = 0
    
    revenue_column = get_revenue_column(filtered_data)
    if revenue_column:
        revenue_series = get_safe_revenue_data(filtered_data, revenue_column)
        total_revenue = revenue_series.sum()
    
    # Estimate commissions based on business unit settings
    for business_unit, settings in business_unit_settings.items():
        unit_data = filtered_data[filtered_data['Business Unit'] == business_unit] if 'Business Unit' in filtered_data.columns else filtered_data
        
        if not unit_data.empty and revenue_column:
            unit_revenue_series = get_safe_revenue_data(unit_data, revenue_column)
            unit_revenue = unit_revenue_series.sum()
            
            # Lead generation commissions
            if 'Lead Generated By' in unit_data.columns:
                lead_entries = unit_data[unit_data['Lead Generated By'].notna()]
                lead_revenue = get_safe_revenue_data(lead_entries, revenue_column).sum()
                lead_gen_commission += lead_revenue * (settings.get('lead_gen_rate', 0) / 100)
            
            # Sales commissions
            if 'Sold By' in unit_data.columns:
                sales_entries = unit_data[unit_data['Sold By'].notna()]
                sales_revenue = get_safe_revenue_data(sales_entries, revenue_column).sum()
                sales_commission += sales_revenue * (settings.get('sold_by_rate', 0) / 100)
            
            # Work done commissions
            if 'Assigned Technicians' in unit_data.columns:
                work_entries = unit_data[unit_data['Assigned Technicians'].notna()]
                work_revenue = get_safe_revenue_data(work_entries, revenue_column).sum()
                work_done_commission += work_revenue * (settings.get('work_done_rate', 0) / 100)
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Revenue", format_currency(total_revenue))
    
    with col2:
        st.metric("Lead Gen Commission", format_currency(lead_gen_commission))
    
    with col3:
        st.metric("Sales Commission", format_currency(sales_commission))
    
    with col4:
        st.metric("Work Done Commission", format_currency(work_done_commission))
    
    # Commission rate summary
    total_commission = lead_gen_commission + sales_commission + work_done_commission
    commission_rate = (total_commission / total_revenue * 100) if total_revenue > 0 else 0
    
    st.metric("Total Commission", format_currency(total_commission), 
             delta=f"{commission_rate:.1f}% of revenue")

def display_commission_breakdown_chart(revenue_data: pd.DataFrame):
    """Display commission breakdown chart"""
    
    # Get commission data for chart
    business_unit_settings = safe_session_get('business_unit_commission_settings', {})
    
    commission_data = []
    
    for business_unit, settings in business_unit_settings.items():
        unit_data = revenue_data[revenue_data['Business Unit'] == business_unit] if 'Business Unit' in revenue_data.columns else revenue_data
        
        if not unit_data.empty:
            revenue_column = get_revenue_column(unit_data)
            if revenue_column:
                unit_revenue_series = get_safe_revenue_data(unit_data, revenue_column)
                unit_revenue = unit_revenue_series.sum()
            
            # Calculate commissions by type
            lead_commission = unit_revenue * (settings.get('lead_gen_rate', 0) / 100)
            sales_commission = unit_revenue * (settings.get('sold_by_rate', 0) / 100)
            work_commission = unit_revenue * (settings.get('work_done_rate', 0) / 100)
            
            commission_data.extend([
                {'Business Unit': business_unit, 'Type': 'Lead Generation', 'Commission': lead_commission},
                {'Business Unit': business_unit, 'Type': 'Sales', 'Commission': sales_commission},
                {'Business Unit': business_unit, 'Type': 'Work Done', 'Commission': work_commission}
            ])
    
    if commission_data:
        commission_df = pd.DataFrame(commission_data)
        commission_df = commission_df[commission_df['Commission'] > 0]  # Filter out zero commissions
        
        # Create stacked bar chart
        fig = px.bar(
            commission_df,
            x='Business Unit',
            y='Commission',
            color='Type',
            title='Commission Breakdown by Business Unit and Type',
            color_discrete_map={
                'Lead Generation': '#1f77b4',
                'Sales': '#ff7f0e', 
                'Work Done': '#2ca02c'
            }
        )
        
        fig.update_layout(
            xaxis_title="Business Unit",
            yaxis_title="Commission Amount ($)",
            yaxis_tickformat="$,.0f",
            legend_title="Commission Type"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No commission data available for chart")

def display_top_performers(revenue_data: pd.DataFrame):
    """Display top performers"""
    
    performers_data = []
    
    # Top sales performers
    revenue_column = get_revenue_column(revenue_data)
    if 'Sold By' in revenue_data.columns and revenue_column:
        revenue_series = get_safe_revenue_data(revenue_data, revenue_column)
        revenue_data_clean = revenue_data.copy()
        revenue_data_clean[revenue_column] = revenue_series
        sales_data = revenue_data_clean.groupby('Sold By')[revenue_column].agg(['sum', 'count']).reset_index()
        sales_data.columns = ['Employee', 'Total Revenue', 'Jobs Count']
        sales_data['Type'] = 'Sales'
        sales_data = sales_data.nlargest(10, 'Total Revenue')
        performers_data.append(sales_data)
    
    # Top lead generators
    if 'Lead Generated By' in revenue_data.columns and revenue_column:
        lead_data = revenue_data_clean.groupby('Lead Generated By')[revenue_column].agg(['sum', 'count']).reset_index()
        lead_data.columns = ['Employee', 'Total Revenue', 'Jobs Count']
        lead_data['Type'] = 'Lead Generation'
        lead_data = lead_data.nlargest(10, 'Total Revenue')
        performers_data.append(lead_data)
    
    # Display performers
    if performers_data:
        col1, col2 = st.columns(2)
        
        if len(performers_data) >= 2:
            with col1:
                st.markdown("##### 🏆 Top Sales Performers")
                sales_performers = performers_data[0]
                for col in ['Total Revenue']:
                    sales_performers[col] = sales_performers[col].apply(format_currency)
                st.dataframe(sales_performers[['Employee', 'Total Revenue', 'Jobs Count']], 
                           hide_index=True, use_container_width=True)
            
            with col2:
                st.markdown("##### 🎯 Top Lead Generators")
                lead_performers = performers_data[1]
                for col in ['Total Revenue']:
                    lead_performers[col] = lead_performers[col].apply(format_currency)
                st.dataframe(lead_performers[['Employee', 'Total Revenue', 'Jobs Count']], 
                           hide_index=True, use_container_width=True)
        else:
            st.dataframe(performers_data[0], hide_index=True, use_container_width=True)
    else:
        st.info("No performance data available")

def display_employee_performance():
    """Employee performance analysis"""
    st.markdown("### 👥 Employee Performance Analysis")
    
    employee_data = safe_session_get('employee_data', pd.DataFrame())
    revenue_data = safe_session_get('saved_revenue_data')
    timesheet_data = safe_session_get('saved_timesheet_data')
    
    if employee_data.empty:
        st.info("No employee data available. Please add employees in Company Setup.")
        return
    
    # Employee selection
    selected_employees = st.multiselect(
        "Select Employees to Analyze",
        employee_data['Name'].tolist(),
        default=employee_data['Name'].tolist()[:5] if len(employee_data) > 5 else employee_data['Name'].tolist()
    )
    
    if not selected_employees:
        st.warning("Please select at least one employee")
        return
    
    # Performance metrics
    st.markdown("#### 📊 Performance Metrics")
    display_employee_performance_metrics(selected_employees, revenue_data, timesheet_data)
    
    # Performance comparison chart
    st.markdown("#### 📈 Performance Comparison")
    display_employee_comparison_chart(selected_employees, revenue_data)

def display_employee_performance_metrics(selected_employees: list, revenue_data, timesheet_data):
    """Display employee performance metrics"""
    
    performance_data = []
    
    for employee in selected_employees:
        emp_metrics = {'Employee': employee}
        
        # Revenue metrics
        if revenue_data is not None and not revenue_data.empty:
            revenue_column = get_revenue_column(revenue_data)
            # Sales revenue
            if 'Sold By' in revenue_data.columns and revenue_column:
                sales_data = revenue_data[revenue_data['Sold By'] == employee]
                sales_revenue_series = get_safe_revenue_data(sales_data, revenue_column)
                emp_metrics['Sales Revenue'] = sales_revenue_series.sum()
                emp_metrics['Sales Count'] = len(sales_data)
            
            # Lead generation revenue
            if 'Lead Generated By' in revenue_data.columns and revenue_column:
                lead_data = revenue_data[revenue_data['Lead Generated By'] == employee]
                lead_revenue_series = get_safe_revenue_data(lead_data, revenue_column)
                emp_metrics['Lead Revenue'] = lead_revenue_series.sum()
                emp_metrics['Lead Count'] = len(lead_data)
        
        # Hours metrics
        if timesheet_data is not None and not timesheet_data.empty:
            if 'Employee Name' in timesheet_data.columns:
                emp_timesheet = timesheet_data[timesheet_data['Employee Name'] == employee]
                
                # Calculate total hours
                hour_cols = [col for col in emp_timesheet.columns if 'hour' in col.lower()]
                total_hours = 0
                for col in hour_cols:
                    total_hours += pd.to_numeric(emp_timesheet[col], errors='coerce').sum()
                
                emp_metrics['Total Hours'] = total_hours
        
        performance_data.append(emp_metrics)
    
    # Display metrics table
    if performance_data:
        perf_df = pd.DataFrame(performance_data)
        
        # Format currency columns
        currency_cols = ['Sales Revenue', 'Lead Revenue']
        for col in currency_cols:
            if col in perf_df.columns:
                perf_df[col] = perf_df[col].apply(format_currency)
        
        # Format hours
        if 'Total Hours' in perf_df.columns:
            perf_df['Total Hours'] = perf_df['Total Hours'].apply(lambda x: f"{x:.1f}")
        
        st.dataframe(perf_df, hide_index=True, use_container_width=True)

def display_employee_comparison_chart(selected_employees: list, revenue_data):
    """Display employee comparison chart"""
    
    if revenue_data is None or revenue_data.empty:
        st.info("No revenue data available for comparison")
        return
    
    # Prepare data for chart
    chart_data = []
    
    revenue_column = get_revenue_column(revenue_data)
    for employee in selected_employees:
        # Sales data
        if 'Sold By' in revenue_data.columns and revenue_column:
            sales_data = revenue_data[revenue_data['Sold By'] == employee]
            sales_revenue_series = get_safe_revenue_data(sales_data, revenue_column)
            sales_revenue = sales_revenue_series.sum()
            chart_data.append({
                'Employee': employee,
                'Type': 'Sales',
                'Revenue': sales_revenue
            })
        
        # Lead generation data  
        if 'Lead Generated By' in revenue_data.columns and revenue_column:
            lead_data = revenue_data[revenue_data['Lead Generated By'] == employee]
            lead_revenue_series = get_safe_revenue_data(lead_data, revenue_column)
            lead_revenue = lead_revenue_series.sum()
            chart_data.append({
                'Employee': employee,
                'Type': 'Lead Generation', 
                'Revenue': lead_revenue
            })
    
    if chart_data:
        chart_df = pd.DataFrame(chart_data)
        chart_df = chart_df[chart_df['Revenue'] > 0]  # Filter out zero values
        
        # Create grouped bar chart
        fig = px.bar(
            chart_df,
            x='Employee',
            y='Revenue',
            color='Type',
            title='Employee Performance Comparison',
            barmode='group'
        )
        
        fig.update_layout(
            xaxis_title="Employee",
            yaxis_title="Revenue ($)",
            yaxis_tickformat="$,.0f"
        )
        
        st.plotly_chart(fig, use_container_width=True)

def display_business_unit_analysis():
    """Business unit performance analysis"""
    st.markdown("### 🏢 Business Unit Analysis")
    
    revenue_data = safe_session_get('saved_revenue_data')
    business_unit_settings = safe_session_get('business_unit_commission_settings', {})
    
    if revenue_data is None or revenue_data.empty:
        st.info("No revenue data available for business unit analysis")
        return
    
    if 'Business Unit' not in revenue_data.columns:
        st.warning("No Business Unit column found in revenue data")
        return
    
    # Business unit metrics
    st.markdown("#### 📊 Business Unit Performance")
    display_business_unit_metrics(revenue_data, business_unit_settings)
    
    # Revenue distribution chart
    st.markdown("#### 📈 Revenue Distribution")
    display_revenue_distribution_chart(revenue_data)
    
    # Commission rate comparison
    st.markdown("#### 💰 Commission Rate Comparison")
    display_commission_rate_comparison(business_unit_settings)

def display_business_unit_metrics(revenue_data: pd.DataFrame, business_unit_settings: dict):
    """Display business unit performance metrics"""
    
    # Group by business unit
    revenue_column = get_revenue_column(revenue_data)
    if revenue_column:
        revenue_series = get_safe_revenue_data(revenue_data, revenue_column)
        revenue_data_clean = revenue_data.copy()
        revenue_data_clean[revenue_column] = revenue_series
        unit_metrics = revenue_data_clean.groupby('Business Unit').agg({
            revenue_column: ['sum', 'count', 'mean']
        }).round(2)
        unit_metrics.columns = ['Total Revenue', 'Job Count', 'Avg Revenue']
    else:
        unit_metrics = pd.DataFrame()
    unit_metrics = unit_metrics.reset_index()
    
    # Add commission rates and estimated commissions
    for idx, row in unit_metrics.iterrows():
        business_unit = row['Business Unit']
        settings = business_unit_settings.get(business_unit, {})
        
        total_revenue = row['Total Revenue']
        total_rate = settings.get('lead_gen_rate', 0) + settings.get('sold_by_rate', 0) + settings.get('work_done_rate', 0)
        estimated_commission = total_revenue * (total_rate / 100)
        
        unit_metrics.loc[idx, 'Commission Rate'] = f"{total_rate:.1f}%"
        unit_metrics.loc[idx, 'Est. Commission'] = estimated_commission
    
    # Format currency columns
    unit_metrics['Total Revenue'] = unit_metrics['Total Revenue'].apply(format_currency)
    unit_metrics['Avg Revenue'] = unit_metrics['Avg Revenue'].apply(format_currency)
    unit_metrics['Est. Commission'] = unit_metrics['Est. Commission'].apply(format_currency)
    
    st.dataframe(unit_metrics, hide_index=True, use_container_width=True)

def display_revenue_distribution_chart(revenue_data: pd.DataFrame):
    """Display revenue distribution by business unit"""
    
    # Revenue by business unit
    revenue_column = get_revenue_column(revenue_data)
    if revenue_column:
        revenue_series = get_safe_revenue_data(revenue_data, revenue_column)
        revenue_data_clean = revenue_data.copy()
        revenue_data_clean[revenue_column] = revenue_series
        unit_revenue = revenue_data_clean.groupby('Business Unit')[revenue_column].sum().reset_index()
        unit_revenue = unit_revenue.sort_values(revenue_column, ascending=False)
        
        # Create pie chart
        fig = px.pie(
            unit_revenue,
            values=revenue_column,
            names='Business Unit',
            title='Revenue Distribution by Business Unit'
        )
    else:
        return
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(showlegend=True)
    
    st.plotly_chart(fig, use_container_width=True)

def display_commission_rate_comparison(business_unit_settings: dict):
    """Display commission rate comparison"""
    
    if not business_unit_settings:
        st.info("No business unit commission settings configured")
        return
    
    # Prepare data for chart
    rate_data = []
    
    for business_unit, settings in business_unit_settings.items():
        rate_data.extend([
            {'Business Unit': business_unit, 'Type': 'Lead Generation', 'Rate': settings.get('lead_gen_rate', 0)},
            {'Business Unit': business_unit, 'Type': 'Sales', 'Rate': settings.get('sold_by_rate', 0)},
            {'Business Unit': business_unit, 'Type': 'Work Done', 'Rate': settings.get('work_done_rate', 0)}
        ])
    
    rate_df = pd.DataFrame(rate_data)
    rate_df = rate_df[rate_df['Rate'] > 0]  # Filter out zero rates
    
    # Create grouped bar chart
    fig = px.bar(
        rate_df,
        x='Business Unit',
        y='Rate',
        color='Type',
        title='Commission Rates by Business Unit',
        barmode='group'
    )
    
    fig.update_layout(
        xaxis_title="Business Unit",
        yaxis_title="Commission Rate (%)",
        yaxis_tickformat=".1f"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_advanced_analytics():
    """Advanced analytics and insights"""
    st.markdown("### 📊 Advanced Analytics")
    
    # Time series analysis
    st.markdown("#### 📈 Trend Analysis")
    display_trend_analysis()
    
    # Efficiency analysis
    st.markdown("#### ⚡ Efficiency Analysis")
    display_efficiency_analysis()
    
    # Correlation analysis
    st.markdown("#### 🔗 Performance Correlations")
    display_correlation_analysis()

def display_trend_analysis():
    """Display trend analysis"""
    
    revenue_data = safe_session_get('saved_revenue_data')
    
    if revenue_data is None or revenue_data.empty or 'Date' not in revenue_data.columns:
        st.info("No date-based revenue data available for trend analysis")
        return
    
    try:
        # Convert date column
        revenue_data['Date'] = pd.to_datetime(revenue_data['Date'], errors='coerce')
        revenue_data = revenue_data.dropna(subset=['Date'])
        
        if revenue_data.empty:
            st.info("No valid dates found in revenue data")
            return
        
        # Daily revenue trend
        revenue_column = get_revenue_column(revenue_data)
        if revenue_column:
            revenue_series = get_safe_revenue_data(revenue_data, revenue_column)
            revenue_data_clean = revenue_data.copy()
            revenue_data_clean[revenue_column] = revenue_series
            daily_revenue = revenue_data_clean.groupby('Date')[revenue_column].sum().reset_index()
            daily_revenue = daily_revenue.sort_values('Date')
            
            # Create line chart
            fig = px.line(
                daily_revenue,
                x='Date',
                y=revenue_column,
                title='Daily Revenue Trend',
                markers=True
            )
            
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Revenue ($)",
                yaxis_tickformat="$,.0f"
            )
        else:
            daily_revenue = pd.DataFrame()
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show trend statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_daily = daily_revenue['Revenue'].mean()
            st.metric("Average Daily Revenue", format_currency(avg_daily))
        
        with col2:
            max_daily = daily_revenue['Revenue'].max()
            st.metric("Peak Daily Revenue", format_currency(max_daily))
        
        with col3:
            total_days = len(daily_revenue)
            st.metric("Days with Revenue", total_days)
            
    except Exception as e:
        st.error(f"Error creating trend analysis: {str(e)}")

def display_efficiency_analysis():
    """Display efficiency analysis"""
    
    employee_data = safe_session_get('employee_data', pd.DataFrame())
    revenue_data = safe_session_get('saved_revenue_data')
    timesheet_data = safe_session_get('saved_timesheet_data')
    
    if employee_data.empty or revenue_data is None or timesheet_data is None:
        st.info("Complete employee, revenue, and timesheet data required for efficiency analysis")
        return
    
    # Calculate efficiency metrics for each employee
    efficiency_data = []
    
    for _, emp in employee_data.iterrows():
        emp_name = emp['Name']
        hourly_rate = emp.get('Hourly Rate', 0)
        
        # Get hours worked
        emp_timesheet = timesheet_data[timesheet_data['Employee Name'] == emp_name]
        hour_cols = [col for col in emp_timesheet.columns if 'hour' in col.lower()]
        total_hours = sum(pd.to_numeric(emp_timesheet[col], errors='coerce').sum() for col in hour_cols)
        
        # Get revenue generated
        sales_revenue = 0
        revenue_column = get_revenue_column(revenue_data)
        if 'Sold By' in revenue_data.columns and revenue_column:
            sales_data = revenue_data[revenue_data['Sold By'] == emp_name]
            sales_revenue_series = get_safe_revenue_data(sales_data, revenue_column)
            sales_revenue = sales_revenue_series.sum()
        
        # Calculate efficiency metrics
        hourly_pay = total_hours * hourly_rate
        revenue_per_hour = sales_revenue / total_hours if total_hours > 0 else 0
        
        efficiency_data.append({
            'Employee': emp_name,
            'Total Hours': total_hours,
            'Hourly Rate': hourly_rate,
            'Hourly Pay': hourly_pay,
            'Sales Revenue': sales_revenue,
            'Revenue per Hour': revenue_per_hour,
            'Efficiency Ratio': revenue_per_hour / hourly_rate if hourly_rate > 0 else 0
        })
    
    if efficiency_data:
        eff_df = pd.DataFrame(efficiency_data)
        eff_df = eff_df[eff_df['Total Hours'] > 0]  # Filter out employees with no hours
        
        # Sort by efficiency ratio
        eff_df = eff_df.sort_values('Efficiency Ratio', ascending=False)
        
        # Format for display
        display_df = eff_df.copy()
        display_df['Hourly Rate'] = display_df['Hourly Rate'].apply(format_currency)
        display_df['Hourly Pay'] = display_df['Hourly Pay'].apply(format_currency)
        display_df['Sales Revenue'] = display_df['Sales Revenue'].apply(format_currency)
        display_df['Revenue per Hour'] = display_df['Revenue per Hour'].apply(format_currency)
        display_df['Efficiency Ratio'] = display_df['Efficiency Ratio'].apply(lambda x: f"{x:.2f}x")
        display_df['Total Hours'] = display_df['Total Hours'].apply(lambda x: f"{x:.1f}")
        
        st.dataframe(display_df, hide_index=True, use_container_width=True)
        
        # Efficiency chart
        if len(eff_df) > 1:
            fig = px.bar(
                eff_df.head(10),
                x='Employee',
                y='Efficiency Ratio',
                title='Top 10 Employee Efficiency Ratios',
                color='Efficiency Ratio',
                color_continuous_scale='Viridis'
            )
            
            fig.update_layout(
                xaxis_title="Employee",
                yaxis_title="Efficiency Ratio (Revenue/Hourly Rate)",
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)

def display_correlation_analysis():
    """Display correlation analysis"""
    
    st.info("Correlation analysis would examine relationships between hours worked, revenue generated, and commission earned. This requires comprehensive historical data.")

def display_export_center():
    """Export center for all reports"""
    st.markdown("### 📥 Export Center")
    st.markdown("Export your data and reports in various formats")
    
    # Export options
    export_col1, export_col2 = st.columns(2)
    
    with export_col1:
        st.markdown("#### 📊 Data Export")
        
        # Revenue data export
        revenue_data = safe_session_get('saved_revenue_data')
        if revenue_data is not None:
            if st.button("📄 Export Revenue Data (CSV)", use_container_width=True):
                csv = revenue_data.to_csv(index=False)
                st.download_button(
                    label="Download Revenue CSV",
                    data=csv,
                    file_name=f"revenue_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        # Employee data export
        employee_data = safe_session_get('employee_data', pd.DataFrame())
        if not employee_data.empty:
            if st.button("👥 Export Employee Data (CSV)", use_container_width=True):
                csv = employee_data.to_csv(index=False)
                st.download_button(
                    label="Download Employee CSV",
                    data=csv,
                    file_name=f"employee_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    with export_col2:
        st.markdown("#### 📈 Report Export")
        
        if st.button("📊 Generate Complete Analytics Report", use_container_width=True):
            generate_complete_report()
        
        if st.button("💰 Generate Commission Summary Report", use_container_width=True):
            generate_commission_report()

def generate_complete_report():
    """Generate a complete analytics report"""
    
    try:
        # Prepare report data
        report_sections = []
        
        # Executive Summary
        revenue_data = safe_session_get('saved_revenue_data')
        if revenue_data is not None and not revenue_data.empty:
            revenue_column = get_revenue_column(revenue_data)
            if revenue_column:
                revenue_series = get_safe_revenue_data(revenue_data, revenue_column)
                total_revenue = revenue_series.sum()
            else:
                total_revenue = 0
            job_count = len(revenue_data)
            avg_job_value = total_revenue / job_count if job_count > 0 else 0
            
            report_sections.append(f"""
EXECUTIVE SUMMARY
=================
Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Report Period: All available data

Key Metrics:
- Total Revenue: {format_currency(total_revenue)}
- Total Jobs: {job_count:,}
- Average Job Value: {format_currency(avg_job_value)}
            """)
        
        # Business Unit Summary
        business_unit_settings = safe_session_get('business_unit_commission_settings', {})
        if business_unit_settings:
            report_sections.append(f"""
BUSINESS UNIT CONFIGURATION
============================
Configured Business Units: {len(business_unit_settings)}

Business Unit Commission Rates:
            """)
            
            for unit, settings in business_unit_settings.items():
                report_sections.append(f"""
- {unit}:
  Lead Generation: {settings.get('lead_gen_rate', 0):.1f}%
  Sales: {settings.get('sold_by_rate', 0):.1f}%
  Work Done: {settings.get('work_done_rate', 0):.1f}%
                """)
        
        # Employee Summary
        employee_data = safe_session_get('employee_data', pd.DataFrame())
        if not employee_data.empty:
            total_employees = len(employee_data)
            active_employees = len(employee_data[employee_data['Status'] == 'Active'])
            commission_eligible = len(employee_data[employee_data['Commission Eligible'] == True])
            
            report_sections.append(f"""
EMPLOYEE SUMMARY
================
Total Employees: {total_employees}
Active Employees: {active_employees}
Commission Eligible: {commission_eligible}
            """)
        
        # Combine report
        full_report = "\n".join(report_sections)
        
        # Offer download
        st.download_button(
            label="📥 Download Complete Report",
            data=full_report,
            file_name=f"complete_analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
        
        st.success("✅ Complete report generated successfully!")
        
    except Exception as e:
        st.error(f"❌ Error generating report: {str(e)}")

def generate_commission_report():
    """Generate a commission-focused report"""
    
    try:
        # This would generate a detailed commission report
        # For now, create a simple summary
        
        business_unit_settings = safe_session_get('business_unit_commission_settings', {})
        revenue_data = safe_session_get('saved_revenue_data')
        
        report = f"""
COMMISSION SUMMARY REPORT
=========================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

COMMISSION CONFIGURATION:
        """
        
        if business_unit_settings:
            for unit, settings in business_unit_settings.items():
                total_rate = settings.get('lead_gen_rate', 0) + settings.get('sold_by_rate', 0) + settings.get('work_done_rate', 0)
                report += f"""
{unit}:
  Total Commission Rate: {total_rate:.1f}%
  - Lead Generation: {settings.get('lead_gen_rate', 0):.1f}%
  - Sales: {settings.get('sold_by_rate', 0):.1f}%
  - Work Done: {settings.get('work_done_rate', 0):.1f}%
                """
        
        if revenue_data is not None and not revenue_data.empty:
            revenue_column = get_revenue_column(revenue_data)
            if revenue_column:
                revenue_series = get_safe_revenue_data(revenue_data, revenue_column)
                total_revenue = revenue_series.sum()
            else:
                total_revenue = 0
            report += f"""

REVENUE SUMMARY:
Total Revenue in System: {format_currency(total_revenue)}
Total Jobs: {len(revenue_data):,}
            """
        
        # Offer download
        st.download_button(
            label="📥 Download Commission Report",
            data=report,
            file_name=f"commission_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
        
        st.success("✅ Commission report generated successfully!")
        
    except Exception as e:
        st.error(f"❌ Error generating commission report: {str(e)}")

def calculate_comprehensive_pay_details(revenue_data, timesheet_data, employee_data, start_date, end_date, selected_employee):
    """Calculate comprehensive pay details for employees"""
    
    # Filter revenue data by date
    filtered_revenue = filter_data_by_date(revenue_data, start_date, end_date)
    
    # Get business unit settings
    business_unit_settings = safe_session_get('business_unit_commission_settings', {})
    
    # Filter employees - only process commission-eligible employees who are not excluded from payroll
    if selected_employee != "All Employees":
        employees_to_process = [selected_employee]
    else:
        # Filter to only commission-eligible employees not excluded from payroll
        eligible_employees = employee_data[
            (employee_data['Commission Eligible'] == True) & 
            (employee_data['Status'] != 'Excluded from Payroll')
        ]
        employees_to_process = eligible_employees['Name'].tolist()
    
    pay_details = []
    
    for employee_name in employees_to_process:
        # Get employee info
        emp_info = employee_data[employee_data['Name'] == employee_name]
        if emp_info.empty:
            continue
            
        emp_row = emp_info.iloc[0]
        
        # Skip employees who are excluded from payroll or not commission eligible
        if (emp_row.get('Status') == 'Excluded from Payroll' or 
            not emp_row.get('Commission Eligible', False)):
            continue
            
        hourly_rate = float(emp_row.get('Hourly Rate', 0))
        commission_plan = emp_row.get('Commission Plan', 'Hourly + Commission')
        employee_status = emp_row.get('Status', 'Active')
        
        # Calculate hours worked
        regular_hours, ot_hours, dt_hours = get_employee_hours_with_overrides(employee_name, timesheet_data)
        total_hours = regular_hours + ot_hours + dt_hours
        
        # Calculate hourly pay
        regular_pay = regular_hours * hourly_rate
        ot_pay = ot_hours * hourly_rate * 1.5
        dt_pay = dt_hours * hourly_rate * 2.0
        total_hourly_pay = regular_pay + ot_pay + dt_pay
        
        # Calculate commissions by type
        commissions = calculate_employee_commissions(employee_name, filtered_revenue, business_unit_settings)
        
        total_commission = sum(commissions.values())
        
        # Calculate final pay based on commission plan
        if commission_plan == 'Efficiency Pay':
            final_pay = max(total_hourly_pay, total_commission)
            efficiency_bonus = final_pay - total_hourly_pay
            pay_method = "Efficiency Pay (Higher of Hourly vs Commission)"
        else:
            final_pay = total_hourly_pay + total_commission
            efficiency_bonus = 0
            pay_method = "Hourly + Commission"
        
        # Compile comprehensive pay details
        pay_detail = {
            'employee_name': employee_name,
            'employee_status': employee_status,
            'hourly_rate': hourly_rate,
            'commission_plan': commission_plan,
            'pay_method': pay_method,
            
            # Hours breakdown
            'regular_hours': regular_hours,
            'ot_hours': ot_hours,
            'dt_hours': dt_hours,
            'total_hours': total_hours,
            
            # Hourly pay breakdown
            'regular_pay': regular_pay,
            'ot_pay': ot_pay,
            'dt_pay': dt_pay,
            'total_hourly_pay': total_hourly_pay,
            
            # Commission breakdown
            'lead_gen_commission': commissions.get('lead_gen', 0),
            'sales_commission': commissions.get('sales', 0),
            'work_done_commission': commissions.get('work_done', 0),
            'total_commission': total_commission,
            
            # Final calculations
            'efficiency_bonus': efficiency_bonus,
            'final_pay': final_pay,
            
            # Additional metrics
            'hourly_equivalent': final_pay / total_hours if total_hours > 0 else 0,
            'commission_percentage': (total_commission / final_pay * 100) if final_pay > 0 else 0
        }
        
        pay_details.append(pay_detail)
    
    return pay_details

def calculate_employee_commissions(employee_name, revenue_data, business_unit_settings):
    """Calculate commissions for a specific employee"""
    
    commissions = {'lead_gen': 0, 'sales': 0, 'work_done': 0}
    revenue_column = get_revenue_column(revenue_data)
    
    if not revenue_column:
        return commissions
    
    # Process each business unit
    for business_unit, settings in business_unit_settings.items():
        # Filter data for this business unit
        unit_data = revenue_data[revenue_data['Business Unit'] == business_unit] if 'Business Unit' in revenue_data.columns else revenue_data
        
        if unit_data.empty:
            continue
        
        # Lead Generation commissions
        if 'Lead Generated By' in unit_data.columns:
            lead_jobs = unit_data[unit_data['Lead Generated By'] == employee_name]
            for _, job in lead_jobs.iterrows():
                revenue = pd.to_numeric(job.get(revenue_column, 0), errors='coerce')
                rate = settings.get('lead_gen_rate', 0) / 100
                commissions['lead_gen'] += revenue * rate
        
        # Sales commissions
        if 'Sold By' in unit_data.columns:
            sales_jobs = unit_data[unit_data['Sold By'] == employee_name]
            for _, job in sales_jobs.iterrows():
                revenue = pd.to_numeric(job.get(revenue_column, 0), errors='coerce')
                rate = settings.get('sold_by_rate', 0) / 100
                commissions['sales'] += revenue * rate
        
        # Work Done commissions
        if 'Assigned Technicians' in unit_data.columns:
            for _, job in unit_data.iterrows():
                techs_str = job.get('Assigned Technicians')
                if pd.notna(techs_str):
                    technicians = [t.strip() for t in str(techs_str).replace('&', ',').split(',') if t.strip()]
                    if employee_name in technicians:
                        revenue = pd.to_numeric(job.get(revenue_column, 0), errors='coerce')
                        rate = settings.get('work_done_rate', 0) / 100
                        commissions['work_done'] += revenue * rate
    
    return commissions


def display_comprehensive_pay_report(pay_details, selected_period):
    """Display comprehensive pay report"""
    
    st.markdown("---")
    
    # Create header with pay period information
    if selected_period:
        period_text = format_pay_period(selected_period)
        pay_date = selected_period['pay_date'].strftime('%B %d, %Y')
        st.markdown(f"### 📊 Detailed Pay Report - {period_text}")
        st.info(f"💰 **Pay Date:** {pay_date}")
    else:
        st.markdown("### 📊 Detailed Pay Report")
    
    # Summary metrics
    display_pay_summary_metrics(pay_details)
    
    st.markdown("---")
    
    # Detailed employee breakdown
    st.markdown("### 👥 Individual Employee Breakdowns")
    
    for i, emp_detail in enumerate(pay_details):
        display_employee_pay_breakdown(emp_detail, i)

def display_pay_summary_metrics(pay_details):
    """Display summary metrics for all employees"""
    
    total_employees = len(pay_details)
    total_hours = sum(emp['total_hours'] for emp in pay_details)
    total_hourly_pay = sum(emp['total_hourly_pay'] for emp in pay_details)
    total_commission = sum(emp['total_commission'] for emp in pay_details)
    total_final_pay = sum(emp['final_pay'] for emp in pay_details)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 Employees", total_employees)
        avg_hours = total_hours / total_employees if total_employees > 0 else 0
        st.metric("⏰ Avg Hours", f"{avg_hours:.1f}")
    
    with col2:
        st.metric("💰 Total Hourly Pay", format_currency(total_hourly_pay))
        st.metric("💸 Total Commission", format_currency(total_commission))
    
    with col3:
        st.metric("🎯 Total Final Pay", format_currency(total_final_pay))
        efficiency_employees = len([emp for emp in pay_details if emp['commission_plan'] == 'Efficiency Pay'])
        st.metric("⚡ Efficiency Pay Employees", efficiency_employees)
    
    with col4:
        avg_hourly_equiv = sum(emp['hourly_equivalent'] for emp in pay_details) / total_employees if total_employees > 0 else 0
        st.metric("📈 Avg Hourly Equivalent", format_currency(avg_hourly_equiv))
        total_efficiency_bonus = sum(emp['efficiency_bonus'] for emp in pay_details)
        st.metric("🚀 Total Efficiency Bonus", format_currency(total_efficiency_bonus))

def display_employee_pay_breakdown(emp_detail, index):
    """Display detailed pay breakdown for individual employee"""
    
    # Create expandable section for each employee
    with st.expander(f"💰 {emp_detail['employee_name']} - Final Pay: {format_currency(emp_detail['final_pay'])}", expanded=index < 3):
        
        # Employee info header
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"**Status:** {emp_detail['employee_status']}")
        with col2:
            st.markdown(f"**Hourly Rate:** {format_currency(emp_detail['hourly_rate'])}")
        with col3:
            st.markdown(f"**Commission Plan:** {emp_detail['commission_plan']}")
        with col4:
            st.markdown(f"**Pay Method:** {emp_detail['pay_method']}")
        
        st.markdown("---")
        
        # Two-column layout for detailed breakdown
        left_col, right_col = st.columns(2)
        
        with left_col:
            # Hours and Hourly Pay Breakdown
            st.markdown("#### ⏰ Hours & Hourly Pay")
            
            hours_data = {
                'Type': ['Regular Hours', 'Overtime (1.5x)', 'Double Time (2x)', 'Total Hours'],
                'Hours': [
                    f"{emp_detail['regular_hours']:.2f}",
                    f"{emp_detail['ot_hours']:.2f}",
                    f"{emp_detail['dt_hours']:.2f}",
                    f"{emp_detail['total_hours']:.2f}"
                ],
                'Rate': [
                    format_currency(emp_detail['hourly_rate']),
                    format_currency(emp_detail['hourly_rate'] * 1.5),
                    format_currency(emp_detail['hourly_rate'] * 2.0),
                    "-"
                ],
                'Pay': [
                    format_currency(emp_detail['regular_pay']),
                    format_currency(emp_detail['ot_pay']),
                    format_currency(emp_detail['dt_pay']),
                    format_currency(emp_detail['total_hourly_pay'])
                ]
            }
            
            hours_df = pd.DataFrame(hours_data)
            st.dataframe(hours_df, hide_index=True, use_container_width=True)
        
        with right_col:
            # Commission Breakdown
            st.markdown("#### 💸 Commission Breakdown")
            
            commission_data = {
                'Type': ['Lead Generation', 'Sales', 'Work Done', 'Total Commission'],
                'Amount': [
                    format_currency(emp_detail['lead_gen_commission']),
                    format_currency(emp_detail['sales_commission']),
                    format_currency(emp_detail['work_done_commission']),
                    format_currency(emp_detail['total_commission'])
                ]
            }
            
            commission_df = pd.DataFrame(commission_data)
            st.dataframe(commission_df, hide_index=True, use_container_width=True)
        
        # Final pay calculation
        st.markdown("---")
        st.markdown("#### 🎯 Final Pay Calculation")
        
        calc_col1, calc_col2, calc_col3 = st.columns(3)
        
        with calc_col1:
            st.metric("Hourly Pay Total", format_currency(emp_detail['total_hourly_pay']))
        
        with calc_col2:
            st.metric("Commission Total", format_currency(emp_detail['total_commission']))
        
        with calc_col3:
            if emp_detail['commission_plan'] == 'Efficiency Pay':
                if emp_detail['efficiency_bonus'] > 0:
                    st.metric("Efficiency Bonus", format_currency(emp_detail['efficiency_bonus']), 
                             delta="Commission > Hourly")
                else:
                    st.metric("Efficiency Result", format_currency(0), 
                             delta="Hourly >= Commission")
            else:
                st.metric("Combined Total", format_currency(emp_detail['final_pay']))
        
        # Additional insights
        st.markdown("**📊 Performance Insights:**")
        insights_col1, insights_col2 = st.columns(2)
        
        with insights_col1:
            st.markdown(f"• **Effective Hourly Rate:** {format_currency(emp_detail['hourly_equivalent'])}")
            st.markdown(f"• **Commission Percentage:** {emp_detail['commission_percentage']:.1f}% of total pay")
        
        with insights_col2:
            if emp_detail['commission_plan'] == 'Efficiency Pay':
                if emp_detail['total_commission'] > emp_detail['total_hourly_pay']:
                    st.success("🚀 Commission exceeded hourly pay - efficiency bonus earned!")
                else:
                    st.info("⏰ Hourly pay was higher - guaranteed minimum earned")
            else:
                st.info("💰 Receiving both hourly pay and commission")

def filter_data_by_date(data: pd.DataFrame, start_date, end_date) -> pd.DataFrame:
    """Filter DataFrame by date range if date column exists"""
    
    if 'Date' not in data.columns:
        return data
    
    try:
        data_copy = data.copy()
        data_copy['Date'] = pd.to_datetime(data_copy['Date'], errors='coerce')
        
        # Filter by date range
        mask = (data_copy['Date'] >= pd.to_datetime(start_date)) & (data_copy['Date'] <= pd.to_datetime(end_date))
        return data_copy[mask]
    
    except Exception:
        # If date filtering fails, return original data
        return data