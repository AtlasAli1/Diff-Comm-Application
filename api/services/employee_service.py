"""
Employee service layer - business logic for employee management
"""

from typing import List, Optional, Tuple
from datetime import datetime
from decimal import Decimal
import pandas as pd

from ..models.employee import (
    Employee,
    EmployeeCreate, 
    EmployeeUpdate,
    EmployeeSummary,
    EmployeeStatus,
    CommissionPlan
)


class EmployeeService:
    """Service class for employee management business logic"""
    
    def __init__(self):
        # In a real application, this would be a database connection
        # For now, we'll use the existing session state integration
        pass
    
    async def get_employees(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[EmployeeStatus] = None,
        department: Optional[str] = None,
        search: Optional[str] = None
    ) -> Tuple[List[Employee], int]:
        """Get employees with filtering and pagination"""
        
        # Get employee data from session state (adapt existing logic)
        from ..adapters.session_adapter import SessionAdapter
        session = SessionAdapter()
        
        employee_df = session.get_employee_data()
        if employee_df.empty:
            return [], 0
        
        # Apply filters
        filtered_df = employee_df.copy()
        
        if status:
            filtered_df = filtered_df[filtered_df['Status'] == status.value]
        
        if department:
            filtered_df = filtered_df[
                filtered_df['Department'].str.contains(department, case=False, na=False)
            ]
        
        if search:
            # Search in name and employee_id
            name_match = filtered_df['Name'].str.contains(search, case=False, na=False)
            id_match = filtered_df.get('Employee ID', pd.Series()).str.contains(search, case=False, na=False)
            filtered_df = filtered_df[name_match | id_match]
        
        total = len(filtered_df)
        
        # Apply pagination
        paginated_df = filtered_df.iloc[skip:skip + limit]
        
        # Convert to Employee models
        employees = []
        for idx, row in paginated_df.iterrows():
            employee = Employee(
                id=idx,
                employee_id=row.get('Employee ID'),
                name=row['Name'],
                department=row.get('Department'),
                hire_date=pd.to_datetime(row.get('Hire Date')).date() if pd.notna(row.get('Hire Date')) else None,
                hourly_rate=Decimal(str(row.get('Hourly Rate', 0))),
                status=EmployeeStatus(row.get('Status', EmployeeStatus.ACTIVE)),
                commission_plan=CommissionPlan(row.get('Commission Plan', CommissionPlan.HOURLY_PLUS_COMMISSION)),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            employees.append(employee)
        
        return employees, total
    
    async def get_employee_by_id(self, employee_id: int) -> Optional[Employee]:
        """Get employee by database ID"""
        
        from ..adapters.session_adapter import SessionAdapter
        session = SessionAdapter()
        
        employee_df = session.get_employee_data()
        if employee_df.empty or employee_id >= len(employee_df):
            return None
        
        try:
            row = employee_df.iloc[employee_id]
            return Employee(
                id=employee_id,
                employee_id=row.get('Employee ID'),
                name=row['Name'],
                department=row.get('Department'),
                hire_date=pd.to_datetime(row.get('Hire Date')).date() if pd.notna(row.get('Hire Date')) else None,
                hourly_rate=Decimal(str(row.get('Hourly Rate', 0))),
                status=EmployeeStatus(row.get('Status', EmployeeStatus.ACTIVE)),
                commission_plan=CommissionPlan(row.get('Commission Plan', CommissionPlan.HOURLY_PLUS_COMMISSION)),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        except IndexError:
            return None
    
    async def get_employee_by_employee_id(self, employee_id: str) -> Optional[Employee]:
        """Get employee by employee ID string"""
        
        from ..adapters.session_adapter import SessionAdapter
        session = SessionAdapter()
        
        employee_df = session.get_employee_data()
        if employee_df.empty or 'Employee ID' not in employee_df.columns:
            return None
        
        matching_rows = employee_df[employee_df['Employee ID'] == employee_id]
        if matching_rows.empty:
            return None
        
        row = matching_rows.iloc[0]
        db_id = matching_rows.index[0]
        
        return Employee(
            id=db_id,
            employee_id=row.get('Employee ID'),
            name=row['Name'],
            department=row.get('Department'),
            hire_date=pd.to_datetime(row.get('Hire Date')).date() if pd.notna(row.get('Hire Date')) else None,
            hourly_rate=Decimal(str(row.get('Hourly Rate', 0))),
            status=EmployeeStatus(row.get('Status', EmployeeStatus.ACTIVE)),
            commission_plan=CommissionPlan(row.get('Commission Plan', CommissionPlan.HOURLY_PLUS_COMMISSION)),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    async def create_employee(self, employee_data: EmployeeCreate) -> Employee:
        """Create a new employee"""
        
        from ..adapters.session_adapter import SessionAdapter
        session = SessionAdapter()
        
        # Convert to DataFrame row
        new_employee_data = {
            'Employee ID': employee_data.employee_id,
            'Name': employee_data.name,
            'Department': employee_data.department,
            'Hire Date': employee_data.hire_date,
            'Hourly Rate': float(employee_data.hourly_rate),
            'Status': employee_data.status.value,
            'Commission Plan': employee_data.commission_plan.value
        }
        
        employee_id = session.add_employee(new_employee_data)
        
        return Employee(
            id=employee_id,
            employee_id=employee_data.employee_id,
            name=employee_data.name,
            department=employee_data.department,
            hire_date=employee_data.hire_date,
            hourly_rate=employee_data.hourly_rate,
            status=employee_data.status,
            commission_plan=employee_data.commission_plan,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    async def update_employee(self, employee_id: int, employee_data: EmployeeUpdate) -> Employee:
        """Update an existing employee"""
        
        from ..adapters.session_adapter import SessionAdapter
        session = SessionAdapter()
        
        # Get current employee data
        current = await self.get_employee_by_id(employee_id)
        if not current:
            raise ValueError(f"Employee with ID {employee_id} not found")
        
        # Prepare update data (only include non-None values)
        update_data = {}
        if employee_data.employee_id is not None:
            update_data['Employee ID'] = employee_data.employee_id
        if employee_data.name is not None:
            update_data['Name'] = employee_data.name
        if employee_data.department is not None:
            update_data['Department'] = employee_data.department
        if employee_data.hire_date is not None:
            update_data['Hire Date'] = employee_data.hire_date
        if employee_data.hourly_rate is not None:
            update_data['Hourly Rate'] = float(employee_data.hourly_rate)
        if employee_data.status is not None:
            update_data['Status'] = employee_data.status.value
        if employee_data.commission_plan is not None:
            update_data['Commission Plan'] = employee_data.commission_plan.value
        
        session.update_employee(employee_id, update_data)
        
        # Return updated employee
        return await self.get_employee_by_id(employee_id)
    
    async def delete_employee(self, employee_id: int):
        """Delete an employee"""
        
        from ..adapters.session_adapter import SessionAdapter
        session = SessionAdapter()
        
        session.delete_employee(employee_id)
    
    async def get_employee_summary(self) -> EmployeeSummary:
        """Get employee summary statistics"""
        
        from ..adapters.session_adapter import SessionAdapter
        session = SessionAdapter()
        
        employee_df = session.get_employee_data()
        if employee_df.empty:
            return EmployeeSummary(
                total_employees=0,
                active_employees=0,
                inactive_employees=0,
                helper_apprentice_employees=0,
                excluded_employees=0,
                avg_hourly_rate=Decimal('0.00'),
                efficiency_pay_count=0,
                hourly_plus_commission_count=0
            )
        
        # Count by status
        status_counts = employee_df['Status'].value_counts()
        
        # Count by commission plan
        plan_counts = employee_df.get('Commission Plan', pd.Series()).value_counts()
        
        # Calculate average hourly rate
        hourly_rates = pd.to_numeric(employee_df.get('Hourly Rate', 0), errors='coerce')
        avg_rate = hourly_rates.mean() if not hourly_rates.empty else 0
        
        return EmployeeSummary(
            total_employees=len(employee_df),
            active_employees=status_counts.get(EmployeeStatus.ACTIVE.value, 0),
            inactive_employees=status_counts.get(EmployeeStatus.INACTIVE.value, 0),
            helper_apprentice_employees=status_counts.get(EmployeeStatus.HELPER_APPRENTICE.value, 0),
            excluded_employees=status_counts.get(EmployeeStatus.EXCLUDED_FROM_PAYROLL.value, 0),
            avg_hourly_rate=Decimal(str(avg_rate)).quantize(Decimal('0.01')),
            efficiency_pay_count=plan_counts.get(CommissionPlan.EFFICIENCY_PAY.value, 0),
            hourly_plus_commission_count=plan_counts.get(CommissionPlan.HOURLY_PLUS_COMMISSION.value, 0)
        )
    
    async def create_employees_bulk(self, employees_data: List[EmployeeCreate]) -> List[Employee]:
        """Create multiple employees at once"""
        
        created_employees = []
        for employee_data in employees_data:
            employee = await self.create_employee(employee_data)
            created_employees.append(employee)
        
        return created_employees