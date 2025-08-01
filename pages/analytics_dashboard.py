import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Any
import io
from sklearn.linear_model import LinearRegression

def analytics_dashboard_page():
    """Enhanced analytics dashboard with interactive visualizations"""
    st.title("📊 Analytics Dashboard")
    
    # Ensure session state is initialized
    if 'calculator' not in st.session_state:
        from models import CommissionCalculator
        st.session_state.calculator = CommissionCalculator()
    
    calc = st.session_state.calculator
    
    # Check if data and calculations exist
    if not calc.employees or not calc.business_units:
        st.warning("⚠️ No data loaded. Please upload data in the Data Management page.")
        if st.button("Go to Data Management"):
            st.session_state.selected_page = "📤 Data Management"
            st.rerun()
        return
    
    if not calc.commissions:
        st.info("💡 No commissions calculated yet. Configure rates and calculate commissions first.")
        if st.button("Go to System Configuration"):
            st.session_state.selected_page = "⚙️ System Configuration"
            st.rerun()
        return
    
    # Get analytics data
    analytics = calc.get_analytics_data()
    
    # Display KPI cards
    display_kpi_cards(analytics['kpis'])
    
    st.divider()
    
    # Analytics tabs
    tabs = st.tabs([
        "📊 Overview",
        "💰 Revenue Analysis",
        "👥 Employee Analysis",
        "🏢 Business Unit Analysis",
        "📈 Trends & Forecasting",
        "🎯 Performance Metrics"
    ])
    
    with tabs[0]:
        overview_analysis(calc, analytics)
    
    with tabs[1]:
        revenue_analysis(calc)
    
    with tabs[2]:
        employee_analysis(calc)
    
    with tabs[3]:
        business_unit_analysis(calc)
    
    with tabs[4]:
        trends_and_forecasting(calc)
    
    with tabs[5]:
        performance_metrics(calc)

def display_kpi_cards(kpis: Dict[str, float]):
    """Display KPI metric cards with styling"""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Revenue",
            f"${kpis['total_revenue']:,.2f}",
            help="Total revenue across all business units"
        )
    
    with col2:
        st.metric(
            "Labor Cost",
            f"${kpis['total_labor_cost']:,.2f}",
            f"{(kpis['total_labor_cost']/kpis['total_revenue']*100):.1f}%" if kpis['total_revenue'] > 0 else "0%",
            delta_color="inverse",
            help="Total labor cost including overtime"
        )
    
    with col3:
        st.metric(
            "Commissions",
            f"${kpis['total_commissions']:,.2f}",
            f"{(kpis['total_commissions']/kpis['total_revenue']*100):.1f}%" if kpis['total_revenue'] > 0 else "0%",
            help="Total commission payouts"
        )
    
    with col4:
        st.metric(
            "Gross Profit",
            f"${kpis['gross_profit']:,.2f}",
            f"{kpis['profit_margin']:.1f}%",
            help="Revenue minus labor and commissions"
        )
    
    with col5:
        efficiency = (kpis['gross_profit'] / kpis['total_revenue'] * 100) if kpis['total_revenue'] > 0 else 0
        st.metric(
            "Efficiency",
            f"{efficiency:.1f}%",
            help="Profit as percentage of revenue"
        )

def overview_analysis(calc, analytics):
    """Overview analysis with key charts"""
    st.subheader("📊 Business Overview")
    
    # Create two columns for charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Revenue breakdown pie chart
        revenue_data = []
        for unit in calc.business_units.values():
            if unit.revenue > 0:
                revenue_data.append({
                    'Business Unit': unit.name,
                    'Revenue': float(unit.revenue)
                })
        
        if revenue_data:
            df_revenue = pd.DataFrame(revenue_data)
            fig_revenue = px.pie(
                df_revenue,
                values='Revenue',
                names='Business Unit',
                title='Revenue Distribution by Business Unit',
                color_discrete_sequence=px.colors.sequential.Blues_r
            )
            fig_revenue.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_revenue, use_container_width=True)
    
    with col2:
        # Cost breakdown
        cost_data = {
            'Category': ['Labor Cost', 'Commissions', 'Profit'],
            'Amount': [
                analytics['kpis']['total_labor_cost'],
                analytics['kpis']['total_commissions'],
                analytics['kpis']['gross_profit']
            ]
        }
        
        df_cost = pd.DataFrame(cost_data)
        fig_cost = px.pie(
            df_cost,
            values='Amount',
            names='Category',
            title='Cost Structure Breakdown',
            color_discrete_map={
                'Labor Cost': '#FF6B6B',
                'Commissions': '#4ECDC4',
                'Profit': '#45B7D1'
            }
        )
        fig_cost.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_cost, use_container_width=True)
    
    # Summary statistics
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📊 Revenue Statistics")
        total_revenue = analytics['kpis']['total_revenue']
        avg_revenue = total_revenue / len(calc.business_units) if calc.business_units else 0
        
        st.write(f"**Total Revenue:** ${total_revenue:,.2f}")
        st.write(f"**Average per Unit:** ${avg_revenue:,.2f}")
        st.write(f"**Business Units:** {len(calc.business_units)}")
    
    with col2:
        st.markdown("### 👥 Employee Statistics")
        total_employees = len(calc.employees)
        active_employees = len([e for e in calc.employees.values() if e.total_hours > 0])
        
        st.write(f"**Total Employees:** {total_employees}")
        st.write(f"**Active Employees:** {active_employees}")
        st.write(f"**Utilization Rate:** {(active_employees/total_employees*100):.1f}%")
    
    with col3:
        st.markdown("### 💰 Commission Statistics")
        total_commissions = analytics['kpis']['total_commissions']
        avg_commission = total_commissions / active_employees if active_employees > 0 else 0
        
        st.write(f"**Total Commissions:** ${total_commissions:,.2f}")
        st.write(f"**Average per Employee:** ${avg_commission:,.2f}")
        st.write(f"**Commission Rate:** {(total_commissions/total_revenue*100):.1f}%")

def revenue_analysis(calc):
    """Detailed revenue analysis"""
    st.subheader("💰 Revenue Analysis")
    
    # Prepare data
    unit_data = []
    for unit in calc.business_units.values():
        unit_summary = calc.get_business_unit_summary(unit.id)
        unit_data.append({
            'Business Unit': unit.name,
            'Category': unit.category or 'Uncategorized',
            'Revenue': float(unit.revenue),
            'Commission Rate': float(unit.commission_rate),
            'Commission Amount': float(unit.commission_amount),
            'Net Revenue': float(unit.revenue - unit.commission_amount),
            'Employees Paid': unit_summary['employees_paid']
        })
    
    df = pd.DataFrame(unit_data)
    
    # Revenue comparison chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Revenue',
        x=df['Business Unit'],
        y=df['Revenue'],
        marker_color='#2C5F75',
        text=df['Revenue'].apply(lambda x: f'${x:,.0f}'),
        textposition='outside'
    ))
    
    fig.add_trace(go.Bar(
        name='Commission',
        x=df['Business Unit'],
        y=df['Commission Amount'],
        marker_color='#922B3E',
        text=df['Commission Amount'].apply(lambda x: f'${x:,.0f}'),
        textposition='outside'
    ))
    
    fig.update_layout(
        title='Revenue vs Commission by Business Unit',
        xaxis_tickangle=-45,
        barmode='group',
        height=500,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Category analysis
    if df['Category'].nunique() > 1:
        st.divider()
        st.markdown("### 🏷️ Revenue by Category")
        
        category_summary = df.groupby('Category').agg({
            'Revenue': 'sum',
            'Commission Amount': 'sum',
            'Net Revenue': 'sum'
        }).reset_index()
        
        fig_cat = px.treemap(
            category_summary,
            path=['Category'],
            values='Revenue',
            title='Revenue Distribution by Category',
            color='Revenue',
            color_continuous_scale='Blues'
        )
        
        st.plotly_chart(fig_cat, use_container_width=True)
    
    # Detailed table
    st.divider()
    st.markdown("### 📋 Detailed Revenue Table")
    
    # Format the dataframe for display
    display_df = df.copy()
    display_df['Revenue'] = display_df['Revenue'].apply(lambda x: f'${x:,.2f}')
    display_df['Commission Amount'] = display_df['Commission Amount'].apply(lambda x: f'${x:,.2f}')
    display_df['Net Revenue'] = display_df['Net Revenue'].apply(lambda x: f'${x:,.2f}')
    display_df['Commission Rate'] = display_df['Commission Rate'].apply(lambda x: f'{x:.1f}%')
    
    st.dataframe(display_df, use_container_width=True)
    
    # Export button
    if st.button("📤 Export Revenue Analysis", use_container_width=True):
        export_revenue_analysis(df)

def employee_analysis(calc):
    """Detailed employee analysis"""
    st.subheader("👥 Employee Analysis")
    
    # Prepare employee data
    emp_data = []
    for emp in calc.employees.values():
        emp_summary = calc.get_employee_summary(emp.id)
        emp_data.append({
            'Employee': emp.name,
            'Department': emp.department or 'Unassigned',
            'Regular Hours': float(emp.regular_hours),
            'OT Hours': float(emp.ot_hours),
            'DT Hours': float(emp.dt_hours),
            'Total Hours': emp_summary['total_hours'],
            'Hourly Rate': float(emp.hourly_rate),
            'Labor Cost': emp_summary['labor_cost'],
            'Commission': emp_summary['total_commission'],
            'Total Earnings': emp_summary['total_earnings']
        })
    
    df = pd.DataFrame(emp_data)
    
    # Top earners chart
    top_10 = df.nlargest(10, 'Total Earnings')
    
    fig_top = go.Figure()
    fig_top.add_trace(go.Bar(
        y=top_10['Employee'],
        x=top_10['Labor Cost'],
        name='Labor Cost',
        orientation='h',
        marker_color='#2C5F75'
    ))
    
    fig_top.add_trace(go.Bar(
        y=top_10['Employee'],
        x=top_10['Commission'],
        name='Commission',
        orientation='h',
        marker_color='#922B3E'
    ))
    
    fig_top.update_layout(
        title='Top 10 Earners - Labor Cost vs Commission',
        barmode='stack',
        height=400,
        xaxis_title='Earnings ($)',
        yaxis_title='Employee'
    )
    
    st.plotly_chart(fig_top, use_container_width=True)
    
    # Hours distribution
    col1, col2 = st.columns(2)
    
    with col1:
        # Hours breakdown
        hours_data = {
            'Type': ['Regular', 'Overtime', 'Double Time'],
            'Hours': [
                df['Regular Hours'].sum(),
                df['OT Hours'].sum(),
                df['DT Hours'].sum()
            ]
        }
        
        fig_hours = px.pie(
            pd.DataFrame(hours_data),
            values='Hours',
            names='Type',
            title='Hours Distribution by Type',
            color_discrete_map={
                'Regular': '#2C5F75',
                'Overtime': '#FFA500',
                'Double Time': '#922B3E'
            }
        )
        st.plotly_chart(fig_hours, use_container_width=True)
    
    with col2:
        # Department analysis
        if df['Department'].nunique() > 1:
            dept_summary = df.groupby('Department').agg({
                'Total Hours': 'sum',
                'Labor Cost': 'sum',
                'Commission': 'sum'
            }).reset_index()
            
            fig_dept = px.bar(
                dept_summary,
                x='Department',
                y=['Labor Cost', 'Commission'],
                title='Earnings by Department',
                color_discrete_map={
                    'Labor Cost': '#2C5F75',
                    'Commission': '#922B3E'
                }
            )
            st.plotly_chart(fig_dept, use_container_width=True)
    
    # Employee efficiency metrics
    st.divider()
    st.markdown("### 📊 Employee Efficiency Metrics")
    
    # Calculate efficiency metrics
    df['Revenue per Hour'] = df.apply(
        lambda row: row['Total Earnings'] / row['Total Hours'] if row['Total Hours'] > 0 else 0,
        axis=1
    )
    
    df['Commission Rate'] = df.apply(
        lambda row: row['Commission'] / row['Total Earnings'] * 100 if row['Total Earnings'] > 0 else 0,
        axis=1
    )
    
    # Scatter plot
    fig_scatter = px.scatter(
        df,
        x='Total Hours',
        y='Total Earnings',
        size='Commission',
        color='Department',
        hover_data=['Employee', 'Revenue per Hour'],
        title='Hours vs Earnings Analysis',
        labels={
            'Total Hours': 'Total Hours Worked',
            'Total Earnings': 'Total Earnings ($)'
        }
    )
    
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_hours = df['Total Hours'].mean()
        st.metric("Avg Hours/Employee", f"{avg_hours:.1f}")
    
    with col2:
        avg_rate = df['Hourly Rate'].mean()
        st.metric("Avg Hourly Rate", f"${avg_rate:.2f}")
    
    with col3:
        avg_earnings = df['Total Earnings'].mean()
        st.metric("Avg Earnings", f"${avg_earnings:,.2f}")
    
    with col4:
        overtime_ratio = (df['OT Hours'].sum() + df['DT Hours'].sum()) / df['Total Hours'].sum() * 100
        st.metric("Overtime %", f"{overtime_ratio:.1f}%")

def business_unit_analysis(calc):
    """Detailed business unit analysis"""
    st.subheader("🏢 Business Unit Analysis")
    
    # Prepare data
    unit_metrics = []
    for unit in calc.business_units.values():
        summary = calc.get_business_unit_summary(unit.id)
        
        unit_metrics.append({
            'Business Unit': unit.name,
            'Category': unit.category or 'Uncategorized',
            'Revenue': float(unit.revenue),
            'Commission Rate': float(unit.commission_rate),
            'Total Commission': summary['total_commission'],
            'Employees Paid': summary['employees_paid'],
            'Profit Margin': (summary['profit_after_commission'] / float(unit.revenue) * 100) if unit.revenue > 0 else 0,
            'Avg Commission/Employee': summary['total_commission'] / summary['employees_paid'] if summary['employees_paid'] > 0 else 0
        })
    
    df = pd.DataFrame(unit_metrics)
    
    # Profitability analysis
    fig_profit = go.Figure()
    
    fig_profit.add_trace(go.Scatter(
        x=df['Commission Rate'],
        y=df['Profit Margin'],
        mode='markers+text',
        marker=dict(
            size=df['Revenue'] / 1000,  # Scale by revenue
            color=df['Employees Paid'],
            colorscale='Blues',
            showscale=True,
            colorbar=dict(title="Employees")
        ),
        text=df['Business Unit'],
        textposition="top center",
        name='Business Units'
    ))
    
    fig_profit.update_layout(
        title='Commission Rate vs Profit Margin Analysis',
        xaxis_title='Commission Rate (%)',
        yaxis_title='Profit Margin (%)',
        height=500
    )
    
    st.plotly_chart(fig_profit, use_container_width=True)
    
    # Commission efficiency
    col1, col2 = st.columns(2)
    
    with col1:
        # Commission per employee
        fig_comm_emp = px.bar(
            df.sort_values('Avg Commission/Employee', ascending=False),
            x='Business Unit',
            y='Avg Commission/Employee',
            title='Average Commission per Employee',
            color='Avg Commission/Employee',
            color_continuous_scale='Reds'
        )
        fig_comm_emp.update_xaxis(tickangle=-45)
        st.plotly_chart(fig_comm_emp, use_container_width=True)
    
    with col2:
        # Revenue per employee
        df['Revenue per Employee'] = df['Revenue'] / df['Employees Paid']
        
        fig_rev_emp = px.bar(
            df.sort_values('Revenue per Employee', ascending=False),
            x='Business Unit',
            y='Revenue per Employee',
            title='Revenue per Employee',
            color='Revenue per Employee',
            color_continuous_scale='Greens'
        )
        fig_rev_emp.update_xaxis(tickangle=-45)
        st.plotly_chart(fig_rev_emp, use_container_width=True)
    
    # Performance matrix
    st.divider()
    st.markdown("### 🎯 Business Unit Performance Matrix")
    
    # Create performance categories
    median_revenue = df['Revenue'].median()
    median_profit = df['Profit Margin'].median()
    
    df['Performance'] = df.apply(
        lambda row: 'Star' if row['Revenue'] >= median_revenue and row['Profit Margin'] >= median_profit
        else 'Growth' if row['Revenue'] < median_revenue and row['Profit Margin'] >= median_profit
        else 'Volume' if row['Revenue'] >= median_revenue and row['Profit Margin'] < median_profit
        else 'Review',
        axis=1
    )
    
    # Matrix chart
    fig_matrix = px.scatter(
        df,
        x='Revenue',
        y='Profit Margin',
        color='Performance',
        size='Total Commission',
        hover_data=['Business Unit', 'Commission Rate', 'Employees Paid'],
        title='Business Unit Performance Matrix',
        color_discrete_map={
            'Star': '#28a745',
            'Growth': '#17a2b8',
            'Volume': '#ffc107',
            'Review': '#dc3545'
        }
    )
    
    # Add quadrant lines
    fig_matrix.add_hline(y=median_profit, line_dash="dash", line_color="gray")
    fig_matrix.add_vline(x=median_revenue, line_dash="dash", line_color="gray")
    
    st.plotly_chart(fig_matrix, use_container_width=True)
    
    # Performance summary
    performance_summary = df['Performance'].value_counts()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("⭐ Star Units", performance_summary.get('Star', 0))
    
    with col2:
        st.metric("📈 Growth Units", performance_summary.get('Growth', 0))
    
    with col3:
        st.metric("📊 Volume Units", performance_summary.get('Volume', 0))
    
    with col4:
        st.metric("⚠️ Review Units", performance_summary.get('Review', 0))

def trends_and_forecasting(calc):
    """Trends analysis and basic forecasting"""
    st.subheader("📈 Trends & Forecasting")
    
    st.info("📊 This section shows simulated historical data and projections. Integrate with your historical database for real trends.")
    
    # Simulate historical data (in real app, load from database)
    months = pd.date_range(end=datetime.now(), periods=12, freq='M')
    
    historical_data = []
    current_revenue = sum(unit.revenue for unit in calc.business_units.values())
    current_labor = sum(emp.total_labor_cost for emp in calc.employees.values())
    current_commission = sum(c.adjusted_amount for c in calc.commissions)
    
    for i, month in enumerate(months):
        # Simulate with some randomness
        revenue_factor = 0.8 + (i / 12) * 0.4 + np.random.uniform(-0.1, 0.1)
        labor_factor = 0.9 + (i / 12) * 0.2 + np.random.uniform(-0.05, 0.05)
        
        historical_data.append({
            'Month': month,
            'Revenue': float(current_revenue) * revenue_factor,
            'Labor Cost': float(current_labor) * labor_factor,
            'Commission': float(current_commission) * revenue_factor * 0.9,
        })
    
    df_hist = pd.DataFrame(historical_data)
    df_hist['Profit'] = df_hist['Revenue'] - df_hist['Labor Cost'] - df_hist['Commission']
    
    # Trend chart
    fig_trend = go.Figure()
    
    fig_trend.add_trace(go.Scatter(
        x=df_hist['Month'],
        y=df_hist['Revenue'],
        mode='lines+markers',
        name='Revenue',
        line=dict(color='#2C5F75', width=3)
    ))
    
    fig_trend.add_trace(go.Scatter(
        x=df_hist['Month'],
        y=df_hist['Labor Cost'],
        mode='lines+markers',
        name='Labor Cost',
        line=dict(color='#FF6B6B', width=2)
    ))
    
    fig_trend.add_trace(go.Scatter(
        x=df_hist['Month'],
        y=df_hist['Commission'],
        mode='lines+markers',
        name='Commission',
        line=dict(color='#4ECDC4', width=2)
    ))
    
    fig_trend.add_trace(go.Scatter(
        x=df_hist['Month'],
        y=df_hist['Profit'],
        mode='lines+markers',
        name='Profit',
        line=dict(color='#45B7D1', width=3, dash='dash')
    ))
    
    fig_trend.update_layout(
        title='12-Month Financial Trends',
        xaxis_title='Month',
        yaxis_title='Amount ($)',
        hovermode='x unified',
        height=500
    )
    
    st.plotly_chart(fig_trend, use_container_width=True)
    
    # Growth metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        revenue_growth = ((df_hist.iloc[-1]['Revenue'] - df_hist.iloc[0]['Revenue']) / df_hist.iloc[0]['Revenue'] * 100)
        st.metric(
            "Revenue Growth",
            f"{revenue_growth:+.1f}%",
            f"${df_hist.iloc[-1]['Revenue'] - df_hist.iloc[0]['Revenue']:,.0f}"
        )
    
    with col2:
        profit_growth = ((df_hist.iloc[-1]['Profit'] - df_hist.iloc[0]['Profit']) / df_hist.iloc[0]['Profit'] * 100)
        st.metric(
            "Profit Growth",
            f"{profit_growth:+.1f}%",
            f"${df_hist.iloc[-1]['Profit'] - df_hist.iloc[0]['Profit']:,.0f}"
        )
    
    with col3:
        margin_current = df_hist.iloc[-1]['Profit'] / df_hist.iloc[-1]['Revenue'] * 100
        margin_start = df_hist.iloc[0]['Profit'] / df_hist.iloc[0]['Revenue'] * 100
        st.metric(
            "Profit Margin",
            f"{margin_current:.1f}%",
            f"{margin_current - margin_start:+.1f}%"
        )
    
    # Simple forecast
    st.divider()
    st.markdown("### 🔮 Simple Forecast (Next 3 Months)")
    
    # Linear regression forecast
    from sklearn.linear_model import LinearRegression
    
    X = np.arange(len(df_hist)).reshape(-1, 1)
    model = LinearRegression()
    
    # Forecast revenue
    model.fit(X, df_hist['Revenue'])
    future_months = pd.date_range(start=df_hist['Month'].iloc[-1] + pd.DateOffset(months=1), periods=3, freq='M')
    future_X = np.arange(len(df_hist), len(df_hist) + 3).reshape(-1, 1)
    revenue_forecast = model.predict(future_X)
    
    # Create forecast dataframe
    forecast_data = pd.DataFrame({
        'Month': future_months,
        'Revenue Forecast': revenue_forecast,
        'Labor Cost Forecast': revenue_forecast * (df_hist['Labor Cost'].sum() / df_hist['Revenue'].sum()),
        'Commission Forecast': revenue_forecast * (df_hist['Commission'].sum() / df_hist['Revenue'].sum())
    })
    
    forecast_data['Profit Forecast'] = (
        forecast_data['Revenue Forecast'] - 
        forecast_data['Labor Cost Forecast'] - 
        forecast_data['Commission Forecast']
    )
    
    # Display forecast
    fig_forecast = go.Figure()
    
    # Historical lines
    for col in ['Revenue', 'Profit']:
        fig_forecast.add_trace(go.Scatter(
            x=df_hist['Month'],
            y=df_hist[col],
            mode='lines',
            name=f'{col} (Historical)',
            line=dict(width=2)
        ))
    
    # Forecast lines
    fig_forecast.add_trace(go.Scatter(
        x=forecast_data['Month'],
        y=forecast_data['Revenue Forecast'],
        mode='lines+markers',
        name='Revenue Forecast',
        line=dict(dash='dash', width=2)
    ))
    
    fig_forecast.add_trace(go.Scatter(
        x=forecast_data['Month'],
        y=forecast_data['Profit Forecast'],
        mode='lines+markers',
        name='Profit Forecast',
        line=dict(dash='dash', width=2)
    ))
    
    fig_forecast.update_layout(
        title='3-Month Revenue & Profit Forecast',
        xaxis_title='Month',
        yaxis_title='Amount ($)',
        height=400
    )
    
    st.plotly_chart(fig_forecast, use_container_width=True)
    
    # Forecast summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        avg_monthly_revenue = forecast_data['Revenue Forecast'].mean()
        st.metric("Avg Monthly Revenue (Forecast)", f"${avg_monthly_revenue:,.2f}")
    
    with col2:
        total_forecast_profit = forecast_data['Profit Forecast'].sum()
        st.metric("Total 3-Month Profit (Forecast)", f"${total_forecast_profit:,.2f}")
    
    with col3:
        forecast_margin = forecast_data['Profit Forecast'].sum() / forecast_data['Revenue Forecast'].sum() * 100
        st.metric("Forecast Profit Margin", f"{forecast_margin:.1f}%")

def performance_metrics(calc):
    """Key performance metrics and scorecards"""
    st.subheader("🎯 Performance Metrics")
    
    # Calculate comprehensive metrics
    metrics = calculate_performance_metrics(calc)
    
    # Performance scorecard
    st.markdown("### 📊 Performance Scorecard")
    
    # Create gauge charts for key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fig_efficiency = create_gauge_chart(
            metrics['operational_efficiency'],
            "Operational Efficiency",
            suffix="%",
            ranges=[0, 60, 80, 100],
            colors=['red', 'yellow', 'green']
        )
        st.plotly_chart(fig_efficiency, use_container_width=True)
    
    with col2:
        fig_utilization = create_gauge_chart(
            metrics['employee_utilization'],
            "Employee Utilization",
            suffix="%",
            ranges=[0, 50, 75, 100],
            colors=['red', 'yellow', 'green']
        )
        st.plotly_chart(fig_utilization, use_container_width=True)
    
    with col3:
        fig_commission_efficiency = create_gauge_chart(
            metrics['commission_efficiency'],
            "Commission Efficiency",
            suffix="%",
            ranges=[0, 70, 85, 100],
            colors=['red', 'yellow', 'green']
        )
        st.plotly_chart(fig_commission_efficiency, use_container_width=True)
    
    # Detailed metrics table
    st.divider()
    st.markdown("### 📋 Detailed Performance Metrics")
    
    metrics_data = {
        'Metric': [
            'Revenue per Employee',
            'Average Commission Rate',
            'Labor Cost Ratio',
            'Overtime Ratio',
            'Profit per Hour',
            'Commission ROI'
        ],
        'Value': [
            f"${metrics['revenue_per_employee']:,.2f}",
            f"{metrics['avg_commission_rate']:.1f}%",
            f"{metrics['labor_cost_ratio']:.1f}%",
            f"{metrics['overtime_ratio']:.1f}%",
            f"${metrics['profit_per_hour']:,.2f}",
            f"{metrics['commission_roi']:.1f}x"
        ],
        'Status': [
            get_metric_status(metrics['revenue_per_employee'], 10000, 20000),
            get_metric_status(metrics['avg_commission_rate'], 15, 10, inverse=True),
            get_metric_status(metrics['labor_cost_ratio'], 40, 30, inverse=True),
            get_metric_status(metrics['overtime_ratio'], 20, 10, inverse=True),
            get_metric_status(metrics['profit_per_hour'], 50, 100),
            get_metric_status(metrics['commission_roi'], 3, 5)
        ],
        'Target': [
            '$20,000+',
            '<10%',
            '<30%',
            '<10%',
            '$100+',
            '5x+'
        ]
    }
    
    df_metrics = pd.DataFrame(metrics_data)
    
    # Style the dataframe
    def style_status(val):
        if val == '🟢 Good':
            return 'color: green'
        elif val == '🟡 Fair':
            return 'color: orange'
        else:
            return 'color: red'
    
    styled_df = df_metrics.style.applymap(style_status, subset=['Status'])
    st.dataframe(styled_df, use_container_width=True)
    
    # Recommendations
    st.divider()
    st.markdown("### 💡 Performance Recommendations")
    
    recommendations = generate_recommendations(metrics)
    
    for i, rec in enumerate(recommendations, 1):
        st.write(f"{i}. {rec}")

# Helper functions
def calculate_performance_metrics(calc):
    """Calculate comprehensive performance metrics"""
    total_revenue = sum(unit.revenue for unit in calc.business_units.values())
    total_labor = sum(emp.total_labor_cost for emp in calc.employees.values())
    total_commission = sum(c.adjusted_amount for c in calc.commissions)
    total_hours = sum(emp.total_hours for emp in calc.employees.values())
    active_employees = len([e for e in calc.employees.values() if e.total_hours > 0])
    
    metrics = {
        'operational_efficiency': ((total_revenue - total_labor - total_commission) / total_revenue * 100) if total_revenue > 0 else 0,
        'employee_utilization': (active_employees / len(calc.employees) * 100) if calc.employees else 0,
        'commission_efficiency': (total_commission / total_revenue * 100) if total_revenue > 0 else 0,
        'revenue_per_employee': float(total_revenue / active_employees) if active_employees > 0 else 0,
        'avg_commission_rate': sum(unit.commission_rate for unit in calc.business_units.values()) / len(calc.business_units) if calc.business_units else 0,
        'labor_cost_ratio': (float(total_labor) / float(total_revenue) * 100) if total_revenue > 0 else 0,
        'overtime_ratio': sum(emp.ot_hours + emp.dt_hours for emp in calc.employees.values()) / float(total_hours) * 100 if total_hours > 0 else 0,
        'profit_per_hour': float(total_revenue - total_labor - total_commission) / float(total_hours) if total_hours > 0 else 0,
        'commission_roi': float(total_revenue) / float(total_commission) if total_commission > 0 else 0
    }
    
    return metrics

def create_gauge_chart(value, title, suffix="%", ranges=None, colors=None):
    """Create a gauge chart"""
    if ranges is None:
        ranges = [0, 50, 75, 100]
    if colors is None:
        colors = ['red', 'yellow', 'green']
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title},
        number={'suffix': suffix},
        gauge={
            'axis': {'range': [None, max(ranges)]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [ranges[i], ranges[i+1]], 'color': colors[i]}
                for i in range(len(ranges)-1)
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': ranges[-2]  # Target value
            }
        }
    ))
    
    fig.update_layout(height=250)
    return fig

def get_metric_status(value, warning_threshold, good_threshold, inverse=False):
    """Get status emoji based on metric value"""
    if inverse:
        if value <= good_threshold:
            return '🟢 Good'
        elif value <= warning_threshold:
            return '🟡 Fair'
        else:
            return '🔴 Poor'
    else:
        if value >= good_threshold:
            return '🟢 Good'
        elif value >= warning_threshold:
            return '🟡 Fair'
        else:
            return '🔴 Poor'

def generate_recommendations(metrics):
    """Generate performance recommendations based on metrics"""
    recommendations = []
    
    if metrics['operational_efficiency'] < 60:
        recommendations.append("⚠️ Operational efficiency is low. Consider reviewing labor costs and commission rates.")
    
    if metrics['overtime_ratio'] > 15:
        recommendations.append("⚠️ High overtime ratio detected. Consider hiring additional staff or redistributing workload.")
    
    if metrics['employee_utilization'] < 75:
        recommendations.append("💡 Employee utilization could be improved. Review work allocation and scheduling.")
    
    if metrics['commission_efficiency'] > 15:
        recommendations.append("💡 Commission rates may be high. Analyze ROI by business unit for optimization opportunities.")
    
    if metrics['profit_per_hour'] < 75:
        recommendations.append("📊 Profit per hour is below target. Focus on high-margin business units or improve efficiency.")
    
    if not recommendations:
        recommendations.append("✅ All metrics are within acceptable ranges. Keep up the good work!")
    
    return recommendations

def export_revenue_analysis(df):
    """Export revenue analysis to Excel"""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Revenue Analysis', index=False)
        
        # Get workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['Revenue Analysis']
        
        # Add formats
        currency_format = workbook.add_format({'num_format': '$#,##0.00'})
        percent_format = workbook.add_format({'num_format': '0.0%'})
        
        # Apply formats
        worksheet.set_column('C:F', 15, currency_format)
        worksheet.set_column('D:D', 15, percent_format)
    
    output.seek(0)
    
    st.download_button(
        label="📥 Download Analysis",
        data=output,
        file_name=f"revenue_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )