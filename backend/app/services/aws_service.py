import json
import os
from datetime import datetime, timezone, timedelta
from typing import Any
import boto3
import httpx
from botocore.exceptions import ClientError, BotoCoreError
from app.core.security import redact_secrets, validate_access_key_id, validate_cloud_region
from app.schemas.aws import (
    CloudProviderConnection,
    ConnectAccountRequest,
    ConnectAzureRequest,
    ConnectGCPRequest,
    ConnectionStatusResponse,
    LeastPrivilegePolicyResponse,
)
from app.schemas.inventory import ResourceItem, InventoryResponse
from app.schemas.monitoring import MonitoringOverviewResponse, MetricSeries, DataPoint


def _mask_key(key: str | None) -> str | None:
    if not key:
        return None
    if len(key) <= 8:
        return "*" * len(key)
    return f"{key[:4]}****{key[-4:]}"


class AWSServiceState:
    def __init__(self):
        self.connected: bool = False
        self.is_demo: bool = True
        self.account_id: str | None = "123456789012"
        self.role_arn: str | None = None
        self.region: str = "us-east-1"
        self.arn: str | None = None
        self.user_id: str | None = None
        self.verified_at: str | None = None
        self.access_key_id: str | None = None
        self.secret_access_key: str | None = None
        self.session_token: str | None = None
        self.temp_credentials: dict[str, Any] | None = None

        # Azure Service Principal state
        self.azure_connected: bool = False
        self.azure_subscription_id: str | None = None
        self.azure_tenant_id: str | None = None
        self.azure_client_id: str | None = None
        self.azure_client_secret: str | None = None
        self.azure_region: str = "eastus"
        self.azure_verified_at: str | None = None
        self.azure_access_token: str | None = None

        # GCP Service Account state
        self.gcp_connected: bool = False
        self.gcp_project_id: str | None = None
        self.gcp_service_account_email: str | None = None
        self.gcp_credentials_json: str | None = None
        self.gcp_region: str = "us-central1"
        self.gcp_verified_at: str | None = None

        self.tracked_managed_resources: list[dict[str, Any]] = []


state = AWSServiceState()


def get_boto3_session(region: str | None = None) -> boto3.Session:
    target_region = region or state.region
    if state.access_key_id and state.secret_access_key:
        kwargs: dict[str, Any] = {
            "aws_access_key_id": state.access_key_id,
            "aws_secret_access_key": state.secret_access_key,
            "region_name": target_region,
        }
        if state.session_token:
            kwargs["aws_session_token"] = state.session_token
        return boto3.Session(**kwargs)

    if state.temp_credentials:
        kwargs = {
            "aws_access_key_id": state.temp_credentials["AccessKeyId"],
            "aws_secret_access_key": state.temp_credentials["SecretAccessKey"],
            "region_name": target_region,
        }
        if state.temp_credentials.get("SessionToken"):
            kwargs["aws_session_token"] = state.temp_credentials["SessionToken"]
        return boto3.Session(**kwargs)

    raise ValueError("AWS Access Key credentials are not configured.")


def _build_azure_status() -> CloudProviderConnection:
    if state.is_demo:
        return CloudProviderConnection(
            provider="azure",
            connected=True,
            is_demo=True,
            region=state.azure_region,
            identifier="sub-demo-0000-0000-0000-cloudforge",
            label="Azure Sandbox Subscription",
            verified_at="2026-10-24T00:00:00Z",
            message="Azure demo sandbox enabled. Resource Manager provisioning is simulated."
        )
    if not state.azure_connected:
        return CloudProviderConnection(
            provider="azure",
            connected=False,
            is_demo=False,
            region=state.azure_region,
            message="Azure Service Principal not connected."
        )
    return CloudProviderConnection(
        provider="azure",
        connected=True,
        is_demo=False,
        region=state.azure_region,
        identifier=state.azure_subscription_id,
        label=_mask_key(state.azure_client_id),
        verified_at=state.azure_verified_at,
        message="Connected to Microsoft Azure via Service Principal credentials."
    )


def _build_gcp_status() -> CloudProviderConnection:
    if state.is_demo:
        return CloudProviderConnection(
            provider="gcp",
            connected=True,
            is_demo=True,
            region=state.gcp_region,
            identifier="cloudforge-demo-proj-01",
            label="cloudforge-sa@cloudforge-demo-proj-01.iam.gserviceaccount.com",
            verified_at="2026-10-24T00:00:00Z",
            message="GCP demo sandbox enabled. Compute/Storage/Cloud SQL provisioning is simulated."
        )
    if not state.gcp_connected:
        return CloudProviderConnection(
            provider="gcp",
            connected=False,
            is_demo=False,
            region=state.gcp_region,
            message="GCP Service Account not connected."
        )
    return CloudProviderConnection(
        provider="gcp",
        connected=True,
        is_demo=False,
        region=state.gcp_region,
        identifier=state.gcp_project_id,
        label=state.gcp_service_account_email,
        verified_at=state.gcp_verified_at,
        message="Connected to Google Cloud Platform via Service Account key."
    )


def get_connection_status() -> ConnectionStatusResponse:
    azure_conn = _build_azure_status()
    gcp_conn = _build_gcp_status()

    if state.is_demo:
        return ConnectionStatusResponse(
            connected=True,
            is_demo=True,
            auth_method="demo",
            access_key_id_masked="AKIA****DEMO",
            account_id="123456789012 (Demo Sandbox)",
            region=state.region,
            arn="arn:aws:iam::123456789012:user/cloudforge-demo-operator",
            user_id="AIDAEXAMPLE123456",
            verified_at="2026-10-24T00:00:00Z",
            read_only_access=True,
            provisioning_access=True,
            missing_permissions=[],
            message="Operating in CloudForge Safe Demo Mode across AWS, Azure, and GCP.",
            azure=azure_conn,
            gcp=gcp_conn,
        )

    if not state.connected:
        return ConnectionStatusResponse(
            connected=False,
            is_demo=False,
            auth_method="access_key",
            region=state.region,
            message="No active AWS connection. Enter your AWS Access Key ID & Secret Access Key or enable Demo Mode.",
            azure=azure_conn,
            gcp=gcp_conn,
        )

    return ConnectionStatusResponse(
        connected=True,
        is_demo=False,
        auth_method="access_key",
        access_key_id_masked=_mask_key(state.access_key_id),
        account_id=state.account_id,
        region=state.region,
        arn=state.arn,
        user_id=state.user_id,
        verified_at=state.verified_at,
        read_only_access=True,
        provisioning_access=True,
        missing_permissions=[],
        message="Connected to live AWS account using IAM Access Key & Secret Access Key.",
        azure=azure_conn,
        gcp=gcp_conn,
    )


def set_demo_mode(enabled: bool) -> ConnectionStatusResponse:
    state.is_demo = enabled
    if enabled:
        state.connected = True
        state.account_id = "123456789012"
        state.role_arn = None
        state.access_key_id = None
        state.secret_access_key = None
        state.session_token = None
    else:
        state.connected = bool(state.access_key_id and state.secret_access_key)
        if not state.connected:
            state.temp_credentials = None
            state.account_id = None
            state.role_arn = None
    return get_connection_status()


def connect_with_access_key(req: ConnectAccountRequest) -> ConnectionStatusResponse:
    cleaned_key = validate_access_key_id(req.access_key_id)
    cleaned_secret = req.secret_access_key.strip()
    cleaned_token = req.session_token.strip() if req.session_token else None
    cleaned_region = validate_cloud_region("aws", req.region)

    try:
        session_kwargs: dict[str, Any] = {
            "aws_access_key_id": cleaned_key,
            "aws_secret_access_key": cleaned_secret,
            "region_name": cleaned_region,
        }
        if cleaned_token:
            session_kwargs["aws_session_token"] = cleaned_token

        session = boto3.Session(**session_kwargs)
        caller = session.client("sts").get_caller_identity()

        missing = []
        try:
            session.client("ec2").describe_vpcs(MaxResults=5)
        except (ClientError, BotoCoreError) as e:
            missing.append(f"ec2:DescribeVpcs ({redact_secrets(str(e))})")

        try:
            session.client("s3").list_buckets()
        except (ClientError, BotoCoreError) as e:
            missing.append(f"s3:ListAllMyBuckets ({redact_secrets(str(e))})")

        state.connected = True
        state.is_demo = False
        state.access_key_id = cleaned_key
        state.secret_access_key = cleaned_secret
        state.session_token = cleaned_token
        state.account_id = caller.get("Account") or req.account_id
        state.role_arn = None
        state.region = cleaned_region
        state.arn = caller.get("Arn")
        state.user_id = caller.get("UserId")
        state.verified_at = datetime.now(timezone.utc).isoformat()
        state.temp_credentials = {
            "AccessKeyId": cleaned_key,
            "SecretAccessKey": cleaned_secret,
            "SessionToken": cleaned_token,
        }

        return ConnectionStatusResponse(
            connected=True,
            is_demo=False,
            auth_method="access_key",
            access_key_id_masked=_mask_key(cleaned_key),
            account_id=state.account_id,
            region=state.region,
            arn=state.arn,
            user_id=state.user_id,
            verified_at=state.verified_at,
            read_only_access=len(missing) == 0,
            provisioning_access=True,
            missing_permissions=missing,
            message="Successfully verified AWS Access Key credentials via STS GetCallerIdentity.",
            azure=_build_azure_status(),
            gcp=_build_gcp_status(),
        )

    except Exception as e:
        state.connected = False
        state.access_key_id = None
        state.secret_access_key = None
        state.session_token = None
        state.temp_credentials = None
        return ConnectionStatusResponse(
            connected=False,
            is_demo=False,
            auth_method="access_key",
            region=cleaned_region,
            missing_permissions=["sts:GetCallerIdentity"],
            message=f"Failed to authenticate AWS Access Key: {redact_secrets(str(e))}",
            azure=_build_azure_status(),
            gcp=_build_gcp_status(),
        )


def disconnect_aws() -> ConnectionStatusResponse:
    state.connected = False
    state.is_demo = False
    state.access_key_id = None
    state.secret_access_key = None
    state.session_token = None
    state.temp_credentials = None
    state.account_id = None
    state.role_arn = None
    state.arn = None
    state.user_id = None
    state.verified_at = None
    return ConnectionStatusResponse(
        connected=False,
        is_demo=False,
        auth_method="access_key",
        region=state.region,
        message="Disconnected from AWS account. Access Key credentials flushed from memory.",
        azure=_build_azure_status(),
        gcp=_build_gcp_status(),
    )


def connect_azure(req: ConnectAzureRequest) -> CloudProviderConnection:
    cleaned_region = validate_cloud_region("azure", req.region)
    sub_id = req.subscription_id.strip()
    tenant_id = req.tenant_id.strip()
    client_id = req.client_id.strip()
    client_secret = req.client_secret.strip()

    try:
        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        resp = httpx.post(
            token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": "https://management.azure.com/.default",
            },
            timeout=10.0,
        )
        if resp.status_code != 200:
            err_body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            err_msg = err_body.get("error_description") or err_body.get("error") or f"HTTP {resp.status_code}"
            return CloudProviderConnection(
                provider="azure",
                connected=False,
                is_demo=False,
                region=cleaned_region,
                message=f"Azure authentication failed: {redact_secrets(err_msg)}",
            )

        token_data = resp.json()
        state.azure_connected = True
        state.is_demo = False
        state.azure_subscription_id = sub_id
        state.azure_tenant_id = tenant_id
        state.azure_client_id = client_id
        state.azure_client_secret = client_secret
        state.azure_region = cleaned_region
        state.azure_access_token = token_data.get("access_token")
        state.azure_verified_at = datetime.now(timezone.utc).isoformat()
        return _build_azure_status()
    except Exception as e:
        return CloudProviderConnection(
            provider="azure",
            connected=False,
            is_demo=False,
            region=cleaned_region,
            message=f"Azure authentication error: {redact_secrets(str(e))}",
        )


def disconnect_azure() -> CloudProviderConnection:
    state.azure_connected = False
    state.azure_subscription_id = None
    state.azure_tenant_id = None
    state.azure_client_id = None
    state.azure_client_secret = None
    state.azure_access_token = None
    state.azure_verified_at = None
    return _build_azure_status()


def connect_gcp(req: ConnectGCPRequest) -> CloudProviderConnection:
    cleaned_region = validate_cloud_region("gcp", req.region)
    raw_creds = req.credentials_json.strip()
    project_id = req.project_id.strip()
    sa_email = req.service_account_email.strip() if req.service_account_email else None

    if raw_creds.startswith("{"):
        try:
            parsed = json.loads(raw_creds)
        except json.JSONDecodeError as e:
            return CloudProviderConnection(
                provider="gcp",
                connected=False,
                is_demo=False,
                region=cleaned_region,
                message=f"Invalid GCP Service Account JSON: {str(e)}",
            )
        if parsed.get("type") != "service_account" or not parsed.get("private_key"):
            return CloudProviderConnection(
                provider="gcp",
                connected=False,
                is_demo=False,
                region=cleaned_region,
                message="GCP JSON must be a valid 'service_account' key containing 'private_key'.",
            )
        project_id = parsed.get("project_id") or project_id
        sa_email = parsed.get("client_email") or sa_email
    elif not sa_email:
        return CloudProviderConnection(
            provider="gcp",
            connected=False,
            is_demo=False,
            region=cleaned_region,
            message="Provide either a full GCP Service Account JSON key or both Service Account Email and Private Key.",
        )

    state.gcp_connected = True
    state.is_demo = False
    state.gcp_project_id = project_id
    state.gcp_service_account_email = sa_email
    state.gcp_credentials_json = raw_creds
    state.gcp_region = cleaned_region
    state.gcp_verified_at = datetime.now(timezone.utc).isoformat()
    return _build_gcp_status()


def disconnect_gcp() -> CloudProviderConnection:
    state.gcp_connected = False
    state.gcp_project_id = None
    state.gcp_service_account_email = None
    state.gcp_credentials_json = None
    state.gcp_verified_at = None
    return _build_gcp_status()


def get_least_privilege_policy_guide() -> LeastPrivilegePolicyResponse:
    external_id = "cloudforge-org-" + os.urandom(6).hex()

    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": "arn:aws:iam::123456789012:root"
                },
                "Action": "sts:AssumeRole",
                "Condition": {
                    "StringEquals": {
                        "sts:ExternalId": external_id
                    }
                }
            }
        ]
    }

    read_only_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "CloudForgeReadOnlyDiscovery",
                "Effect": "Allow",
                "Action": [
                    "ec2:DescribeInstances",
                    "ec2:DescribeVpcs",
                    "ec2:DescribeSubnets",
                    "ec2:DescribeSecurityGroups",
                    "s3:ListAllMyBuckets",
                    "s3:GetBucketLocation",
                    "rds:DescribeDBInstances",
                    "cloudwatch:GetMetricData",
                    "cloudwatch:ListMetrics"
                ],
                "Resource": "*"
            }
        ]
    }

    provisioning_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "CloudForgeScopedProvisioning",
                "Effect": "Allow",
                "Action": [
                    "ec2:*Vpc*",
                    "ec2:*Subnet*",
                    "ec2:*RouteTable*",
                    "ec2:*InternetGateway*",
                    "ec2:*NatGateway*",
                    "ec2:*SecurityGroup*",
                    "ec2:RunInstances",
                    "ec2:TerminateInstances",
                    "ec2:Describe*",
                    "s3:CreateBucket",
                    "s3:DeleteBucket",
                    "s3:PutBucket*",
                    "rds:CreateDBInstance",
                    "rds:DeleteDBInstance",
                    "rds:ModifyDBInstance"
                ],
                "Resource": "*",
                "Condition": {
                    "StringEquals": {
                        "aws:RequestTag/ManagedBy": "CloudForge"
                    }
                }
            }
        ]
    }

    steps = [
        "1. In AWS Console, open IAM > Users > Create user (e.g. cloudforge-provisioner).",
        "2. Attach the scoped Read-Only & Provisioning policies (avoid full AdministratorAccess in production).",
        "3. Open the user's Security credentials tab and click Create access key > Third-party service / CLI.",
        "4. Copy the Access Key ID (AKIA...) and Secret Access Key.",
        "5. Paste the Access Key ID and Secret Access Key into CloudForge to authenticate and provision resources."
    ]

    return LeastPrivilegePolicyResponse(
        external_id=external_id,
        trust_policy=trust_policy,
        read_only_policy=read_only_policy,
        provisioning_policy=provisioning_policy,
        setup_steps=steps
    )


def fetch_inventory(region: str | None = None) -> InventoryResponse:
    target_region = region or state.region

    if state.is_demo:
        resources = [
            ResourceItem(
                id="vpc-0a12b34c56d78e9f0",
                name="cloudforge-dev-vpc",
                provider="aws",
                resource_type="vpc",
                region=target_region,
                status="available",
                created_at="2026-10-20T10:15:00Z",
                managed_by="cloudforge",
                tags={"Environment": "dev", "ManagedBy": "CloudForge", "Project": "CorePlatform"},
                metadata={"CidrBlock": "10.0.0.0/16"}
            ),
            ResourceItem(
                id="i-08a123fbc456789de",
                name="cloudforge-api-server",
                provider="aws",
                resource_type="ec2",
                region=target_region,
                status="running",
                created_at="2026-10-21T08:30:00Z",
                managed_by="cloudforge",
                tags={"Environment": "dev", "ManagedBy": "CloudForge", "Name": "cloudforge-api-server"},
                metadata={"InstanceType": "t3.medium", "PrivateIp": "10.0.10.45", "State": "running"}
            ),
            ResourceItem(
                id="i-099cdef012345678a",
                name="legacy-bastion-host",
                provider="aws",
                resource_type="ec2",
                region=target_region,
                status="running",
                created_at="2026-05-14T14:22:00Z",
                managed_by="aws_native",
                tags={"Name": "legacy-bastion-host", "CreatedBy": "ManualConsole"},
                metadata={"InstanceType": "t3.nano", "PublicIp": "54.210.12.33", "State": "running"}
            ),
            ResourceItem(
                id="s3-cloudforge-assets-7782",
                name="cloudforge-assets-7782",
                provider="aws",
                resource_type="s3",
                region=target_region,
                status="available",
                created_at="2026-10-20T10:20:00Z",
                managed_by="cloudforge",
                tags={"ManagedBy": "CloudForge", "Bucket": "cloudforge-assets-7782"},
                metadata={"Versioning": "Enabled", "Encryption": "AES256", "PublicAccessBlock": "AllBlocked"}
            ),
            ResourceItem(
                id="db-cloudforge-postgres",
                name="cloudforge-postgres",
                provider="aws",
                resource_type="rds",
                region=target_region,
                status="available",
                created_at="2026-10-20T10:25:00Z",
                managed_by="cloudforge",
                tags={"Environment": "dev", "ManagedBy": "CloudForge"},
                metadata={"Engine": "postgres 15.4", "InstanceClass": "db.t3.micro", "AllocatedStorage": "20 GB"}
            ),
            ResourceItem(
                id="az-vnet-cloudforge-eastus",
                name="cloudforge-azure-vnet",
                provider="azure",
                resource_type="vnet",
                region=state.azure_region,
                status="available",
                created_at="2026-10-22T09:00:00Z",
                managed_by="cloudforge",
                tags={"Environment": "dev", "ManagedBy": "CloudForge", "Cloud": "Azure"},
                metadata={"AddressSpace": "10.1.0.0/16", "ResourceGroup": "rg-cloudforge-dev"}
            ),
            ResourceItem(
                id="az-vm-web-01",
                name="cloudforge-azure-vm",
                provider="azure",
                resource_type="vm",
                region=state.azure_region,
                status="running",
                created_at="2026-10-22T09:05:00Z",
                managed_by="cloudforge",
                tags={"Environment": "dev", "ManagedBy": "CloudForge"},
                metadata={"VmSize": "Standard_B2s", "OS": "Ubuntu 22.04 LTS"}
            ),
            ResourceItem(
                id="gcp-gce-worker-01",
                name="cloudforge-gcp-instance",
                provider="gcp",
                resource_type="gce",
                region=state.gcp_region,
                status="running",
                created_at="2026-10-23T11:10:00Z",
                managed_by="cloudforge",
                tags={"environment": "dev", "managed_by": "cloudforge"},
                metadata={"MachineType": "e2-medium", "Network": "cloudforge-gcp-vpc"}
            ),
            ResourceItem(
                id="gcp-gcs-artifacts-4190",
                name="cloudforge-gcp-artifacts",
                provider="gcp",
                resource_type="gcs",
                region=state.gcp_region,
                status="available",
                created_at="2026-10-23T11:12:00Z",
                managed_by="cloudforge",
                tags={"managed_by": "cloudforge"},
                metadata={"StorageClass": "STANDARD", "UniformBucketAccess": "Enabled"}
            ),
        ]
        for tr in state.tracked_managed_resources:
            resources.append(ResourceItem(
                id=tr.get("id", "res-unknown"),
                name=tr.get("name", "Provisioned Resource"),
                provider=tr.get("provider", "aws"),
                resource_type=tr.get("type", "ec2"),
                region=tr.get("region", target_region),
                status=tr.get("status", "available"),
                created_at=tr.get("created_at", datetime.now(timezone.utc).isoformat()),
                managed_by="cloudforge",
                tags=tr.get("tags", {"ManagedBy": "CloudForge"}),
                metadata=tr.get("metadata", {})
            ))

        return InventoryResponse(
            account_id="123456789012 (Demo Mode)",
            region=target_region,
            is_demo=True,
            total_count=len(resources),
            managed_count=sum(1 for r in resources if r.managed_by == "cloudforge"),
            discovered_count=sum(1 for r in resources if r.managed_by != "cloudforge"),
            permission_status={"ec2": True, "s3": True, "rds": True, "azure": True, "gcp": True},
            errors=[],
            resources=resources
        )

    resources: list[ResourceItem] = []
    errors: list[str] = []
    permissions = {
        "ec2": False,
        "s3": False,
        "rds": False,
        "azure": state.azure_connected,
        "gcp": state.gcp_connected,
    }

    if state.connected and (state.access_key_id or state.temp_credentials):
        permissions["ec2"] = True
        permissions["s3"] = True
        permissions["rds"] = True
        session = get_boto3_session(target_region)

        try:
            ec2 = session.client("ec2")
            vpcs = ec2.describe_vpcs().get("Vpcs", [])
            for v in vpcs:
                v_id = v.get("VpcId", "")
                tags = {t.get("Key", ""): t.get("Value", "") for t in v.get("Tags", [])}
                is_cf = tags.get("ManagedBy") == "CloudForge" or tags.get("Project") == "CloudForge"
                resources.append(ResourceItem(
                    id=v_id,
                    name=tags.get("Name", v_id),
                    provider="aws",
                    resource_type="vpc",
                    region=target_region,
                    status=v.get("State", "available"),
                    managed_by="cloudforge" if is_cf else "aws_native",
                    tags=tags,
                    metadata={"CidrBlock": v.get("CidrBlock", "")}
                ))

            insts = ec2.describe_instances()
            for resv in insts.get("Reservations", []):
                for inst in resv.get("Instances", []):
                    i_id = inst.get("InstanceId", "")
                    tags = {t.get("Key", ""): t.get("Value", "") for t in inst.get("Tags", [])}
                    is_cf = tags.get("ManagedBy") == "CloudForge" or tags.get("Project") == "CloudForge"
                    resources.append(ResourceItem(
                        id=i_id,
                        name=tags.get("Name", i_id),
                        provider="aws",
                        resource_type="ec2",
                        region=target_region,
                        status=inst.get("State", {}).get("Name", "unknown"),
                        created_at=inst.get("LaunchTime", "").isoformat() if inst.get("LaunchTime") else None,
                        managed_by="cloudforge" if is_cf else "aws_native",
                        tags=tags,
                        metadata={"InstanceType": inst.get("InstanceType", ""), "PrivateIp": inst.get("PrivateIpAddress", "")}
                    ))
        except Exception as e:
            permissions["ec2"] = False
            errors.append(f"EC2/VPC inventory error: {redact_secrets(str(e))}")

        try:
            s3 = session.client("s3")
            buckets = s3.list_buckets().get("Buckets", [])
            for b in buckets:
                b_name = b.get("Name", "")
                resources.append(ResourceItem(
                    id=f"s3-{b_name}",
                    name=b_name,
                    provider="aws",
                    resource_type="s3",
                    region="global",
                    status="available",
                    created_at=b.get("CreationDate", "").isoformat() if b.get("CreationDate") else None,
                    managed_by="cloudforge" if "cloudforge" in b_name else "aws_native",
                    tags={},
                    metadata={}
                ))
        except Exception as e:
            permissions["s3"] = False
            errors.append(f"S3 inventory error: {redact_secrets(str(e))}")

        try:
            rds = session.client("rds")
            dbs = rds.describe_db_instances().get("DBInstances", [])
            for db in dbs:
                db_id = db.get("DBInstanceIdentifier", "")
                tags = {t.get("Key", ""): t.get("Value", "") for t in db.get("TagList", [])}
                is_cf = tags.get("ManagedBy") == "CloudForge" or "cloudforge" in db_id
                resources.append(ResourceItem(
                    id=db_id,
                    name=db_id,
                    provider="aws",
                    resource_type="rds",
                    region=target_region,
                    status=db.get("DBInstanceStatus", "available"),
                    created_at=db.get("InstanceCreateTime", "").isoformat() if db.get("InstanceCreateTime") else None,
                    managed_by="cloudforge" if is_cf else "aws_native",
                    tags=tags,
                    metadata={"Engine": db.get("Engine", ""), "InstanceClass": db.get("DBInstanceClass", "")}
                ))
        except Exception as e:
            permissions["rds"] = False
            errors.append(f"RDS inventory error: {redact_secrets(str(e))}")

    seen_ids = {r.id for r in resources}
    for tr in state.tracked_managed_resources:
        res_id = tr.get("id", "res-unknown")
        if res_id not in seen_ids:
            resources.append(ResourceItem(
                id=res_id,
                name=tr.get("name", "Provisioned Resource"),
                provider=tr.get("provider", "aws"),
                resource_type=tr.get("type", "ec2"),
                region=tr.get("region", target_region),
                status=tr.get("status", "available"),
                created_at=tr.get("created_at", datetime.now(timezone.utc).isoformat()),
                managed_by="cloudforge",
                tags=tr.get("tags", {"ManagedBy": "CloudForge"}),
                metadata=tr.get("metadata", {})
            ))

    if not state.connected and not state.azure_connected and not state.gcp_connected and not resources:
        errors.append("No cloud account connected. Connect AWS Access Keys, Azure, or GCP, or enable Demo Mode.")

    return InventoryResponse(
        account_id=state.account_id or state.azure_subscription_id or state.gcp_project_id or "Not Connected",
        region=target_region,
        is_demo=False,
        total_count=len(resources),
        managed_count=sum(1 for r in resources if r.managed_by == "cloudforge"),
        discovered_count=sum(1 for r in resources if r.managed_by != "cloudforge"),
        permission_status=permissions,
        errors=errors,
        resources=resources
    )


def fetch_monitoring(hours: int = 6) -> MonitoringOverviewResponse:
    if state.is_demo:
        now = datetime.now(timezone.utc)
        data_points_cpu_1 = []
        data_points_cpu_2 = []
        data_points_net = []

        for i in range(12):
            t = (now - timedelta(minutes=(11 - i) * 30)).isoformat()
            data_points_cpu_1.append(DataPoint(timestamp=t, value=round(12.4 + (i % 4) * 2.1, 1)))
            data_points_cpu_2.append(DataPoint(timestamp=t, value=round(18.0 + ((i + 2) % 5) * 2.8, 1)))
            data_points_net.append(DataPoint(timestamp=t, value=round(45.2 + (i * 3.5), 1)))

        return MonitoringOverviewResponse(
            account_id="123456789012 (Demo Sandbox)",
            region=state.region,
            is_demo=True,
            time_range_hours=hours,
            has_metrics_permission=True,
            notice="Displaying CloudWatch demonstration metrics for CloudForge EC2 resources.",
            metrics=[
                MetricSeries(
                    metric_name="CPUUtilization",
                    unit="Percent",
                    resource_id="i-08a123fbc456789de",
                    resource_name="cloudforge-api-server",
                    data_points=data_points_cpu_1
                ),
                MetricSeries(
                    metric_name="CPUUtilization",
                    unit="Percent",
                    resource_id="i-099cdef012345678a",
                    resource_name="legacy-bastion-host",
                    data_points=data_points_cpu_2
                ),
                MetricSeries(
                    metric_name="NetworkOut",
                    unit="Megabytes",
                    resource_id="i-08a123fbc456789de",
                    resource_name="cloudforge-api-server",
                    data_points=data_points_net
                )
            ]
        )

    if not state.connected or not (state.access_key_id or state.temp_credentials):
        return MonitoringOverviewResponse(
            account_id=state.account_id or "Not Connected",
            region=state.region,
            is_demo=False,
            time_range_hours=hours,
            has_metrics_permission=False,
            notice="AWS account is not connected. Connect with Access Keys or activate Demo Mode to view metrics.",
            metrics=[]
        )

    try:
        session = get_boto3_session(state.region)
        cw = session.client("cloudwatch")
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)

        response = cw.get_metric_data(
            MetricDataQueries=[
                {
                    'Id': 'cpu_query',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/EC2',
                            'MetricName': 'CPUUtilization'
                        },
                        'Period': 300,
                        'Stat': 'Average'
                    },
                    'ReturnData': True
                }
            ],
            StartTime=start_time,
            EndTime=end_time
        )

        results = response.get('MetricDataResults', [])
        series = []
        for r in results:
            timestamps = [ts.isoformat() for ts in r.get('Timestamps', [])]
            values = r.get('Values', [])
            points = [DataPoint(timestamp=t, value=round(v, 2)) for t, v in zip(reversed(timestamps), reversed(values))]
            series.append(MetricSeries(
                metric_name="CPUUtilization",
                unit="Percent",
                resource_id="AWS/EC2 Fleet",
                resource_name="Aggregated EC2 Fleet",
                data_points=points
            ))

        return MonitoringOverviewResponse(
            account_id=state.account_id,
            region=state.region,
            is_demo=False,
            time_range_hours=hours,
            has_metrics_permission=True,
            notice=f"Live CloudWatch metrics retrieved from {state.region}.",
            metrics=series
        )
    except Exception as e:
        return MonitoringOverviewResponse(
            account_id=state.account_id,
            region=state.region,
            is_demo=False,
            time_range_hours=hours,
            has_metrics_permission=False,
            notice=f"Failed to query CloudWatch metrics: {redact_secrets(str(e))}",
            metrics=[]
        )
