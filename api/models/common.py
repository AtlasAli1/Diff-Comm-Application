"""
Common Pydantic models used across the API
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Generic, TypeVar
from datetime import datetime
from enum import Enum

T = TypeVar('T')


class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = True
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class PaginatedResponse(BaseResponse, Generic[T]):
    """Paginated response model"""
    data: List[T]
    pagination: Dict[str, Any] = Field(
        description="Pagination metadata",
        example={
            "page": 1,
            "per_page": 50,
            "total": 100,
            "pages": 2,
            "has_next": True,
            "has_prev": False
        }
    )


class HealthStatus(str, Enum):
    """Health check status values"""
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    UNHEALTHY = "unhealthy"


class HealthResponse(BaseResponse):
    """Health check response"""
    status: HealthStatus
    version: str = "1.0.0"
    uptime: Optional[str] = None
    checks: Dict[str, Any] = Field(
        default_factory=dict,
        description="Individual health check results"
    )


class ValidationError(BaseModel):
    """Validation error detail"""
    field: str
    message: str
    invalid_value: Optional[Any] = None