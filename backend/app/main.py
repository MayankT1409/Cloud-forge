from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.security import redact_secrets
from app.api import (
    dashboard,
    provisioning,
    advisor,
    reports,
    pricing,
    aws_account,
    inventory,
    monitoring
)

app = FastAPI(
    title="CloudForge API",
    description="Internal Developer Platform for Automated Infrastructure Provisioning, Multi-Cloud Cost Arbitrage & Architecture Recommendations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    clean_error = redact_secrets(str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": f"An internal server error occurred: {clean_error}"}
    )

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "CloudForge API",
        "demo_mode": settings.DEMO_MODE,
        "version": "1.0.0"
    }

@app.get("/ready")
def readiness_check():
    return {
        "status": "ready",
        "workspaces_writable": settings.WORKSPACE_DIR.exists(),
        "reports_writable": settings.REPORTS_DIR.exists()
    }

api_v1 = settings.API_V1_STR
app.include_router(dashboard.router, prefix=api_v1)
app.include_router(provisioning.router, prefix=api_v1)
app.include_router(advisor.router, prefix=api_v1)
app.include_router(reports.router, prefix=api_v1)
app.include_router(pricing.router, prefix=api_v1)
app.include_router(aws_account.router, prefix=api_v1)
app.include_router(inventory.router, prefix=api_v1)
app.include_router(monitoring.router, prefix=api_v1)

# Serve compiled frontend assets if available
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
