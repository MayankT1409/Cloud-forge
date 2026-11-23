from fastapi import APIRouter
from app.schemas.pricing import CostEstimationRequest, CostEstimationResponse, MultiCloudCostComparison
from app.services.pricing_service import calculate_costs, calculate_multi_cloud_costs

router = APIRouter(prefix="/pricing", tags=["Pricing"])

@router.post("/estimate", response_model=CostEstimationResponse)
def estimate_infrastructure_costs(req: CostEstimationRequest):
    return calculate_costs(req)

@router.post("/multi-cloud-estimate", response_model=MultiCloudCostComparison)
def estimate_multi_cloud_costs(req: CostEstimationRequest):
    return calculate_multi_cloud_costs(req)
