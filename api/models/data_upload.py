"""
Data upload-related Pydantic models
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal

from .common import BaseResponse


class UploadValidationError(BaseModel):
    """Upload validation error detail"""
    row: Optional[int] = Field(None, description="Row number where error occurred")
    column: Optional[str] = Field(None, description="Column name where error occurred")
    error_type: str = Field(..., description="Type of validation error")
    message: str = Field(..., description="Error message")
    value: Optional[Any] = Field(None, description="Invalid value")


class UploadStats(BaseModel):
    """Upload statistics"""
    total_rows: int = Field(..., description="Total rows in uploaded file")
    valid_rows: int = Field(..., description="Number of valid rows")
    invalid_rows: int = Field(..., description="Number of invalid rows")
    duplicate_rows: int = Field(default=0, description="Number of duplicate rows")
    columns_found: List[str] = Field(default_factory=list, description="Column names found in file")
    file_size_mb: float = Field(..., description="File size in MB")


class UploadResponse(BaseResponse):
    """Response model for data upload operations"""
    stats: UploadStats
    validation_errors: List[UploadValidationError] = Field(default_factory=list)
    preview_data: List[Dict[str, Any]] = Field(default_factory=list, description="First 5 rows of data")


class TimesheetData(BaseModel):
    """Timesheet data row model"""
    employee_name: str = Field(..., description="Employee name")
    regular_hours: Decimal = Field(default=Decimal('0.00'), ge=0, description="Regular hours worked")
    ot_hours: Decimal = Field(default=Decimal('0.00'), ge=0, description="Overtime hours worked")
    dt_hours: Decimal = Field(default=Decimal('0.00'), ge=0, description="Double-time hours worked")
    date: Optional[date] = Field(None, description="Work date")
    department: Optional[str] = Field(None, description="Department")


class RevenueData(BaseModel):
    """Revenue data row model"""
    job_number: Optional[str] = Field(None, description="Job number or ID")
    business_unit: str = Field(..., description="Business unit name")
    revenue_amount: Decimal = Field(..., ge=0, description="Revenue amount")
    date: Optional[date] = Field(None, description="Job date")
    lead_generated_by: Optional[str] = Field(None, description="Employee who generated lead")
    sold_by: Optional[str] = Field(None, description="Employee who made sale")
    assigned_technicians: Optional[str] = Field(None, description="Technicians assigned to job")


class EmployeeImportData(BaseModel):
    """Employee import data row model"""
    employee_id: Optional[str] = Field(None, description="Employee ID")
    name: str = Field(..., description="Employee name")
    department: Optional[str] = Field(None, description="Department")
    hire_date: Optional[date] = Field(None, description="Hire date")
    hourly_rate: Decimal = Field(..., ge=0, description="Hourly rate")
    status: str = Field(default="Active", description="Employee status")
    commission_plan: str = Field(default="Hourly + Commission", description="Commission plan")


class BulkUploadRequest(BaseModel):
    """Request for bulk data upload"""
    data_type: str = Field(..., description="Type of data (timesheet, revenue, employee)")
    overwrite_existing: bool = Field(default=False, description="Whether to overwrite existing data")
    validate_only: bool = Field(default=False, description="Only validate data without saving")


class BulkUploadResponse(BaseResponse):
    """Response for bulk data upload"""
    data_type: str
    processed_count: int
    skipped_count: int
    error_count: int
    validation_errors: List[UploadValidationError] = Field(default_factory=list)
    preview_data: List[Dict[str, Any]] = Field(default_factory=list)