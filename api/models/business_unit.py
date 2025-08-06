"""
Business Unit-related Pydantic models
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List
from datetime import datetime
from decimal import Decimal

from .common import BaseResponse


class CommissionRates(BaseModel):
    """Commission rates configuration"""
    lead_gen_rate: Decimal = Field(default=Decimal('0.00'), ge=0, le=100, description="Lead generation commission rate (%)")
    sold_by_rate: Decimal = Field(default=Decimal('0.00'), ge=0, le=100, description="Sales commission rate (%)")
    work_done_rate: Decimal = Field(default=Decimal('0.00'), ge=0, le=100, description="Work done commission rate (%)")
    
    @validator('lead_gen_rate', 'sold_by_rate', 'work_done_rate', pre=True)
    def validate_rates(cls, v):
        """Convert to Decimal and validate"""
        try:
            return Decimal(str(v))
        except (ValueError, TypeError):
            raise ValueError("Rate must be a valid number")


class BusinessUnitBase(BaseModel):
    """Base business unit model"""
    name: str = Field(..., min_length=1, max_length=100, description="Business unit name")
    description: Optional[str] = Field(None, max_length=255, description="Business unit description")
    enabled: bool = Field(default=True, description="Whether this business unit is active")
    rates: CommissionRates = Field(default_factory=CommissionRates, description="Commission rates configuration")


class BusinessUnitCreate(BusinessUnitBase):
    """Model for creating new business units"""
    auto_added: bool = Field(default=False, description="Whether this was auto-detected from data")


class BusinessUnitUpdate(BaseModel):
    """Model for updating existing business units"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    enabled: Optional[bool] = None
    rates: Optional[CommissionRates] = None


class BusinessUnit(BusinessUnitBase):
    """Full business unit model with database fields"""
    id: int = Field(..., description="Database primary key")
    auto_added: bool = Field(default=False, description="Whether this was auto-detected")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        from_attributes = True


class BusinessUnitResponse(BaseResponse):
    """Response model for business unit operations"""
    data: BusinessUnit


class BusinessUnitListResponse(BaseResponse):
    """Response model for business unit list operations"""
    data: List[BusinessUnit]
    total: int = Field(description="Total number of business units")


class BusinessUnitStats(BaseModel):
    """Business unit statistics"""
    total_units: int
    enabled_units: int
    disabled_units: int
    auto_added_units: int
    manually_created_units: int
    avg_lead_gen_rate: Decimal
    avg_sales_rate: Decimal
    avg_work_done_rate: Decimal


class BusinessUnitStatsResponse(BaseResponse):
    """Response model for business unit statistics"""
    data: BusinessUnitStats