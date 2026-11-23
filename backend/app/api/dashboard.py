from fastapi import APIRouter
from app.services.aws_service import get_connection_status, fetch_inventory
from app.services.terraform_service import list_recent_operations
from app.core.audit import get_recent_audit_events
from app.core.config import REPORTS_DIR

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary")
def get_dashboard_summary():
    aws_conn = get_connection_status()
    inventory = fetch_inventory()
    recent_ops = list_recent_operations(10)
    audit_events = get_recent_audit_events(10)
    
    report_count = len(list(REPORTS_DIR.glob("*.pdf"))) if REPORTS_DIR.exists() else 0

    return {
        "aws_connection": aws_conn,
        "is_demo": aws_conn.is_demo,
        "resource_counts": {
            "total": inventory.total_count,
            "managed": inventory.managed_count,
            "discovered": inventory.discovered_count,
            "by_type": {
                "ec2": sum(1 for r in inventory.resources if r.resource_type == "ec2"),
                "vpc": sum(1 for r in inventory.resources if r.resource_type == "vpc"),
                "s3": sum(1 for r in inventory.resources if r.resource_type == "s3"),
                "rds": sum(1 for r in inventory.resources if r.resource_type == "rds"),
            }
        },
        "recent_operations": recent_ops,
        "audit_events": audit_events,
        "total_reports_generated": report_count,
        "estimated_monthly_spend": 135.50 if aws_conn.is_demo else 0.0,
        "data_notice": "Real AWS metrics or explicit CloudForge Demo Sandbox indicators applied."
    }
