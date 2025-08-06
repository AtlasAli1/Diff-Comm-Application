"""
Health check endpoints
"""

from fastapi import APIRouter
from datetime import datetime, timedelta
import psutil
import os

from ..models.common import HealthResponse, HealthStatus

router = APIRouter()

# Store startup time
STARTUP_TIME = datetime.now()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for monitoring
    
    Returns system health status and basic metrics
    """
    try:
        uptime = datetime.now() - STARTUP_TIME
        uptime_str = str(uptime).split('.')[0]  # Remove microseconds
        
        # System checks
        checks = {}
        overall_status = HealthStatus.HEALTHY
        
        # Memory check
        try:
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            checks["memory"] = {
                "status": "healthy" if memory_usage < 85 else "degraded" if memory_usage < 95 else "unhealthy",
                "usage_percent": memory_usage,
                "available_gb": round(memory.available / (1024**3), 2)
            }
            
            if memory_usage >= 95:
                overall_status = HealthStatus.UNHEALTHY
            elif memory_usage >= 85:
                overall_status = HealthStatus.DEGRADED
                
        except Exception as e:
            checks["memory"] = {"status": "error", "message": str(e)}
            overall_status = HealthStatus.DEGRADED
        
        # CPU check
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            checks["cpu"] = {
                "status": "healthy" if cpu_usage < 80 else "degraded" if cpu_usage < 95 else "unhealthy",
                "usage_percent": cpu_usage
            }
            
            if cpu_usage >= 95 and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.UNHEALTHY
            elif cpu_usage >= 80 and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED
                
        except Exception as e:
            checks["cpu"] = {"status": "error", "message": str(e)}
            if overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED
        
        # Disk check
        try:
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            checks["disk"] = {
                "status": "healthy" if disk_usage < 85 else "degraded" if disk_usage < 95 else "unhealthy",
                "usage_percent": disk_usage,
                "free_gb": round(disk.free / (1024**3), 2)
            }
            
            if disk_usage >= 95 and overall_status != HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
            elif disk_usage >= 85 and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED
                
        except Exception as e:
            checks["disk"] = {"status": "error", "message": str(e)}
            if overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED
        
        return HealthResponse(
            status=overall_status,
            uptime=uptime_str,
            checks=checks,
            message="System operational" if overall_status == HealthStatus.HEALTHY else "System issues detected"
        )
        
    except Exception as e:
        return HealthResponse(
            success=False,
            status=HealthStatus.UNHEALTHY,
            message=f"Health check failed: {str(e)}",
            checks={"error": {"status": "error", "message": str(e)}}
        )


@router.get("/health/ready")
async def readiness_check():
    """
    Kubernetes readiness probe endpoint
    
    Returns 200 if service is ready to handle requests
    """
    return {"status": "ready", "timestamp": datetime.now().isoformat()}


@router.get("/health/live")  
async def liveness_check():
    """
    Kubernetes liveness probe endpoint
    
    Returns 200 if service is alive
    """
    return {"status": "alive", "timestamp": datetime.now().isoformat()}