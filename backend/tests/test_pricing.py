from app.schemas.pricing import CostEstimationRequest
from app.services.pricing_service import calculate_costs, calculate_multi_cloud_costs

def test_pricing_calculation():
    req = CostEstimationRequest(
        region="us-east-1",
        compute_instance_type="t3.medium",
        compute_count=2,
        storage_gb=50,
        db_enabled=True,
        db_instance_class="db.t3.micro",
        db_storage_gb=20,
        db_multi_az=False,
        nat_gateway_count=1,
        bandwidth_gb=250,
        s3_storage_gb=100
    )
    res = calculate_costs(req)
    
    assert res.currency == "USD"
    assert res.total_monthly_usd > 0
    assert len(res.items) >= 5
    assert len(res.comparisons) == 3

def test_multi_cloud_pricing_comparison():
    req = CostEstimationRequest(
        region="us-east-1",
        compute_instance_type="t3.medium",
        compute_count=2,
        storage_gb=50,
        db_enabled=True,
        db_instance_class="db.t3.micro",
        db_storage_gb=20,
        db_multi_az=True,
        nat_gateway_count=1,
        bandwidth_gb=200,
        s3_storage_gb=100
    )
    res = calculate_multi_cloud_costs(req)
    
    assert "aws" in res.providers
    assert "azure" in res.providers
    assert "gcp" in res.providers
    assert res.providers["aws"].total_monthly_usd > 0
    assert res.providers["azure"].total_monthly_usd > 0
    assert res.providers["gcp"].total_monthly_usd > 0
    assert res.cheapest_provider in ("AWS", "Azure", "GCP")
    assert res.monthly_arbitrage_savings_usd >= 0
    assert len(res.arbitrage_insights) >= 3
