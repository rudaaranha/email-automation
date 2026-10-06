"""
API endpoints for the Alert System.

This module defines all HTTP endpoints that expose the alert system
functionality. It uses FastAPI's dependency injection to get the
AlertSystem singleton instance.

Endpoints:
    GET /                           - System information
    GET /health                     - Health check for Cloud Run
    POST /api/v1/execute            - Execute alert system
    GET /api/v1/status              - Get system status
    GET /api/v1/activities          - List all activities (debug)
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from src.dependencies import get_alert_system, get_system_status, is_ready
from src.alert_system import AlertSystem
from src.models import (
    ExecuteRequest,
    ExecuteResponse,
    StatusResponse,
    HealthResponse,
    ErrorResponse,
    ExecutionMode
)


# ============================================
# ROUTER CREATION
# ============================================

# Create router with prefix and tags for API documentation
router = APIRouter(prefix="/api/v1", tags=["Alerts"])


# ============================================
# ROOT ENDPOINT (no prefix)
# ============================================

@router.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - returns basic system information.
    
    This is a simple welcome endpoint that shows the API is running.
    Accessible at the base URL without the /api/v1 prefix.
    
    Returns:
        dict: System name, version, and documentation link
    """
    return {
        "name": "Sistema de Alertas de Atividades",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "online"
    }


# ============================================
# HEALTH CHECK ENDPOINT
# ============================================

@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check for Cloud Run",
    description="Verifies if the system is healthy and ready to receive requests."
)
async def health_check(
    alert_system: AlertSystem = Depends(get_alert_system)
):
    """
    Health check endpoint used by Cloud Run and monitoring tools.
    
    Verifies:
        - System is initialized
        - Google Sheets API is accessible
        - SMTP is configured
    
    Returns:
        HealthResponse: Status of the system
    """
    # Check if system is initialized
    if not is_ready():
        return HealthResponse(
            status="degraded",
            google_sheets_api=False,
            smtp_configured=False,
            sheets_accessible=[]
        )
    
    # Check Google Sheets accessibility
    sheets_accessible = []
    google_sheets_ok = True
    
    try:
        # Try to access a configured spreadsheet
        for project_name, sheet_id in alert_system.config.SPREADSHEETS.items():
            if sheet_id:
                try:
                    # Just try to open the spreadsheet
                    alert_system.spreadsheet_manager.client.open_by_key(sheet_id)
                    sheets_accessible.append(project_name)
                except Exception:
                    google_sheets_ok = False
    except Exception:
        google_sheets_ok = False
    
    # Check SMTP configuration
    smtp_ok = (
        alert_system.config.EMAIL_NATS is not None and
        alert_system.config.SENHA_APP_NATS is not None
    )
    
    status = "ok" if (google_sheets_ok and smtp_ok) else "degraded"
    
    return HealthResponse(
        status=status,
        google_sheets_api=google_sheets_ok,
        smtp_configured=smtp_ok,
        sheets_accessible=sheets_accessible
    )


# ============================================
# EXECUTE ENDPOINT
# ============================================

@router.post(
    "/execute",
    response_model=ExecuteResponse,
    responses={
        500: {"model": ErrorResponse}
    },
    summary="Execute alert system",
    description="Processes all spreadsheets and sends email alerts based on activity status."
)
async def execute_alerts(
    request: ExecuteRequest,
    alert_system: AlertSystem = Depends(get_alert_system)
):
    """
    Execute the alert system.
    
    This is the main endpoint that triggers the alert processing.
    It can process all configured projects or a specific one.
    
    Args:
        request: ExecuteRequest with optional project and mode
        
    Returns:
        ExecuteResponse: Summary of the execution
        
    Raises:
        HTTPException 500: If execution fails
    """
    try:
        # Apply execution mode explicity for every request
        is_test_mode = request.mode == ExecutionMode.TEST
        
        alert_system.config.TEST_MODE = is_test_mode
        alert_system.email_dispatcher.test_mode = is_test_mode
        
        # Execute based on project parameter
        if request.project:
            # Execute single project
            result = alert_system.process_single_project(request.project)
            
            if "error" in result:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result["error"]
                )
            
            return ExecuteResponse(
                success=True,
                timestamp=datetime.now(),
                mode=request.mode,
                projects_processed=1,
                total_activities=result.get("total_activities", 0),
                alerts_sent=result.get("alerts_sent", {}),
                errors=result.get("errors", [])
            )
        else:
            # Execute all projects
            result = alert_system.process_all_spreadsheets()
            
            return ExecuteResponse(
                success=True,
                timestamp=datetime.now(),
                mode=request.mode,
                projects_processed=result.get("total_spreadsheets", 0),
                total_activities=result.get("total_activities", 0),
                alerts_sent=result.get("alerts_sent", {}),
                errors=result.get("errors", [])
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Catch any unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execution failed: {str(e)}"
        )


# ============================================
# STATUS ENDPOINT
# ============================================

def get_status_info():
    """Dependency that returns system status"""
    return get_system_status()

# @router.get(
#     "/status",
#     response_model=StatusResponse,
#     summary="Get system status",
#     description="Returns the current status of the alert system."
# )
# async def get_status(alert_system: AlertSystem = Depends(get_alert_system)):
#     """
#     Get the current status of the system.
    
#     Returns information about:
#         - System health
#         - Test mode state
#         - Configured projects
#         - Execution schedule
    
#     Returns:
#         StatusResponse: System status information
#     """
#     status_info = get_system_status()
    
#     # Get configured projects from config
#     config = get_alert_system().config
#     configured_projects = list(config.SPREADSHEETS.keys())
    
#     return StatusResponse(
#         status="healthy" if status_info.get("alert_system_initialized", False) else "unhealthy",
#         timestamp=datetime.now(),
#         test_mode=status_info.get("test_mode", False),
#         configured_projects=configured_projects,
#         execution_hours=config.EXECUTION_HOUR,
#         total_alerts_sent_today=0,  # Future: implement metrics
#         last_execution=None  # Future: store last execution time
#     )

@router.get(
    "/status",
    response_model=StatusResponse,
    summary="Get system status",
    description="Returns the current status of the alert system."
)
async def get_status(
    alert_system: AlertSystem = Depends(get_alert_system),
    status_info: dict = Depends(get_status_info)
):
    """
    Get the current status of the system.
    """
    configured_projects = list(alert_system.config.SPREADSHEETS.keys())
    
    return StatusResponse(
        status="healthy" if status_info.get("alert_system_initialized", False) else "unhealthy",
        timestamp=datetime.now(),
        test_mode=status_info.get("test_mode", False),
        configured_projects=configured_projects,
        execution_hours=alert_system.config.EXECUTION_HOUR,
        total_alerts_sent_today=0,
        last_execution=None
    )
