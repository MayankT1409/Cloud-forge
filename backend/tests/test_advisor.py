import pytest
from app.schemas.advisor import QuestionnaireInput
from app.services.advisor_engine import analyze_and_recommend
from app.services.pdf_generator import generate_pdf_report

def test_advisor_default_recommendation():
    q = QuestionnaireInput()
    rec = analyze_and_recommend(q)
    
    assert rec.report_id.startswith("cfr-")
    assert rec.recommended_tier == "Standard Baseline"
    assert rec.estimated_monthly_cost > 0
    assert len(rec.recommended_services) >= 5
    assert len(rec.multi_cloud_mapping) >= 5
    assert "cheapest_cloud" in rec.multi_cloud_comparison
    assert "graph TD" in rec.diagram_mermaid

def test_advisor_high_scale_workload():
    q = QuestionnaireInput(
        app_type="microservices",
        concurrent_users=2500,
        daily_users=100000,
        cpu_cores=16,
        ram_gb=32,
        db_required=True,
        db_engine="aurora_postgres",
        multi_az=True,
        waf_required=True
    )
    rec = analyze_and_recommend(q)
    
    assert "High-Capacity" in rec.recommended_tier
    assert rec.compute_sizing["instance_count"] == 3
    service_names = [s.service_name for s in rec.recommended_services]
    assert any("Aurora" in s for s in service_names)

def test_pdf_generation_validity():
    q = QuestionnaireInput()
    rec = analyze_and_recommend(q)
    pdf_path = generate_pdf_report(rec, q)
    
    assert pdf_path.exists()
    assert pdf_path.suffix == ".pdf"
    assert pdf_path.stat().st_size > 5000
