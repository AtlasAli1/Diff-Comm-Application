"""Analytics and reporting business service."""

import pandas as pd
import numpy as np
from decimal import Decimal
from typing import Dict, List, Any
import plotly.graph_objects as go
import plotly.express as px
from scipy import stats
from sklearn.linear_model import LinearRegression
from loguru import logger


class AnalyticsService:
    """Handles analytics calculations and visualization generation."""

    def __init__(self):
        self.chart_colors = {
            'primary': '#2C5F75',
            'secondary': '#922B3E',
            'success': '#28a745',
            'warning': '#ffc107',
            'info': '#17a2b8',
            'accent': '#6f42c1'
        }

    def calculate_kpis(self, commission_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate key performance indicators.

        Args:
            commission_data: Commission summary data

        Returns:
            Dictionary with KPI calculations
        """
        try:
            kpis = {
                'total_revenue': commission_data.get('total_revenue', Decimal('0')),
                'total_commissions': commission_data.get('total_commissions', Decimal('0')),
                'total_labor_cost': commission_data.get('total_labor_cost', Decimal('0')),
                'gross_profit': commission_data.get('gross_profit', Decimal('0')),
                'profit_margin': commission_data.get('profit_margin', Decimal('0')),
                'commission_rate': Decimal('0'),
                'labor_efficiency': Decimal('0'),
                'revenue_per_employee': Decimal('0')
            }

            # Calculate derived KPIs
            if kpis['total_revenue'] > 0:
                kpis['commission_rate'] = (kpis['total_commissions'] / kpis['total_revenue'] * 100).quantize(
                    Decimal('0.01')
                )

                if commission_data.get('employees_count', 0) > 0:
                    kpis['revenue_per_employee'] = (kpis['total_revenue'] /
                                                   Decimal(str(commission_data['employees_count']))).quantize(
                        Decimal('0.01')
                    )

            if kpis['total_labor_cost'] > 0:
                kpis['labor_efficiency'] = (kpis['total_revenue'] / kpis['total_labor_cost']).quantize(
                    Decimal('0.01')
                )

            logger.debug(f"Calculated KPIs: {len(kpis)} metrics")
            return kpis

        except Exception as e:
            logger.error(f"Error calculating KPIs: {e}")
            return {}

    def generate_employee_performance_chart(self, employees_data: List[Dict[str, Any]],
                                          chart_type: str = 'bar') -> go.Figure:
        """Generate employee performance visualization.

        Args:
            employees_data: List of employee performance data
            chart_type: Type of chart ('bar', 'pie', 'scatter', 'box')

        Returns:
            Plotly figure object
        """
        try:
            if not employees_data:
                return go.Figure().add_annotation(
                    text="No employee data available",
                    x=0.5, y=0.5, showarrow=False
                )

            # Filter out helper/apprentice employees from performance charts
            filtered_employees = [emp for emp in employees_data if not emp.get('is_helper', False)]
            
            if not filtered_employees:
                return go.Figure().add_annotation(
                    text="No commission-eligible employees found",
                    x=0.5, y=0.5, showarrow=False
                )

            df = pd.DataFrame(filtered_employees)
            logger.debug(f"Employee performance chart: {len(filtered_employees)} eligible employees, {len(employees_data) - len(filtered_employees)} helpers excluded")

            if chart_type == 'bar':
                fig = go.Figure()

                # Add commission bars
                fig.add_trace(go.Bar(
                    x=df['name'],
                    y=[float(comm) for comm in df['commission']],
                    name='Commission',
                    marker_color=self.chart_colors['primary']
                ))

                # Add labor cost bars
                fig.add_trace(go.Bar(
                    x=df['name'],
                    y=[float(cost) for cost in df['labor_cost']],
                    name='Labor Cost',
                    marker_color=self.chart_colors['secondary']
                ))

                fig.update_layout(
                    title='Employee Performance: Commission vs Labor Cost',
                    xaxis_title='Employee',
                    yaxis_title='Amount ($)',
                    barmode='group',
                    template='plotly_white'
                )

            elif chart_type == 'pie':
                total_earnings = [float(emp['total_earnings']) for emp in employees_data]

                fig = go.Figure(data=[go.Pie(
                    labels=df['name'],
                    values=total_earnings,
                    hole=0.3,
                    marker_colors=px.colors.qualitative.Set3
                )])

                fig.update_layout(
                    title='Total Earnings Distribution by Employee',
                    template='plotly_white'
                )

            elif chart_type == 'scatter':
                fig = go.Figure()

                fig.add_trace(go.Scatter(
                    x=[float(cost) for cost in df['labor_cost']],
                    y=[float(comm) for comm in df['commission']],
                    mode='markers+text',
                    text=df['name'],
                    textposition='top center',
                    marker=dict(
                        size=10,
                        color=self.chart_colors['accent'],
                        opacity=0.7
                    ),
                    name='Employees'
                ))

                fig.update_layout(
                    title='Commission vs Labor Cost Relationship',
                    xaxis_title='Labor Cost ($)',
                    yaxis_title='Commission ($)',
                    template='plotly_white'
                )

            elif chart_type == 'box':
                commission_values = [float(emp['commission']) for emp in employees_data]
                labor_values = [float(emp['labor_cost']) for emp in employees_data]

                fig = go.Figure()

                fig.add_trace(go.Box(
                    y=commission_values,
                    name='Commission',
                    marker_color=self.chart_colors['primary']
                ))

                fig.add_trace(go.Box(
                    y=labor_values,
                    name='Labor Cost',
                    marker_color=self.chart_colors['secondary']
                ))

                fig.update_layout(
                    title='Commission and Labor Cost Distribution',
                    yaxis_title='Amount ($)',
                    template='plotly_white'
                )

            return fig

        except Exception as e:
            logger.error(f"Error generating employee performance chart: {e}")
            return go.Figure().add_annotation(
                text=f"Error generating chart: {str(e)}",
                x=0.5, y=0.5, showarrow=False
            )

    def generate_commission_breakdown_chart(self, commission_data: Dict[str, Any]) -> go.Figure:
        """Generate commission type breakdown visualization.

        Args:
            commission_data: Commission breakdown data

        Returns:
            Plotly figure object
        """
        try:
            employees_data = commission_data.get('employees', [])

            if not employees_data:
                return go.Figure().add_annotation(
                    text="No commission data available",
                    x=0.5, y=0.5, showarrow=False
                )

            # Aggregate commission types
            total_lead_gen = sum(float(emp['commission_breakdown']['lead_generation'])
                               for emp in employees_data)
            total_sales = sum(float(emp['commission_breakdown']['sales'])
                            for emp in employees_data)
            total_work_done = sum(float(emp['commission_breakdown']['work_done'])
                                for emp in employees_data)

            fig = go.Figure(data=[go.Pie(
                labels=['Lead Generation', 'Sales', 'Work Done'],
                values=[total_lead_gen, total_sales, total_work_done],
                hole=0.4,
                marker_colors=[self.chart_colors['primary'],
                             self.chart_colors['secondary'],
                             self.chart_colors['success']]
            )])

            fig.update_layout(
                title='Commission Breakdown by Type',
                template='plotly_white',
                annotations=[dict(text=f"Total<br>${total_lead_gen + total_sales + total_work_done:,.2f}",
                                x=0.5, y=0.5, font_size=12, showarrow=False)]
            )

            return fig

        except Exception as e:
            logger.error(f"Error generating commission breakdown chart: {e}")
            return go.Figure().add_annotation(
                text=f"Error generating chart: {str(e)}",
                x=0.5, y=0.5, showarrow=False
            )

    def generate_forecast_analysis(self, historical_data: List[Dict[str, Any]],
                                 periods: int = 12) -> Dict[str, Any]:
        """Generate commission forecasting analysis.

        Args:
            historical_data: Historical commission data
            periods: Number of periods to forecast

        Returns:
            Dictionary with forecast data and confidence intervals
        """
        try:
            if len(historical_data) < 3:
                return {
                    'forecast': [],
                    'confidence_lower': [],
                    'confidence_upper': [],
                    'trend': 'insufficient_data',
                    'r_squared': 0,
                    'error': 'Insufficient historical data for forecasting'
                }

            # Prepare data
            df = pd.DataFrame(historical_data)
            df['period'] = range(len(df))

            # Extract numeric values
            y_values = [float(item.get('total_commission', 0)) for item in historical_data]
            x_values = np.array(range(len(y_values))).reshape(-1, 1)

            # Fit linear regression model
            model = LinearRegression()
            model.fit(x_values, y_values)

            # Calculate R-squared
            y_pred = model.predict(x_values)
            r_squared = stats.pearsonr(y_values, y_pred)[0] ** 2 if len(y_values) > 1 else 0

            # Generate forecast
            future_periods = np.array(range(len(y_values), len(y_values) + periods)).reshape(-1, 1)
            forecast = model.predict(future_periods)

            # Calculate confidence intervals (simplified)
            residuals = y_values - y_pred
            mse = np.mean(residuals ** 2)
            std_error = np.sqrt(mse)

            confidence_interval = 1.96 * std_error  # 95% confidence
            confidence_lower = forecast - confidence_interval
            confidence_upper = forecast + confidence_interval

            # Determine trend
            trend = 'increasing' if model.coef_[0] > 0 else 'decreasing' if model.coef_[0] < 0 else 'stable'

            logger.info(f"Generated forecast for {periods} periods with R² = {r_squared:.3f}")

            return {
                'forecast': forecast.tolist(),
                'confidence_lower': confidence_lower.tolist(),
                'confidence_upper': confidence_upper.tolist(),
                'trend': trend,
                'r_squared': r_squared,
                'slope': float(model.coef_[0]),
                'intercept': float(model.intercept_)
            }

        except Exception as e:
            logger.error(f"Error generating forecast: {e}")
            return {
                'forecast': [],
                'confidence_lower': [],
                'confidence_upper': [],
                'trend': 'error',
                'r_squared': 0,
                'error': str(e)
            }

    def calculate_period_comparison(self, current_data: Dict[str, Any],
                                  previous_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate period-over-period comparison metrics.

        Args:
            current_data: Current period commission data
            previous_data: Previous period commission data

        Returns:
            Dictionary with comparison metrics
        """
        try:
            comparison = {
                'revenue_change': 0,
                'commission_change': 0,
                'labor_cost_change': 0,
                'profit_change': 0,
                'employee_count_change': 0,
                'efficiency_change': 0
            }

            # Calculate percentage changes
            current_revenue = float(current_data.get('total_revenue', 0))
            previous_revenue = float(previous_data.get('total_revenue', 0))

            if previous_revenue > 0:
                comparison['revenue_change'] = ((current_revenue - previous_revenue) /
                                              previous_revenue * 100)

            current_commission = float(current_data.get('total_commissions', 0))
            previous_commission = float(previous_data.get('total_commissions', 0))

            if previous_commission > 0:
                comparison['commission_change'] = ((current_commission - previous_commission) /
                                                 previous_commission * 100)

            current_labor = float(current_data.get('total_labor_cost', 0))
            previous_labor = float(previous_data.get('total_labor_cost', 0))

            if previous_labor > 0:
                comparison['labor_cost_change'] = ((current_labor - previous_labor) /
                                                  previous_labor * 100)

            current_profit = float(current_data.get('gross_profit', 0))
            previous_profit = float(previous_data.get('gross_profit', 0))

            if previous_profit != 0:  # Handle negative profits
                comparison['profit_change'] = ((current_profit - previous_profit) /
                                             abs(previous_profit) * 100)

            # Employee count change
            current_employees = current_data.get('employees_count', 0)
            previous_employees = previous_data.get('employees_count', 0)

            if previous_employees > 0:
                comparison['employee_count_change'] = ((current_employees - previous_employees) /
                                                      previous_employees * 100)

            # Efficiency change (revenue per employee)
            current_efficiency = current_revenue / current_employees if current_employees > 0 else 0
            previous_efficiency = previous_revenue / previous_employees if previous_employees > 0 else 0

            if previous_efficiency > 0:
                comparison['efficiency_change'] = ((current_efficiency - previous_efficiency) /
                                                  previous_efficiency * 100)

            logger.debug(f"Period comparison calculated: {len(comparison)} metrics")
            return comparison

        except Exception as e:
            logger.error(f"Error calculating period comparison: {e}")
            return {}

    def generate_trend_analysis(self, time_series_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate trend analysis for commission data over time.

        Args:
            time_series_data: List of time-series commission data

        Returns:
            Dictionary with trend analysis results
        """
        try:
            if len(time_series_data) < 2:
                return {
                    'trend_direction': 'insufficient_data',
                    'volatility': 0,
                    'growth_rate': 0,
                    'seasonal_pattern': None
                }

            # Extract values
            values = [float(item.get('total_commission', 0)) for item in time_series_data]

            # Calculate trend direction using linear regression slope
            x = np.arange(len(values))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)

            trend_direction = 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable'

            # Calculate volatility (coefficient of variation)
            mean_value = np.mean(values)
            std_value = np.std(values)
            volatility = (std_value / mean_value * 100) if mean_value > 0 else 0

            # Calculate compound growth rate
            if len(values) > 1 and values[0] > 0:
                periods = len(values) - 1
                growth_rate = ((values[-1] / values[0]) ** (1/periods) - 1) * 100
            else:
                growth_rate = 0

            # Simple seasonal pattern detection (for monthly data)
            seasonal_pattern = None
            if len(values) >= 12:
                # Group by month position and calculate averages
                monthly_avgs = []
                for month in range(12):
                    month_values = [values[i] for i in range(month, len(values), 12)]
                    if month_values:
                        monthly_avgs.append(np.mean(month_values))

                if len(monthly_avgs) == 12:
                    peak_month = monthly_avgs.index(max(monthly_avgs)) + 1
                    low_month = monthly_avgs.index(min(monthly_avgs)) + 1
                    seasonal_pattern = {
                        'peak_month': peak_month,
                        'low_month': low_month,
                        'seasonality_strength': (max(monthly_avgs) - min(monthly_avgs)) / np.mean(monthly_avgs) * 100
                    }

            logger.info(f"Trend analysis: {trend_direction} trend, {volatility:.1f}% volatility")

            return {
                'trend_direction': trend_direction,
                'slope': slope,
                'r_squared': r_value ** 2,
                'volatility': volatility,
                'growth_rate': growth_rate,
                'seasonal_pattern': seasonal_pattern
            }

        except Exception as e:
            logger.error(f"Error generating trend analysis: {e}")
            return {
                'trend_direction': 'error',
                'volatility': 0,
                'growth_rate': 0,
                'seasonal_pattern': None,
                'error': str(e)
            }
