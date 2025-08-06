"""
Pay Period management API endpoints
"""

from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from datetime import datetime, date

from ..models.pay_period import (
    PayPeriod,
    PayPeriodCreate,
    PayPeriodResponse,
    PayPeriodListResponse,
    PayScheduleConfig,
    PayScheduleConfigResponse,
    PayPeriodGeneration,
    PayPeriodStats,
    PayPeriodStatsResponse
)
from ..services.pay_period_service import PayPeriodService

router = APIRouter()
pay_period_service = PayPeriodService()


@router.get("/pay-periods", response_model=PayPeriodListResponse)
async def get_pay_periods(
    year: Optional[int] = None,
    current_only: bool = False
):
    """
    Get all pay periods with optional filtering
    
    - **year**: Filter by year (defaults to current year)
    - **current_only**: Return only the current active pay period
    """
    try:
        if current_only:
            current_period = await pay_period_service.get_current_pay_period()
            periods = [current_period] if current_period else []
            total = len(periods)
        else:
            periods, total = await pay_period_service.get_pay_periods(year=year)
        
        return PayPeriodListResponse(
            data=periods,
            total=total,
            message=f"Retrieved {len(periods)} pay periods"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve pay periods: {str(e)}"
        )


@router.get("/pay-periods/{period_id}", response_model=PayPeriodResponse)
async def get_pay_period(period_id: int):
    """
    Get a specific pay period by ID
    
    - **period_id**: The database ID of the pay period
    """
    try:
        pay_period = await pay_period_service.get_pay_period_by_id(period_id)
        if not pay_period:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pay period with ID {period_id} not found"
            )
        
        return PayPeriodResponse(
            data=pay_period,
            message="Pay period retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve pay period: {str(e)}"
        )


@router.get("/pay-periods/current", response_model=PayPeriodResponse)
async def get_current_pay_period():
    """
    Get the current active pay period
    """
    try:
        current_period = await pay_period_service.get_current_pay_period()
        if not current_period:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No current pay period found. Please configure pay periods first."
            )
        
        return PayPeriodResponse(
            data=current_period,
            message="Current pay period retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve current pay period: {str(e)}"
        )


@router.post("/pay-periods", response_model=PayPeriodResponse, status_code=status.HTTP_201_CREATED)
async def create_pay_period(pay_period_data: PayPeriodCreate):
    """
    Create a new pay period
    
    - **pay_period_data**: Pay period information to create
    """
    try:
        # Check for overlapping periods
        existing_periods, _ = await pay_period_service.get_pay_periods()
        for existing in existing_periods:
            if (pay_period_data.start_date <= existing.end_date and 
                pay_period_data.end_date >= existing.start_date):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Pay period overlaps with existing period {existing.period_number}"
                )
        
        pay_period = await pay_period_service.create_pay_period(pay_period_data)
        
        return PayPeriodResponse(
            data=pay_period,
            message="Pay period created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create pay period: {str(e)}"
        )


@router.post("/pay-periods/generate", response_model=PayPeriodListResponse)
async def generate_pay_periods(generation_data: PayPeriodGeneration):
    """
    Generate multiple pay periods based on schedule configuration
    
    - **generation_data**: Schedule configuration and number of periods to generate
    """
    try:
        # Clear existing periods first (optional - could be a parameter)
        # await pay_period_service.clear_all_pay_periods()
        
        periods = await pay_period_service.generate_pay_periods(
            generation_data.config,
            generation_data.num_periods
        )
        
        return PayPeriodListResponse(
            data=periods,
            total=len(periods),
            message=f"Generated {len(periods)} pay periods successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate pay periods: {str(e)}"
        )


@router.get("/pay-periods/config", response_model=PayScheduleConfigResponse)
async def get_pay_schedule_config():
    """
    Get current pay schedule configuration
    """
    try:
        config = await pay_period_service.get_pay_schedule_config()
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No pay schedule configuration found"
            )
        
        return PayScheduleConfigResponse(
            data=config,
            message="Pay schedule configuration retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve pay schedule config: {str(e)}"
        )


@router.post("/pay-periods/config", response_model=PayScheduleConfigResponse)
async def set_pay_schedule_config(config: PayScheduleConfig):
    """
    Set pay schedule configuration
    
    - **config**: Pay schedule configuration
    """
    try:
        saved_config = await pay_period_service.save_pay_schedule_config(config)
        
        return PayScheduleConfigResponse(
            data=saved_config,
            message="Pay schedule configuration saved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save pay schedule config: {str(e)}"
        )


@router.get("/pay-periods/stats", response_model=PayPeriodStatsResponse)
async def get_pay_period_stats():
    """
    Get pay period statistics and summary information
    """
    try:
        stats = await pay_period_service.get_pay_period_stats()
        
        return PayPeriodStatsResponse(
            data=stats,
            message="Pay period statistics retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve pay period stats: {str(e)}"
        )


@router.delete("/pay-periods/{period_id}")
async def delete_pay_period(period_id: int):
    """
    Delete a pay period
    
    - **period_id**: The database ID of the pay period to delete
    """
    try:
        # Check if pay period exists
        existing_period = await pay_period_service.get_pay_period_by_id(period_id)
        if not existing_period:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pay period with ID {period_id} not found"
            )
        
        await pay_period_service.delete_pay_period(period_id)
        
        return {
            "success": True,
            "message": f"Pay period {existing_period.period_number} deleted successfully",
            "timestamp": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete pay period: {str(e)}"
        )