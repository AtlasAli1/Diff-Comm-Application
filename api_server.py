#!/usr/bin/env python3
"""
Commission Calculator Pro - REST API Server
Provides REST API endpoints for external integrations
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import json
from datetime import datetime, date
import os
from pathlib import Path

# Initialize FastAPI app
app = FastAPI(
    title="Commission Calculator Pro API",
    description="REST API for commission calculations and data management",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Data models
class Employee(BaseModel):
    employee_id: str
    name: str
    department: Optional[str] = None
    role: Optional[str] = None
    hourly_rate: float
    commission_rate: Optional[float] = 5.0
    start_date: Optional[date] = None
    status: Optional[str] = "Active"

class TimesheetEntry(BaseModel):
    employee_name: str
    regular_hours: float
    ot_hours: Optional[float] = 0
    dt_hours: Optional[float] = 0
    date: Optional[str] = None

class RevenueEntry(BaseModel):
    business_unit: str
    revenue: float
    period: Optional[str] = None
    date: Optional[str] = None

class LeadEntry(BaseModel):
    employee_name: str
    lead_value: float
    commission_rate: float
    status: str
    date: str
    description: Optional[str] = None

class CommissionCalculationRequest(BaseModel):
    employee_names: List[str]
    start_date: date
    end_date: date
    calculate_hourly: bool = True
    calculate_leads: bool = True

class CommissionResult(BaseModel):
    employee: str
    hourly_commission: float
    lead_commission: float
    total_commission: float
    details: Dict[str, Any]

# Authentication
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Simple token verification - replace with proper auth in production"""
    token = credentials.credentials
    # For demo purposes, accept any token that starts with 'api_'
    if not token.startswith('api_'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    return token

# Data storage paths
DATA_DIR = Path(__file__).parent / "api_data"
DATA_DIR.mkdir(exist_ok=True)

EMPLOYEES_FILE = DATA_DIR / "employees.json"
TIMESHEET_FILE = DATA_DIR / "timesheet.json"
REVENUE_FILE = DATA_DIR / "revenue.json"
LEADS_FILE = DATA_DIR / "leads.json"

# Utility functions
def load_json_data(file_path: Path) -> List[Dict]:
    """Load data from JSON file"""
    if file_path.exists():
        with open(file_path, 'r') as f:
            return json.load(f)
    return []

def save_json_data(file_path: Path, data: List[Dict]):
    """Save data to JSON file"""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def df_to_dict_list(df: pd.DataFrame) -> List[Dict]:
    """Convert DataFrame to list of dictionaries"""
    return df.to_dict('records')

# API Endpoints

@app.get("/")
async def root():
    """API status endpoint"""
    return {
        "message": "Commission Calculator Pro API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Employee endpoints
@app.get("/api/employees", response_model=List[Employee])
async def get_employees(token: str = Depends(verify_token)):
    """Get all employees"""
    data = load_json_data(EMPLOYEES_FILE)
    return data

@app.post("/api/employees", response_model=Employee)
async def create_employee(employee: Employee, token: str = Depends(verify_token)):
    """Create a new employee"""
    data = load_json_data(EMPLOYEES_FILE)
    
    # Check if employee already exists
    if any(emp['employee_id'] == employee.employee_id for emp in data):
        raise HTTPException(status_code=400, detail="Employee ID already exists")
    
    emp_dict = employee.dict()
    data.append(emp_dict)
    save_json_data(EMPLOYEES_FILE, data)
    
    return employee

@app.put("/api/employees/{employee_id}", response_model=Employee)
async def update_employee(employee_id: str, employee: Employee, token: str = Depends(verify_token)):
    """Update an employee"""
    data = load_json_data(EMPLOYEES_FILE)
    
    for i, emp in enumerate(data):
        if emp['employee_id'] == employee_id:
            data[i] = employee.dict()
            save_json_data(EMPLOYEES_FILE, data)
            return employee
    
    raise HTTPException(status_code=404, detail="Employee not found")

@app.delete("/api/employees/{employee_id}")
async def delete_employee(employee_id: str, token: str = Depends(verify_token)):
    """Delete an employee"""
    data = load_json_data(EMPLOYEES_FILE)
    
    for i, emp in enumerate(data):
        if emp['employee_id'] == employee_id:
            del data[i]
            save_json_data(EMPLOYEES_FILE, data)
            return {"message": "Employee deleted successfully"}
    
    raise HTTPException(status_code=404, detail="Employee not found")

# Timesheet endpoints
@app.get("/api/timesheet")
async def get_timesheet(token: str = Depends(verify_token)):
    """Get all timesheet entries"""
    data = load_json_data(TIMESHEET_FILE)
    return data

@app.post("/api/timesheet/bulk")
async def upload_timesheet_bulk(entries: List[TimesheetEntry], token: str = Depends(verify_token)):
    """Bulk upload timesheet entries"""
    data = load_json_data(TIMESHEET_FILE)
    
    for entry in entries:
        data.append(entry.dict())
    
    save_json_data(TIMESHEET_FILE, data)
    return {"message": f"Added {len(entries)} timesheet entries"}

# Revenue endpoints
@app.get("/api/revenue")
async def get_revenue(token: str = Depends(verify_token)):
    """Get all revenue entries"""
    data = load_json_data(REVENUE_FILE)
    return data

@app.post("/api/revenue/bulk")
async def upload_revenue_bulk(entries: List[RevenueEntry], token: str = Depends(verify_token)):
    """Bulk upload revenue entries"""
    data = load_json_data(REVENUE_FILE)
    
    for entry in entries:
        data.append(entry.dict())
    
    save_json_data(REVENUE_FILE, data)
    return {"message": f"Added {len(entries)} revenue entries"}

# Lead endpoints
@app.get("/api/leads")
async def get_leads(token: str = Depends(verify_token)):
    """Get all leads"""
    data = load_json_data(LEADS_FILE)
    return data

@app.post("/api/leads", response_model=LeadEntry)
async def create_lead(lead: LeadEntry, token: str = Depends(verify_token)):
    """Create a new lead"""
    data = load_json_data(LEADS_FILE)
    lead_dict = lead.dict()
    data.append(lead_dict)
    save_json_data(LEADS_FILE, data)
    return lead

# Commission calculation endpoints
@app.post("/api/commissions/calculate", response_model=List[CommissionResult])
async def calculate_commissions(request: CommissionCalculationRequest, token: str = Depends(verify_token)):
    """Calculate commissions for specified employees"""
    
    # Load data
    employees = load_json_data(EMPLOYEES_FILE)
    timesheet = load_json_data(TIMESHEET_FILE)
    leads = load_json_data(LEADS_FILE)
    
    # Convert to DataFrames
    emp_df = pd.DataFrame(employees) if employees else pd.DataFrame()
    timesheet_df = pd.DataFrame(timesheet) if timesheet else pd.DataFrame()
    leads_df = pd.DataFrame(leads) if leads else pd.DataFrame()
    
    results = []
    
    for employee_name in request.employee_names:
        result = {
            "employee": employee_name,
            "hourly_commission": 0,
            "lead_commission": 0,
            "total_commission": 0,
            "details": {}
        }
        
        # Calculate hourly commission
        if request.calculate_hourly and not emp_df.empty and not timesheet_df.empty:
            emp_data = emp_df[emp_df['name'] == employee_name]
            if len(emp_data) > 0:
                hourly_rate = emp_data.iloc[0]['hourly_rate']
                commission_rate = emp_data.iloc[0].get('commission_rate', 5.0)
                
                # Filter timesheet data
                emp_timesheet = timesheet_df[timesheet_df['employee_name'] == employee_name]
                if len(emp_timesheet) > 0:
                    total_hours = (
                        emp_timesheet['regular_hours'].sum() +
                        emp_timesheet.get('ot_hours', 0).sum() +
                        emp_timesheet.get('dt_hours', 0).sum()
                    )
                    
                    hourly_earnings = total_hours * hourly_rate
                    hourly_commission = hourly_earnings * (commission_rate / 100)
                    
                    result["hourly_commission"] = hourly_commission
                    result["details"]["hours"] = total_hours
                    result["details"]["hourly_rate"] = hourly_rate
                    result["details"]["commission_rate"] = commission_rate
        
        # Calculate lead commission
        if request.calculate_leads and not leads_df.empty:
            # Convert date strings to datetime
            leads_df['date'] = pd.to_datetime(leads_df['date'])
            
            emp_leads = leads_df[
                (leads_df['employee_name'] == employee_name) &
                (leads_df['date'].dt.date >= request.start_date) &
                (leads_df['date'].dt.date <= request.end_date) &
                (leads_df['status'] == 'Closed Won')
            ]
            
            if len(emp_leads) > 0:
                lead_commission = (emp_leads['lead_value'] * emp_leads['commission_rate'] / 100).sum()
                result["lead_commission"] = lead_commission
                result["details"]["closed_leads"] = len(emp_leads)
                result["details"]["lead_value"] = emp_leads['lead_value'].sum()
        
        result["total_commission"] = result["hourly_commission"] + result["lead_commission"]
        results.append(result)
    
    return results

@app.get("/api/commissions/summary")
async def get_commission_summary(
    start_date: date,
    end_date: date,
    token: str = Depends(verify_token)
):
    """Get commission summary for date range"""
    
    # Load data
    employees = load_json_data(EMPLOYEES_FILE)
    timesheet = load_json_data(TIMESHEET_FILE)
    leads = load_json_data(LEADS_FILE)
    
    # Calculate totals
    total_employees = len(employees)
    total_leads = len([l for l in leads if l.get('status') == 'Closed Won'])
    
    # Convert to DataFrames for calculations
    timesheet_df = pd.DataFrame(timesheet) if timesheet else pd.DataFrame()
    leads_df = pd.DataFrame(leads) if leads else pd.DataFrame()
    
    total_hours = 0
    if not timesheet_df.empty:
        total_hours = (
            timesheet_df.get('regular_hours', 0).sum() +
            timesheet_df.get('ot_hours', 0).sum() +
            timesheet_df.get('dt_hours', 0).sum()
        )
    
    total_lead_value = 0
    if not leads_df.empty:
        # Filter by date range
        leads_df['date'] = pd.to_datetime(leads_df['date'])
        filtered_leads = leads_df[
            (leads_df['date'].dt.date >= start_date) &
            (leads_df['date'].dt.date <= end_date) &
            (leads_df['status'] == 'Closed Won')
        ]
        total_lead_value = filtered_leads['lead_value'].sum()
    
    return {
        "period": f"{start_date} to {end_date}",
        "total_employees": total_employees,
        "total_hours": total_hours,
        "total_leads": total_leads,
        "total_lead_value": total_lead_value,
        "generated_at": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8504)