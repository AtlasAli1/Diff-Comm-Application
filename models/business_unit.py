from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
import uuid
from decimal import Decimal

class BusinessUnit(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=1, max_length=100)
    commission_rate: Decimal = Field(default=Decimal('0'), ge=0, le=100)
    revenue: Decimal = Field(default=Decimal('0'), ge=0)
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('commission_rate', 'revenue')
    def round_to_two_places(cls, v):
        return v.quantize(Decimal('0.01'))
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Business unit name cannot be empty')
        return v.strip()
    
    @validator('commission_rate')
    def validate_commission_rate(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Commission rate must be between 0 and 100')
        return v
    
    @property
    def commission_amount(self) -> Decimal:
        """Calculate commission amount based on revenue and rate"""
        return (self.revenue * self.commission_rate) / Decimal('100')
    
    def update_rate(self, new_rate: Decimal) -> None:
        """Update commission rate with validation"""
        if new_rate < 0 or new_rate > 100:
            raise ValueError('Commission rate must be between 0 and 100')
        self.commission_rate = new_rate
        self.updated_at = datetime.now()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'commission_rate': float(self.commission_rate),
            'revenue': float(self.revenue),
            'commission_amount': float(self.commission_amount),
            'description': self.description,
            'category': self.category,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Commission(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    business_unit_id: str
    amount: Decimal = Field(ge=0)
    percentage: Decimal = Field(default=Decimal('100'), ge=0, le=100)
    period_start: datetime
    period_end: datetime
    status: str = Field(default='pending', pattern='^(pending|approved|paid|cancelled)$')
    notes: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @validator('amount', 'percentage')
    def round_to_two_places(cls, v):
        return v.quantize(Decimal('0.01'))
    
    @property
    def adjusted_amount(self) -> Decimal:
        """Calculate adjusted commission amount based on percentage"""
        return (self.amount * self.percentage) / Decimal('100')
    
    def approve(self, approved_by: str) -> None:
        """Approve the commission"""
        self.status = 'approved'
        self.approved_by = approved_by
        self.approved_at = datetime.now()
        self.updated_at = datetime.now()
    
    def mark_paid(self) -> None:
        """Mark commission as paid"""
        if self.status != 'approved':
            raise ValueError('Commission must be approved before marking as paid')
        self.status = 'paid'
        self.paid_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'business_unit_id': self.business_unit_id,
            'amount': float(self.amount),
            'percentage': float(self.percentage),
            'adjusted_amount': float(self.adjusted_amount),
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'status': self.status,
            'notes': self.notes,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class CommissionSplit(BaseModel):
    """Model for manual commission splits between employees"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    employee_splits: Dict[str, Decimal] = Field(default_factory=dict)
    total_amount: Decimal = Field(ge=0, decimal_places=2)
    created_by: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @validator('employee_splits')
    def validate_splits(cls, v):
        total = sum(v.values())
        if abs(total - Decimal('100')) > Decimal('0.01'):
            raise ValueError('Employee splits must sum to 100%')
        return v
    
    def calculate_employee_amount(self, employee_id: str) -> Decimal:
        """Calculate commission amount for specific employee"""
        if employee_id not in self.employee_splits:
            return Decimal('0')
        return (self.total_amount * self.employee_splits[employee_id]) / Decimal('100')