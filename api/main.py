"""
Main FastAPI application for Commission Calculator Pro API
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import traceback
from datetime import datetime

# Import routers
from .routers import (
    employees,
    pay_periods,
    commissions,
    data_upload,
    business_units,
    reports,
    health
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("🚀 Commission Calculator Pro API starting up...")
    yield
    logger.info("📴 Commission Calculator Pro API shutting down...")


# Create FastAPI application
app = FastAPI(
    title="Commission Calculator Pro API",
    description="""
    REST API for commission calculations, employee management, and payroll processing.
    
    ## Features
    
    * **Employee Management**: CRUD operations for employees with status tracking
    * **Pay Period Management**: Automated pay period calculation and scheduling  
    * **Commission Calculations**: Complex commission calculations with multiple rate types
    * **Data Upload**: Bulk upload timesheet, revenue, and employee data
    * **Business Unit Configuration**: Manage commission rates by business unit
    * **Reports & Analytics**: Generate detailed commission and payroll reports
    
    ## Authentication
    
    This API uses session-based authentication with secure cookie handling.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://commission-calculator-pro.vercel.app"],  # Add Vercel domain when known
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors gracefully"""
    logger.error(f"Unexpected error in {request.method} {request.url}: {str(exc)}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again.",
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url.path)
        }
    )


# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(employees.router, prefix="/api/v1", tags=["Employees"])  
app.include_router(pay_periods.router, prefix="/api/v1", tags=["Pay Periods"])
app.include_router(commissions.router, prefix="/api/v1", tags=["Commissions"])
app.include_router(data_upload.router, prefix="/api/v1", tags=["Data Upload"])
app.include_router(business_units.router, prefix="/api/v1", tags=["Business Units"])
app.include_router(reports.router, prefix="/api/v1", tags=["Reports"])


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """API root endpoint"""
    return {
        "message": "Commission Calculator Pro API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "operational",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )