import json
from fastapi import APIRouter, HTTPException, status
from app.schemas.advisor import QuestionnaireInput, RecommendationResponse
from app.services.advisor_engine import analyze_and_recommend
from app.services.pdf_generator import generate_pdf_report
from app.core.config import REPORTS_DIR

router = APIRouter(prefix="/advisor", tags=["Advisor"])

saved_recommendations: dict[str, dict] = {}

@router.post("/recommend", response_model=RecommendationResponse)
def get_recommendation(q: QuestionnaireInput):
    try:
        rec = analyze_and_recommend(q)
        pdf_path = generate_pdf_report(rec, q)
        
        saved_recommendations[rec.report_id] = {
            "recommendation": rec.model_dump(),
            "questionnaire": q.model_dump(),
            "pdf_file": pdf_path.name
        }

        meta_file = REPORTS_DIR / f"{rec.report_id}.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(saved_recommendations[rec.report_id], f, indent=2)

        return rec
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Advisor calculation failed: {str(e)}"
        )
