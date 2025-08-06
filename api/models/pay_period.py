"""
Pay Period-related Pydantic models
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

from .common import BaseResponse


class PaySchedule(str, Enum):
    """Pay schedule frequency options"""
    WEEKLY = "Weekly"
    BIWEEKLY = "Bi-Weekly"  
    SEMIMONTHLY = "Semi-Monthly"
    MONTHLY = "Monthly"


class PayPeriodBase(BaseModel):
    """Base pay period model"""
    period_number: int = Field(..., ge=1, description="Pay period number for the year")
    start_date: date = Field(..., description="Pay period start date")
    end_date: date = Field(..., description="Pay period end date") 
    pay_date: date = Field(..., description="Actual pay date")
    is_current: bool = Field(False, description="Is this the current active pay period")
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        """Ensure end_date is after start_date"""
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError("End date must be after start date")
        return v
    
    @validator('pay_date') 
    def validate_pay_date(cls, v, values):
        """Ensure pay_date is after end_date"""
        if 'end_date' in values and v < values['end_date']:
            raise ValueError("Pay date must be on or after end date")
        return v


class PayPeriodCreate(PayPeriodBase):
    """Model for creating new pay periods"""
    pass


class PayPeriod(PayPeriodBase):
    """Full pay period model with database fields"""
    id: int = Field(..., description="Database primary key")
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        from_attributes = True


class PayPeriodResponse(BaseResponse):
    """Response model for pay period operations"""
    data: PayPeriod


class PayPeriodListResponse(BaseResponse):
    """Response model for pay period list operations"""  
    data: List[PayPeriod]
    total: int = Field(description="Total number of pay periods")


class PayScheduleConfig(BaseModel):
    """Pay schedule configuration"""
    schedule: PaySchedule = Field(..., description="Pay frequency")
    first_period_start: date = Field(..., description="First pay period start date")
    pay_delay_days: int = Field(
        default=0, 
        ge=0, 
        le=30,
        description="Days after period end before pay date"
    )
    
    class Config:
        use_enum_values = True


class PayScheduleConfigResponse(BaseResponse):
    """Response model for pay schedule configuration"""
    data: PayScheduleConfig


class PayPeriodGeneration(BaseModel):
    """Model for generating multiple pay periods"""
    config: PayScheduleConfig
    num_periods: int = Field(
        default=26, 
        ge=1, 
        le=52,
        description="Number of pay periods to generate"
    )


class PayPeriodStats(BaseModel):
    """Pay period statistics"""
    total_periods: int
    current_period_number: Optional[int] = None
    next_pay_date: Optional[date] = None
    periods_remaining: int = 0
    schedule_type: Optional[PaySchedule] = None
    
    class Config:
        use_enum_values = True


class PayPeriodStatsResponse(BaseResponse):
    """Response model for pay period statistics"""
    data: PayPeriodStats