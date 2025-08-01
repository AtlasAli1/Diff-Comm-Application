from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
import uuid
from decimal import Decimal

class Employee(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=1, max_length=100)
    hourly_rate: Decimal = Field(default=Decimal('0'), ge=0)
    regular_hours: Decimal = Field(default=Decimal('0'), ge=0)
    ot_hours: Decimal = Field(default=Decimal('0'), ge=0)
    dt_hours: Decimal = Field(default=Decimal('0'), ge=0)
    department: Optional[str] = None
    employee_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Employee name cannot be empty')
        return v.strip()
    
    @validator('hourly_rate', 'regular_hours', 'ot_hours', 'dt_hours')
    def validate_positive_and_round(cls, v):
        if v < 0:
            raise ValueError('Value must be non-negative')
        return v.quantize(Decimal('0.01'))
    
    @property
    def total_hours(self) -> Decimal:
        """Calculate total hours worked"""
        return self.regular_hours + self.ot_hours + self.dt_hours
    
    @property
    def regular_cost(self) -> Decimal:
        """Calculate regular hours cost"""
        return self.regular_hours * self.hourly_rate
    
    @property
    def overtime_cost(self) -> Decimal:
        """Calculate overtime cost at 1.5x rate"""
        return self.ot_hours * self.hourly_rate * Decimal('1.5')
    
    @property
    def double_time_cost(self) -> Decimal:
        """Calculate double time cost at 2x rate"""
        return self.dt_hours * self.hourly_rate * Decimal('2.0')
    
    @property
    def total_labor_cost(self) -> Decimal:
        """Calculate total labor cost including all hour types"""
        return self.regular_cost + self.overtime_cost + self.double_time_cost
    
    def update_hours(self, regular: Optional[Decimal] = None, 
                     ot: Optional[Decimal] = None, 
                     dt: Optional[Decimal] = None) -> None:
        """Update employee hours with validation"""
        if regular is not None:
            self.regular_hours = max(Decimal('0'), regular)
        if ot is not None:
            self.ot_hours = max(Decimal('0'), ot)
        if dt is not None:
            self.dt_hours = max(Decimal('0'), dt)
        self.updated_at = datetime.now()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'hourly_rate': float(self.hourly_rate),
            'regular_hours': float(self.regular_hours),
            'ot_hours': float(self.ot_hours),
            'dt_hours': float(self.dt_hours),
            'total_hours': float(self.total_hours),
            'total_labor_cost': float(self.total_labor_cost),
            'department': self.department,
            'employee_id': self.employee_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }