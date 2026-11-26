from pydantic import BaseModel, Field


class ConnectAccountRequest(BaseModel):
    access_key_id: str = Field(..., min_length=16, description="AWS IAM Access Key ID (e.g. AKIA...)")
    secret_access_key: str = Field(..., min_length=16, description="AWS IAM Secret Access Key")
    region: str = Field("us-east-1", description="Default AWS region to target")
    session_token: str | None = Field(None, description="Optional AWS STS session token")
    account_id: str | None = Field(None, description="Optional 12-digit AWS Account ID")


class ConnectAzureRequest(BaseModel):
    subscription_id: str = Field(..., min_length=8, description="Azure Subscription ID (UUID)")
    tenant_id: str = Field(..., min_length=8, description="Azure Active Directory Tenant ID (UUID)")
    client_id: str = Field(..., min_length=8, description="Azure Service Principal Client ID")
    client_secret: str = Field(..., min_length=6, description="Azure Service Principal Client Secret")
    region: str = Field("eastus", description="Default Azure location")


class ConnectGCPRequest(BaseModel):
    project_id: str = Field(..., min_length=3, description="Google Cloud Project ID")
    service_account_email: str | None = Field(None, description="GCP Service Account email")
    credentials_json: str = Field(..., min_length=10, description="GCP Service Account JSON key or private key")
    region: str = Field("us-central1", description="Default GCP region")


class CloudProviderConnection(BaseModel):
    provider: str
    connected: bool
    is_demo: bool
    region: str
    identifier: str | None = None
    label: str | None = None
    verified_at: str | None = None
    message: str


class ConnectionStatusResponse(BaseModel):
    connected: bool
    is_demo: bool
    auth_method: str = "access_key"
    access_key_id_masked: str | None = None
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
    azure: CloudProviderConnection | None = None
    gcp: CloudProviderConnection | None = None


class LeastPrivilegePolicyResponse(BaseModel):
    external_id: str
    trust_policy: dict
    read_only_policy: dict
    provisioning_policy: dict
    setup_steps: list[str]
