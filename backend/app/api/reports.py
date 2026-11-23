import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from app.core.config import REPORTS_DIR
from app.api.advisor import saved_recommendations

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("")
def list_reports():
    reports = []
    if REPORTS_DIR.exists():
        for json_file in REPORTS_DIR.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    rec = data.get("recommendation", {})
                    reports.append({
                        "report_id": rec.get("report_id"),
                        "created_at": rec.get("created_at"),
                        "recommended_tier": rec.get("recommended_tier"),
                        "estimated_monthly_cost": rec.get("estimated_monthly_cost"),
                        "pdf_available": (REPORTS_DIR / f"CloudForge_Report_{rec.get('report_id')}.pdf").exists()
                    })
            except Exception:
                continue
    return sorted(reports, key=lambda x: x.get("created_at", ""), reverse=True)

@router.get("/{report_id}")
def get_report_json(report_id: str):
    json_file = REPORTS_DIR / f"{report_id}.json"
    if json_file.exists():
        with open(json_file, "r", encoding="utf-8") as f:
            return json.load(f)
    if report_id in saved_recommendations:
        return saved_recommendations[report_id]
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

@router.get("/{report_id}/pdf")
def download_pdf_report(report_id: str):
    pdf_file = REPORTS_DIR / f"CloudForge_Report_{report_id}.pdf"
    if not pdf_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF report for '{report_id}' not found."
        )
    return FileResponse(
        path=str(pdf_file),
        media_type="application/pdf",
        filename=pdf_file.name
    )
