"""
Employee management API endpoints
"""

from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional
from datetime import datetime

from ..models.employee import (
    Employee,
    EmployeeCreate,
    EmployeeUpdate, 
    EmployeeResponse,
    EmployeeListResponse,
    EmployeeSummary,
    EmployeeSummaryResponse,
    EmployeeStatus
)
from ..services.employee_service import EmployeeService

router = APIRouter()
employee_service = EmployeeService()


@router.get("/employees", response_model=EmployeeListResponse)
async def get_employees(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    status: Optional[EmployeeStatus] = Query(None, description="Filter by employee status"),
    department: Optional[str] = Query(None, description="Filter by department"),
    search: Optional[str] = Query(None, description="Search by name or employee ID")
):
    """
    Get all employees with optional filtering and pagination
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **status**: Filter by employee status
    - **department**: Filter by department name
    - **search**: Search term for name or employee ID
    """
    try:
        employees, total = await employee_service.get_employees(
            skip=skip,
            limit=limit,
            status=status,
            department=department,
            search=search
        )
        
        return EmployeeListResponse(
            data=employees,
            total=total,
            message=f"Retrieved {len(employees)} employees"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve employees: {str(e)}"
        )


@router.get("/employees/{employee_id}", response_model=EmployeeResponse)
async def get_employee(employee_id: int):
    """
    Get a specific employee by ID
    
    - **employee_id**: The database ID of the employee
    """
    try:
        employee = await employee_service.get_employee_by_id(employee_id)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee with ID {employee_id} not found"
            )
        
        return EmployeeResponse(
            data=employee,
            message="Employee retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve employee: {str(e)}"
        )


@router.post("/employees", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(employee_data: EmployeeCreate):
    """
    Create a new employee
    
    - **employee_data**: Employee information to create
    """
    try:
        # Check if employee ID already exists (if provided)
        if employee_data.employee_id:
            existing = await employee_service.get_employee_by_employee_id(employee_data.employee_id)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Employee with ID '{employee_data.employee_id}' already exists"
                )
        
        employee = await employee_service.create_employee(employee_data)
        
        return EmployeeResponse(
            data=employee,
            message="Employee created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create employee: {str(e)}"
        )


@router.put("/employees/{employee_id}", response_model=EmployeeResponse)
async def update_employee(employee_id: int, employee_data: EmployeeUpdate):
    """
    Update an existing employee
    
    - **employee_id**: The database ID of the employee to update
    - **employee_data**: Updated employee information
    """
    try:
        # Check if employee exists
        existing_employee = await employee_service.get_employee_by_id(employee_id)
        if not existing_employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee with ID {employee_id} not found"
            )
        
        # Check if new employee_id conflicts with existing employee (if changed)
        if employee_data.employee_id and employee_data.employee_id != existing_employee.employee_id:
            existing_with_id = await employee_service.get_employee_by_employee_id(employee_data.employee_id)
            if existing_with_id and existing_with_id.id != employee_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Employee with ID '{employee_data.employee_id}' already exists"
                )
        
        employee = await employee_service.update_employee(employee_id, employee_data)
        
        return EmployeeResponse(
            data=employee,
            message="Employee updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update employee: {str(e)}"
        )


@router.delete("/employees/{employee_id}")
async def delete_employee(employee_id: int):
    """
    Delete an employee
    
    - **employee_id**: The database ID of the employee to delete
    """
    try:
        # Check if employee exists
        existing_employee = await employee_service.get_employee_by_id(employee_id)
        if not existing_employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee with ID {employee_id} not found"
            )
        
        await employee_service.delete_employee(employee_id)
        
        return {
            "success": True,
            "message": f"Employee {existing_employee.name} deleted successfully",
            "timestamp": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete employee: {str(e)}"
        )


@router.get("/employees/summary", response_model=EmployeeSummaryResponse)
async def get_employee_summary():
    """
    Get employee summary statistics
    
    Returns counts by status, commission plans, and average rates
    """
    try:
        summary = await employee_service.get_employee_summary()
        
        return EmployeeSummaryResponse(
            data=summary,
            message="Employee summary retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve employee summary: {str(e)}"
        )


@router.post("/employees/bulk", response_model=EmployeeListResponse)
async def create_employees_bulk(employees_data: List[EmployeeCreate]):
    """
    Create multiple employees at once
    
    - **employees_data**: List of employee information to create
    """
    if len(employees_data) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 100 employees can be created at once"
        )
    
    try:
        # Validate unique employee IDs within the batch
        employee_ids = [emp.employee_id for emp in employees_data if emp.employee_id]
        if len(employee_ids) != len(set(employee_ids)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate employee IDs found in batch"
            )
        
        employees = await employee_service.create_employees_bulk(employees_data)
        
        return EmployeeListResponse(
            data=employees,
            total=len(employees),
            message=f"Successfully created {len(employees)} employees"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create employees: {str(e)}"
        )