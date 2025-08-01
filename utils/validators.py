import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal
from loguru import logger

class DataValidator:
    """Validate and clean data imports"""
    
    @staticmethod
    def validate_timesheet_data(df: pd.DataFrame) -> Tuple[bool, List[str], pd.DataFrame]:
        """Validate timesheet data format and content"""
        errors = []
        warnings = []
        
        # Check if DataFrame is empty
        if df.empty:
            errors.append("Timesheet data is empty")
            return False, errors, df
        
        # Required columns
        required_columns = ['Employee Name', 'Regular Hours', 'OT Hours', 'DT Hours']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            errors.append(f"Missing required columns: {', '.join(missing_columns)}")
            return False, errors, df
        
        # Clean data
        cleaned_df = df.copy()
        
        # Clean employee names
        cleaned_df['Employee Name'] = cleaned_df['Employee Name'].astype(str).str.strip()
        cleaned_df = cleaned_df[cleaned_df['Employee Name'] != '']
        cleaned_df = cleaned_df[~cleaned_df['Employee Name'].str.lower().isin(['nan', 'none', 'null'])]
        
        # Validate and clean hours columns
        for col in ['Regular Hours', 'OT Hours', 'DT Hours']:
            # Convert to numeric
            cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce').fillna(0)
            
            # Check for negative values
            if (cleaned_df[col] < 0).any():
                errors.append(f"Negative values found in {col}")
            
            # Cap at reasonable maximum (e.g., 100 hours per period)
            if (cleaned_df[col] > 100).any():
                warnings.append(f"Very high values (>100) found in {col}")
        
        # Check for duplicate employees
        duplicates = cleaned_df[cleaned_df['Employee Name'].duplicated()]['Employee Name'].unique()
        if len(duplicates) > 0:
            warnings.append(f"Duplicate employees found: {', '.join(duplicates)}")
        
        # Additional optional columns
        optional_columns = ['Department', 'Employee ID', 'Pay Period']
        for col in optional_columns:
            if col in cleaned_df.columns:
                cleaned_df[col] = cleaned_df[col].astype(str).str.strip()
        
        # Log validation results
        logger.info(f"Timesheet validation: {len(cleaned_df)} valid rows, {len(errors)} errors, {len(warnings)} warnings")
        
        return len(errors) == 0, errors + warnings, cleaned_df
    
    @staticmethod
    def validate_revenue_data(df: pd.DataFrame) -> Tuple[bool, List[str], pd.DataFrame]:
        """Validate revenue data format and content"""
        errors = []
        warnings = []
        
        # Check if DataFrame is empty
        if df.empty:
            errors.append("Revenue data is empty")
            return False, errors, df
        
        # Check for revenue column (flexible naming)
        revenue_columns = [col for col in df.columns if 'revenue' in col.lower() or 'amount' in col.lower()]
        if not revenue_columns:
            errors.append("No revenue/amount column found")
            return False, errors, df
        
        # Use first matching column
        revenue_col = revenue_columns[0]
        
        # Clean data
        cleaned_df = df.copy()
        
        # Rename revenue column for consistency
        cleaned_df.rename(columns={revenue_col: 'Revenue'}, inplace=True)
        
        # Convert revenue to numeric
        cleaned_df['Revenue'] = pd.to_numeric(cleaned_df['Revenue'], errors='coerce').fillna(0)
        
        # Check for negative revenue
        if (cleaned_df['Revenue'] < 0).any():
            warnings.append("Negative revenue values found")
        
        # Look for business unit column
        unit_columns = [col for col in df.columns if 'unit' in col.lower() or 'business' in col.lower() or 'department' in col.lower()]
        
        if unit_columns:
            unit_col = unit_columns[0]
            cleaned_df['Business Unit'] = cleaned_df[unit_col].astype(str).str.strip()
        else:
            # Try to infer from other columns
            if 'Job' in cleaned_df.columns or 'Project' in cleaned_df.columns:
                col_name = 'Job' if 'Job' in cleaned_df.columns else 'Project'
                cleaned_df['Business Unit'] = cleaned_df[col_name].astype(str).str.strip()
            else:
                cleaned_df['Business Unit'] = 'Unassigned'
                warnings.append("No business unit column found, all revenue assigned to 'Unassigned'")
        
        # Clean business unit names
        cleaned_df['Business Unit'] = cleaned_df['Business Unit'].replace(['', 'nan', 'NaN', 'none', 'None', 'null'], 'Unassigned')
        
        # Remove rows with zero revenue
        zero_revenue_count = (cleaned_df['Revenue'] == 0).sum()
        if zero_revenue_count > 0:
            warnings.append(f"{zero_revenue_count} rows with zero revenue removed")
            cleaned_df = cleaned_df[cleaned_df['Revenue'] != 0]
        
        # Check total revenue
        total_revenue = cleaned_df['Revenue'].sum()
        if total_revenue == 0:
            errors.append("Total revenue is zero")
        
        # Log validation results
        logger.info(f"Revenue validation: {len(cleaned_df)} valid rows, ${total_revenue:,.2f} total, {len(errors)} errors, {len(warnings)} warnings")
        
        return len(errors) == 0, errors + warnings, cleaned_df
    
    @staticmethod
    def validate_commission_rates(rates: Dict[str, float]) -> Tuple[bool, List[str]]:
        """Validate commission rate configuration"""
        errors = []
        
        if not rates:
            errors.append("No commission rates configured")
            return False, errors
        
        for unit, rate in rates.items():
            if rate < 0:
                errors.append(f"Negative commission rate for {unit}")
            elif rate > 100:
                errors.append(f"Commission rate over 100% for {unit}")
            elif rate == 0:
                logger.warning(f"Zero commission rate for {unit}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_hourly_rates(employees: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate hourly rate configuration"""
        errors = []
        warnings = []
        
        if not employees:
            errors.append("No employees configured")
            return False, errors
        
        for emp_id, emp_data in employees.items():
            if isinstance(emp_data, dict):
                rate = emp_data.get('hourly_rate', 0)
                name = emp_data.get('name', 'Unknown')
            else:
                rate = getattr(emp_data, 'hourly_rate', 0)
                name = getattr(emp_data, 'name', 'Unknown')
            
            if rate <= 0:
                errors.append(f"Zero or negative hourly rate for {name}")
            elif rate < 15:  # Minimum wage check
                warnings.append(f"Low hourly rate (${rate}) for {name}")
            elif rate > 200:  # Sanity check
                warnings.append(f"Very high hourly rate (${rate}) for {name}")
        
        return len(errors) == 0, errors + warnings
    
    @staticmethod
    def validate_commission_split(splits: Dict[str, Decimal]) -> Tuple[bool, str]:
        """Validate commission split percentages"""
        if not splits:
            return False, "No splits defined"
        
        total = sum(splits.values())
        
        if abs(total - Decimal('100')) > Decimal('0.01'):
            return False, f"Splits must sum to 100%, current total: {total}%"
        
        for employee, percentage in splits.items():
            if percentage < 0:
                return False, f"Negative split percentage for {employee}"
            elif percentage > 100:
                return False, f"Split percentage over 100% for {employee}"
        
        return True, "Valid"
    
    @staticmethod
    def validate_date_range(start_date: datetime, end_date: datetime) -> Tuple[bool, str]:
        """Validate date range"""
        if start_date >= end_date:
            return False, "Start date must be before end date"
        
        # Check if range is reasonable (not more than 1 year)
        if (end_date - start_date).days > 365:
            return False, "Date range exceeds 1 year"
        
        # Check if dates are not in future
        if end_date > datetime.now():
            return False, "End date cannot be in the future"
        
        return True, "Valid"
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe file operations"""
        import re
        
        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Limit length
        if len(filename) > 200:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:200-len(ext)-1] + '.' + ext if ext else name[:200]
        
        return filename