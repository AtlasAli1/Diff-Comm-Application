import pandas as pd
import json
import csv
from datetime import datetime
from typing import Dict, List, Any, Optional
import io
from pathlib import Path
import xlsxwriter
from loguru import logger

class ExportManager:
    """Handle various export formats for commission data"""
    
    def __init__(self):
        self.brand_colors = {
            'primary': '#2C5F75',
            'secondary': '#922B3E',
            'success': '#28a745',
            'warning': '#ffc107',
            'info': '#17a2b8'
        }
    
    def export_to_csv(self, data: List[Dict[str, Any]], filename: str = None) -> str:
        """Export data to CSV format"""
        if not data:
            return ""
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        
        return output.getvalue()
    
    def export_to_json(self, data: Any, pretty: bool = True) -> str:
        """Export data to JSON format"""
        return json.dumps(data, indent=2 if pretty else None, default=str)
    
    def export_to_excel(self, datasets: Dict[str, pd.DataFrame], 
                       filename: str = "commission_report.xlsx") -> bytes:
        """Export multiple datasets to Excel with formatting"""
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            # Define formats
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': self.brand_colors['primary'],
                'font_color': 'white',
                'border': 1
            })
            
            currency_format = workbook.add_format({
                'num_format': '$#,##0.00',
                'border': 1
            })
            
            percent_format = workbook.add_format({
                'num_format': '0.00%',
                'border': 1
            })
            
            date_format = workbook.add_format({
                'num_format': 'yyyy-mm-dd',
                'border': 1
            })
            
            # Write each dataset
            for sheet_name, df in datasets.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                worksheet = writer.sheets[sheet_name]
                
                # Format headers
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Auto-fit columns
                for idx, col in enumerate(df.columns):
                    series = df[col]
                    max_len = max(
                        series.astype(str).map(len).max(),
                        len(str(series.name))
                    ) + 2
                    worksheet.set_column(idx, idx, max_len)
                
                # Apply number formats
                for idx, col in enumerate(df.columns):
                    if 'amount' in col.lower() or 'cost' in col.lower() or 'revenue' in col.lower():
                        worksheet.set_column(idx, idx, 15, currency_format)
                    elif 'rate' in col.lower() or 'percentage' in col.lower():
                        worksheet.set_column(idx, idx, 12, percent_format)
                    elif 'date' in col.lower():
                        worksheet.set_column(idx, idx, 12, date_format)
        
        output.seek(0)
        return output.getvalue()
    
    def generate_payroll_export(self, commission_data: List[Dict[str, Any]], 
                               period_start: str, period_end: str) -> pd.DataFrame:
        """Generate payroll-ready export"""
        payroll_data = []
        
        for item in commission_data:
            # Note helpers/apprentices should have zero commission
            is_helper = item.get('is_helper', False)
            payroll_data.append({
                'Employee ID': item.get('employee_id', ''),
                'Employee Name': item.get('employee_name', ''),
                'Pay Period Start': period_start,
                'Pay Period End': period_end,
                'Regular Hours': item.get('regular_hours', 0),
                'OT Hours': item.get('ot_hours', 0),
                'DT Hours': item.get('dt_hours', 0),
                'Hourly Rate': item.get('hourly_rate', 0),
                'Labor Cost': item.get('labor_cost', 0),
                'Commission Amount': 0 if is_helper else item.get('commission_amount', 0),
                'Total Earnings': item.get('labor_cost', 0) + (0 if is_helper else item.get('commission_amount', 0)),
                'Department': item.get('department', ''),
                'Helper/Apprentice': 'Yes' if is_helper else 'No',
                'Status': 'Approved'
            })
        
        return pd.DataFrame(payroll_data)
    
    def generate_executive_summary(self, analytics_data: Dict[str, Any]) -> str:
        """Generate executive summary report"""
        summary = f"""
# Executive Commission Summary
**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Key Performance Indicators

- **Total Revenue:** ${analytics_data['kpis']['total_revenue']:,.2f}
- **Total Labor Cost:** ${analytics_data['kpis']['total_labor_cost']:,.2f}
- **Total Commissions:** ${analytics_data['kpis']['total_commissions']:,.2f}
- **Gross Profit:** ${analytics_data['kpis']['gross_profit']:,.2f}
- **Profit Margin:** {analytics_data['kpis']['profit_margin']:.1f}%

## Summary Statistics

- **Active Employees:** {analytics_data['employees']}
- **Business Units:** {analytics_data['business_units']}
- **Pending Commissions:** {analytics_data['active_commissions']}

## Period Coverage
- **Start Date:** {analytics_data['period']['start']}
- **End Date:** {analytics_data['period']['end']}

---
*This report was automatically generated by the Commission Calculator Pro system.*
"""
        return summary
    
    def generate_employee_detail_report(self, employee_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Generate detailed employee report"""
        report_data = []
        
        for emp in employee_data:
            report_data.append({
                'Employee Name': emp['employee']['name'],
                'Employee ID': emp['employee'].get('employee_id', 'N/A'),
                'Department': emp['employee'].get('department', 'N/A'),
                'Hourly Rate': emp['employee']['hourly_rate'],
                'Regular Hours': emp['employee']['regular_hours'],
                'OT Hours': emp['employee']['ot_hours'],
                'DT Hours': emp['employee']['dt_hours'],
                'Total Hours': emp['total_hours'],
                'Labor Cost': emp['labor_cost'],
                'Commission': emp['total_commission'],
                'Total Earnings': emp['total_earnings'],
                'Status': 'Active' if emp['employee']['is_active'] else 'Inactive',
                'Helper/Apprentice': 'Yes' if emp['employee'].get('is_helper', False) else 'No'
            })
        
        return pd.DataFrame(report_data)
    
    def generate_business_unit_report(self, unit_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Generate business unit analysis report"""
        report_data = []
        
        for unit in unit_data:
            report_data.append({
                'Business Unit': unit['business_unit']['name'],
                'Category': unit['business_unit'].get('category', 'N/A'),
                'Revenue': unit['revenue'],
                'Commission Rate': unit['commission_rate'],
                'Total Commission': unit['total_commission'],
                'Profit After Commission': unit['profit_after_commission'],
                'Employees Paid': unit['employees_paid'],
                'Commission %': (unit['total_commission'] / unit['revenue'] * 100) if unit['revenue'] > 0 else 0
            })
        
        return pd.DataFrame(report_data)
    
    def generate_commission_breakdown(self, commission_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Generate detailed commission breakdown"""
        breakdown_data = []
        
        for comm in commission_data:
            breakdown_data.append({
                'Commission ID': comm['id'],
                'Employee': comm.get('employee_name', 'Unknown'),
                'Business Unit': comm.get('business_unit_name', 'Unknown'),
                'Base Amount': comm['amount'],
                'Split %': comm['percentage'],
                'Adjusted Amount': comm['adjusted_amount'],
                'Period Start': comm['period_start'],
                'Period End': comm['period_end'],
                'Status': comm['status'],
                'Approved By': comm.get('approved_by', 'N/A'),
                'Approved Date': comm.get('approved_at', 'N/A'),
                'Paid Date': comm.get('paid_at', 'N/A')
            })
        
        return pd.DataFrame(breakdown_data)
    
    def create_pdf_report(self, report_data: Dict[str, Any], filename: str = "report.pdf") -> bytes:
        """Create PDF report (placeholder for future implementation)"""
        # This would require additional libraries like reportlab or weasyprint
        # For now, return a simple text representation
        logger.warning("PDF export not yet implemented")
        return b"PDF export coming soon"