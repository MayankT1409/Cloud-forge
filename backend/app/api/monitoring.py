from fastapi import APIRouter, Query
from app.schemas.monitoring import MonitoringOverviewResponse
from app.services.aws_service import fetch_monitoring

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])

@router.get("/overview", response_model=MonitoringOverviewResponse)
def get_monitoring_overview(hours: int = Query(6, ge=1, le=168, description="Time range in hours")):
    return fetch_monitoring(hours)
