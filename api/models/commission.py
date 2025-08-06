"""
Commission calculation-related Pydantic models
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from .common import BaseResponse


class CommissionType(str, Enum):
    """Commission calculation types"""
    LEAD_GENERATION = "Lead Generation"
    SALES = "Sales"  
    WORK_DONE = "Work Done"


class CommissionRequest(BaseModel):
    """Request model for commission calculations"""
    employee_ids: List[int] = Field(..., description="List of employee IDs to calculate for")
    start_date: date = Field(..., description="Calculation period start date")
    end_date: date = Field(..., description="Calculation period end date")
    pay_period_id: Optional[int] = Field(None, description="Specific pay period ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "employee_ids": [1, 2, 3],
                "start_date": "2024-01-01",
                "end_date": "2024-01-14", 
                "pay_period_id": 1
            }
        }


class CommissionDetail(BaseModel):
    """Individual commission calculation detail"""
    employee_id: int
    employee_name: str
    commission_type: CommissionType
    business_unit: str
    revenue_amount: Decimal
    commission_rate: Decimal
    commission_amount: Decimal
    job_number: Optional[str] = None
    
    class Config:
        use_enum_values = True


class EfficiencyPayDetail(BaseModel):
    """Efficiency pay calculation detail"""
    employee_id: int
    employee_name: str
    commission_plan: str
    regular_hours: Decimal
    ot_hours: Decimal
    dt_hours: Decimal
    total_hours: Decimal
    hourly_rate: Decimal
    hourly_pay: Decimal
    commission_total: Decimal
    efficiency_pay: Decimal
    final_pay: Decimal


class CommissionCalculation(BaseModel):
    """Complete commission calculation result"""
    employee_id: int
    employee_name: str
    period_start: date
    period_end: date
    
    # Revenue-based commissions
    lead_generation_commission: Decimal = Field(default=Decimal('0.00'))
    sales_commission: Decimal = Field(default=Decimal('0.00'))
    work_done_commission: Decimal = Field(default=Decimal('0.00'))
    total_commission: Decimal = Field(default=Decimal('0.00'))
    
    # Pay details
    hourly_pay: Optional[Decimal] = None
    efficiency_pay: Optional[Decimal] = None
    final_pay: Optional[Decimal] = None
    
    # Details
    commission_details: List[CommissionDetail] = []
    efficiency_details: Optional[EfficiencyPayDetail] = None


class CommissionSummary(BaseModel):
    """Summary of commission calculations"""
    period_start: date
    period_end: date
    total_employees: int
    total_commission_amount: Decimal
    total_hourly_pay: Decimal
    total_efficiency_pay: Decimal
    total_final_pay: Decimal
    
    # Breakdown by type
    lead_generation_total: Decimal
    sales_total: Decimal
    work_done_total: Decimal
    
    # Business unit breakdown
    business_unit_summary: Dict[str, Decimal] = {}


class EfficiencyPayResult(BaseModel):
    """Result of efficiency pay calculation"""
    employees_calculated: int
    total_efficiency_pay: Decimal
    positive_efficiency_count: int
    negative_efficiency_count: int
    average_efficiency_pay: Decimal


class CommissionResponse(BaseResponse):
    """Response model for commission calculations"""
    data: List[CommissionCalculation]
    summary: CommissionSummary
    efficiency_results: Optional[EfficiencyPayResult] = None