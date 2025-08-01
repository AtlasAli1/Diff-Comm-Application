from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd
import numpy as np
from loguru import logger
from .employee import Employee
from .business_unit import BusinessUnit, Commission, CommissionSplit

# Try to import notifications, but don't fail if not available
try:
    from utils.notifications import notify_commission_calculated
except ImportError:
    notify_commission_calculated = None

class CommissionCalculator:
    """Enhanced commission calculator with audit trails and advanced features"""
    
    def __init__(self):
        self.employees: Dict[str, Employee] = {}
        self.business_units: Dict[str, BusinessUnit] = {}
        self.commissions: List[Commission] = []
        self.commission_splits: Dict[str, CommissionSplit] = {}
        self.audit_log: List[Dict[str, Any]] = []
        self.timesheet_data: Optional[pd.DataFrame] = None
        self.revenue_data: Optional[pd.DataFrame] = None
        self.calculation_cache: Dict[str, Any] = {}
        self.period_start: Optional[datetime] = None
        self.period_end: Optional[datetime] = None
        
    def log_action(self, action: str, details: Dict[str, Any]) -> None:
        """Log actions for audit trail"""
        log_entry = {
            'timestamp': datetime.now(),
            'action': action,
            'details': details,
            'user': details.get('user', 'system')
        }
        self.audit_log.append(log_entry)
        logger.info(f"Action logged: {action} - {details}")
    
    def add_employee(self, employee: Employee) -> None:
        """Add or update employee with validation"""
        if employee.id in self.employees:
            self.log_action('update_employee', {'employee_id': employee.id, 'name': employee.name})
        else:
            self.log_action('add_employee', {'employee_id': employee.id, 'name': employee.name})
        self.employees[employee.id] = employee
        self.clear_cache()
    
    def add_business_unit(self, unit: BusinessUnit) -> None:
        """Add or update business unit"""
        if unit.id in self.business_units:
            self.log_action('update_business_unit', {'unit_id': unit.id, 'name': unit.name})
        else:
            self.log_action('add_business_unit', {'unit_id': unit.id, 'name': unit.name})
        self.business_units[unit.id] = unit
        self.clear_cache()
    
    def import_timesheet_data(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Import timesheet data with validation"""
        errors = []
        
        # Validate required columns
        required_cols = ['Employee Name', 'Regular Hours', 'OT Hours', 'DT Hours']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            errors.append(f"Missing required columns: {', '.join(missing_cols)}")
            return False, errors
        
        # Clean and validate data
        try:
            df = df.copy()
            df['Employee Name'] = df['Employee Name'].astype(str).str.strip()
            
            # Convert hours to Decimal
            for col in ['Regular Hours', 'OT Hours', 'DT Hours']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                df[col] = df[col].apply(lambda x: Decimal(str(x)))
            
            # Process each row
            for _, row in df.iterrows():
                emp_name = row['Employee Name']
                if pd.isna(emp_name) or emp_name == '':
                    continue
                
                # Find or create employee
                employee = self.find_employee_by_name(emp_name)
                if not employee:
                    employee = Employee(name=emp_name)
                    self.add_employee(employee)
                
                # Update hours
                employee.update_hours(
                    regular=row['Regular Hours'],
                    ot=row['OT Hours'],
                    dt=row['DT Hours']
                )
            
            self.timesheet_data = df
            self.log_action('import_timesheet', {'rows': len(df), 'timestamp': datetime.now()})
            return True, []
            
        except Exception as e:
            errors.append(f"Error processing timesheet: {str(e)}")
            logger.error(f"Timesheet import error: {e}")
            return False, errors
    
    def import_revenue_data(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Import revenue data with validation"""
        errors = []
        
        # Validate required columns
        if 'Revenue' not in df.columns:
            errors.append("Missing 'Revenue' column")
            return False, errors
        
        try:
            df = df.copy()
            
            # Convert revenue to Decimal
            df['Revenue'] = pd.to_numeric(df['Revenue'], errors='coerce').fillna(0)
            df['Revenue'] = df['Revenue'].apply(lambda x: Decimal(str(x)))
            
            # Extract business units
            if 'Business Unit' in df.columns:
                df['Business Unit'] = df['Business Unit'].astype(str).str.strip()
            else:
                # Try to infer from other columns
                df['Business Unit'] = 'Unassigned'
            
            # Process each business unit
            unit_revenues = df.groupby('Business Unit')['Revenue'].sum()
            
            for unit_name, revenue in unit_revenues.items():
                if pd.isna(unit_name) or unit_name == '' or unit_name == 'nan':
                    unit_name = 'Unassigned'
                
                # Find or create business unit
                unit = self.find_business_unit_by_name(unit_name)
                if not unit:
                    unit = BusinessUnit(name=unit_name)
                    self.add_business_unit(unit)
                
                unit.revenue = revenue
            
            self.revenue_data = df
            self.log_action('import_revenue', {'rows': len(df), 'timestamp': datetime.now()})
            return True, []
            
        except Exception as e:
            errors.append(f"Error processing revenue: {str(e)}")
            logger.error(f"Revenue import error: {e}")
            return False, errors
    
    def find_employee_by_name(self, name: str) -> Optional[Employee]:
        """Find employee by name (case-insensitive)"""
        name_lower = name.lower().strip()
        for employee in self.employees.values():
            if employee.name.lower() == name_lower:
                return employee
        return None
    
    def find_business_unit_by_name(self, name: str) -> Optional[BusinessUnit]:
        """Find business unit by name (case-insensitive)"""
        name_lower = name.lower().strip()
        for unit in self.business_units.values():
            if unit.name.lower() == name_lower:
                return unit
        return None
    
    def calculate_commissions(self, period_start: datetime, period_end: datetime) -> List[Commission]:
        """Calculate commissions for all employees and business units"""
        self.period_start = period_start
        self.period_end = period_end
        self.commissions.clear()
        
        # Calculate total commission pool for each business unit
        for unit in self.business_units.values():
            if unit.revenue <= 0:
                continue
            
            commission_pool = unit.commission_amount
            
            # Get active employees with hours
            active_employees = [
                emp for emp in self.employees.values() 
                if emp.is_active and emp.total_hours > 0
            ]
            
            if not active_employees:
                continue
            
            # Calculate total labor cost for distribution
            total_labor = sum(emp.total_labor_cost for emp in active_employees)
            
            # Distribute commission based on labor contribution
            for employee in active_employees:
                if total_labor > 0:
                    labor_percentage = employee.total_labor_cost / total_labor
                    commission_amount = commission_pool * labor_percentage
                else:
                    # Equal distribution if no labor costs
                    commission_amount = commission_pool / Decimal(len(active_employees))
                
                # Check for manual splits
                split_percentage = self.get_manual_split_percentage(employee.id, unit.id)
                
                commission = Commission(
                    employee_id=employee.id,
                    business_unit_id=unit.id,
                    amount=commission_amount,
                    percentage=split_percentage,
                    period_start=period_start,
                    period_end=period_end
                )
                
                self.commissions.append(commission)
                
                # Send notification if available
                if notify_commission_calculated and commission_amount > 0:
                    notify_commission_calculated(
                        employee_name=employee.name,
                        amount=float(commission_amount),
                        period=f"{period_start.date()} to {period_end.date()}"
                    )
        
        self.log_action('calculate_commissions', {
            'period_start': period_start,
            'period_end': period_end,
            'total_commissions': len(self.commissions)
        })
        
        return self.commissions
    
    def get_manual_split_percentage(self, employee_id: str, business_unit_id: str) -> Decimal:
        """Get manual split percentage if exists"""
        for split in self.commission_splits.values():
            if employee_id in split.employee_splits:
                return split.employee_splits[employee_id]
        return Decimal('100')  # Default to 100% if no split
    
    def get_employee_summary(self, employee_id: str) -> Dict[str, Any]:
        """Get comprehensive employee summary"""
        employee = self.employees.get(employee_id)
        if not employee:
            return {}
        
        employee_commissions = [
            c for c in self.commissions if c.employee_id == employee_id
        ]
        
        total_commission = sum(c.adjusted_amount for c in employee_commissions)
        
        return {
            'employee': employee.to_dict(),
            'total_hours': float(employee.total_hours),
            'labor_cost': float(employee.total_labor_cost),
            'total_commission': float(total_commission),
            'total_earnings': float(employee.total_labor_cost + total_commission),
            'commissions_by_unit': [
                {
                    'business_unit': self.business_units[c.business_unit_id].name,
                    'amount': float(c.adjusted_amount)
                }
                for c in employee_commissions
            ]
        }
    
    def get_business_unit_summary(self, unit_id: str) -> Dict[str, Any]:
        """Get comprehensive business unit summary"""
        unit = self.business_units.get(unit_id)
        if not unit:
            return {}
        
        unit_commissions = [
            c for c in self.commissions if c.business_unit_id == unit_id
        ]
        
        total_commission = sum(c.adjusted_amount for c in unit_commissions)
        
        return {
            'business_unit': unit.to_dict(),
            'revenue': float(unit.revenue),
            'commission_rate': float(unit.commission_rate),
            'total_commission': float(total_commission),
            'profit_after_commission': float(unit.revenue - total_commission),
            'employees_paid': len(set(c.employee_id for c in unit_commissions)),
            'commission_breakdown': [
                {
                    'employee': self.employees[c.employee_id].name,
                    'amount': float(c.adjusted_amount)
                }
                for c in unit_commissions
            ]
        }
    
    def get_analytics_data(self) -> Dict[str, Any]:
        """Get comprehensive analytics data"""
        total_revenue = sum(unit.revenue for unit in self.business_units.values())
        total_labor = sum(emp.total_labor_cost for emp in self.employees.values())
        total_commissions = sum(c.adjusted_amount for c in self.commissions)
        
        return {
            'kpis': {
                'total_revenue': float(total_revenue),
                'total_labor_cost': float(total_labor),
                'total_commissions': float(total_commissions),
                'gross_profit': float(total_revenue - total_labor - total_commissions),
                'profit_margin': float((total_revenue - total_labor - total_commissions) / total_revenue * 100) if total_revenue > 0 else 0
            },
            'employees': len(self.employees),
            'business_units': len(self.business_units),
            'active_commissions': len([c for c in self.commissions if c.status == 'pending']),
            'period': {
                'start': self.period_start.isoformat() if self.period_start else None,
                'end': self.period_end.isoformat() if self.period_end else None
            }
        }
    
    def clear_cache(self) -> None:
        """Clear calculation cache"""
        self.calculation_cache.clear()
    
    def export_to_dict(self) -> Dict[str, Any]:
        """Export all data to dictionary"""
        return {
            'employees': {id: emp.to_dict() for id, emp in self.employees.items()},
            'business_units': {id: unit.to_dict() for id, unit in self.business_units.items()},
            'commissions': [c.to_dict() for c in self.commissions],
            'commission_splits': {id: split.dict() for id, split in self.commission_splits.items()},
            'audit_log': self.audit_log[-100:],  # Last 100 entries
            'analytics': self.get_analytics_data(),
            'export_timestamp': datetime.now().isoformat()
        }