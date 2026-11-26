from pydantic import BaseModel
from fastapi import APIRouter
from app.schemas.aws import (
    ConnectAccountRequest,
    ConnectAzureRequest,
    ConnectGCPRequest,
    CloudProviderConnection,
    ConnectionStatusResponse,
    LeastPrivilegePolicyResponse,
)
from app.services.aws_service import (
    get_connection_status,
    connect_with_access_key,
    disconnect_aws,
    set_demo_mode,
    get_least_privilege_policy_guide,
    connect_azure,
    disconnect_azure,
    connect_gcp,
    disconnect_gcp,
)

router = APIRouter(prefix="/aws", tags=["AWS & Multi-Cloud Connection"])


class DemoModeToggle(BaseModel):
    enabled: bool


@router.get("/status", response_model=ConnectionStatusResponse)
def get_aws_status():
    return get_connection_status()


@router.post("/connect", response_model=ConnectionStatusResponse)
def connect_account(req: ConnectAccountRequest):
    return connect_with_access_key(req)


@router.post("/disconnect", response_model=ConnectionStatusResponse)
def disconnect_account():
    return disconnect_aws()


@router.post("/demo-mode", response_model=ConnectionStatusResponse)
def toggle_demo_mode(req: DemoModeToggle):
    return set_demo_mode(req.enabled)


@router.get("/policy-guide", response_model=LeastPrivilegePolicyResponse)
def get_policy_guide():
    return get_least_privilege_policy_guide()


@router.post("/azure/connect", response_model=CloudProviderConnection)
def connect_azure_account(req: ConnectAzureRequest):
    return connect_azure(req)


@router.post("/azure/disconnect", response_model=CloudProviderConnection)
def disconnect_azure_account():
    return disconnect_azure()


@router.post("/gcp/connect", response_model=CloudProviderConnection)
def connect_gcp_account(req: ConnectGCPRequest):
    return connect_gcp(req)


@router.post("/gcp/disconnect", response_model=CloudProviderConnection)
def disconnect_gcp_account():
    return disconnect_gcp()
