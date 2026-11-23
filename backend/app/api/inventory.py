from fastapi import APIRouter, Query
from app.schemas.inventory import InventoryResponse
from app.services.aws_service import fetch_inventory

router = APIRouter(prefix="/inventory", tags=["Inventory"])

@router.get("/resources", response_model=InventoryResponse)
def get_inventory(region: str | None = Query(None, description="Filter by AWS Region")):
    return fetch_inventory(region)
