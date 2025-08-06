"""
Employee-related Pydantic models
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum
from decimal import Decimal

from .common import BaseResponse


class EmployeeStatus(str, Enum):
    """Employee status options"""
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    HELPER_APPRENTICE = "Helper/Apprentice"  
    EXCLUDED_FROM_PAYROLL = "Excluded from Payroll"


class CommissionPlan(str, Enum):
    """Commission plan options"""
    HOURLY_PLUS_COMMISSION = "Hourly + Commission"
    EFFICIENCY_PAY = "Efficiency Pay"


class EmployeeBase(BaseModel):
    """Base employee model with common fields"""
    employee_id: Optional[str] = Field(None, description="Employee ID/Number")
    name: str = Field(..., min_length=1, max_length=100, description="Full employee name")
    department: Optional[str] = Field(None, max_length=50, description="Department name")
    hire_date: Optional[date] = Field(None, description="Employee hire date")
    hourly_rate: Decimal = Field(..., ge=0, description="Hourly pay rate")
    status: EmployeeStatus = Field(EmployeeStatus.ACTIVE, description="Employee status")
    commission_plan: CommissionPlan = Field(
        CommissionPlan.HOURLY_PLUS_COMMISSION, 
        description="Commission calculation method"
    )

    @validator('hourly_rate', pre=True)
    def validate_hourly_rate(cls, v):
        """Convert to Decimal and validate"""
        try:
            return Decimal(str(v))
        except (ValueError, TypeError):
            raise ValueError("Hourly rate must be a valid number")

    class Config:
        use_enum_values = True


class EmployeeCreate(EmployeeBase):
    """Model for creating new employees"""
    pass


class EmployeeUpdate(BaseModel):
    """Model for updating existing employees"""
    employee_id: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    department: Optional[str] = Field(None, max_length=50)
    hire_date: Optional[date] = None
    hourly_rate: Optional[Decimal] = Field(None, ge=0)
    status: Optional[EmployeeStatus] = None
    commission_plan: Optional[CommissionPlan] = None

    @validator('hourly_rate', pre=True)
    def validate_hourly_rate(cls, v):
        if v is None:
            return v
        try:
            return Decimal(str(v))
        except (ValueError, TypeError):
            raise ValueError("Hourly rate must be a valid number")

    class Config:
        use_enum_values = True


class Employee(EmployeeBase):
    """Full employee model with database fields"""
    id: int = Field(..., description="Database primary key")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True
        use_enum_values = True


class EmployeeResponse(BaseResponse):
    """Response model for employee operations"""
    data: Employee


class EmployeeListResponse(BaseResponse):
    """Response model for employee list operations"""
    data: List[Employee]
    total: int = Field(description="Total number of employees")


class EmployeeSummary(BaseModel):
    """Employee summary statistics"""
    total_employees: int
    active_employees: int
    inactive_employees: int
    helper_apprentice_employees: int
    excluded_employees: int
    avg_hourly_rate: Decimal
    efficiency_pay_count: int
    hourly_plus_commission_count: int


class EmployeeSummaryResponse(BaseResponse):
    """Response model for employee summary"""
    data: EmployeeSummary