from typing import Literal
from pydantic import BaseModel, Field

class ResourceItem(BaseModel):
    id: str
    name: str
    resource_type: Literal["ec2", "vpc", "s3", "rds", "iam_role", "subnet", "nat_gateway"]
    region: str
    status: str
    created_at: str | None = None
    managed_by: Literal["cloudforge", "aws_native", "untracked"]
    tags: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, str] = Field(default_factory=dict)

class InventoryResponse(BaseModel):
    account_id: str
    region: str
    is_demo: bool
    total_count: int
    managed_count: int
    discovered_count: int
    permission_status: dict[str, bool]
    errors: list[str] = []
    resources: list[ResourceItem]
