import pytest
from app.api.dashboard import get_dashboard_summary
from app.api.aws_account import get_aws_status, get_policy_guide, toggle_demo_mode, DemoModeToggle
from app.api.inventory import get_inventory
from app.api.monitoring import get_monitoring_overview
from app.api.pricing import estimate_multi_cloud_costs
from app.schemas.pricing import CostEstimationRequest

def test_dashboard_summary_api():
    summary = get_dashboard_summary()
    assert summary["aws_connection"] is not None
    assert summary["resource_counts"]["total"] >= 0
    assert summary["estimated_monthly_spend"] >= 0
    assert "CloudForge" in summary["data_notice"]

def test_aws_account_api():
    status = get_aws_status()
    assert status.region is not None
    assert status.is_demo is True or status.connected is False or status.connected is True

    guide = get_policy_guide()
    assert guide.external_id is not None
    assert "Statement" in guide.trust_policy
    assert "Statement" in guide.read_only_policy
    assert len(guide.setup_steps) >= 4

    # Test toggling demo mode
    updated = toggle_demo_mode(DemoModeToggle(enabled=True))
    assert updated.is_demo is True

def test_inventory_api():
    inv = get_inventory(region="us-east-1")
    assert inv.region == "us-east-1"
    assert inv.total_count >= 0
    assert isinstance(inv.resources, list)
    if inv.is_demo:
        assert inv.total_count >= 1

def test_monitoring_api():
    mon = get_monitoring_overview(hours=6)
    assert mon.time_range_hours == 6
    assert isinstance(mon.metrics, list)
    if mon.is_demo:
        assert len(mon.metrics) >= 1
        assert len(mon.metrics[0].data_points) >= 1

def test_multi_cloud_pricing_api():
    req = CostEstimationRequest(
        compute_type="t3.medium",
        compute_count=2,
        storage_gb=50,
        db_enabled=True,
        db_class="db.t3.micro",
        nat_gateway_count=1
    )
    res = estimate_multi_cloud_costs(req)
    assert "aws" in res.providers
    assert "azure" in res.providers
    assert "gcp" in res.providers
    assert res.cheapest_provider.lower() in ["aws", "azure", "gcp"]
    assert len(res.arbitrage_insights) >= 1
