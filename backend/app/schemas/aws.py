from pydantic import BaseModel, Field

class ConnectAccountRequest(BaseModel):
    role_arn: str = Field(..., description="AWS IAM Role ARN with trust relationship to CloudForge")
    external_id: str = Field(..., description="Unique External ID used in trust policy")
    account_id: str = Field(..., description="12-digit AWS Account ID")
    region: str = Field("us-east-1", description="Default AWS region to target")

class ConnectionStatusResponse(BaseModel):
    connected: bool
    is_demo: bool
    account_id: str | None = None
    role_arn: str | None = None
    region: str
    arn: str | None = None
    user_id: str | None = None
    verified_at: str | None = None
    read_only_access: bool = False
    provisioning_access: bool = False
    missing_permissions: list[str] = []
    message: str

class LeastPrivilegePolicyResponse(BaseModel):
    external_id: str
    trust_policy: dict
    read_only_policy: dict
    provisioning_policy: dict
    setup_steps: list[str]
