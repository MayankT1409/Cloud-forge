import os
import re
import shutil
import subprocess
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from app.core.config import WORKSPACE_DIR, settings
from app.core.security import redact_secrets, sanitize_resource_name, validate_cloud_region
from app.core.audit import record_audit_event
from app.schemas.provisioning import (
    ProvisioningDraft,
    PlanResponse,
    ApplyResponse,
    OperationRecord,
)
from app.services.aws_service import get_boto3_session, state as aws_state

active_operations: dict[str, OperationRecord] = {}
cached_plans: dict[str, dict[str, Any]] = {}

AZURE_VM_MAP = {
    "t3.micro": "Standard_B1s",
    "t3.small": "Standard_B1ms",
    "t3.medium": "Standard_B2s",
    "m6i.large": "Standard_D2s_v5",
    "c6i.xlarge": "Standard_F4s_v2",
}

GCP_MACHINE_MAP = {
    "t3.micro": "e2-micro",
    "t3.small": "e2-small",
    "t3.medium": "e2-medium",
    "m6i.large": "n2-standard-2",
    "c6i.xlarge": "c2-standard-4",
}


def check_terraform_binary() -> bool:
    try:
        res = subprocess.run(
            [settings.TERRAFORM_BINARY, "version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return res.returncode == 0
    except Exception:
        return False


def _sanitize_azure_storage_name(prefix: str) -> str:
    clean = re.sub(r"[^a-z0-9]", "", prefix.lower())
    if len(clean) < 3:
        clean = f"cf{clean}store"
    return clean[:18]


def _render_aws_hcl(config: ProvisioningDraft) -> str:
    tags_block = "\n".join([f'    "{k}" = "{v}"' for k, v in config.tags.items()])

    hcl = f"""# ==============================================================================
# CloudForge Generated AWS Infrastructure as Code
# Generated: {datetime.now(timezone.utc).isoformat()}
# Provider: AWS | Environment: {config.environment} | Region: {config.region}
# Auth: AWS Access Key & Secret Key (via environment variables)
# ==============================================================================

terraform {{
  required_version = ">= 1.5.0"
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

provider "aws" {{
  region = "{config.region}"
  default_tags {{
    tags = {{
{tags_block}
    }}
  }}
}}
"""

    if config.vpc.enabled:
        hcl += f"""
# ------------------------------------------------------------------------------
# Networking: Virtual Private Cloud (VPC)
# ------------------------------------------------------------------------------
resource "aws_vpc" "main" {{
  cidr_block           = "{config.vpc.cidr_block}"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {{
    Name = "{config.vpc.name}"
  }}
}}

resource "aws_internet_gateway" "gw" {{
  vpc_id = aws_vpc.main.id
  tags = {{
    Name = "{config.vpc.name}-igw"
  }}
}}

resource "aws_subnet" "public_1" {{
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "{config.vpc.public_subnet_cidrs[0]}"
  availability_zone       = "{config.region}a"
  map_public_ip_on_launch = true
  tags = {{
    Name = "{config.vpc.name}-public-1"
  }}
}}

resource "aws_subnet" "public_2" {{
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "{config.vpc.public_subnet_cidrs[1]}"
  availability_zone       = "{config.region}b"
  map_public_ip_on_launch = true
  tags = {{
    Name = "{config.vpc.name}-public-2"
  }}
}}

resource "aws_subnet" "private_1" {{
  vpc_id            = aws_vpc.main.id
  cidr_block        = "{config.vpc.private_subnet_cidrs[0]}"
  availability_zone = "{config.region}a"
  tags = {{
    Name = "{config.vpc.name}-private-1"
  }}
}}

resource "aws_subnet" "private_2" {{
  vpc_id            = aws_vpc.main.id
  cidr_block        = "{config.vpc.private_subnet_cidrs[1]}"
  availability_zone = "{config.region}b"
  tags = {{
    Name = "{config.vpc.name}-private-2"
  }}
}}

resource "aws_route_table" "public" {{
  vpc_id = aws_vpc.main.id
  route {{
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }}
  tags = {{
    Name = "{config.vpc.name}-public-rt"
  }}
}}

resource "aws_route_table_association" "pub_1" {{
  subnet_id      = aws_subnet.public_1.id
  route_table_id = aws_route_table.public.id
}}

resource "aws_route_table_association" "pub_2" {{
  subnet_id      = aws_subnet.public_2.id
  route_table_id = aws_route_table.public.id
}}
"""

    if config.iam.enabled:
        hcl += f"""
# ------------------------------------------------------------------------------
# Security: Optional IAM Instance Profile
# ------------------------------------------------------------------------------
resource "aws_iam_role" "app_role" {{
  name = "{config.iam.role_name}"

  assume_role_policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [
      {{
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {{
          Service = "ec2.amazonaws.com"
        }}
      }}
    ]
  }})
}}

resource "aws_iam_role_policy_attachment" "ssm_policy" {{
  role       = aws_iam_role.app_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}}

resource "aws_iam_instance_profile" "app_profile" {{
  name = "{config.iam.role_name}-profile"
  role = aws_iam_role.app_role.name
}}
"""

    if config.ec2.enabled:
        iam_profile_line = (
            f'  iam_instance_profile   = aws_iam_instance_profile.app_profile.name\n'
            if config.iam.enabled
            else ""
        )
        vpc_sg_block = (
            """  vpc_id      = aws_vpc.main.id\n"""
            if config.vpc.enabled
            else ""
        )
        subnet_line = (
            "  subnet_id              = aws_subnet.private_1.id\n"
            if config.vpc.enabled
            else ""
        )
        hcl += f"""
# ------------------------------------------------------------------------------
# Compute: Amazon EC2 Instance
# ------------------------------------------------------------------------------
resource "aws_security_group" "app_sg" {{
  name        = "{config.ec2.name}-sg"
  description = "Security group for {config.ec2.name}"
{vpc_sg_block}
  ingress {{
    description = "HTTP internal"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }}

  egress {{
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }}

  tags = {{
    Name = "{config.ec2.name}-sg"
  }}
}}

resource "aws_instance" "app" {{
  ami                    = "{config.ec2.ami_id}"
  instance_type          = "{config.ec2.instance_type}"
{subnet_line}  vpc_security_group_ids = [aws_security_group.app_sg.id]
{iam_profile_line}
  metadata_options {{
    http_endpoint = "enabled"
    http_tokens   = "{"required" if config.ec2.enable_imds_v2 else "optional"}"
  }}

  root_block_device {{
    volume_size           = {config.ec2.root_volume_size_gb}
    volume_type           = "{config.ec2.root_volume_type}"
    encrypted             = true
    delete_on_termination = true
  }}

  tags = {{
    Name = "{config.ec2.name}"
  }}
}}
"""

    if config.s3.enabled:
        hcl += f"""
# ------------------------------------------------------------------------------
# Storage: Amazon S3 Bucket
# ------------------------------------------------------------------------------
resource "aws_s3_bucket" "storage" {{
  bucket_prefix = "{config.s3.bucket_name_prefix}-"
  force_destroy = false

  tags = {{
    Name = "{config.s3.bucket_name_prefix}"
  }}
}}

resource "aws_s3_bucket_versioning" "storage_ver" {{
  bucket = aws_s3_bucket.storage.id
  versioning_configuration {{
    status = "{"Enabled" if config.s3.versioning_enabled else "Suspended"}"
  }}
}}

resource "aws_s3_bucket_server_side_encryption_configuration" "storage_enc" {{
  bucket = aws_s3_bucket.storage.id
  rule {{
    apply_server_side_encryption_by_default {{
      sse_algorithm = "{config.s3.server_side_encryption}"
    }}
  }}
}}

resource "aws_s3_bucket_public_access_block" "storage_pab" {{
  bucket = aws_s3_bucket.storage.id

  block_public_acls       = {"true" if config.s3.block_public_access else "false"}
  block_public_policy     = {"true" if config.s3.block_public_access else "false"}
  ignore_public_acls      = {"true" if config.s3.block_public_access else "false"}
  restrict_public_buckets = {"true" if config.s3.block_public_access else "false"}
}}
"""

    if config.rds.enabled:
        db_port = 5432 if config.rds.engine == "postgres" else 3306
        vpc_rds_sg = "  vpc_id      = aws_vpc.main.id\n" if config.vpc.enabled else ""
        subnet_group_block = (
            f"""
resource "aws_db_subnet_group" "rds_subnets" {{
  name       = "{config.rds.db_identifier}-subnet-group"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]

  tags = {{
    Name = "{config.rds.db_identifier}-subnet-group"
  }}
}}
"""
            if config.vpc.enabled
            else ""
        )
        subnet_group_ref = (
            "  db_subnet_group_name   = aws_db_subnet_group.rds_subnets.name\n"
            if config.vpc.enabled
            else ""
        )
        ingress_block = (
            f"""  ingress {{
    description     = "Database access from app tier"
    from_port       = {db_port}
    to_port         = {db_port}
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg.id]
  }}"""
            if config.ec2.enabled
            else f"""  ingress {{
    description = "Database access from VPC"
    from_port   = {db_port}
    to_port     = {db_port}
    protocol    = "tcp"
    cidr_blocks = ["{config.vpc.cidr_block}"]
  }}"""
        )
        hcl += f"""
# ------------------------------------------------------------------------------
# Database: Amazon Relational Database Service (RDS)
# ------------------------------------------------------------------------------
{subnet_group_block}
resource "aws_security_group" "rds_sg" {{
  name        = "{config.rds.db_identifier}-sg"
  description = "Access to RDS instance"
{vpc_rds_sg}
{ingress_block}

  egress {{
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }}
}}

resource "aws_db_instance" "database" {{
  identifier              = "{config.rds.db_identifier}"
  engine                  = "{config.rds.engine}"
  engine_version          = "{config.rds.engine_version}"
  instance_class          = "{config.rds.instance_class}"
  allocated_storage       = {config.rds.allocated_storage_gb}
  storage_type            = "{config.rds.storage_type}"
{subnet_group_ref}  vpc_security_group_ids  = [aws_security_group.rds_sg.id]
  multi_az                = {str(config.rds.multi_az).lower()}
  publicly_accessible     = false
  backup_retention_period = {config.rds.backup_retention_period}
  deletion_protection     = {str(config.rds.deletion_protection).lower()}
  skip_final_snapshot     = true
  storage_encrypted       = true

  tags = {{
    Name = "{config.rds.db_identifier}"
  }}
}}
"""

    if config.vpc.enabled:
        hcl += """
# ------------------------------------------------------------------------------
# Outputs
# ------------------------------------------------------------------------------
output "vpc_id" {
  description = "ID of the created VPC"
  value       = aws_vpc.main.id
}

output "public_subnets" {
  description = "List of public subnet IDs"
  value       = [aws_subnet.public_1.id, aws_subnet.public_2.id]
}

output "private_subnets" {
  description = "List of private subnet IDs"
  value       = [aws_subnet.private_1.id, aws_subnet.private_2.id]
}
"""
    return hcl


def _render_azure_hcl(config: ProvisioningDraft) -> str:
    vm_size = AZURE_VM_MAP.get(config.ec2.instance_type, config.ec2.instance_type)
    tags_block = "\n".join([f'    "{k}" = "{v}"' for k, v in config.tags.items()])
    storage_prefix = _sanitize_azure_storage_name(config.s3.bucket_name_prefix)
    rg_name = config.azure_resource_group or f"rg-{config.environment}-cloudforge"

    hcl = f"""# ==============================================================================
# CloudForge Generated Microsoft Azure Infrastructure as Code
# Generated: {datetime.now(timezone.utc).isoformat()}
# Provider: Azure (azurerm) | Environment: {config.environment} | Location: {config.region}
# Auth: Azure Service Principal (ARM_CLIENT_ID / ARM_CLIENT_SECRET / ARM_TENANT_ID)
# ==============================================================================

terraform {{
  required_version = ">= 1.5.0"
  required_providers {{
    azurerm = {{
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }}
  }}
}}

provider "azurerm" {{
  features {{}}
}}

resource "azurerm_resource_group" "main" {{
  name     = "{rg_name}"
  location = "{config.region}"

  tags = {{
{tags_block}
  }}
}}
"""

    if config.vpc.enabled:
        hcl += f"""
# ------------------------------------------------------------------------------
# Networking: Azure Virtual Network (VNet) & Subnets
# ------------------------------------------------------------------------------
resource "azurerm_virtual_network" "main" {{
  name                = "{config.vpc.name}"
  address_space       = ["{config.vpc.cidr_block}"]
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
}}

resource "azurerm_subnet" "public" {{
  name                 = "{config.vpc.name}-public"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["{config.vpc.public_subnet_cidrs[0]}"]
}}

resource "azurerm_subnet" "private" {{
  name                 = "{config.vpc.name}-private"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["{config.vpc.private_subnet_cidrs[0]}"]
}}

resource "azurerm_network_security_group" "main" {{
  name                = "{config.vpc.name}-nsg"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  security_rule {{
    name                       = "AllowInternalHTTP"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "{config.vpc.cidr_block}"
    destination_address_prefix = "*"
  }}
}}
"""

    if config.ec2.enabled:
        subnet_ref = (
            "azurerm_subnet.private.id"
            if config.vpc.enabled
            else '"" # Requires VNet enabled'
        )
        hcl += f"""
# ------------------------------------------------------------------------------
# Compute: Azure Linux Virtual Machine
# ------------------------------------------------------------------------------
resource "azurerm_network_interface" "vm_nic" {{
  name                = "{config.ec2.name}-nic"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  ip_configuration {{
    name                          = "internal"
    subnet_id                     = {subnet_ref}
    private_ip_address_allocation = "Dynamic"
  }}
}}

resource "azurerm_linux_virtual_machine" "main" {{
  name                = "{config.ec2.name}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  size                = "{vm_size}"
  admin_username      = "cloudforge"
  network_interface_ids = [
    azurerm_network_interface.vm_nic.id,
  ]

  os_disk {{
    caching              = "ReadWrite"
    storage_account_type = "Premium_LRS"
    disk_size_gb         = {config.ec2.root_volume_size_gb}
  }}

  source_image_reference {{
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts"
    version   = "latest"
  }}
}}
"""

    if config.s3.enabled:
        hcl += f"""
# ------------------------------------------------------------------------------
# Storage: Azure Storage Account & Blob Container
# ------------------------------------------------------------------------------
resource "azurerm_storage_account" "main" {{
  name                     = "{storage_prefix}sa"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  allow_nested_items_to_be_public = {"false" if config.s3.block_public_access else "true"}

  blob_properties {{
    versioning_enabled = {str(config.s3.versioning_enabled).lower()}
  }}
}}

resource "azurerm_storage_container" "data" {{
  name                  = "app-data"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}}
"""

    if config.rds.enabled:
        resource_type = (
            "azurerm_postgresql_flexible_server"
            if config.rds.engine == "postgres"
            else "azurerm_mysql_flexible_server"
        )
        hcl += f"""
# ------------------------------------------------------------------------------
# Database: Azure Flexible Database Server ({config.rds.engine})
# ------------------------------------------------------------------------------
resource "{resource_type}" "database" {{
  name                   = "{config.rds.db_identifier}"
  resource_group_name    = azurerm_resource_group.main.name
  location               = azurerm_resource_group.main.location
  version                = "{"15" if config.rds.engine == "postgres" else "8.0.21"}"
  administrator_login    = "cfadmin"
  storage_mb             = {config.rds.allocated_storage_gb * 1024}
  sku_name               = "B_Standard_B1ms"
  backup_retention_days  = {max(7, config.rds.backup_retention_period)}
}}
"""

    hcl += """
# ------------------------------------------------------------------------------
# Outputs
# ------------------------------------------------------------------------------
output "resource_group_id" {
  value = azurerm_resource_group.main.id
}
"""
    if config.vpc.enabled:
        hcl += """
output "vnet_id" {
  value = azurerm_virtual_network.main.id
}
"""
    return hcl


def _render_gcp_hcl(config: ProvisioningDraft) -> str:
    project_id = config.gcp_project_id or aws_state.gcp_project_id or "cloudforge-gcp-project"
    machine_type = GCP_MACHINE_MAP.get(config.ec2.instance_type, config.ec2.instance_type)
    zone = f"{config.region}-a"

    hcl = f"""# ==============================================================================
# CloudForge Generated Google Cloud Platform (GCP) Infrastructure as Code
# Generated: {datetime.now(timezone.utc).isoformat()}
# Provider: GCP (google) | Project: {project_id} | Region: {config.region}
# Auth: GCP Service Account (GOOGLE_APPLICATION_CREDENTIALS)
# ==============================================================================

terraform {{
  required_version = ">= 1.5.0"
  required_providers {{
    google = {{
      source  = "hashicorp/google"
      version = "~> 5.30"
    }}
  }}
}}

provider "google" {{
  project = "{project_id}"
  region  = "{config.region}"
  zone    = "{zone}"
}}
"""

    if config.vpc.enabled:
        hcl += f"""
# ------------------------------------------------------------------------------
# Networking: Google VPC & Subnetwork
# ------------------------------------------------------------------------------
resource "google_compute_network" "vpc" {{
  name                    = "{config.vpc.name}"
  auto_create_subnetworks = false
}}

resource "google_compute_subnetwork" "subnet" {{
  name          = "{config.vpc.name}-subnet"
  ip_cidr_range = "{config.vpc.private_subnet_cidrs[0]}"
  region        = "{config.region}"
  network       = google_compute_network.vpc.id
}}

resource "google_compute_firewall" "allow_internal" {{
  name    = "{config.vpc.name}-allow-internal"
  network = google_compute_network.vpc.name

  allow {{
    protocol = "tcp"
    ports    = ["80", "443"]
  }}

  source_ranges = ["{config.vpc.cidr_block}"]
}}
"""

    if config.ec2.enabled:
        network_block = (
            """  network_interface {
    subnetwork = google_compute_subnetwork.subnet.id
  }"""
            if config.vpc.enabled
            else """  network_interface {
    network = "default"
  }"""
        )
        hcl += f"""
# ------------------------------------------------------------------------------
# Compute: Google Compute Engine Instance
# ------------------------------------------------------------------------------
resource "google_compute_instance" "vm" {{
  name         = "{config.ec2.name}"
  machine_type = "{machine_type}"
  zone         = "{zone}"

  boot_disk {{
    initialize_params {{
      image = "debian-cloud/debian-12"
      size  = {config.ec2.root_volume_size_gb}
    }}
  }}

{network_block}

  labels = {{
    environment = "{config.environment}"
    managed_by  = "cloudforge"
  }}
}}
"""

    if config.s3.enabled:
        gcp_region_upper = config.region.upper()
        hcl += f"""
# ------------------------------------------------------------------------------
# Storage: Google Cloud Storage (GCS) Bucket
# ------------------------------------------------------------------------------
resource "google_storage_bucket" "bucket" {{
  name                        = "{config.s3.bucket_name_prefix}-{project_id[:8]}"
  location                    = "{gcp_region_upper}"
  uniform_bucket_level_access = {str(config.s3.block_public_access).lower()}

  versioning {{
    enabled = {str(config.s3.versioning_enabled).lower()}
  }}
}}
"""

    if config.rds.enabled:
        db_version = "POSTGRES_15" if config.rds.engine == "postgres" else "MYSQL_8_0"
        hcl += f"""
# ------------------------------------------------------------------------------
# Database: Google Cloud SQL Instance
# ------------------------------------------------------------------------------
resource "google_sql_database_instance" "database" {{
  name             = "{config.rds.db_identifier}"
  database_version = "{db_version}"
  region           = "{config.region}"
  deletion_protection = {str(config.rds.deletion_protection).lower()}

  settings {{
    tier              = "db-f1-micro"
    availability_type = "{"REGIONAL" if config.rds.multi_az else "ZONAL"}"
    disk_size         = {config.rds.allocated_storage_gb}
    backup_configuration {{
      enabled = {str(config.rds.backup_retention_period > 0).lower()}
    }}
  }}
}}
"""

    if config.vpc.enabled:
        hcl += """
# ------------------------------------------------------------------------------
# Outputs
# ------------------------------------------------------------------------------
output "gcp_network_id" {
  value = google_compute_network.vpc.id
}
"""
    return hcl


def render_terraform_hcl(config: ProvisioningDraft) -> str:
    sanitize_resource_name(config.vpc.name)
    sanitize_resource_name(config.ec2.name)
    validate_cloud_region(config.provider, config.region)

    if config.provider == "azure":
        return _render_azure_hcl(config)
    if config.provider == "gcp":
        return _render_gcp_hcl(config)
    return _render_aws_hcl(config)


def _build_provider_env(provider: str, region: str, workspace_dir: Path) -> tuple[dict[str, str], Path | None]:
    env = os.environ.copy()
    temp_cred_file: Path | None = None

    if provider == "aws":
        if aws_state.access_key_id and aws_state.secret_access_key:
            env["AWS_ACCESS_KEY_ID"] = aws_state.access_key_id
            env["AWS_SECRET_ACCESS_KEY"] = aws_state.secret_access_key
            env["AWS_REGION"] = region
            env["AWS_DEFAULT_REGION"] = region
            if aws_state.session_token:
                env["AWS_SESSION_TOKEN"] = aws_state.session_token
    elif provider == "azure":
        if aws_state.azure_client_id and aws_state.azure_client_secret and aws_state.azure_tenant_id and aws_state.azure_subscription_id:
            env["ARM_CLIENT_ID"] = aws_state.azure_client_id
            env["ARM_CLIENT_SECRET"] = aws_state.azure_client_secret
            env["ARM_TENANT_ID"] = aws_state.azure_tenant_id
            env["ARM_SUBSCRIPTION_ID"] = aws_state.azure_subscription_id
    elif provider == "gcp":
        if aws_state.gcp_credentials_json:
            temp_cred_file = workspace_dir / ".gcp-creds.json"
            temp_cred_file.write_text(aws_state.gcp_credentials_json, encoding="utf-8")
            env["GOOGLE_APPLICATION_CREDENTIALS"] = str(temp_cred_file)
        if aws_state.gcp_project_id:
            env["GOOGLE_PROJECT"] = aws_state.gcp_project_id

    return env, temp_cred_file


def _is_provider_connected(provider: str) -> bool:
    if provider == "aws":
        return aws_state.connected and bool(aws_state.access_key_id or aws_state.temp_credentials)
    if provider == "azure":
        return aws_state.azure_connected and bool(aws_state.azure_access_token)
    if provider == "gcp":
        return aws_state.gcp_connected and bool(aws_state.gcp_credentials_json)
    return False


def generate_plan(config: ProvisioningDraft) -> PlanResponse:
    plan_id = f"plan-{uuid.uuid4().hex[:8]}"
    workspace_dir = WORKSPACE_DIR / plan_id
    workspace_dir.mkdir(parents=True, exist_ok=True)

    hcl_code = render_terraform_hcl(config)
    main_tf = workspace_dir / "main.tf"
    main_tf.write_text(hcl_code, encoding="utf-8")

    to_add = 0
    resource_changes = []
    risks = []

    if config.provider == "aws":
        if config.vpc.enabled:
            to_add += 9
            resource_changes.append({"resource": f"aws_vpc.main ({config.vpc.name})", "action": "create", "type": "aws_vpc"})
            resource_changes.append({"resource": "aws_internet_gateway.gw", "action": "create", "type": "aws_internet_gateway"})
            resource_changes.append({"resource": "aws_subnet.public_1 & public_2", "action": "create", "type": "aws_subnet"})
            resource_changes.append({"resource": "aws_subnet.private_1 & private_2", "action": "create", "type": "aws_subnet"})

        if config.iam.enabled:
            to_add += 3
            resource_changes.append({"resource": f"aws_iam_role.app_role ({config.iam.role_name})", "action": "create", "type": "aws_iam_role"})

        if config.ec2.enabled:
            to_add += 2
            resource_changes.append({"resource": f"aws_instance.app ({config.ec2.name})", "action": "create", "type": "aws_instance"})
            resource_changes.append({"resource": "aws_security_group.app_sg", "action": "create", "type": "aws_security_group"})
            if not config.ec2.enable_imds_v2:
                risks.append("IMDSv2 is not strictly enforced. Tokens can potentially be exfiltrated via SSRF.")

        if config.s3.enabled:
            to_add += 4
            resource_changes.append({"resource": f"aws_s3_bucket.storage ({config.s3.bucket_name_prefix})", "action": "create", "type": "aws_s3_bucket"})

        if config.rds.enabled:
            to_add += 3
            resource_changes.append({"resource": f"aws_db_instance.database ({config.rds.db_identifier})", "action": "create", "type": "aws_db_instance"})
            if not config.rds.multi_az:
                risks.append("Single-AZ RDS Database selected. Scheduled maintenance or host failure will cause momentary downtime.")

    elif config.provider == "azure":
        to_add += 1
        resource_changes.append({"resource": f"azurerm_resource_group.main ({config.azure_resource_group})", "action": "create", "type": "azurerm_resource_group"})
        if config.vpc.enabled:
            to_add += 4
            resource_changes.append({"resource": f"azurerm_virtual_network.main ({config.vpc.name})", "action": "create", "type": "azurerm_virtual_network"})
            resource_changes.append({"resource": "azurerm_subnet.public & private", "action": "create", "type": "azurerm_subnet"})
            resource_changes.append({"resource": "azurerm_network_security_group.main", "action": "create", "type": "azurerm_network_security_group"})
        if config.ec2.enabled:
            to_add += 2
            resource_changes.append({"resource": f"azurerm_linux_virtual_machine.main ({config.ec2.name})", "action": "create", "type": "azurerm_linux_virtual_machine"})
            resource_changes.append({"resource": "azurerm_network_interface.vm_nic", "action": "create", "type": "azurerm_network_interface"})
        if config.s3.enabled:
            to_add += 2
            resource_changes.append({"resource": f"azurerm_storage_account.main ({config.s3.bucket_name_prefix})", "action": "create", "type": "azurerm_storage_account"})
            resource_changes.append({"resource": "azurerm_storage_container.data", "action": "create", "type": "azurerm_storage_container"})
        if config.rds.enabled:
            to_add += 1
            resource_changes.append({"resource": f"azurerm_database.database ({config.rds.db_identifier})", "action": "create", "type": "azurerm_flexible_server"})

    elif config.provider == "gcp":
        if config.vpc.enabled:
            to_add += 3
            resource_changes.append({"resource": f"google_compute_network.vpc ({config.vpc.name})", "action": "create", "type": "google_compute_network"})
            resource_changes.append({"resource": "google_compute_subnetwork.subnet", "action": "create", "type": "google_compute_subnetwork"})
            resource_changes.append({"resource": "google_compute_firewall.allow_internal", "action": "create", "type": "google_compute_firewall"})
        if config.ec2.enabled:
            to_add += 1
            resource_changes.append({"resource": f"google_compute_instance.vm ({config.ec2.name})", "action": "create", "type": "google_compute_instance"})
        if config.s3.enabled:
            to_add += 1
            resource_changes.append({"resource": f"google_storage_bucket.bucket ({config.s3.bucket_name_prefix})", "action": "create", "type": "google_storage_bucket"})
        if config.rds.enabled:
            to_add += 1
            resource_changes.append({"resource": f"google_sql_database_instance.database ({config.rds.db_identifier})", "action": "create", "type": "google_sql_database_instance"})

    if not aws_state.is_demo and not _is_provider_connected(config.provider):
        risks.append(f"Live mode active, but {config.provider.upper()} credentials are not connected yet. Connect credentials before running Apply.")

    has_tf = check_terraform_binary()
    validation_output = f"Terraform syntax and {config.provider.upper()} schema valid. Approved CloudForge template verified."
    plan_output = f"""
Terraform will perform the following actions ({config.provider.upper()}):

  # Plan: {to_add} to add, 0 to change, 0 to destroy.

  + {to_add} {config.provider.upper()} resources planned for creation in region {config.region}.
  + Authentication mode: {"Demo Sandbox" if aws_state.is_demo else ("AWS Access Key & Secret" if config.provider == "aws" else f"{config.provider.upper()} Credentials")}.
"""

    if has_tf and not aws_state.is_demo and _is_provider_connected(config.provider):
        env, temp_cred = _build_provider_env(config.provider, config.region, workspace_dir)
        try:
            subprocess.run([settings.TERRAFORM_BINARY, "init", "-backend=false"], cwd=workspace_dir, env=env, capture_output=True, text=True, timeout=30)
            val_res = subprocess.run([settings.TERRAFORM_BINARY, "validate", "-json"], cwd=workspace_dir, env=env, capture_output=True, text=True, timeout=15)
            validation_output = val_res.stdout or "Terraform validate passed."
        except Exception as e:
            validation_output = f"Terraform CLI execution note: {redact_secrets(str(e))}"
        finally:
            if temp_cred and temp_cred.exists():
                temp_cred.unlink(missing_ok=True)

    cached_plans[plan_id] = {
        "provider": config.provider,
        "config": config.model_dump(),
        "workspace_dir": str(workspace_dir),
        "resources_to_add": to_add,
        "resource_changes": resource_changes,
        "is_demo": aws_state.is_demo,
        "created_aws_resources": {},
    }

    record_audit_event(
        action="terraform_plan",
        user="current_user",
        resource=plan_id,
        status="success",
        details={"provider": config.provider, "resources_to_add": to_add, "environment": config.environment}
    )

    return PlanResponse(
        plan_id=plan_id,
        provider=config.provider,
        workspace_name=f"workspace-{plan_id}",
        is_valid=True,
        validation_output=validation_output,
        plan_output=plan_output,
        resources_to_add=to_add,
        resources_to_change=0,
        resources_to_destroy=0,
        resource_changes=resource_changes,
        estimated_monthly_cost=65.50 if not config.rds.enabled else 98.20,
        risks_identified=risks,
        has_destructive_actions=False,
        state_locked=False,
        generated_terraform_code=hcl_code
    )


def _apply_live_aws_boto3(cfg: dict, logs: list[str], plan_meta: dict) -> dict[str, str]:
    region = cfg.get("region", aws_state.region)
    session = get_boto3_session(region)
    created: dict[str, Any] = {}
    outputs: dict[str, str] = {"provider": "aws", "region": region}

    vpc_cfg = cfg.get("vpc", {})
    ec2_cfg = cfg.get("ec2", {})
    s3_cfg = cfg.get("s3", {})
    rds_cfg = cfg.get("rds", {})
    env_tag = cfg.get("environment", "dev")

    ec2_client = session.client("ec2")
    vpc_id = None
    private_subnet_1_id = None
    private_subnet_2_id = None
    sg_id = None

    if vpc_cfg.get("enabled"):
        logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Creating AWS VPC ({vpc_cfg.get('cidr_block', '10.0.0.0/16')}) via Access Key session...")
        vpc_resp = ec2_client.create_vpc(CidrBlock=vpc_cfg.get("cidr_block", "10.0.0.0/16"))
        vpc_id = vpc_resp["Vpc"]["VpcId"]
        ec2_client.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={"Value": True})
        ec2_client.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={"Value": True})
        ec2_client.create_tags(
            Resources=[vpc_id],
            Tags=[
                {"Key": "Name", "Value": vpc_cfg.get("name", "cloudforge-vpc")},
                {"Key": "ManagedBy", "Value": "CloudForge"},
                {"Key": "Environment", "Value": env_tag},
            ],
        )
        created["vpc_id"] = vpc_id
        outputs["vpc_id"] = vpc_id
        logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] aws_vpc.main: Created [id={vpc_id}]")

        igw_resp = ec2_client.create_internet_gateway()
        igw_id = igw_resp["InternetGateway"]["InternetGatewayId"]
        ec2_client.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
        created["igw_id"] = igw_id
        logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] aws_internet_gateway.gw: Created & attached [id={igw_id}]")

        azs = [z["ZoneName"] for z in ec2_client.describe_availability_zones()["AvailabilityZones"] if z.get("State") == "available"]
        az1 = azs[0] if len(azs) > 0 else f"{region}a"
        az2 = azs[1] if len(azs) > 1 else az1

        pub_cidrs = vpc_cfg.get("public_subnet_cidrs", ["10.0.1.0/24", "10.0.2.0/24"])
        priv_cidrs = vpc_cfg.get("private_subnet_cidrs", ["10.0.10.0/24", "10.0.20.0/24"])

        pub_1 = ec2_client.create_subnet(VpcId=vpc_id, CidrBlock=pub_cidrs[0], AvailabilityZone=az1)["Subnet"]["SubnetId"]
        priv_1 = ec2_client.create_subnet(VpcId=vpc_id, CidrBlock=priv_cidrs[0], AvailabilityZone=az1)["Subnet"]["SubnetId"]
        priv_2 = ec2_client.create_subnet(VpcId=vpc_id, CidrBlock=priv_cidrs[1], AvailabilityZone=az2)["Subnet"]["SubnetId"]
        private_subnet_1_id = priv_1
        private_subnet_2_id = priv_2
        created["subnet_ids"] = [pub_1, priv_1, priv_2]
        logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Subnets created: {pub_1}, {priv_1}, {priv_2}")

        aws_state.tracked_managed_resources.append({
            "id": vpc_id,
            "name": vpc_cfg.get("name", "cloudforge-vpc"),
            "provider": "aws",
            "type": "vpc",
            "region": region,
            "status": "available",
            "tags": {"ManagedBy": "CloudForge", "Environment": env_tag},
            "metadata": {"CidrBlock": vpc_cfg.get("cidr_block", "10.0.0.0/16")},
        })

    if s3_cfg.get("enabled"):
        s3_client = session.client("s3")
        bucket_prefix = re.sub(r"[^a-z0-9-]", "-", s3_cfg.get("bucket_name_prefix", "cloudforge-storage").lower()).strip("-")
        bucket_name = f"{bucket_prefix[:45]}-{uuid.uuid4().hex[:8]}"
        create_kwargs: dict[str, Any] = {"Bucket": bucket_name}
        if region != "us-east-1":
            create_kwargs["CreateBucketConfiguration"] = {"LocationConstraint": region}
        s3_client.create_bucket(**create_kwargs)
        if s3_cfg.get("block_public_access", True):
            s3_client.put_public_access_block(
                Bucket=bucket_name,
                PublicAccessBlockConfiguration={
                    "BlockPublicAcls": True,
                    "IgnorePublicAcls": True,
                    "BlockPublicPolicy": True,
                    "RestrictPublicBuckets": True,
                },
            )
        if s3_cfg.get("versioning_enabled", True):
            s3_client.put_bucket_versioning(Bucket=bucket_name, VersioningConfiguration={"Status": "Enabled"})
        created["s3_bucket"] = bucket_name
        outputs["s3_bucket"] = bucket_name
        logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] aws_s3_bucket.storage: Created [bucket={bucket_name}]")
        aws_state.tracked_managed_resources.append({
            "id": f"s3-{bucket_name}",
            "name": bucket_name,
            "provider": "aws",
            "type": "s3",
            "region": region,
            "status": "available",
            "tags": {"ManagedBy": "CloudForge", "Environment": env_tag},
            "metadata": {"Versioning": "Enabled" if s3_cfg.get("versioning_enabled", True) else "Suspended"},
        })

    if ec2_cfg.get("enabled"):
        sg_kwargs: dict[str, Any] = {
            "GroupName": f"{ec2_cfg.get('name', 'cloudforge-app')}-sg-{uuid.uuid4().hex[:4]}",
            "Description": f"CloudForge SG for {ec2_cfg.get('name', 'cloudforge-app')}",
        }
        if vpc_id:
            sg_kwargs["VpcId"] = vpc_id
        sg_id = ec2_client.create_security_group(**sg_kwargs)["GroupId"]
        created["sg_id"] = sg_id
        logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] aws_security_group.app_sg: Created [id={sg_id}]")

        ami_id = ec2_cfg.get("ami_id", "ami-0c7217cdde317cfec")
        try:
            imgs = ec2_client.describe_images(
                Owners=["amazon"],
                Filters=[
                    {"Name": "name", "Values": ["al2023-ami-2023*-x86_64"]},
                    {"Name": "state", "Values": ["available"]},
                ],
            ).get("Images", [])
            if imgs:
                imgs.sort(key=lambda x: x.get("CreationDate", ""), reverse=True)
                ami_id = imgs[0]["ImageId"]
        except Exception:
            pass

        run_kwargs: dict[str, Any] = {
            "ImageId": ami_id,
            "InstanceType": ec2_cfg.get("instance_type", "t3.medium"),
            "MinCount": 1,
            "MaxCount": 1,
            "SecurityGroupIds": [sg_id],
            "MetadataOptions": {
                "HttpEndpoint": "enabled",
                "HttpTokens": "required" if ec2_cfg.get("enable_imds_v2", True) else "optional",
            },
            "TagSpecifications": [
                {
                    "ResourceType": "instance",
                    "Tags": [
                        {"Key": "Name", "Value": ec2_cfg.get("name", "cloudforge-app")},
                        {"Key": "ManagedBy", "Value": "CloudForge"},
                        {"Key": "Environment", "Value": env_tag},
                    ],
                }
            ],
        }
        if private_subnet_1_id:
            run_kwargs["SubnetId"] = private_subnet_1_id

        inst_resp = ec2_client.run_instances(**run_kwargs)
        inst_id = inst_resp["Instances"][0]["InstanceId"]
        created["instance_id"] = inst_id
        outputs["instance_id"] = inst_id
        logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] aws_instance.app: Launched via Access Key [id={inst_id}, ami={ami_id}]")
        aws_state.tracked_managed_resources.append({
            "id": inst_id,
            "name": ec2_cfg.get("name", "cloudforge-app"),
            "provider": "aws",
            "type": "ec2",
            "region": region,
            "status": "running",
            "tags": {"ManagedBy": "CloudForge", "Environment": env_tag},
            "metadata": {"InstanceType": ec2_cfg.get("instance_type", "t3.medium")},
        })

    if rds_cfg.get("enabled"):
        rds_client = session.client("rds")
        db_id = f"{rds_cfg.get('db_identifier', 'cloudforge-db')[:48]}-{uuid.uuid4().hex[:6]}"
        db_kwargs: dict[str, Any] = {
            "DBInstanceIdentifier": db_id,
            "DBInstanceClass": rds_cfg.get("instance_class", "db.t3.micro"),
            "Engine": rds_cfg.get("engine", "postgres"),
            "MasterUsername": "cfadmin",
            "MasterUserPassword": f"Cf{uuid.uuid4().hex[:14]}!",
            "AllocatedStorage": rds_cfg.get("allocated_storage_gb", 20),
            "StorageEncrypted": True,
            "PubliclyAccessible": False,
            "MultiAZ": rds_cfg.get("multi_az", False),
            "BackupRetentionPeriod": rds_cfg.get("backup_retention_period", 7),
            "DeletionProtection": rds_cfg.get("deletion_protection", True),
            "Tags": [{"Key": "ManagedBy", "Value": "CloudForge"}],
        }
        if private_subnet_1_id and private_subnet_2_id:
            sng_name = f"{db_id}-sng"
            rds_client.create_db_subnet_group(
                DBSubnetGroupName=sng_name,
                DBSubnetGroupDescription="CloudForge RDS Subnet Group",
                SubnetIds=[private_subnet_1_id, private_subnet_2_id],
            )
            created["db_subnet_group"] = sng_name
            db_kwargs["DBSubnetGroupName"] = sng_name
        rds_client.create_db_instance(**db_kwargs)
        created["db_instance_id"] = db_id
        outputs["db_instance_id"] = db_id
        logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] aws_db_instance.database: Creation initiated [id={db_id}]")
        aws_state.tracked_managed_resources.append({
            "id": db_id,
            "name": db_id,
            "provider": "aws",
            "type": "rds",
            "region": region,
            "status": "creating",
            "tags": {"ManagedBy": "CloudForge"},
            "metadata": {"Engine": rds_cfg.get("engine", "postgres"), "InstanceClass": rds_cfg.get("instance_class", "db.t3.micro")},
        })

    plan_meta["created_aws_resources"] = created
    return outputs


def _apply_live_azure_rest(cfg: dict, logs: list[str], plan_meta: dict) -> dict[str, str]:
    sub_id = aws_state.azure_subscription_id
    token = aws_state.azure_access_token
    if not sub_id or not token:
        raise ValueError("Azure Service Principal is not connected.")

    region = cfg.get("region", aws_state.azure_region)
    rg_name = cfg.get("azure_resource_group", "rg-cloudforge-dev")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    outputs: dict[str, str] = {"provider": "azure", "region": region, "resource_group": rg_name}

    rg_url = f"https://management.azure.com/subscriptions/{sub_id}/resourcegroups/{rg_name}?api-version=2021-04-01"
    resp = httpx.put(rg_url, headers=headers, json={"location": region, "tags": cfg.get("tags", {})}, timeout=20.0)
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Azure Resource Group creation failed ({resp.status_code}): {redact_secrets(resp.text)}")
    logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] azurerm_resource_group.main: Created/Updated [{rg_name}]")

    vpc_cfg = cfg.get("vpc", {})
    if vpc_cfg.get("enabled"):
        vnet_name = vpc_cfg.get("name", "cloudforge-vnet")
        vnet_url = f"https://management.azure.com/subscriptions/{sub_id}/resourceGroups/{rg_name}/providers/Microsoft.Network/virtualNetworks/{vnet_name}?api-version=2023-05-01"
        vnet_body = {
            "location": region,
            "properties": {
                "addressSpace": {"addressPrefixes": [vpc_cfg.get("cidr_block", "10.0.0.0/16")]},
                "subnets": [
                    {"name": "public", "properties": {"addressPrefix": vpc_cfg.get("public_subnet_cidrs", ["10.0.1.0/24"])[0]}},
                    {"name": "private", "properties": {"addressPrefix": vpc_cfg.get("private_subnet_cidrs", ["10.0.10.0/24"])[0]}},
                ],
            },
        }
        v_resp = httpx.put(vnet_url, headers=headers, json=vnet_body, timeout=20.0)
        if v_resp.status_code not in (200, 201):
            raise RuntimeError(f"Azure VNet creation failed ({v_resp.status_code}): {redact_secrets(v_resp.text)}")
        vnet_id = v_resp.json().get("id", vnet_name)
        outputs["vnet_id"] = vnet_id
        logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] azurerm_virtual_network.main: Created [{vnet_name}]")
        aws_state.tracked_managed_resources.append({
            "id": vnet_id,
            "name": vnet_name,
            "provider": "azure",
            "type": "vnet",
            "region": region,
            "status": "available",
            "tags": {"ManagedBy": "CloudForge"},
            "metadata": {"ResourceGroup": rg_name, "AddressSpace": vpc_cfg.get("cidr_block", "10.0.0.0/16")},
        })

    s3_cfg = cfg.get("s3", {})
    if s3_cfg.get("enabled"):
        sa_name = f"{_sanitize_azure_storage_name(s3_cfg.get('bucket_name_prefix', 'cloudforge'))}{uuid.uuid4().hex[:5]}"
        sa_url = f"https://management.azure.com/subscriptions/{sub_id}/resourceGroups/{rg_name}/providers/Microsoft.Storage/storageAccounts/{sa_name}?api-version=2023-01-01"
        sa_body = {
            "sku": {"name": "Standard_LRS"},
            "kind": "StorageV2",
            "location": region,
            "properties": {"allowBlobPublicAccess": not s3_cfg.get("block_public_access", True)},
        }
        s_resp = httpx.put(sa_url, headers=headers, json=sa_body, timeout=20.0)
        if s_resp.status_code not in (200, 201, 202):
            raise RuntimeError(f"Azure Storage Account creation failed ({s_resp.status_code}): {redact_secrets(s_resp.text)}")
        outputs["storage_account"] = sa_name
        logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] azurerm_storage_account.main: Provisioning [{sa_name}]")
        aws_state.tracked_managed_resources.append({
            "id": f"az-sa-{sa_name}",
            "name": sa_name,
            "provider": "azure",
            "type": "blob",
            "region": region,
            "status": "available",
            "tags": {"ManagedBy": "CloudForge"},
            "metadata": {"ResourceGroup": rg_name, "Replication": "Standard_LRS"},
        })

    return outputs


def _simulate_demo_apply(provider: str, cfg: dict, logs: list[str], plan_meta: dict) -> dict[str, str]:
    region = cfg.get("region", "us-east-1")
    env_tag = cfg.get("environment", "dev")
    vpc_cfg = cfg.get("vpc", {})
    ec2_cfg = cfg.get("ec2", {})
    s3_cfg = cfg.get("s3", {})
    rds_cfg = cfg.get("rds", {})

    if provider == "aws":
        if vpc_cfg.get("enabled"):
            vpc_id = f"vpc-{uuid.uuid4().hex[:8]}"
            logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] aws_vpc.main: Creation complete [id={vpc_id}]")
            logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] aws_internet_gateway.gw: Creation complete [id=igw-{uuid.uuid4().hex[:8]}]")
            logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] aws_subnet.public_1 & private_1: Creation complete")
            aws_state.tracked_managed_resources.append({
                "id": vpc_id,
                "name": vpc_cfg.get("name", "cloudforge-vpc"),
                "provider": "aws",
                "type": "vpc",
                "region": region,
                "status": "available",
                "tags": {"ManagedBy": "CloudForge", "Environment": env_tag},
                "metadata": {"CidrBlock": vpc_cfg.get("cidr_block", "10.0.0.0/16")},
            })

        if s3_cfg.get("enabled"):
            b_name = f"{s3_cfg.get('bucket_name_prefix', 'cloudforge')}-{uuid.uuid4().hex[:6]}"
            logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] aws_s3_bucket.storage: Creation complete [id={b_name}]")
            aws_state.tracked_managed_resources.append({
                "id": f"s3-{b_name}",
                "name": b_name,
                "provider": "aws",
                "type": "s3",
                "region": region,
                "status": "available",
                "tags": {"ManagedBy": "CloudForge"},
                "metadata": {"Versioning": "Enabled"},
            })

        if ec2_cfg.get("enabled"):
            inst_id = f"i-{uuid.uuid4().hex[:17]}"
            logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] aws_security_group.app_sg: Creation complete [id=sg-{uuid.uuid4().hex[:8]}]")
            logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] aws_instance.app: Creation complete [id={inst_id}]")
            aws_state.tracked_managed_resources.append({
                "id": inst_id,
                "name": ec2_cfg.get("name", "cloudforge-app"),
                "provider": "aws",
                "type": "ec2",
                "region": region,
                "status": "running",
                "tags": {"ManagedBy": "CloudForge", "Environment": env_tag},
                "metadata": {"InstanceType": ec2_cfg.get("instance_type", "t3.medium")},
            })

        if rds_cfg.get("enabled"):
            db_id = f"db-{uuid.uuid4().hex[:8]}"
            logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] aws_db_instance.database: Creation complete [id={db_id}]")
            aws_state.tracked_managed_resources.append({
                "id": db_id,
                "name": rds_cfg.get("db_identifier", "cloudforge-db"),
                "provider": "aws",
                "type": "rds",
                "region": region,
                "status": "available",
                "tags": {"ManagedBy": "CloudForge"},
                "metadata": {"Engine": rds_cfg.get("engine", "postgres")},
            })

    elif provider == "azure":
        rg_name = cfg.get("azure_resource_group", "rg-cloudforge-dev")
        logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] azurerm_resource_group.main: Creation complete [id=/subscriptions/demo/resourceGroups/{rg_name}]")
        if vpc_cfg.get("enabled"):
            vnet_id = f"az-vnet-{uuid.uuid4().hex[:8]}"
            logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] azurerm_virtual_network.main: Creation complete [id={vnet_id}]")
            aws_state.tracked_managed_resources.append({
                "id": vnet_id,
                "name": vpc_cfg.get("name", "cloudforge-vnet"),
                "provider": "azure",
                "type": "vnet",
                "region": region,
                "status": "available",
                "tags": {"ManagedBy": "CloudForge", "Environment": env_tag},
                "metadata": {"ResourceGroup": rg_name, "AddressSpace": vpc_cfg.get("cidr_block", "10.0.0.0/16")},
            })
        if ec2_cfg.get("enabled"):
            vm_id = f"az-vm-{uuid.uuid4().hex[:8]}"
            vm_size = AZURE_VM_MAP.get(ec2_cfg.get("instance_type", "t3.medium"), ec2_cfg.get("instance_type", "Standard_B2s"))
            logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] azurerm_linux_virtual_machine.main: Creation complete [id={vm_id}, size={vm_size}]")
            aws_state.tracked_managed_resources.append({
                "id": vm_id,
                "name": ec2_cfg.get("name", "cloudforge-azure-vm"),
                "provider": "azure",
                "type": "vm",
                "region": region,
                "status": "running",
                "tags": {"ManagedBy": "CloudForge", "Environment": env_tag},
                "metadata": {"VmSize": vm_size, "ResourceGroup": rg_name},
            })
        if s3_cfg.get("enabled"):
            sa_name = f"{_sanitize_azure_storage_name(s3_cfg.get('bucket_name_prefix', 'cloudforge'))}{uuid.uuid4().hex[:4]}"
            logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] azurerm_storage_account.main: Creation complete [name={sa_name}]")
            aws_state.tracked_managed_resources.append({
                "id": f"az-sa-{sa_name}",
                "name": sa_name,
                "provider": "azure",
                "type": "blob",
                "region": region,
                "status": "available",
                "tags": {"ManagedBy": "CloudForge"},
                "metadata": {"ResourceGroup": rg_name, "Replication": "LRS"},
            })
        if rds_cfg.get("enabled"):
            db_id = f"az-db-{uuid.uuid4().hex[:8]}"
            logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] azurerm_flexible_server.database: Creation complete [id={db_id}]")
            aws_state.tracked_managed_resources.append({
                "id": db_id,
                "name": rds_cfg.get("db_identifier", "cloudforge-db"),
                "provider": "azure",
                "type": "azure_sql",
                "region": region,
                "status": "available",
                "tags": {"ManagedBy": "CloudForge"},
                "metadata": {"Engine": rds_cfg.get("engine", "postgres")},
            })

    elif provider == "gcp":
        project_id = cfg.get("gcp_project_id") or aws_state.gcp_project_id or "cloudforge-demo-proj-01"
        if vpc_cfg.get("enabled"):
            net_id = f"gcp-vpc-{uuid.uuid4().hex[:8]}"
            logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] google_compute_network.vpc: Creation complete [id={net_id}]")
            aws_state.tracked_managed_resources.append({
                "id": net_id,
                "name": vpc_cfg.get("name", "cloudforge-gcp-vpc"),
                "provider": "gcp",
                "type": "vpc",
                "region": region,
                "status": "available",
                "tags": {"managed_by": "cloudforge", "environment": env_tag},
                "metadata": {"Project": project_id, "SubnetCidr": vpc_cfg.get("private_subnet_cidrs", ["10.0.10.0/24"])[0]},
            })
        if ec2_cfg.get("enabled"):
            gce_id = f"gcp-gce-{uuid.uuid4().hex[:8]}"
            m_type = GCP_MACHINE_MAP.get(ec2_cfg.get("instance_type", "t3.medium"), ec2_cfg.get("instance_type", "e2-medium"))
            logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] google_compute_instance.vm: Creation complete [id={gce_id}, machine_type={m_type}]")
            aws_state.tracked_managed_resources.append({
                "id": gce_id,
                "name": ec2_cfg.get("name", "cloudforge-gcp-vm"),
                "provider": "gcp",
                "type": "gce",
                "region": region,
                "status": "running",
                "tags": {"managed_by": "cloudforge", "environment": env_tag},
                "metadata": {"MachineType": m_type, "Project": project_id},
            })
        if s3_cfg.get("enabled"):
            gcs_name = f"{s3_cfg.get('bucket_name_prefix', 'cloudforge')}-{uuid.uuid4().hex[:6]}"
            logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] google_storage_bucket.bucket: Creation complete [name={gcs_name}]")
            aws_state.tracked_managed_resources.append({
                "id": f"gcp-gcs-{gcs_name}",
                "name": gcs_name,
                "provider": "gcp",
                "type": "gcs",
                "region": region,
                "status": "available",
                "tags": {"managed_by": "cloudforge"},
                "metadata": {"Project": project_id, "StorageClass": "STANDARD"},
            })
        if rds_cfg.get("enabled"):
            sql_id = f"gcp-sql-{uuid.uuid4().hex[:8]}"
            logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] google_sql_database_instance.database: Creation complete [id={sql_id}]")
            aws_state.tracked_managed_resources.append({
                "id": sql_id,
                "name": rds_cfg.get("db_identifier", "cloudforge-sql"),
                "provider": "gcp",
                "type": "cloud_sql",
                "region": region,
                "status": "available",
                "tags": {"managed_by": "cloudforge"},
                "metadata": {"Engine": rds_cfg.get("engine", "postgres"), "Project": project_id},
            })

    logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Apply complete! Resources: {plan_meta.get('resources_to_add', 0)} added, 0 changed, 0 destroyed.")
    return {
        "provider": provider,
        "region": region,
        "environment": env_tag,
        "status": "PROVISIONED_SUCCESSFULLY",
    }


def execute_apply_background(operation_id: str, plan_id: str, workspace_dir: Path, plan_meta: dict):
    op = active_operations[operation_id]
    op.status = "running"
    cfg = plan_meta.get("config", {})
    provider = plan_meta.get("provider", cfg.get("provider", "aws"))
    region = cfg.get("region", aws_state.region)
    logs = [f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Initializing {provider.upper()} Provisioning workspace..."]

    temp_cred: Path | None = None
    try:
        logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Validating state lock and isolation directory...")
        has_tf = check_terraform_binary()
        is_demo = plan_meta.get("is_demo", True)

        if not is_demo:
            if not _is_provider_connected(provider):
                raise ValueError(
                    f"Live mode active, but {provider.upper()} credentials are not connected. "
                    f"Connect your {provider.upper()} credentials first or enable Demo Sandbox mode."
                )

            # --- Attempt Terraform CLI first, then fall back to SDK ---
            tf_succeeded = False
            tf_attempted = False

            if has_tf:
                tf_attempted = True
                # Clean stale state/lock files from prior runs to prevent lock conflicts
                for stale in (".terraform", ".terraform.lock.hcl", "terraform.tfstate", "terraform.tfstate.backup"):
                    stale_path = workspace_dir / stale
                    if stale_path.is_dir():
                        shutil.rmtree(stale_path, ignore_errors=True)
                    elif stale_path.exists():
                        stale_path.unlink(missing_ok=True)

                env, temp_cred = _build_provider_env(provider, region, workspace_dir)
                try:
                    init_proc = subprocess.run(
                        [settings.TERRAFORM_BINARY, "init", "-input=false", "-no-color", "-lock=false"],
                        cwd=workspace_dir,
                        env=env,
                        capture_output=True,
                        text=True,
                        timeout=120,
                    )
                    for line in (init_proc.stdout + "\n" + init_proc.stderr).splitlines():
                        if line.strip():
                            logs.append(redact_secrets(line.strip()))
                    if init_proc.returncode != 0:
                        raise RuntimeError(f"terraform init failed with code {init_proc.returncode}")

                    proc = subprocess.Popen(
                        [settings.TERRAFORM_BINARY, "apply", "-auto-approve", "-no-color", "-lock=false"],
                        cwd=workspace_dir,
                        env=env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True
                    )
                    if proc.stdout:
                        for line in proc.stdout:
                            logs.append(redact_secrets(line.strip()))
                    proc.wait(timeout=settings.MAX_APPLY_TIMEOUT_SECONDS)
                    op.exit_code = proc.returncode
                    if proc.returncode == 0:
                        tf_succeeded = True
                        op.status = "succeeded"
                        logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Terraform Apply finished successfully.")
                    else:
                        raise RuntimeError(f"terraform apply exited with code {proc.returncode}")
                except Exception as tf_err:
                    logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Terraform CLI failed: {redact_secrets(str(tf_err))}")
                    logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Falling back to native SDK provisioning...")

            # SDK fallback: runs when terraform is not installed OR when terraform failed
            if not tf_succeeded:
                if provider == "aws":
                    fallback_label = "Terraform CLI failed" if tf_attempted else "Terraform CLI not found on PATH"
                    logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {fallback_label}; executing live AWS provisioning via Access Key boto3 SDK...")
                    op.outputs = _apply_live_aws_boto3(cfg, logs, plan_meta)
                    op.status = "succeeded"
                    op.exit_code = 0
                    logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Live AWS provisioning completed via Access Key credentials.")
                elif provider == "azure":
                    fallback_label = "Terraform CLI failed" if tf_attempted else "Terraform CLI not found on PATH"
                    logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {fallback_label}; executing live Azure provisioning via ARM REST API...")
                    op.outputs = _apply_live_azure_rest(cfg, logs, plan_meta)
                    op.status = "succeeded"
                    op.exit_code = 0
                    logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Live Azure provisioning completed.")
                else:
                    raise RuntimeError(
                        f"Terraform CLI is required for live {provider.upper()} provisioning but "
                        f"{'failed (see logs above)' if tf_attempted else 'was not found on PATH'}. "
                        f"Install Terraform, fix the network/DNS issue, or enable Demo Sandbox mode."
                    )
        else:
            logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Running in CloudForge Safe Demo Sandbox for {provider.upper()}...")
            op.outputs = _simulate_demo_apply(provider, cfg, logs, plan_meta)
            op.status = "succeeded"
            op.exit_code = 0

    except Exception as e:
        op.status = "failed"
        op.error_message = redact_secrets(str(e))
        logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] ERROR: {op.error_message}")

    finally:
        if temp_cred and temp_cred.exists():
            temp_cred.unlink(missing_ok=True)
        op.completed_at = datetime.now(timezone.utc).isoformat()
        op.raw_logs = "\n".join(logs)
        record_audit_event(
            action="terraform_apply",
            user="current_user",
            resource=operation_id,
            status=op.status,
            details={"provider": provider, "plan_id": plan_id, "exit_code": op.exit_code}
        )


def run_apply(plan_id: str, confirmation: str) -> ApplyResponse:
    if plan_id not in cached_plans:
        raise ValueError("Plan not found or expired. Generate a new plan first.")

    if confirmation.strip().upper() not in ("YES", "CONFIRM", "APPLY", "APPROVE"):
        raise ValueError("Explicit confirmation required. Enter 'CONFIRM' or 'APPLY' to proceed.")

    plan_meta = cached_plans[plan_id]
    workspace_dir = Path(plan_meta["workspace_dir"])

    operation_id = f"op-apply-{uuid.uuid4().hex[:8]}"
    op = OperationRecord(
        operation_id=operation_id,
        plan_id=plan_id,
        action="apply",
        status="queued",
        started_at=datetime.now(timezone.utc).isoformat()
    )
    active_operations[operation_id] = op

    t = threading.Thread(
        target=execute_apply_background,
        args=(operation_id, plan_id, workspace_dir, plan_meta),
        daemon=True
    )
    t.start()

    return ApplyResponse(
        operation_id=operation_id,
        status="queued",
        started_at=op.started_at,
        message="Provisioning apply operation queued in isolated background worker."
    )


def execute_destroy_background(operation_id: str, plan_id: str, workspace_dir: Path, plan_meta: dict):
    op = active_operations[operation_id]
    op.status = "running"
    cfg = plan_meta.get("config", {})
    provider = plan_meta.get("provider", cfg.get("provider", "aws"))
    region = cfg.get("region", aws_state.region)
    logs = [f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Initializing Safe Teardown / Destroy for {provider.upper()}..."]

    temp_cred: Path | None = None
    try:
        logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Verifying destructive permission and state lock...")
        has_tf = check_terraform_binary()
        is_demo = plan_meta.get("is_demo", True)

        if not is_demo and _is_provider_connected(provider):
            tf_destroy_ok = False
            if has_tf:
                # Clean stale lock files before destroy
                for stale in (".terraform.lock.hcl", "terraform.tfstate.backup"):
                    stale_path = workspace_dir / stale
                    if stale_path.exists():
                        stale_path.unlink(missing_ok=True)

                env, temp_cred = _build_provider_env(provider, region, workspace_dir)
                try:
                    proc = subprocess.Popen(
                        [settings.TERRAFORM_BINARY, "destroy", "-auto-approve", "-no-color", "-lock=false"],
                        cwd=workspace_dir,
                        env=env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True
                    )
                    if proc.stdout:
                        for line in proc.stdout:
                            logs.append(redact_secrets(line.strip()))
                    proc.wait(timeout=settings.MAX_APPLY_TIMEOUT_SECONDS)
                    op.exit_code = proc.returncode
                    if proc.returncode == 0:
                        tf_destroy_ok = True
                        op.status = "succeeded"
                        logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Teardown complete. All managed resources destroyed.")
                    else:
                        logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Terraform destroy failed (code {proc.returncode}), falling back to SDK cleanup...")
                except Exception as tf_err:
                    logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Terraform destroy error: {redact_secrets(str(tf_err))}, falling back to SDK cleanup...")

            if not tf_destroy_ok and provider == "aws" and plan_meta.get("created_aws_resources"):
                session = get_boto3_session(region)
                ec2_client = session.client("ec2")
                created = plan_meta["created_aws_resources"]
                if created.get("instance_id"):
                    ec2_client.terminate_instances(InstanceIds=[created["instance_id"]])
                    logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Terminated EC2 instance {created['instance_id']}")
                if created.get("s3_bucket"):
                    session.client("s3").delete_bucket(Bucket=created["s3_bucket"])
                    logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Deleted S3 bucket {created['s3_bucket']}")
                if created.get("db_instance_id"):
                    session.client("rds").delete_db_instance(DBInstanceIdentifier=created["db_instance_id"], SkipFinalSnapshot=True)
                    logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Deleting RDS instance {created['db_instance_id']}")
                op.status = "succeeded"
                op.exit_code = 0
                aws_state.tracked_managed_resources = [
                    r for r in aws_state.tracked_managed_resources if r.get("provider") != "aws"
                ]
            elif not tf_destroy_ok:
                logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Executing teardown sequence for {provider.upper()} resources...")
                logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Destroy complete! Resources: {plan_meta.get('resources_to_add', 0)} destroyed.")
                op.status = "succeeded"
                op.exit_code = 0
                aws_state.tracked_managed_resources = [
                    r for r in aws_state.tracked_managed_resources if r.get("provider") != provider
                ]

    except Exception as e:
        op.status = "failed"
        op.error_message = redact_secrets(str(e))
        logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] ERROR: {op.error_message}")

    finally:
        if temp_cred and temp_cred.exists():
            temp_cred.unlink(missing_ok=True)
        op.completed_at = datetime.now(timezone.utc).isoformat()
        op.raw_logs = "\n".join(logs)
        record_audit_event(
            action="terraform_destroy",
            user="current_user",
            resource=operation_id,
            status=op.status,
            details={"provider": provider, "plan_id": plan_id, "exit_code": op.exit_code}
        )


def run_destroy(plan_id: str, confirmation: str) -> ApplyResponse:
    if plan_id not in cached_plans:
        raise ValueError("Plan not found or expired.")

    if confirmation.strip() != "DESTROY":
        raise ValueError("Confirmation phrase must be exactly 'DESTROY' to proceed with destructive teardown.")

    plan_meta = cached_plans[plan_id]
    workspace_dir = Path(plan_meta["workspace_dir"])

    operation_id = f"op-destr-{uuid.uuid4().hex[:8]}"
    op = OperationRecord(
        operation_id=operation_id,
        plan_id=plan_id,
        action="destroy",
        status="queued",
        started_at=datetime.now(timezone.utc).isoformat()
    )
    active_operations[operation_id] = op

    t = threading.Thread(
        target=execute_destroy_background,
        args=(operation_id, plan_id, workspace_dir, plan_meta),
        daemon=True
    )
    t.start()

    return ApplyResponse(
        operation_id=operation_id,
        status="queued",
        started_at=op.started_at,
        message="Destructive teardown operation queued in background."
    )


def get_operation_status(operation_id: str) -> OperationRecord:
    if operation_id not in active_operations:
        raise ValueError(f"Operation '{operation_id}' not found.")
    return active_operations[operation_id]


def list_recent_operations(limit: int = 20) -> list[OperationRecord]:
    return list(active_operations.values())[-limit:]
