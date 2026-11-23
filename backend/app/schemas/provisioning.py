from typing import Literal
from pydantic import BaseModel, Field

class VPCConfig(BaseModel):
    enabled: bool = True
    name: str = Field("cloudforge-vpc", min_length=2, max_length=64)
    cidr_block: str = Field("10.0.0.0/16")
    enable_nat_gateway: bool = Field(True, description="Enables outbound internet for private subnets")
    single_nat_gateway: bool = Field(True, description="Single NAT GW to optimize costs vs Multi-AZ NAT")
    public_subnet_cidrs: list[str] = Field(default_factory=lambda: ["10.0.1.0/24", "10.0.2.0/24"])
    private_subnet_cidrs: list[str] = Field(default_factory=lambda: ["10.0.10.0/24", "10.0.20.0/24"])

class EC2Config(BaseModel):
    enabled: bool = True
    name: str = Field("cloudforge-app-server", min_length=2, max_length=64)
    instance_type: str = Field("t3.medium")
    ami_id: str = Field("ami-0c7217cdde317cfec", description="Amazon Linux 2023 or custom AMI")
    root_volume_size_gb: int = Field(30, ge=10, le=1000)
    root_volume_type: Literal["gp3", "gp2"] = "gp3"
    associate_public_ip: bool = False
    enable_imds_v2: bool = True
    user_data_base64: str | None = None

class S3Config(BaseModel):
    enabled: bool = True
    bucket_name_prefix: str = Field("cloudforge-storage", min_length=3, max_length=50)
    versioning_enabled: bool = True
    block_public_access: bool = True
    server_side_encryption: Literal["AES256", "aws:kms"] = "AES256"

class RDSConfig(BaseModel):
    enabled: bool = False
    db_identifier: str = Field("cloudforge-db", min_length=3, max_length=63)
    engine: Literal["postgres", "mysql"] = "postgres"
    engine_version: str = Field("15.4")
    instance_class: str = Field("db.t3.micro")
    allocated_storage_gb: int = Field(20, ge=20, le=1000)
    storage_type: Literal["gp3", "gp2"] = "gp3"
    multi_az: bool = False
    publicly_accessible: bool = False
    backup_retention_period: int = Field(7, ge=0, le=35)
    deletion_protection: bool = True

class IAMConfig(BaseModel):
    enabled: bool = True
    role_name: str = Field("cloudforge-ec2-role", min_length=3, max_length=64)
    attach_ssm_policy: bool = Field(True, description="AmazonSSMManagedInstanceCore for secure SSH-free management")
    attach_s3_readonly: bool = True

class ProvisioningDraft(BaseModel):
    environment: Literal["dev", "staging", "prod"] = "dev"
    region: str = Field("us-east-1")
    tags: dict[str, str] = Field(default_factory=lambda: {"Project": "CloudForge", "ManagedBy": "Terraform"})
    vpc: VPCConfig = Field(default_factory=VPCConfig)
    ec2: EC2Config = Field(default_factory=EC2Config)
    s3: S3Config = Field(default_factory=S3Config)
    rds: RDSConfig = Field(default_factory=RDSConfig)
    iam: IAMConfig = Field(default_factory=IAMConfig)

class PlanRequest(BaseModel):
    config: ProvisioningDraft

class PlanResponse(BaseModel):
    plan_id: str
    workspace_name: str
    is_valid: bool
    validation_output: str
    plan_output: str
    resources_to_add: int
    resources_to_change: int
    resources_to_destroy: int
    resource_changes: list[dict]
    estimated_monthly_cost: float
    risks_identified: list[str]
    has_destructive_actions: bool
    state_locked: bool
    generated_terraform_code: str

class ApplyRequest(BaseModel):
    plan_id: str
    confirmation_phrase: str = Field(..., description="Must explicitly confirm operation")

class ApplyResponse(BaseModel):
    operation_id: str
    status: Literal["queued", "running", "succeeded", "failed"]
    started_at: str
    message: str

class DestroyRequest(BaseModel):
    plan_id: str
    confirmation_phrase: str = Field(..., description="Must type 'DESTROY' to proceed with teardown")

class OperationRecord(BaseModel):
    operation_id: str
    plan_id: str
    action: Literal["plan", "apply", "destroy"]
    status: Literal["queued", "running", "succeeded", "failed"]
    started_at: str
    completed_at: str | None = None
    exit_code: int | None = None
    raw_logs: str = ""
    outputs: dict[str, str] = Field(default_factory=dict)
    error_message: str | None = None
