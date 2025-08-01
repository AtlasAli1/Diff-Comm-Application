"""
Enhanced Timesheet Processing for Multiple Formats
"""
import pandas as pd
import numpy as np
import re
from decimal import Decimal
from typing import Dict, List, Tuple, Any, Optional
import streamlit as st

class TimesheetProcessor:
    """Enhanced timesheet processor supporting multiple formats"""
    
    def __init__(self):
        self.supported_formats = {
            'format_1': 'Individual entries to be totaled by employee',
            'format_2': 'Employee totals sheet with time format conversion'
        }
    
    def detect_format(self, df: pd.DataFrame, sheet_names: List[str] = None) -> str:
        """Detect which timesheet format is being used"""
        
        # Check for employee totals sheet (Format 2)
        if sheet_names:
            total_sheets = [s for s in sheet_names if 'total' in s.lower() or 'summary' in s.lower()]
            if total_sheets:
                return 'format_2'
        
        # Check for time format columns (HH:MM:SS format indicates Format 2)
        for col in df.columns:
            if any(keyword in str(col).lower() for keyword in ['regular', 'overtime', 'double']):
                # Sample some values to check format
                sample_values = df[col].dropna().head(5)
                for val in sample_values:
                    val_str = str(val)
                    if ':' in val_str and len(val_str.split(':')) >= 2:
                        return 'format_2'  # Time format detected
        
        # Check column patterns for Format 1
        cols = [str(col).lower() for col in df.columns]
        if any('employee' in col for col in cols) and any('hours' in col for col in cols):
            # Check if data needs aggregation (multiple rows per employee)
            if 'employee' in ' '.join(cols):
                employee_col = [col for col in df.columns if 'employee' in str(col).lower()][0]
                if len(df[employee_col].unique()) < len(df):
                    return 'format_1'  # Multiple rows per employee
        
        return 'format_1'  # Default
    
    def convert_time_to_decimal(self, time_value: Any) -> Decimal:
        """Convert various time formats to decimal hours"""
        
        if pd.isna(time_value) or time_value == '' or time_value is None:
            return Decimal('0.00')
        
        # Handle datetime.time objects
        if hasattr(time_value, 'hour') and hasattr(time_value, 'minute'):
            hours = time_value.hour
            minutes = time_value.minute
            decimal_hours = hours + (minutes / 60.0)
            return Decimal(str(decimal_hours)).quantize(Decimal('0.01'))
        
        # Handle datetime.datetime objects (extract time part)
        if hasattr(time_value, 'time'):
            time_part = time_value.time()
            hours = time_part.hour
            minutes = time_part.minute
            decimal_hours = hours + (minutes / 60.0)
            return Decimal(str(decimal_hours)).quantize(Decimal('0.01'))
        
        time_str = str(time_value).strip()
        
        # If already decimal, return as is
        try:
            return Decimal(str(float(time_str))).quantize(Decimal('0.01'))
        except (ValueError, TypeError):
            pass
        
        # Handle HH:MM format
        if ':' in time_str:
            try:
                parts = time_str.split(':')
                hours = int(parts[0])
                minutes = int(parts[1]) if len(parts) > 1 else 0
                decimal_hours = hours + (minutes / 60.0)
                return Decimal(str(decimal_hours)).quantize(Decimal('0.01'))
            except (ValueError, IndexError):
                pass
        
        # Handle "X hours Y minutes" format
        hour_match = re.search(r'(\d+)\s*h', time_str.lower())
        min_match = re.search(r'(\d+)\s*m', time_str.lower())
        
        hours = int(hour_match.group(1)) if hour_match else 0
        minutes = int(min_match.group(1)) if min_match else 0
        
        if hours > 0 or minutes > 0:
            decimal_hours = hours + (minutes / 60.0)
            return Decimal(str(decimal_hours)).quantize(Decimal('0.01'))
        
        # Try to extract just numbers
        number_match = re.search(r'(\d+\.?\d*)', time_str)
        if number_match:
            return Decimal(number_match.group(1)).quantize(Decimal('0.01'))
        
        return Decimal('0.00')
    
    def process_format_1(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process Format 1: Individual entries that need totaling by employee"""
        
        # Find employee column
        employee_cols = [col for col in df.columns if 'employee' in str(col).lower()]
        if not employee_cols:
            raise ValueError("No employee column found")
        
        employee_col = employee_cols[0]
        
        # Find hour columns
        hour_columns = {}
        for col in df.columns:
            col_lower = str(col).lower()
            if ('regular' in col_lower or 'reg' in col_lower) and 'hour' in col_lower:
                hour_columns['regular'] = col
            elif 'ot' in col_lower or 'overtime' in col_lower:
                hour_columns['ot'] = col
            elif 'dt' in col_lower or 'double' in col_lower:
                hour_columns['dt'] = col
        
        if not hour_columns:
            # Try generic hour columns
            for col in df.columns:
                if 'hour' in str(col).lower():
                    if 'regular' not in hour_columns:
                        hour_columns['regular'] = col
                    elif 'ot' not in hour_columns:
                        hour_columns['ot'] = col
                    elif 'dt' not in hour_columns:
                        hour_columns['dt'] = col
        
        # Group by employee and sum hours
        result_data = []
        
        for employee in df[employee_col].unique():
            if pd.isna(employee):
                continue
                
            employee_data = df[df[employee_col] == employee]
            
            totals = {
                'Employee Name': employee,
                'Regular Hours': Decimal('0.00'),
                'OT Hours': Decimal('0.00'),
                'DT Hours': Decimal('0.00')
            }
            
            # Sum hours for this employee
            for _, row in employee_data.iterrows():
                if 'regular' in hour_columns:
                    totals['Regular Hours'] += self.convert_time_to_decimal(row[hour_columns['regular']])
                if 'ot' in hour_columns:
                    totals['OT Hours'] += self.convert_time_to_decimal(row[hour_columns['ot']])
                if 'dt' in hour_columns:
                    totals['DT Hours'] += self.convert_time_to_decimal(row[hour_columns['dt']])
            
            # Calculate total hours
            totals['Total Hours'] = totals['Regular Hours'] + totals['OT Hours'] + totals['DT Hours']
            
            result_data.append(totals)
        
        return pd.DataFrame(result_data)
    
    def process_format_2(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process Format 2: Employee totals sheet with time conversion"""
        
        # Find employee column
        employee_cols = [col for col in df.columns if 'employee' in str(col).lower() and 'id' not in str(col).lower()]
        if not employee_cols:
            # Try name columns
            employee_cols = [col for col in df.columns if 'name' in str(col).lower()]
        if not employee_cols:
            raise ValueError("No employee column found")
        
        employee_col = employee_cols[0]
        
        # Find hour columns (order matters - check specific patterns first)
        hour_columns = {}
        for col in df.columns:
            col_lower = str(col).lower().strip()
            if 'regular' in col_lower and 'hour' not in col_lower:
                hour_columns['regular'] = col
            elif col_lower == 'overtime' or 'overtime' in col_lower:
                hour_columns['ot'] = col
            elif 'double' in col_lower and 'ot' in col_lower:
                hour_columns['dt'] = col
            elif col_lower == 'dt hours' or col_lower == 'dt':
                hour_columns['dt'] = col
        
        # Convert data
        result_data = []
        
        for _, row in df.iterrows():
            if pd.isna(row[employee_col]):
                continue
                
            employee_data = {
                'Employee Name': row[employee_col],
                'Regular Hours': Decimal('0.00'),
                'OT Hours': Decimal('0.00'),
                'DT Hours': Decimal('0.00')
            }
            
            # Convert time formats to decimal
            if 'regular' in hour_columns:
                employee_data['Regular Hours'] = self.convert_time_to_decimal(row[hour_columns['regular']])
            if 'ot' in hour_columns:
                employee_data['OT Hours'] = self.convert_time_to_decimal(row[hour_columns['ot']])
            if 'dt' in hour_columns:
                employee_data['DT Hours'] = self.convert_time_to_decimal(row[hour_columns['dt']])
            
            # Calculate total
            employee_data['Total Hours'] = (
                employee_data['Regular Hours'] + 
                employee_data['OT Hours'] + 
                employee_data['DT Hours']
            )
            
            result_data.append(employee_data)
        
        return pd.DataFrame(result_data)
    
    def process_timesheet(self, file_data, filename: str = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Main processing function that handles both formats"""
        
        try:
            # Read Excel file
            if filename and filename.endswith('.csv'):
                df = pd.read_csv(file_data)
                sheet_names = None
            else:
                # Read all sheets to detect format
                all_sheets = pd.read_excel(file_data, sheet_name=None)
                sheet_names = list(all_sheets.keys())
                
                # Look for employee totals sheet first
                totals_sheet = None
                for sheet_name in sheet_names:
                    if 'total' in sheet_name.lower() and 'employee' in sheet_name.lower():
                        totals_sheet = sheet_name
                        break
                
                # If no employee totals found, look for any totals sheet
                if not totals_sheet:
                    for sheet_name in sheet_names:
                        if 'total' in sheet_name.lower():
                            totals_sheet = sheet_name
                            break
                
                # Use totals sheet if found, otherwise use first sheet
                df = all_sheets[totals_sheet] if totals_sheet else all_sheets[sheet_names[0]]
            
            # Detect format
            format_type = self.detect_format(df, sheet_names)
            
            # Process based on format
            if format_type == 'format_2':
                processed_df = self.process_format_2(df)
            else:
                processed_df = self.process_format_1(df)
            
            # Create summary
            summary = {
                'format_detected': format_type,
                'total_employees': len(processed_df),
                'total_regular_hours': processed_df['Regular Hours'].sum(),
                'total_ot_hours': processed_df['OT Hours'].sum(),
                'total_dt_hours': processed_df['DT Hours'].sum(),
                'total_hours': processed_df['Total Hours'].sum(),
                'sheets_processed': sheet_names if sheet_names else ['CSV']
            }
            
            return processed_df, summary
            
        except Exception as e:
            st.error(f"Error processing timesheet: {str(e)}")
            raise
    
    def display_processing_results(self, df: pd.DataFrame, summary: Dict[str, Any], use_expander: bool = False):
        """Display processing results in Streamlit"""
        
        if use_expander:
            st.success(f"✅ Processed successfully using {summary['format_detected']}")
        else:
            st.success(f"✅ Timesheet processed successfully using {summary['format_detected']}")
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Employees", summary['total_employees'])
        with col2:
            st.metric("Regular Hours", f"{summary['total_regular_hours']:.2f}")
        with col3:
            st.metric("OT Hours", f"{summary['total_ot_hours']:.2f}")
        with col4:
            st.metric("DT Hours", f"{summary['total_dt_hours']:.2f}")
        
        # Show processed data (compact version if in expander)
        if use_expander:
            st.write("**📊 Employee Hours Sample:**")
            # Show only top 5 employees
            display_df = df.head(5).copy()
        else:
            st.subheader("📊 Processed Employee Hours")
            display_df = df.copy()
        
        # Format for display
        for col in ['Regular Hours', 'OT Hours', 'DT Hours', 'Total Hours']:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: f"{float(x):.2f}")
        
        st.dataframe(display_df, use_container_width=True)
        
        # Processing details (only if not in expander to avoid nesting)
        if not use_expander:
            with st.expander("🔍 Processing Details"):
                st.write(f"**Format Detected:** {summary['format_detected']}")
                st.write(f"**Sheets Processed:** {', '.join(summary['sheets_processed'])}")
                st.write(f"**Total Hours:** {summary['total_hours']:.2f}")
        else:
            st.write(f"**Format:** {summary['format_detected']} | **Total Hours:** {summary['total_hours']:.2f}")