"""
Main entry point for the FastAPI application.

This module creates and configures the FastAPI application,
includes all routers, and provides a function to run the server.

Usage:
    uvicorn main:app --reload
    
    Or directly:
    python main.py
"""

from fastapi import FastAPI
from src.api import router
from src.dependencies import get_alert_system, is_ready
from src.models import HealthResponse


# ============================================
# CREATE APPLICATION
# ============================================

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured application instance
    """
    app = FastAPI(
        title="Sistema de Alertas de Atividades",
        description="""
        API para monitoramento de atividades em planilhas Google Sheets.
        
        Funcionalidades:
        - Leitura automática de planilhas
        - Disparo de alertas por email
        - Suporte a múltiplos projetos
        - Modo de teste para validação
        """,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        contact={
            "name": "NATS - Núcleo de Avaliação de Tecnologias em Saúde",
            "email": "seuemail@exemplo.com",
        },
        license_info={
            "name": "MIT"
        },
    )

    
    # Include the API router
    app.include_router(router)
    
    # ============================================
    # ROOT ENDPOINT
    # ============================================
    
    @app.get("/", tags=["Root"])
    async def root():
        """
        Root endpoint - returns basic system information.
        
        This is a simple welcome endpoint that shows the API is running.
        """
        return {
            "name": "Sistema de Alertas de Atividades",
            "version": "1.0.0",
            "docs": "/docs",
            "status": "online"
        }
    
    # ============================================
    # HEALTH CHECK (without prefix)
    # ============================================
    
    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health_check():
        """
        Health check endpoint for Cloud Run and monitoring tools.
        """
        # Check if system is initialized
        if not is_ready():
            return HealthResponse(
                status="degraded",
                google_sheets_api=False,
                smtp_configured=False,
                sheets_accessible=[]
            )
        
        # Get alert system to check connections
        alert_system = get_alert_system()
        
        # Check Google Sheets accessibility
        sheets_accessible = []
        google_sheets_ok = True
        
        try:
            for project_name, sheet_id in alert_system.config.SPREADSHEETS.items():
                if sheet_id:
                    try:
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
    
    return app


# ============================================
# CREATE APPLICATION INSTANCE
# ============================================

app = create_app()


# ============================================
# RUN SERVER (development only)
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
