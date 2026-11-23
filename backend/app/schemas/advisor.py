from typing import Literal
from pydantic import BaseModel, Field

AppType = Literal[
    "static_website",
    "web_application",
    "api_backend",
    "background_worker",
    "data_processing",
    "microservices"
]

EnvironmentType = Literal["development", "staging", "production"]

class QuestionnaireInput(BaseModel):
    # App profile
    app_type: AppType = Field("web_application", description="Type of application")
    runtime: str = Field("Python / FastAPI", description="Programming language and runtime")
    environment: EnvironmentType = Field("production", description="Deployment environment")
    
    # Traffic & Scale
    daily_users: int = Field(5000, ge=0, description="Expected daily active users")
    concurrent_users: int = Field(200, ge=0, description="Peak concurrent users")
    traffic_pattern: Literal["steady", "spiky", "predictable_peaks"] = Field("steady", description="Traffic behavior")
    scaling_required: bool = Field(True, description="Whether automated scaling is required")
    
    # Compute & Storage Sizing
    cpu_cores: int = Field(2, ge=1, le=128, description="Estimated compute CPU cores")
    ram_gb: int = Field(4, ge=1, le=512, description="Estimated RAM in GB")
    storage_gb: int = Field(50, ge=5, le=10000, description="Estimated block storage in GB")
    bandwidth_gb_month: int = Field(100, ge=1, le=100000, description="Estimated monthly outbound bandwidth in GB")
    
    # Database
    db_required: bool = Field(True, description="Whether relational or document DB is required")
    db_engine: Literal["postgres", "mysql", "aurora_postgres", "aurora_mysql", "dynamodb", "none"] = Field("postgres")
    db_size_gb: int = Field(20, ge=0, le=10000, description="Allocated database storage in GB")
    db_connections: int = Field(50, ge=1, le=5000, description="Expected concurrent database connections")
    
    # Object Storage & Files
    file_storage_required: bool = Field(True, description="Need S3 bucket for uploads/assets")
    file_storage_gb: int = Field(100, ge=0, description="Estimated object storage in GB")
    
    # Networking & Security
    network_access: Literal["public_facing", "private_vpc", "hybrid_vpn"] = Field("public_facing")
    encryption_at_rest: bool = Field(True, description="Enforce AWS KMS encryption at rest")
    encryption_in_transit: bool = Field(True, description="Enforce TLS/HTTPS")
    waf_required: bool = Field(False, description="Deploy AWS WAF for DDoS/OWASP protection")
    
    # Availability & Backup
    multi_az: bool = Field(True, description="Multi-Availability Zone redundancy")
    sla_target: Literal["99.0", "99.9", "99.99"] = Field("99.9", description="Target availability SLA percentage")
    backup_retention_days: int = Field(7, ge=0, le=365, description="Automated backup retention days")
    
    # Budget & Region
    monthly_budget_usd: float = Field(200.0, ge=10.0, description="Target monthly budget in USD")
    preferred_region: str = Field("us-east-1", description="Target AWS region")
    existing_constraints: str = Field("", description="Any existing VPCs, compliance or tech stack constraints")

class RecommendedService(BaseModel):
    service_name: str
    category: str
    purpose: str
    configuration_details: str
    is_required: bool
    rationale: str

class AlternativeOption(BaseModel):
    tier_name: str
    description: str
    monthly_cost_estimate: float
    tradeoffs: list[str]
    services_summary: list[str]

class MultiCloudServiceMapping(BaseModel):
    tier_component: str
    aws_service: str
    azure_service: str
    gcp_service: str
    portability_guidance: str

class RecommendationResponse(BaseModel):
    report_id: str
    created_at: str
    executive_summary: str
    recommended_tier: str
    recommended_services: list[RecommendedService]
    compute_sizing: dict
    database_sizing: dict
    networking_and_security: list[str]
    disaster_recovery_plan: list[str]
    monitoring_and_logging: list[str]
    estimated_monthly_cost: float
    estimated_annual_cost: float
    cost_currency: str = "USD"
    alternatives: list[AlternativeOption]
    multi_cloud_mapping: list[MultiCloudServiceMapping] = []
    multi_cloud_comparison: dict = {}
    risks_and_bottlenecks: list[str]
    step_by_step_implementation_plan: list[str]
    diagram_mermaid: str
    assumptions: list[str]
    is_demo: bool = False
