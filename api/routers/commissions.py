"""
Commission calculation API endpoints
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from datetime import date, datetime

from ..models.commission import (
    CommissionRequest,
    CommissionResponse,
    CommissionSummary
)
from ..services.commission_service import CommissionService

router = APIRouter()
commission_service = CommissionService()


@router.post("/commissions/calculate", response_model=CommissionResponse)
async def calculate_commissions(request: CommissionRequest):
    """
    Calculate commissions for specified employees and pay period
    
    - **request**: Commission calculation request with employees and date range
    
    Example request:
    ```json
    {
        "employee_ids": [0, 1, 2],
        "start_date": "2024-01-01", 
        "end_date": "2024-01-14",
        "pay_period_id": 1
    }
    ```
    """
    try:
        if not request.employee_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one employee ID must be specified"
            )
        
        if request.start_date >= request.end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before end date"
            )
        
        # Perform commission calculations
        calculations, summary, efficiency_results = await commission_service.calculate_commissions(request)
        
        return CommissionResponse(
            data=calculations,
            summary=summary,
            efficiency_results=efficiency_results,
            message=f"Calculated commissions for {len(calculations)} employees"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate commissions: {str(e)}"
        )


@router.get("/commissions/summary")
async def get_commission_summary(
    start_date: date = Query(..., description="Period start date"),
    end_date: date = Query(..., description="Period end date"),
    employee_ids: Optional[List[int]] = Query(None, description="Optional employee IDs to filter")
):
    """
    Get commission summary for date range
    
    - **start_date**: Period start date
    - **end_date**: Period end date  
    - **employee_ids**: Optional list of employee IDs to filter
    
    Returns summary without detailed calculations for quick overview.
    """
    try:
        if start_date >= end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before end date"
            )
        
        # Create request for calculation
        request = CommissionRequest(
            employee_ids=employee_ids or [],
            start_date=start_date,
            end_date=end_date
        )
        
        # If no employee IDs specified, get all employees
        if not request.employee_ids:
            from ..adapters.session_adapter import SessionAdapter
            session = SessionAdapter()
            employee_df = session.get_employee_data()
            if not employee_df.empty:
                request.employee_ids = list(range(len(employee_df)))
        
        if not request.employee_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No employees found"
            )
        
        # Get summary only
        _, summary, _ = await commission_service.calculate_commissions(request)
        
        return {
            "success": True,
            "data": summary,
            "message": "Commission summary retrieved successfully",
            "timestamp": datetime.now()
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get commission summary: {str(e)}"
        )


@router.post("/commissions/calculate-for-pay-period")
async def calculate_commissions_for_pay_period(
    pay_period_id: int,
    employee_ids: Optional[List[int]] = None
):
    """
    Calculate commissions for a specific pay period
    
    - **pay_period_id**: The pay period ID to calculate for
    - **employee_ids**: Optional list of employee IDs (calculates for all if not specified)
    """
    try:
        # Get pay period details
        from ..services.pay_period_service import PayPeriodService
        pay_period_service = PayPeriodService()
        
        pay_period = await pay_period_service.get_pay_period_by_id(pay_period_id)
        if not pay_period:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pay period with ID {pay_period_id} not found"
            )
        
        # Get all employees if none specified
        if not employee_ids:
            from ..adapters.session_adapter import SessionAdapter
            session = SessionAdapter()
            employee_df = session.get_employee_data()
            if not employee_df.empty:
                employee_ids = list(range(len(employee_df)))
        
        if not employee_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No employees found"
            )
        
        # Create request
        request = CommissionRequest(
            employee_ids=employee_ids,
            start_date=pay_period.start_date,
            end_date=pay_period.end_date,
            pay_period_id=pay_period_id
        )
        
        # Calculate commissions
        calculations, summary, efficiency_results = await commission_service.calculate_commissions(request)
        
        return CommissionResponse(
            data=calculations,
            summary=summary,
            efficiency_results=efficiency_results,
            message=f"Calculated commissions for pay period {pay_period.period_number}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate commissions for pay period: {str(e)}"
        )