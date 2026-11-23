from typing import Literal
from pydantic import BaseModel, Field

class CostItem(BaseModel):
    category: Literal["compute", "storage", "database", "networking", "management", "other"]
    resource_name: str
    unit: str
    unit_price_usd: float
    quantity: float
    monthly_cost_usd: float
    assumptions: str

class PricingComparison(BaseModel):
    tier: str
    monthly_cost_usd: float
    summary: str
    key_differences: list[str]

class CostEstimationRequest(BaseModel):
    region: str = "us-east-1"
    compute_instance_type: str = "t3.medium"
    compute_count: int = 1
    storage_gb: int = 50
    db_enabled: bool = True
    db_instance_class: str = "db.t3.micro"
    db_storage_gb: int = 20
    db_multi_az: bool = False
    nat_gateway_count: int = 1
    bandwidth_gb: int = 100
    s3_storage_gb: int = 50

class ProviderCostBreakdown(BaseModel):
    provider: Literal["aws", "azure", "gcp"]
    provider_name: str
    region_name: str
    monthly_compute_usd: float
    monthly_storage_usd: float
    monthly_database_usd: float
    monthly_networking_usd: float
    total_monthly_usd: float
    total_annual_usd: float
    items: list[CostItem]

class MultiCloudCostComparison(BaseModel):
    currency: str = "USD"
    pricing_date: str
    data_source: str
    providers: dict[str, ProviderCostBreakdown]
    cheapest_provider: str
    most_expensive_provider: str
    monthly_arbitrage_savings_usd: float
    annual_arbitrage_savings_usd: float
    arbitrage_insights: list[str]

class CostEstimationResponse(BaseModel):
    region: str
    currency: str = "USD"
    pricing_date: str
    data_source: str
    total_monthly_usd: float
    total_annual_usd: float
    items: list[CostItem]
    comparisons: list[PricingComparison]
    disclaimers: list[str]
    is_live_aws_quote: bool = False
