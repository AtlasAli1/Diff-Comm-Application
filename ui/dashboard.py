"""
Dashboard UI Module
Contains the main dashboard view with KPIs, system status, and analytics overview
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from decimal import Decimal
from .utils import (
    safe_session_get, 
    safe_session_check,
    format_currency,
    format_percentage,
    safe_dataframe_operation,
    get_revenue_column,
    get_safe_revenue_data,
    get_current_pay_period,
    format_pay_period,
    is_pay_period_configured,
    cache_expensive_operation,
    get_or_compute_employee_summary,
    optimize_dataframe_memory
)
from .config import get_config

def display_dashboard_tab():
    """Clean and organized dashboard with optimized space utilization"""
    st.markdown("## 🏠 Dashboard")
    
    # Welcome message
    display_welcome_message()
    
    # Show KPIs
    display_kpis()
    
    st.divider()
    
    # Enhanced two-column layout: System status and Business metrics
    col1, col2 = st.columns([1, 1])
    
    with col1:
        display_system_status()
    
    with col2:
        display_business_metrics()
    
    st.divider()
    
    # Enhanced analytics section with better space utilization
    display_enhanced_analytics()

def display_welcome_message():
    """Display a clean welcome message with pay period info"""
    user_info = safe_session_get('user', {'username': 'User'})
    current_time = datetime.now().strftime("%B %d, %Y")
    
    # Check if pay periods are configured
    if is_pay_period_configured():
        current_period = get_current_pay_period()
        if current_period:
            period_info = f"<p style='margin: 0.5rem 0 0 0; opacity: 0.9;'>📅 {format_pay_period(current_period)} | Pay Date: {current_period['pay_date'].strftime('%b %d')}</p>"
        else:
            period_info = "<p style='margin: 0.5rem 0 0 0; opacity: 0.9;'>📅 No active pay period</p>"
    else:
        period_info = "<p style='margin: 0.5rem 0 0 0; opacity: 0.9;'>⚠️ Pay periods not configured</p>"
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 1.5rem; border-radius: 10px; color: white; margin-bottom: 1.5rem;">
        <h3 style="margin: 0; color: white;">Welcome back, {user_info['username']}! 👋</h3>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">{current_time}</p>
        {period_info}
    </div>
    """, unsafe_allow_html=True)
    
    # If pay periods not configured, show warning with helpful guidance
    if not is_pay_period_configured():
        st.warning("⚠️ **Important:** Pay periods are not configured to enable commission calculations.")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.info("📋 **Next Steps:**\n1. Click the **⚙️ Company Setup** tab above\n2. Go to **Pay Period Setup**\n3. Configure your pay schedule")
        with col2:
            # Show a prominent call-to-action
            st.markdown("""
            <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); 
                        padding: 1rem; border-radius: 8px; text-align: center; color: white; margin-top: 0.5rem;">
                <strong>👆 Click "Company Setup" tab to get started!</strong>
            </div>
            """, unsafe_allow_html=True)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def compute_revenue_metrics(revenue_data_json: str) -> dict:
    """Compute revenue metrics with caching"""
    if not revenue_data_json:
        return {'total_revenue': 0, 'job_count': 0}
    
    revenue_df = pd.read_json(revenue_data_json)
    revenue_column = get_revenue_column(revenue_df)
    
    if revenue_column:
        revenue_series = get_safe_revenue_data(revenue_df, revenue_column)
        return {
            'total_revenue': revenue_series.sum(),
            'job_count': len(revenue_df)
        }
    else:
        return {'total_revenue': 0, 'job_count': 0}

@st.cache_data(ttl=300)  # Cache for 5 minutes  
def compute_timesheet_metrics(timesheet_data_json: str) -> dict:
    """Compute timesheet metrics with caching"""
    if not timesheet_data_json:
        return {'total_hours': 0, 'employee_count': 0}
    
    timesheet_df = pd.read_json(timesheet_data_json)
    hour_cols = [col for col in timesheet_df.columns if 'hour' in col.lower()]
    
    if hour_cols:
        total_hours = 0
        for col in hour_cols:
            hour_series = pd.to_numeric(timesheet_df[col], errors='coerce')
            total_hours += hour_series.sum()
        
        employee_count = timesheet_df['Employee Name'].nunique() if 'Employee Name' in timesheet_df.columns else 0
        return {
            'total_hours': total_hours,
            'employee_count': employee_count
        }
    else:
        return {'total_hours': 0, 'employee_count': 0}

def display_kpis():
    """Display key performance indicators with caching optimization"""
    config = get_config()
    
    # Get data from session state
    revenue_df = safe_session_get('saved_revenue_data', pd.DataFrame())
    timesheet_df = safe_session_get('saved_timesheet_data', pd.DataFrame())
    employee_df = safe_session_get('employee_data', pd.DataFrame())
    
    # Optimize DataFrames for memory if enabled
    if config.get_performance_setting('enable_memory_optimization', True):
        if not revenue_df.empty:
            revenue_df = optimize_dataframe_memory(revenue_df)
        if not timesheet_df.empty:
            timesheet_df = optimize_dataframe_memory(timesheet_df)
        if not employee_df.empty:
            employee_df = optimize_dataframe_memory(employee_df)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Total Revenue - cached calculation
        revenue_data_json = revenue_df.to_json() if not revenue_df.empty else ""
        revenue_metrics = compute_revenue_metrics(revenue_data_json)
        
        if revenue_metrics['total_revenue'] > 0:
            st.metric("💰 Total Revenue", format_currency(revenue_metrics['total_revenue']), 
                     delta=f"{revenue_metrics['job_count']} jobs")
        else:
            st.metric("💰 Total Revenue", format_currency(0), delta="No data")
    
    with col2:
        # Total Commission (estimate) - cached calculation
        if revenue_metrics['total_revenue'] > 0:
            def compute_commission_estimate(total_revenue, business_settings_json):
                if not business_settings_json:
                    return total_revenue * 0.075  # Default 7.5%
                
                business_settings = eval(business_settings_json) if business_settings_json else {}
                total_rate = 0
                unit_count = 0
                for settings in business_settings.values():
                    unit_rate = settings.get('lead_gen_rate', 0) + settings.get('sold_by_rate', 0) + settings.get('work_done_rate', 0)
                    total_rate += unit_rate
                    unit_count += 1
                
                avg_rate = (total_rate / unit_count / 100) if unit_count > 0 else 0.075
                return total_revenue * avg_rate, avg_rate
            
            business_settings = safe_session_get('business_unit_commission_settings', {})
            estimated_commission, avg_rate = compute_commission_estimate(
                revenue_metrics['total_revenue'], str(business_settings)
            )
            st.metric("💸 Est. Commissions", format_currency(estimated_commission),
                     delta=f"{avg_rate*100:.1f}% avg rate")
        else:
            st.metric("💸 Est. Commissions", format_currency(0), delta="No data")
    
    with col3:
        # Active Employees - use cached summary
        if not employee_df.empty:
            employee_summary = get_or_compute_employee_summary(employee_df)
            active_count = employee_summary.get('active_employees', 0)
            total_count = employee_summary.get('total_employees', 0)
            st.metric("👥 Active Employees", active_count, 
                     delta=f"{total_count} total")
        else:
            st.metric("👥 Active Employees", 0, delta="No employees")
    
    with col4:
        # Total Hours - cached calculation
        timesheet_data_json = timesheet_df.to_json() if not timesheet_df.empty else ""
        timesheet_metrics = compute_timesheet_metrics(timesheet_data_json)
        
        if timesheet_metrics['total_hours'] > 0:
            st.metric("⏰ Total Hours", f"{timesheet_metrics['total_hours']:,.0f}", 
                     delta=f"{timesheet_metrics['employee_count']} employees")
        else:
            st.metric("⏰ Total Hours", 0, delta="No timesheet")

def display_system_status():
    """Display clean system status"""
    st.markdown("### 📊 System Status")
    
    # Check data availability
    revenue_available = safe_session_check('saved_revenue_data') and safe_session_get('saved_revenue_data') is not None
    timesheet_available = safe_session_check('saved_timesheet_data') and safe_session_get('saved_timesheet_data') is not None
    employee_available = safe_session_check('employee_data') and not safe_session_get('employee_data', pd.DataFrame()).empty
    
    # Data status with cleaner display
    status_items = [
        ("💰 Revenue Data", revenue_available, len(safe_session_get('saved_revenue_data', [])) if revenue_available else 0),
        ("⏰ Timesheet Data", timesheet_available, len(safe_session_get('saved_timesheet_data', [])) if timesheet_available else 0),
        ("👥 Employee Data", employee_available, len(safe_session_get('employee_data', [])) if employee_available else 0)
    ]
    
    for item_name, available, count in status_items:
        if available:
            st.success(f"{item_name}: ✅ {count:,} records")
        else:
            st.info(f"{item_name}: ⏳ Not loaded")

def display_business_metrics():
    """Display enhanced business metrics and insights"""
    st.markdown("### 📈 Business Insights")
    
    # Get data for calculations
    revenue_df = safe_session_get('saved_revenue_data', pd.DataFrame())
    employee_df = safe_session_get('employee_data', pd.DataFrame())
    business_settings = safe_session_get('business_unit_commission_settings', {})
    
    # Pay period metrics
    if is_pay_period_configured():
        current_period = get_current_pay_period()
        if current_period:
            st.markdown("**📅 Current Pay Period:**")
            
            # Days until pay date
            from datetime import datetime
            today = datetime.now().date()
            days_to_pay = (current_period['pay_date'] - today).days
            
            if days_to_pay >= 0:
                st.info(f"💰 **{days_to_pay} days** until next pay date ({current_period['pay_date'].strftime('%b %d')})")
            else:
                st.success(f"✅ Pay date was {abs(days_to_pay)} days ago")
        else:
            st.warning("⚠️ No active pay period found")
    
    # Business unit performance
    if not revenue_df.empty and 'Business Unit' in revenue_df.columns:
        st.markdown("**🏢 Business Unit Overview:**")
        
        revenue_column = get_revenue_column(revenue_df)
        if revenue_column:
            # Top performing business unit
            unit_performance = revenue_df.groupby('Business Unit')[revenue_column].agg(['sum', 'count']).reset_index()
            unit_performance.columns = ['Business Unit', 'Total Revenue', 'Job Count']
            unit_performance = unit_performance.sort_values('Total Revenue', ascending=False)
            
            if not unit_performance.empty:
                top_unit = unit_performance.iloc[0]
                st.metric(
                    "🥇 Top Business Unit",
                    top_unit['Business Unit'],
                    delta=f"{format_currency(top_unit['Total Revenue'])} revenue"
                )
    
    # Commission configuration status
    if business_settings:
        st.markdown("**⚙️ Commission Setup:**")
        configured_units = len(business_settings)
        active_units = len([k for k, v in business_settings.items() if v.get('enabled', True)])
        
        st.metric("📋 Business Units", f"{active_units}/{configured_units}", 
                 delta="configured" if configured_units > 0 else "needs setup")
    
    # Employee insights  
    if not employee_df.empty:
        st.markdown("**👥 Workforce Summary:**")
        
        employee_summary = get_or_compute_employee_summary(employee_df)
        efficiency_count = employee_summary.get('efficiency_pay_count', 0)
        total_active = employee_summary.get('active_employees', 0)
        
        if total_active > 0:
            efficiency_percentage = (efficiency_count / total_active) * 100
            st.metric("⚡ Efficiency Pay", f"{efficiency_count} employees", 
                     delta=f"{efficiency_percentage:.0f}% of active")
        
        avg_rate = employee_summary.get('avg_hourly_rate', 0)
        if avg_rate > 0:
            st.metric("💵 Avg Hourly Rate", format_currency(avg_rate))

def display_enhanced_analytics():
    """Enhanced analytics section with better space utilization"""
    st.markdown("### 📊 Analytics & Performance")
    
    revenue_df = safe_session_get('saved_revenue_data', pd.DataFrame())
    employee_df = safe_session_get('employee_data', pd.DataFrame())
    
    if revenue_df.empty:
        st.info("📊 Upload revenue data to see detailed analytics")
        return
    
    # Three-column layout for better space utilization
    col1, col2, col3 = st.columns(3)
    
    with col1:
        display_revenue_by_unit_chart(revenue_df)
    
    with col2:
        display_top_performers_chart(revenue_df)
    
    with col3:
        display_commission_distribution_chart(revenue_df, employee_df)
    
    st.divider()
    
    # Full-width trend analysis
    display_revenue_trend_analysis(revenue_df)

def display_revenue_by_unit_chart(revenue_df):
    """Display revenue by business unit chart"""
    revenue_column = get_revenue_column(revenue_df)
    
    if 'Business Unit' in revenue_df.columns and revenue_column:
        # Clean revenue data
        revenue_series = get_safe_revenue_data(revenue_df, revenue_column)
        revenue_df_clean = revenue_df.copy()
        revenue_df_clean[revenue_column] = revenue_series
        
        # Group by business unit
        unit_revenue = revenue_df_clean.groupby('Business Unit')[revenue_column].sum().reset_index()
        unit_revenue = unit_revenue.sort_values(revenue_column, ascending=False).head(5)
        
        # Create bar chart
        fig = px.bar(
            unit_revenue,
            x='Business Unit',
            y=revenue_column,
            title='Revenue by Business Unit (Top 5)',
            color=revenue_column,
            color_continuous_scale='Blues'
        )
        fig.update_layout(
            xaxis_title="",
            yaxis_title="Revenue ($)",
            yaxis_tickformat="$,.0f",
            showlegend=False,
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Business Unit data not available")

def display_top_performers_chart(revenue_df):
    """Display top performers chart"""
    revenue_column = get_revenue_column(revenue_df)
    
    if 'Sold By' in revenue_df.columns and revenue_column:
        # Clean revenue data and group by salesperson
        revenue_df_clean = revenue_df.copy()
        revenue_df_clean[revenue_column] = get_safe_revenue_data(revenue_df_clean, revenue_column)
        
        sales_by_person = revenue_df_clean.groupby('Sold By')[revenue_column].sum().reset_index()
        sales_by_person = sales_by_person.sort_values(revenue_column, ascending=True).tail(5)
        
        # Create horizontal bar chart
        fig = px.bar(
            sales_by_person,
            y='Sold By',
            x=revenue_column,
            orientation='h',
            title='Top 5 Sales Performers',
            color=revenue_column,
            color_continuous_scale='Greens'
        )
        fig.update_layout(
            xaxis_title="Revenue ($)",
            yaxis_title="",
            xaxis_tickformat="$,.0f",
            showlegend=False,
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sales performance data not available")

def display_commission_distribution_chart(revenue_df, employee_df):
    """Display commission distribution analysis"""
    st.markdown("**💸 Commission Distribution**")
    
    if employee_df.empty:
        st.info("Employee data needed for commission analysis")
        return
    
    business_settings = safe_session_get('business_unit_commission_settings', {})
    if not business_settings:
        st.info("Commission rates not configured")
        return
    
    # Calculate estimated commissions by plan type
    plan_distribution = employee_df['Commission Plan'].value_counts()
    
    if not plan_distribution.empty:
        fig = px.pie(
            values=plan_distribution.values,
            names=plan_distribution.index,
            title='Commission Plan Distribution'
        )
        fig.update_layout(
            showlegend=True,
            height=300,
            margin=dict(t=50, b=50, l=50, r=50)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Commission plan data not available")

def display_revenue_trend_analysis(revenue_df):
    """Display revenue trend analysis over time"""
    st.markdown("**📈 Revenue Trends**")
    
    if 'Date' not in revenue_df.columns:
        st.info("Date column needed for trend analysis")
        return
    
    revenue_column = get_revenue_column(revenue_df)
    if not revenue_column:
        st.info("Revenue column not found")
        return
    
    try:
        # Convert date column and prepare data
        revenue_trend_df = revenue_df.copy()
        revenue_trend_df['Date'] = pd.to_datetime(revenue_trend_df['Date'], errors='coerce')
        revenue_trend_df = revenue_trend_df.dropna(subset=['Date'])
        
        if revenue_trend_df.empty:
            st.info("No valid date data for trend analysis")
            return
        
        # Group by month for trend analysis
        revenue_trend_df['Month'] = revenue_trend_df['Date'].dt.to_period('M')
        monthly_revenue = revenue_trend_df.groupby('Month')[revenue_column].agg(['sum', 'count']).reset_index()
        monthly_revenue.columns = ['Month', 'Revenue', 'Job_Count']
        monthly_revenue['Month'] = monthly_revenue['Month'].astype(str)
        
        if len(monthly_revenue) > 1:
            # Create dual-axis chart
            fig = go.Figure()
            
            # Revenue bars
            fig.add_trace(go.Bar(
                x=monthly_revenue['Month'],
                y=monthly_revenue['Revenue'],
                name='Revenue',
                marker_color='lightblue',
                yaxis='y'
            ))
            
            # Job count line
            fig.add_trace(go.Scatter(
                x=monthly_revenue['Month'],
                y=monthly_revenue['Job_Count'],
                mode='lines+markers',
                name='Job Count',
                line=dict(color='orange', width=3),
                yaxis='y2'
            ))
            
            fig.update_layout(
                title='Monthly Revenue and Job Volume Trends',
                xaxis_title='Month',
                yaxis=dict(title='Revenue ($)', tickformat='$,.0f', side='left'),
                yaxis2=dict(title='Job Count', overlaying='y', side='right'),
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Single month - show daily breakdown if possible
            daily_revenue = revenue_trend_df.groupby(revenue_trend_df['Date'].dt.date)[revenue_column].sum().reset_index()
            daily_revenue.columns = ['Date', 'Revenue']
            
            if len(daily_revenue) > 1:
                fig = px.line(
                    daily_revenue,
                    x='Date',
                    y='Revenue',
                    title='Daily Revenue Trend',
                    markers=True
                )
                fig.update_layout(
                    yaxis_tickformat='$,.0f',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Insufficient data points for trend analysis")
    
    except Exception as e:
        st.info(f"Unable to generate trend analysis: {str(e)}")

# Remove the old analytics function
def display_analytics_overview():
    """Legacy function - replaced by display_enhanced_analytics"""
    pass

