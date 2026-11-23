import uuid
from datetime import datetime, timezone
from app.schemas.advisor import (
    QuestionnaireInput,
    RecommendationResponse,
    RecommendedService,
    AlternativeOption,
    MultiCloudServiceMapping
)

def analyze_and_recommend(q: QuestionnaireInput) -> RecommendationResponse:
    report_id = f"cfr-{uuid.uuid4().hex[:8]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    services: list[RecommendedService] = []
    assumptions: list[str] = []
    risks: list[str] = []

    # 1. Compute Sizing
    if q.concurrent_users > 1000 or q.daily_users > 50000:
        recommended_instance = "m6i.xlarge" if q.ram_gb > 8 else "c6i.xlarge"
        instance_count = 3
        sizing_tier = "High-Capacity Scaled Cluster"
        assumptions.append("3x compute nodes behind Application Load Balancer to absorb peak traffic.")
    elif q.concurrent_users > 200 or q.daily_users > 10000:
        recommended_instance = "t3.large"
        instance_count = 2
        sizing_tier = "Multi-Instance Redundant"
        assumptions.append("Dual t3.large instances across separate AZs to prevent single-instance downtime.")
    else:
        recommended_instance = "t3.medium"
        instance_count = 1 if q.environment == "development" else 2
        sizing_tier = "Standard Baseline"
        assumptions.append(f"Baseline {instance_count}x {recommended_instance} provides adequate headroom for {q.concurrent_users} peak concurrent users.")

    # 2. Networking
    services.append(RecommendedService(
        service_name="Amazon VPC (Virtual Private Cloud)",
        category="Networking",
        purpose="Isolated private network boundary across multi-AZ",
        configuration_details=f"CIDR: 10.0.0.0/16 with 2 Public Subnets & 2 Private Subnets in {q.preferred_region}.",
        is_required=True,
        rationale="Mandatory baseline isolation for cloud workloads to enforce least-privilege network routing."
    ))

    if q.network_access == "public_facing":
        services.append(RecommendedService(
            service_name="AWS Application Load Balancer (ALB)",
            category="Networking",
            purpose="Layer 7 Traffic Distribution and SSL/TLS Termination",
            configuration_details="Public ALB terminating HTTPS (port 443) with ACM Certificate and forwarding to private targets.",
            is_required=True,
            rationale="Terminating SSL at the ALB offloads crypto calculations from app servers and hides backend instances from direct public exposure."
        ))
        services.append(RecommendedService(
            service_name="AWS NAT Gateway",
            category="Networking",
            purpose="Outbound internet access for private subnet workloads",
            configuration_details="Single NAT Gateway (dev/staging) or Dual NAT Gateways (production) in public subnets.",
            is_required=True,
            rationale="Allows backend instances in private subnets to pull container images, OS patches, and third-party APIs without accepting inbound internet connections."
        ))

    # 3. Compute
    services.append(RecommendedService(
        service_name=f"Amazon EC2 ({recommended_instance})",
        category="Compute",
        purpose=f"Hosts {q.runtime} application logic",
        configuration_details=f"{instance_count} instance(s), {q.storage_gb} GB gp3 EBS root volume, IMDSv2 enforced.",
        is_required=True,
        rationale=f"Selected {recommended_instance} matches your target of {q.cpu_cores} vCPU and {q.ram_gb} GB memory requirements with burstable/general performance."
    ))

    # 4. Database
    if q.db_required:
        if q.db_engine in ("aurora_postgres", "aurora_mysql"):
            db_service_name = "Amazon Aurora Serverless v2"
            db_config = f"{q.db_engine.replace('_', ' ').title()} - Min 0.5 ACU, Max 8 ACU, Multi-AZ storage."
            db_rationale = "Aurora provides 3x throughput of standard RDS and instant horizontal auto-scaling for unpredictable traffic spikes."
        elif q.db_engine == "dynamodb":
            db_service_name = "Amazon DynamoDB"
            db_config = "On-demand capacity mode with point-in-time recovery enabled."
            db_rationale = "NoSQL fully managed key-value store with sub-10ms response times and zero server maintenance."
        else:
            db_service_name = f"Amazon RDS ({q.db_engine.title()})"
            db_instance = "db.t3.medium" if q.concurrent_users > 300 else "db.t3.micro"
            db_config = f"{db_instance}, {q.db_size_gb} GB gp3 storage, Multi-AZ: {q.multi_az}, automated backups: {q.backup_retention_days} days."
            db_rationale = "Fully managed relational database handles automated patching, replication, failover, and point-in-time snapshots far more reliably than self-hosted database on EC2."

        services.append(RecommendedService(
            service_name=db_service_name,
            category="Database",
            purpose="Persistent application transactional storage",
            configuration_details=db_config,
            is_required=True,
            rationale=db_rationale
        ))

    # 5. Object Storage
    if q.file_storage_required:
        services.append(RecommendedService(
            service_name="Amazon S3 (Simple Storage Service)",
            category="Storage",
            purpose="Durable object storage for file uploads and static assets",
            configuration_details="Standard tier bucket with S3 Public Access Block, KMS SSE-S3 encryption, and versioning.",
            is_required=True,
            rationale="11 9's durability with server-side encryption prevents file corruption and accidental data loss."
        ))

    # 6. Security & IAM
    services.append(RecommendedService(
        service_name="AWS IAM (Identity and Access Management)",
        category="Security",
        purpose="Least-privilege role-based access for EC2 instances and operations",
        configuration_details="Instance profile with AmazonSSMManagedInstanceCore (no open SSH port 22 needed).",
        is_required=True,
        rationale="Eliminates static hardcoded API keys on EC2 instances by utilizing IAM temporary role credentials."
    ))

    if q.waf_required:
        services.append(RecommendedService(
            service_name="AWS WAF (Web Application Firewall)",
            category="Security",
            purpose="OWASP Top 10 protection and rate limiting",
            configuration_details="Attached to ALB with AWSManagedRulesCommonRuleSet and SQLi rule groups.",
            is_required=False,
            rationale="Blocks common exploits, malicious crawlers, and layer 7 volumetric attacks before reaching instances."
        ))

    # 7. Monitoring
    services.append(RecommendedService(
        service_name="Amazon CloudWatch & AWS Systems Manager",
        category="Monitoring",
        purpose="Centralized metrics, alarms, and SSM Session Manager shell access",
        configuration_details="CloudWatch Agent for memory & disk metrics; Alarms on CPU > 80% and 5xx HTTP response counts.",
        is_required=True,
        rationale="Provides real-time visibility into operational health without opening bastion hosts or inbound firewall ports."
    ))

    # Cost Calculation
    monthly_estimate = 45.0
    if q.network_access == "public_facing":
        monthly_estimate += 32.85
        monthly_estimate += 22.00
    monthly_estimate += instance_count * (30.0 if "medium" in recommended_instance else 60.0)
    if q.db_required:
        monthly_estimate += 25.0 if not q.multi_az else 55.0
    if q.file_storage_required:
        monthly_estimate += round(q.file_storage_gb * 0.023, 2)
    monthly_estimate = round(monthly_estimate, 2)
    annual_estimate = round(monthly_estimate * 12, 2)

    # Multi-Cloud Equivalent Services Matrix
    multi_cloud_matrix = [
        MultiCloudServiceMapping(
            tier_component="Compute Tier",
            aws_service=f"AWS EC2 ({recommended_instance})",
            azure_service=f"Azure VM ({'Standard_D2s_v5' if 'large' in recommended_instance else 'Standard_B2s'})",
            gcp_service=f"GCP Compute Engine ({'n2-standard-2' if 'large' in recommended_instance else 'e2-standard-2'})",
            portability_guidance="Package app into OCI container images (Docker) to run identically on EC2, Azure VM, or Google Compute Engine."
        ),
        MultiCloudServiceMapping(
            tier_component="Relational Database",
            aws_service=f"Amazon RDS ({q.db_engine.title()})",
            azure_service=f"Azure Database for {q.db_engine.title()} (Flexible Server)",
            gcp_service=f"Google Cloud SQL for {q.db_engine.title()}",
            portability_guidance="Enforce standard dialect conventions and avoid proprietary database extensions to retain zero-friction database portability."
        ),
        MultiCloudServiceMapping(
            tier_component="Object / File Storage",
            aws_service="Amazon S3 Standard",
            azure_service="Azure Blob Storage (Hot LRS)",
            gcp_service="Google Cloud Storage (Standard)",
            portability_guidance="Use S3-compatible SDK abstraction or multi-cloud storage libraries to swap bucket endpoints without code rewrites."
        ),
        MultiCloudServiceMapping(
            tier_component="Traffic Distribution",
            aws_service="AWS Application Load Balancer (ALB)",
            azure_service="Azure Application Gateway v2",
            gcp_service="Google Cloud Load Balancing",
            portability_guidance="Standard HTTP health checks (GET /health) and automated TLS certificate management across all three load balancers."
        ),
        MultiCloudServiceMapping(
            tier_component="Identity & Security",
            aws_service="AWS IAM Instance Profile / STS",
            azure_service="Azure System-Assigned Managed Identity",
            gcp_service="Google Cloud IAM Service Account",
            portability_guidance="Never bake static API keys into container images. Rely on metadata identity services provided natively by each cloud."
        ),
        MultiCloudServiceMapping(
            tier_component="Observability & Metrics",
            aws_service="Amazon CloudWatch",
            azure_service="Azure Monitor & Log Analytics",
            gcp_service="Google Cloud Monitoring (Cloud Operations)",
            portability_guidance="Export telemetry via OpenTelemetry (OTel) agent for vendor-neutral metric collection across AWS, Azure, and GCP."
        )
    ]

    # Multi-Cloud Cost Comparison Summary
    azure_est = round(monthly_estimate * 0.96, 2) # Azure typically ~4% lower due to cheaper Blob storage
    gcp_est = round(monthly_estimate * 0.94, 2)   # GCP E2 typically ~6% lower due to core pricing
    multi_cloud_comp = {
        "aws_monthly_usd": monthly_estimate,
        "azure_monthly_usd": azure_est,
        "gcp_monthly_usd": gcp_est,
        "cheapest_cloud": "GCP" if gcp_est <= azure_est and gcp_est <= monthly_estimate else "Azure" if azure_est <= monthly_estimate else "AWS",
        "monthly_delta_usd": round(abs(monthly_estimate - min(azure_est, gcp_est)), 2)
    }

    alternatives = [
        AlternativeOption(
            tier_name="Minimal Development Tier",
            description="Cost-optimized single-instance setup with public subnet and single-AZ RDS.",
            monthly_cost_estimate=round(monthly_estimate * 0.40, 2),
            tradeoffs=[
                "No Multi-AZ failover (brief downtime during maintenance or AZ outages)",
                "No Application Load Balancer (direct instance exposure)",
                "Single point of failure on the app server"
            ],
            services_summary=["1x t3.micro/small", "Single-AZ RDS", "Direct Elastic IP", "Basic CloudWatch"]
        ),
        AlternativeOption(
            tier_name="Balanced Production Tier (Recommended)",
            description="Resilient dual-AZ deployment with private app instances, ALB, and managed RDS.",
            monthly_cost_estimate=monthly_estimate,
            tradeoffs=[
                "Moderate monthly cost baseline (~$150-$250/mo)",
                "Requires NAT gateway for private egress"
            ],
            services_summary=[f"{instance_count}x {recommended_instance}", "Multi-AZ RDS", "ALB", "NAT Gateway", "CloudWatch Alarms"]
        ),
        AlternativeOption(
            tier_name="High Availability Enterprise Tier",
            description="Multi-AZ Aurora Cluster with ECS Fargate containers, Auto Scaling, and CloudFront CDN.",
            monthly_cost_estimate=round(monthly_estimate * 2.2, 2),
            tradeoffs=[
                "Higher baseline cloud expenditure",
                "Greater configuration and CI/CD orchestration complexity"
            ],
            services_summary=["ECS Fargate Auto-scaled", "Aurora Multi-AZ Cluster", "CloudFront + WAF", "Dual NAT Gateways"]
        ),
    ]

    risks.extend([
        "Database connection pooling: ensure your application runtime utilizes connection pooling (e.g., PgBouncer or SQLAlchemy pool) to avoid exhausting RDS connections.",
        "NAT Gateway outbound egress bandwidth: intensive outbound API calls or downloads incur $0.045/GB transfer costs.",
        "Single-AZ database risk: if Multi-AZ is disabled, an underlying AWS hardware failure can cause 15-45 minutes of unplanned database recovery time.",
        "Load Testing Disclaimer: This architecture is a structured recommendation based on stated parameters. It does NOT guarantee performance under arbitrary load until validated with synthetic load testing (e.g. k6, Locust)."
    ])

    plan_steps = [
        "Step 1: Deploy VPC, Internet Gateway, Public Subnets, Private Subnets, and NAT Gateway via CloudForge Terraform module.",
        "Step 2: Provision Security Groups enforcing strict ingress: ALB allows 80/443; EC2 allows only ALB ingress; RDS allows only EC2 security group ingress.",
        "Step 3: Provision Amazon RDS instance in private database subnet group and securely store master credentials in AWS Secrets Manager.",
        "Step 4: Provision Amazon S3 bucket with versioning and default KMS encryption; attach least-privilege IAM policy to the EC2 Instance Profile.",
        "Step 5: Launch EC2 instances in private subnets utilizing the CloudForge template with IMDSv2 and SSM Agent enabled.",
        "Step 6: Configure Application Load Balancer target groups with health checks (e.g. GET /health) and associate ACM TLS certificate.",
        "Step 7: Configure CloudWatch alarms for CPU > 80%, Memory > 85%, and RDS FreeStorageSpace < 5 GB."
    ]

    mermaid_diagram = f"""graph TD
    User([End Users]) -->|HTTPS:443| ALB[Application Load Balancer]
    subgraph VPC [VPC 10.0.0.0/16]
        subgraph PublicSubnets [Public Subnets AZ-a / AZ-b]
            ALB
            NAT[NAT Gateway]
        end
        subgraph PrivateSubnets [Private App Subnets AZ-a / AZ-b]
            EC2_A[EC2 {recommended_instance} 1]
            EC2_B[EC2 {recommended_instance} 2]
        end
        subgraph DBSubnets [Private DB Subnets AZ-a / AZ-b]
            RDS[(RDS {q.db_engine.title()}{' Multi-AZ' if q.multi_az else ''})]
        end
    end
    ALB -->|HTTP:8000| EC2_A
    ALB -->|HTTP:8000| EC2_B
    EC2_A -->|Port 5432| RDS
    EC2_B -->|Port 5432| RDS
    EC2_A -.->|Outbound updates| NAT
    EC2_B -.->|Outbound updates| NAT
    EC2_A -->|IAM Role / SDK| S3[Amazon S3 Storage]
    EC2_B -->|IAM Role / SDK| S3
    EC2_A -.->|Metrics & Logs| CW[Amazon CloudWatch]
    EC2_B -.->|Metrics & Logs| CW
    NAT --> IGW[Internet Gateway]
    """

    exec_summary = (
        f"CloudForge evaluated your requirements for a {q.environment} {q.app_type.replace('_', ' ')} "
        f"running on {q.runtime}. With an anticipated {q.concurrent_users} peak concurrent users and "
        f"{q.daily_users} daily active users, we recommend the '{sizing_tier}' architecture. "
        f"This model prioritizes security isolation by housing compute and database workloads in private subnets "
        f"behind an Application Load Balancer with SSM-managed operational access."
    )

    return RecommendationResponse(
        report_id=report_id,
        created_at=now_iso,
        executive_summary=exec_summary,
        recommended_tier=sizing_tier,
        recommended_services=services,
        compute_sizing={
            "instance_family": recommended_instance,
            "instance_count": instance_count,
            "vcpu_total": instance_count * (4 if "xlarge" in recommended_instance else 2),
            "ram_total_gb": instance_count * (16 if "xlarge" in recommended_instance else (8 if "large" in recommended_instance else 4)),
            "storage_gb_per_instance": q.storage_gb,
            "storage_type": "gp3 (3000 IOPS baseline)"
        },
        database_sizing={
            "engine": q.db_engine,
            "multi_az": q.multi_az,
            "allocated_storage_gb": q.db_size_gb,
            "backup_retention_days": q.backup_retention_days,
            "expected_connections": q.db_connections
        },
        networking_and_security=[
            "Strict VPC isolation: no direct public IPs on application or database instances.",
            "Least-privilege security groups: ingress strictly restricted to upstream components.",
            "AWS Systems Manager Session Manager for operational access without SSH key distribution or bastion hosts.",
            "IMDSv2 enforced on all compute instances to prevent SSRF credential exfiltration.",
            "All data encrypted at rest with AWS KMS and in transit with TLS 1.3."
        ],
        disaster_recovery_plan=[
            f"Multi-AZ deployment: automatic failover with RTO < 60s and RPO = 0.",
            f"Automated database snapshots retained for {q.backup_retention_days} days.",
            "Cross-region AMI copy recommended if multi-region disaster recovery is required."
        ],
        monitoring_and_logging=[
            "CloudWatch Metrics: EC2 CPUUtilization, DiskReadOps, NetworkIn/Out.",
            "CloudWatch Alarms: Trigger alert at CPU > 80% for 5 minutes.",
            "ALB HTTP 5xx error rate monitoring with Slack/Email notifications via Amazon SNS.",
            "AWS CloudTrail enabled across all regions for audit logging of management events."
        ],
        estimated_monthly_cost=monthly_estimate,
        estimated_annual_cost=annual_estimate,
        cost_currency="USD",
        alternatives=alternatives,
        multi_cloud_mapping=multi_cloud_matrix,
        multi_cloud_comparison=multi_cloud_comp,
        risks_and_bottlenecks=risks,
        step_by_step_implementation_plan=plan_steps,
        diagram_mermaid=mermaid_diagram,
        assumptions=assumptions,
        is_demo=False
    )
