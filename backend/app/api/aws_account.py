from pydantic import BaseModel
from fastapi import APIRouter
from app.schemas.aws import ConnectAccountRequest, ConnectionStatusResponse, LeastPrivilegePolicyResponse
from app.services.aws_service import (
    get_connection_status,
    connect_with_role,
    disconnect_aws,
    set_demo_mode,
    get_least_privilege_policy_guide
)

router = APIRouter(prefix="/aws", tags=["AWS Connection"])

class DemoModeToggle(BaseModel):
    enabled: bool

@router.get("/status", response_model=ConnectionStatusResponse)
def get_aws_status():
    return get_connection_status()

@router.post("/connect", response_model=ConnectionStatusResponse)
def connect_account(req: ConnectAccountRequest):
    return connect_with_role(req)

@router.post("/disconnect", response_model=ConnectionStatusResponse)
def disconnect_account():
    return disconnect_aws()

@router.post("/demo-mode", response_model=ConnectionStatusResponse)
def toggle_demo_mode(req: DemoModeToggle):
    return set_demo_mode(req.enabled)

@router.get("/policy-guide", response_model=LeastPrivilegePolicyResponse)
def get_policy_guide():
    return get_least_privilege_policy_guide()
