"""
Business Unit management API endpoints
"""

from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from datetime import datetime

from ..models.business_unit import (
    BusinessUnit,
    BusinessUnitCreate,
    BusinessUnitUpdate,
    BusinessUnitResponse,
    BusinessUnitListResponse,
    BusinessUnitStats,
    BusinessUnitStatsResponse
)
from ..services.business_unit_service import BusinessUnitService

router = APIRouter()
business_unit_service = BusinessUnitService()


@router.get("/business-units", response_model=BusinessUnitListResponse)
async def get_business_units():
    """
    Get all business units and their commission configurations
    """
    try:
        business_units, total = await business_unit_service.get_business_units()
        
        return BusinessUnitListResponse(
            data=business_units,
            total=total,
            message=f"Retrieved {len(business_units)} business units"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve business units: {str(e)}"
        )


@router.get("/business-units/{unit_id}", response_model=BusinessUnitResponse)
async def get_business_unit(unit_id: int):
    """
    Get a specific business unit by ID
    
    - **unit_id**: The database ID of the business unit
    """
    try:
        business_unit = await business_unit_service.get_business_unit_by_id(unit_id)
        if not business_unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Business unit with ID {unit_id} not found"
            )
        
        return BusinessUnitResponse(
            data=business_unit,
            message="Business unit retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve business unit: {str(e)}"
        )


@router.post("/business-units", response_model=BusinessUnitResponse, status_code=status.HTTP_201_CREATED)
async def create_business_unit(business_unit_data: BusinessUnitCreate):
    """
    Create or update business unit commission configuration
    
    - **business_unit_data**: Business unit configuration
    
    Example request:
    ```json
    {
        "name": "HVAC Services",
        "description": "Heating and cooling services",
        "enabled": true,
        "rates": {
            "lead_gen_rate": 2.5,
            "sold_by_rate": 3.0,
            "work_done_rate": 1.5
        },
        "auto_added": false
    }
    ```
    """
    try:
        # Check if business unit already exists
        existing_unit = await business_unit_service.get_business_unit_by_name(business_unit_data.name)
        if existing_unit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Business unit '{business_unit_data.name}' already exists"
            )
        
        business_unit = await business_unit_service.create_or_update_business_unit(business_unit_data)
        
        return BusinessUnitResponse(
            data=business_unit,
            message="Business unit created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create business unit: {str(e)}"
        )


@router.put("/business-units/{unit_id}", response_model=BusinessUnitResponse)
async def update_business_unit(unit_id: int, business_unit_data: BusinessUnitUpdate):
    """
    Update an existing business unit
    
    - **unit_id**: The database ID of the business unit to update
    - **business_unit_data**: Updated business unit information
    """
    try:
        # Check if business unit exists
        existing_unit = await business_unit_service.get_business_unit_by_id(unit_id)
        if not existing_unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Business unit with ID {unit_id} not found"
            )
        
        # Check for name conflicts if renaming
        if business_unit_data.name and business_unit_data.name != existing_unit.name:
            existing_with_name = await business_unit_service.get_business_unit_by_name(business_unit_data.name)
            if existing_with_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Business unit '{business_unit_data.name}' already exists"
                )
        
        business_unit = await business_unit_service.update_business_unit(unit_id, business_unit_data)
        
        return BusinessUnitResponse(
            data=business_unit,
            message="Business unit updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update business unit: {str(e)}"
        )


@router.delete("/business-units/{unit_id}")
async def delete_business_unit(unit_id: int):
    """
    Delete a business unit
    
    - **unit_id**: The database ID of the business unit to delete
    """
    try:
        # Check if business unit exists
        existing_unit = await business_unit_service.get_business_unit_by_id(unit_id)
        if not existing_unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Business unit with ID {unit_id} not found"
            )
        
        await business_unit_service.delete_business_unit(unit_id)
        
        return {
            "success": True,
            "message": f"Business unit '{existing_unit.name}' deleted successfully",
            "timestamp": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete business unit: {str(e)}"
        )


@router.get("/business-units/stats", response_model=BusinessUnitStatsResponse)
async def get_business_unit_stats():
    """
    Get business unit statistics
    
    Returns counts, averages, and other summary information about business units.
    """
    try:
        stats = await business_unit_service.get_business_unit_stats()
        
        return BusinessUnitStatsResponse(
            data=stats,
            message="Business unit statistics retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve business unit stats: {str(e)}"
        )