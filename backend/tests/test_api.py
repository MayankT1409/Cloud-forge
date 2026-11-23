from app.main import health_check, readiness_check
from app.api.dashboard import get_dashboard_summary
from app.api.pricing import estimate_infrastructure_costs
from app.api.advisor import get_recommendation
from app.api.reports import list_reports, get_report_json
from app.api.provisioning import create_plan, execute_apply, check_operation, get_operations
from app.api.aws_account import get_aws_status, toggle_demo_mode, DemoModeToggle, get_policy_guide
from app.api.inventory import get_inventory
from app.api.monitoring import get_monitoring_overview
from app.schemas.pricing import CostEstimationRequest
from app.schemas.advisor import QuestionnaireInput
from app.schemas.provisioning import ProvisioningDraft, ApplyRequest

def test_health_and_readiness_handlers():
    h = health_check()
    assert h["status"] == "healthy"
    assert h["version"] == "1.0.0"

    r = readiness_check()
    assert r["status"] == "ready"
    assert r["workspaces_writable"] is True

def test_dashboard_handler():
    d = get_dashboard_summary()
    assert "aws_connection" in d
    assert "resource_counts" in d
    assert d["resource_counts"]["total"] >= 4

def test_pricing_handler():
    req = CostEstimationRequest(
        region="us-east-1",
        compute_instance_type="t3.medium",
        compute_count=2,
        storage_gb=40,
        db_enabled=True,
        nat_gateway_count=1
    )
    res = estimate_infrastructure_costs(req)
    assert res.total_monthly_usd > 0
    assert len(res.items) >= 4
    assert res.currency == "USD"

def test_advisor_and_reports_handler():
    q = QuestionnaireInput(
        app_type="api_backend",
        runtime="Go / Gin",
        environment="staging",
        concurrent_users=300
    )
    rec = get_recommendation(q)
    assert rec.report_id.startswith("cfr-")
    assert rec.recommended_tier is not None

    reps = list_reports()
    assert any(r["report_id"] == rec.report_id for r in reps)

    stored = get_report_json(rec.report_id)
    assert "recommendation" in stored
    assert stored["recommendation"]["report_id"] == rec.report_id

def test_provisioning_plan_and_apply_handlers():
    draft = ProvisioningDraft(environment="dev", region="us-east-1")
    plan = create_plan(draft)
    assert plan.plan_id.startswith("plan-")
    assert plan.is_valid is True
    assert plan.resources_to_add > 0

    apply_req = ApplyRequest(plan_id=plan.plan_id, confirmation_phrase="CONFIRM")
    apply_res = execute_apply(apply_req)
    assert apply_res.operation_id.startswith("op-apply-")
    assert apply_res.status == "queued"

    op = check_operation(apply_res.operation_id)
    assert op.operation_id == apply_res.operation_id

    ops = get_operations()
    assert any(o.operation_id == apply_res.operation_id for o in ops)

def test_aws_account_handlers():
    demo_res = toggle_demo_mode(DemoModeToggle(enabled=True))
    assert demo_res.is_demo is True
    assert demo_res.connected is True

    status = get_aws_status()
    assert status.connected is True

    policy_guide = get_policy_guide()
    assert "Statement" in policy_guide.trust_policy
    assert len(policy_guide.setup_steps) >= 5

def test_inventory_and_monitoring_handlers():
    inv = get_inventory(None)
    assert inv.total_count >= 4
    assert len(inv.resources) > 0

    mon = get_monitoring_overview(hours=6)
    assert mon.has_metrics_permission is True
    assert len(mon.metrics) >= 2
