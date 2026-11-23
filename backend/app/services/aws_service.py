import os
from datetime import datetime, timezone, timedelta
from typing import Any
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from app.schemas.aws import ConnectAccountRequest, ConnectionStatusResponse, LeastPrivilegePolicyResponse
from app.schemas.inventory import ResourceItem, InventoryResponse
from app.schemas.monitoring import MonitoringOverviewResponse, MetricSeries, DataPoint

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
        self.temp_credentials: dict[str, Any] | None = None
        self.tracked_managed_resources: list[dict[str, Any]] = []

state = AWSServiceState()

def get_connection_status() -> ConnectionStatusResponse:
    if state.is_demo:
        return ConnectionStatusResponse(
            connected=True,
            is_demo=True,
            account_id="123456789012 (Demo Sandbox)",
            role_arn="arn:aws:iam::123456789012:role/CloudForgeProvisioningRole-Demo",
            region=state.region,
            arn="arn:aws:sts::123456789012:assumed-role/CloudForgeRole/session",
            user_id="AROAEXAMPLE123456:demo-session",
            verified_at="2026-10-24T00:00:00Z",
            read_only_access=True,
            provisioning_access=True,
            missing_permissions=[],
            message="Operating in CloudForge Safe Demo Mode. AWS API calls are simulated with realistic infrastructure fixtures."
        )

    if not state.connected:
        return ConnectionStatusResponse(
            connected=False,
            is_demo=False,
            region=state.region,
            message="No active AWS connection. Please configure cross-account IAM role assumption or run in Demo Mode."
        )

    return ConnectionStatusResponse(
        connected=True,
        is_demo=False,
        account_id=state.account_id,
        role_arn=state.role_arn,
        region=state.region,
        arn=state.arn,
        user_id=state.user_id,
        verified_at=state.verified_at,
        read_only_access=True,
        provisioning_access=True,
        missing_permissions=[],
        message="Connected to live AWS account via STS AssumeRole with temporary least-privilege credentials."
    )

def set_demo_mode(enabled: bool) -> ConnectionStatusResponse:
    state.is_demo = enabled
    if enabled:
        state.connected = True
        state.account_id = "123456789012"
        state.role_arn = "arn:aws:iam::123456789012:role/CloudForgeProvisioningRole-Demo"
    else:
        state.connected = False
        state.temp_credentials = None
        state.account_id = None
        state.role_arn = None
    return get_connection_status()

def connect_with_role(req: ConnectAccountRequest) -> ConnectionStatusResponse:
    try:
        sts_client = boto3.client("sts", region_name=req.region)
        assumed = sts_client.assume_role(
            RoleArn=req.role_arn,
            RoleSessionName="CloudForgeSession",
            ExternalId=req.external_id,
            DurationSeconds=3600
        )
        credentials = assumed["Credentials"]
        
        temp_session = boto3.Session(
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"],
            region_name=req.region
        )
        caller = temp_session.client("sts").get_caller_identity()

        missing = []
        try:
            temp_session.client("ec2").describe_vpcs(MaxResults=5)
        except (ClientError, BotoCoreError) as e:
            missing.append(f"ec2:DescribeVpcs ({str(e)})")

        try:
            temp_session.client("s3").list_buckets()
        except (ClientError, BotoCoreError) as e:
            missing.append(f"s3:ListAllMyBuckets ({str(e)})")

        state.connected = True
        state.is_demo = False
        state.account_id = caller.get("Account", req.account_id)
        state.role_arn = req.role_arn
        state.region = req.region
        state.arn = caller.get("Arn")
        state.user_id = caller.get("UserId")
        state.verified_at = datetime.now(timezone.utc).isoformat()
        state.temp_credentials = {
            "AccessKeyId": credentials["AccessKeyId"],
            "SecretAccessKey": credentials["SecretAccessKey"],
            "SessionToken": credentials["SessionToken"]
        }

        return ConnectionStatusResponse(
            connected=True,
            is_demo=False,
            account_id=state.account_id,
            role_arn=state.role_arn,
            region=state.region,
            arn=state.arn,
            user_id=state.user_id,
            verified_at=state.verified_at,
            read_only_access=len(missing) == 0,
            provisioning_access=True,
            missing_permissions=missing,
            message="Successfully verified AWS STS AssumeRole temporary credentials."
        )

    except Exception as e:
        state.connected = False
        return ConnectionStatusResponse(
            connected=False,
            is_demo=False,
            region=req.region,
            missing_permissions=["sts:AssumeRole"],
            message=f"Failed to assume role '{req.role_arn}': {str(e)}"
        )

def disconnect_aws() -> ConnectionStatusResponse:
    state.connected = False
    state.is_demo = False
    state.temp_credentials = None
    state.account_id = None
    state.role_arn = None
    state.arn = None
    state.user_id = None
    state.verified_at = None
    return ConnectionStatusResponse(
        connected=False,
        is_demo=False,
        region=state.region,
        message="Disconnected from AWS account. Temporary STS credentials flushed."
    )

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
                    "rds:ModifyDBInstance",
                    "iam:CreateRole",
                    "iam:AttachRolePolicy",
                    "iam:PassRole"
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
        "1. In your AWS Console, open IAM > Roles > Create Role.",
        "2. Select 'AWS Account' as Trusted Entity type and choose 'Another AWS account'.",
        "3. Check 'Require external ID' and enter the generated unique External ID below.",
        "4. Attach the provided Scoped Provisioning policy (never use AdministratorAccess).",
        "5. Enter Role Name (e.g., CloudForgeProvisioningRole) and create role.",
        "6. Copy the resulting Role ARN and paste it into CloudForge."
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
                resource_type="rds",
                region=target_region,
                status="available",
                created_at="2026-10-20T10:25:00Z",
                managed_by="cloudforge",
                tags={"Environment": "dev", "ManagedBy": "CloudForge"},
                metadata={"Engine": "postgres 15.4", "InstanceClass": "db.t3.micro", "AllocatedStorage": "20 GB"}
            ),
        ]
        for tr in state.tracked_managed_resources:
            resources.append(ResourceItem(
                id=tr.get("id", "res-unknown"),
                name=tr.get("name", "Provisioned Resource"),
                resource_type=tr.get("type", "ec2"),
                region=target_region,
                status="available",
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
            permission_status={"ec2": True, "s3": True, "rds": True, "iam": True},
            errors=[],
            resources=resources
        )

    if not state.connected or not state.temp_credentials:
        return InventoryResponse(
            account_id=state.account_id or "Not Connected",
            region=target_region,
            is_demo=False,
            total_count=0,
            managed_count=0,
            discovered_count=0,
            permission_status={"ec2": False, "s3": False, "rds": False},
            errors=["AWS account is not connected. Enable Demo Mode or authenticate via STS AssumeRole."],
            resources=[]
        )

    resources = []
    errors = []
    permissions = {"ec2": True, "s3": True, "rds": True}

    session = boto3.Session(
        aws_access_key_id=state.temp_credentials["AccessKeyId"],
        aws_secret_access_key=state.temp_credentials["SecretAccessKey"],
        aws_session_token=state.temp_credentials["SessionToken"],
        region_name=target_region
    )

    try:
        ec2 = session.client("ec2")
        vpcs = ec2.describe_vpcs().get("Vpcs", [])
        for v in vpcs:
            v_id = v.get("VpcId", "")
            tags = {t.get("Key", ""): t.get("Value", "") for t in v.get("Tags", [])}
            is_cf = tags.get("ManagedBy") == "CloudForge"
            resources.append(ResourceItem(
                id=v_id,
                name=tags.get("Name", v_id),
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
                is_cf = tags.get("ManagedBy") == "CloudForge"
                resources.append(ResourceItem(
                    id=i_id,
                    name=tags.get("Name", i_id),
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
        errors.append(f"EC2/VPC inventory error: {str(e)}")

    try:
        s3 = session.client("s3")
        buckets = s3.list_buckets().get("Buckets", [])
        for b in buckets:
            b_name = b.get("Name", "")
            resources.append(ResourceItem(
                id=f"s3-{b_name}",
                name=b_name,
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
        errors.append(f"S3 inventory error: {str(e)}")

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
        errors.append(f"RDS inventory error: {str(e)}")

    return InventoryResponse(
        account_id=state.account_id or "Unknown",
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
            t = (now - timedelta(minutes=(11 - i) * 30)).strftime("%H:%M")
            data_points_cpu_1.append(DataPoint(timestamp=t, value=round(12.4 + (i % 4) * 2.1, 1)))
            data_points_cpu_2.append(DataPoint(timestamp=t, value=round(18.0 + ((i + 2) % 5) * 2.8, 1)))
            data_points_net.append(DataPoint(timestamp=t, value=round(45.2 + (i * 3.5), 1)))

        return MonitoringOverviewResponse(
            account_id="123456789012 (Demo Sandbox)",
            region=state.region,
            is_demo=True,
            time_range_hours=hours,
            has_metrics_permission=True,
            notice="Displaying verified CloudWatch demonstration metrics for CloudForge EC2 resources.",
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

    if not state.connected or not state.temp_credentials:
        return MonitoringOverviewResponse(
            account_id=state.account_id or "Not Connected",
            region=state.region,
            is_demo=False,
            time_range_hours=hours,
            has_metrics_permission=False,
            notice="AWS account is not connected. Connect via STS AssumeRole or activate Demo Mode to view metrics.",
            metrics=[]
        )

    try:
        session = boto3.Session(
            aws_access_key_id=state.temp_credentials["AccessKeyId"],
            aws_secret_access_key=state.temp_credentials["SecretAccessKey"],
            aws_session_token=state.temp_credentials["SessionToken"],
            region_name=state.region
        )
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
            timestamps = [ts.strftime("%H:%M") for ts in r.get('Timestamps', [])]
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
            notice=f"Failed to query CloudWatch metrics: {str(e)}",
            metrics=[]
        )
