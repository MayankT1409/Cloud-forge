from datetime import datetime, timezone
from app.schemas.pricing import (
    CostEstimationRequest,
    CostEstimationResponse,
    CostItem,
    PricingComparison,
    ProviderCostBreakdown,
    MultiCloudCostComparison
)

HOURS_PER_MONTH = 730

# Published On-Demand Reference Catalogs (Updated 2026 Reference Data)
AWS_CATALOG = {
    "us-east-1": {
        "compute": {
            "t3.nano": 0.0052,
            "t3.micro": 0.0104,
            "t3.small": 0.0208,
            "t3.medium": 0.0416,
            "t3.large": 0.0832,
            "t3.xlarge": 0.1664,
            "m6i.large": 0.096,
            "m6i.xlarge": 0.192,
            "c6i.large": 0.085,
        },
        "ebs_gp3_per_gb_month": 0.08,
        "s3_standard_per_gb_month": 0.023,
        "nat_gateway_per_hour": 0.045,
        "nat_gateway_data_per_gb": 0.045,
        "data_transfer_out_per_gb": 0.09,
        "rds": {
            "db.t3.micro": 0.017,
            "db.t3.small": 0.034,
            "db.t3.medium": 0.068,
            "db.m6g.large": 0.180,
            "storage_per_gb_month": 0.115,
            "multi_az_multiplier": 2.0,
        }
    },
    "us-west-2": {
        "compute": {
            "t3.nano": 0.0052,
            "t3.micro": 0.0104,
            "t3.small": 0.0208,
            "t3.medium": 0.0416,
            "t3.large": 0.0832,
            "t3.xlarge": 0.1664,
            "m6i.large": 0.096,
            "m6i.xlarge": 0.192,
            "c6i.large": 0.085,
        },
        "ebs_gp3_per_gb_month": 0.08,
        "s3_standard_per_gb_month": 0.023,
        "nat_gateway_per_hour": 0.045,
        "nat_gateway_data_per_gb": 0.045,
        "data_transfer_out_per_gb": 0.09,
        "rds": {
            "db.t3.micro": 0.017,
            "db.t3.small": 0.034,
            "db.t3.medium": 0.068,
            "db.m6g.large": 0.180,
            "storage_per_gb_month": 0.115,
            "multi_az_multiplier": 2.0,
        }
    },
    "eu-west-1": {
        "compute": {
            "t3.nano": 0.0057,
            "t3.micro": 0.0114,
            "t3.small": 0.0228,
            "t3.medium": 0.0456,
            "t3.large": 0.0912,
            "t3.xlarge": 0.1824,
            "m6i.large": 0.107,
            "m6i.xlarge": 0.214,
            "c6i.large": 0.095,
        },
        "ebs_gp3_per_gb_month": 0.088,
        "s3_standard_per_gb_month": 0.024,
        "nat_gateway_per_hour": 0.048,
        "nat_gateway_data_per_gb": 0.048,
        "data_transfer_out_per_gb": 0.09,
        "rds": {
            "db.t3.micro": 0.019,
            "db.t3.small": 0.038,
            "db.t3.medium": 0.076,
            "db.m6g.large": 0.198,
            "storage_per_gb_month": 0.127,
            "multi_az_multiplier": 2.0,
        }
    }
}

AZURE_CATALOG = {
    "us-east-1": { # Maps to East US
        "region_name": "East US",
        "compute": {
            "t3.nano": ("Standard_B1ls", 0.0052),
            "t3.micro": ("Standard_B1s", 0.0104),
            "t3.small": ("Standard_B1ms", 0.0207),
            "t3.medium": ("Standard_B2s", 0.0416),
            "t3.large": ("Standard_B2ms", 0.0832),
            "t3.xlarge": ("Standard_B4ms", 0.1660),
            "m6i.large": ("Standard_D2s_v5", 0.096),
            "m6i.xlarge": ("Standard_D4s_v5", 0.192),
            "c6i.large": ("Standard_F2s_v2", 0.085),
        },
        "disk_ssd_per_gb_month": 0.075,
        "blob_hot_per_gb_month": 0.018, # Azure Blob Hot LRS
        "nat_gateway_per_hour": 0.045,
        "nat_gateway_data_per_gb": 0.045,
        "data_transfer_out_per_gb": 0.087,
        "db": {
            "db.t3.micro": ("Burstable B1ms (Flexible Server)", 0.018),
            "db.t3.small": ("Burstable B2s (Flexible Server)", 0.036),
            "db.t3.medium": ("General Purpose D2ds_v5", 0.068),
            "db.m6g.large": ("General Purpose D4ds_v5", 0.176),
            "storage_per_gb_month": 0.115,
            "ha_multiplier": 2.0,
        }
    }
}

GCP_CATALOG = {
    "us-east-1": { # Maps to us-east4 (N. Virginia)
        "region_name": "us-east4 (Virginia)",
        "compute": {
            "t3.nano": ("e2-micro (shared core)", 0.0084),
            "t3.micro": ("e2-small (shared core)", 0.0168),
            "t3.small": ("e2-medium (1 vCPU, 4GB)", 0.0335),
            "t3.medium": ("e2-standard-2 (2 vCPU, 8GB)", 0.0410),
            "t3.large": ("e2-standard-4 (4 vCPU, 16GB)", 0.0820),
            "t3.xlarge": ("e2-standard-8 (8 vCPU, 32GB)", 0.1640),
            "m6i.large": ("n2-standard-2 (2 vCPU, 8GB)", 0.0971),
            "m6i.xlarge": ("n2-standard-4 (4 vCPU, 16GB)", 0.1942),
            "c6i.large": ("c2-standard-4 (compute opt)", 0.0880),
        },
        "disk_balanced_per_gb_month": 0.100,
        "gcs_standard_per_gb_month": 0.020,
        "cloud_nat_per_hour": 0.045,
        "cloud_nat_data_per_gb": 0.045,
        "data_transfer_out_per_gb": 0.085,
        "db": {
            "db.t3.micro": ("Cloud SQL db-f1-micro", 0.015),
            "db.t3.small": ("Cloud SQL db-g1-small", 0.030),
            "db.t3.medium": ("Cloud SQL db-custom-2-7680", 0.065),
            "db.m6g.large": ("Cloud SQL db-custom-4-15360", 0.170),
            "storage_per_gb_month": 0.170,
            "ha_multiplier": 2.0,
        }
    }
}

def calculate_costs(req: CostEstimationRequest) -> CostEstimationResponse:
    region = req.region if req.region in AWS_CATALOG else "us-east-1"
    prices = AWS_CATALOG[region]
    items: list[CostItem] = []

    # 1. Compute
    ec2_rate = prices["compute"].get(req.compute_instance_type, 0.0416)
    ec2_monthly = round(ec2_rate * HOURS_PER_MONTH * req.compute_count, 2)
    items.append(CostItem(
        category="compute",
        resource_name=f"AWS EC2 ({req.compute_instance_type}) x {req.compute_count}",
        unit="Instance Hours",
        unit_price_usd=ec2_rate,
        quantity=HOURS_PER_MONTH * req.compute_count,
        monthly_cost_usd=ec2_monthly,
        assumptions=f"730 operational hours/month @ ${ec2_rate}/hr in {region}."
    ))

    # 2. Block Storage (EBS)
    ebs_rate = prices["ebs_gp3_per_gb_month"]
    ebs_monthly = round(ebs_rate * req.storage_gb * req.compute_count, 2)
    items.append(CostItem(
        category="storage",
        resource_name=f"AWS EBS gp3 ({req.storage_gb} GB/inst)",
        unit="GB-month",
        unit_price_usd=ebs_rate,
        quantity=float(req.storage_gb * req.compute_count),
        monthly_cost_usd=ebs_monthly,
        assumptions="Baseline 3,000 IOPS and 125 MB/s included in gp3."
    ))

    # 3. Object Storage (S3)
    if req.s3_storage_gb > 0:
        s3_rate = prices["s3_standard_per_gb_month"]
        s3_monthly = round(s3_rate * req.s3_storage_gb, 2)
        items.append(CostItem(
            category="storage",
            resource_name=f"AWS S3 Standard ({req.s3_storage_gb} GB)",
            unit="GB-month",
            unit_price_usd=s3_rate,
            quantity=float(req.s3_storage_gb),
            monthly_cost_usd=s3_monthly,
            assumptions="Standard tier storage with 11 9's durability."
        ))

    # 4. Relational Database (RDS)
    if req.db_enabled:
        rds_rate = prices["rds"].get(req.db_instance_class, 0.017)
        if req.db_multi_az:
            rds_rate *= prices["rds"]["multi_az_multiplier"]
        rds_compute_monthly = round(rds_rate * HOURS_PER_MONTH, 2)
        items.append(CostItem(
            category="database",
            resource_name=f"AWS RDS ({req.db_instance_class}{' Multi-AZ' if req.db_multi_az else ''})",
            unit="Instance Hours",
            unit_price_usd=rds_rate,
            quantity=float(HOURS_PER_MONTH),
            monthly_cost_usd=rds_compute_monthly,
            assumptions=f"Continuous 730 hrs/mo. {'Dual AZ standby deployment.' if req.db_multi_az else 'Single AZ.'}"
        ))

        db_storage_rate = prices["rds"]["storage_per_gb_month"]
        if req.db_multi_az:
            db_storage_rate *= 2.0
        rds_storage_monthly = round(db_storage_rate * req.db_storage_gb, 2)
        items.append(CostItem(
            category="database",
            resource_name=f"AWS RDS Storage ({req.db_storage_gb} GB)",
            unit="GB-month",
            unit_price_usd=db_storage_rate,
            quantity=float(req.db_storage_gb),
            monthly_cost_usd=rds_storage_monthly,
            assumptions="General Purpose SSD (gp3) allocation."
        ))

    # 5. NAT Gateway
    if req.nat_gateway_count > 0:
        nat_hourly = prices["nat_gateway_per_hour"]
        nat_compute_monthly = round(nat_hourly * HOURS_PER_MONTH * req.nat_gateway_count, 2)
        nat_data_monthly = round(prices["nat_gateway_data_per_gb"] * req.bandwidth_gb, 2)
        items.append(CostItem(
            category="networking",
            resource_name=f"AWS VPC NAT Gateway x {req.nat_gateway_count}",
            unit="Gateway Hours + Processed GB",
            unit_price_usd=nat_hourly,
            quantity=float(HOURS_PER_MONTH * req.nat_gateway_count),
            monthly_cost_usd=round(nat_compute_monthly + nat_data_monthly, 2),
            assumptions=f"Hourly uptime (${nat_compute_monthly}) + {req.bandwidth_gb} GB egress traffic (${nat_data_monthly})."
        ))

    # 6. Egress Data Transfer
    if req.bandwidth_gb > 100:
        chargeable_gb = req.bandwidth_gb - 100
        transfer_rate = prices["data_transfer_out_per_gb"]
        transfer_monthly = round(chargeable_gb * transfer_rate, 2)
        items.append(CostItem(
            category="networking",
            resource_name="AWS Internet Egress Data Transfer",
            unit="GB-month",
            unit_price_usd=transfer_rate,
            quantity=float(chargeable_gb),
            monthly_cost_usd=transfer_monthly,
            assumptions="AWS Free Tier includes 100 GB/month internet egress."
        ))

    total_monthly = round(sum(i.monthly_cost_usd for i in items), 2)
    total_annual = round(total_monthly * 12, 2)

    comparisons = [
        PricingComparison(
            tier="Minimal Dev / Single AZ",
            monthly_cost_usd=round(total_monthly * 0.45, 2),
            summary="t3.small, single NAT gateway, no multi-AZ DB, 20 GB storage.",
            key_differences=["Saves ~55% cost", "No high availability standby", "Best for development/testing"]
        ),
        PricingComparison(
            tier="Balanced Production (Current Config)",
            monthly_cost_usd=total_monthly,
            summary=f"{req.compute_instance_type}, private VPC, RDS {req.db_instance_class}.",
            key_differences=["Reliable production baseline", "Private subnets with NAT", "Balanced performance"]
        ),
        PricingComparison(
            tier="High-Availability Enterprise",
            monthly_cost_usd=round(total_monthly * 2.1, 2),
            summary="Multi-AZ NAT gateways, Aurora DB cluster, Application Load Balancer, CloudWatch detailed monitoring.",
            key_differences=["Redundant across 3 AZs", "Zero single-point-of-failure", "Automated failover in < 30s"]
        ),
    ]

    disclaimers = [
        f"Prices based on official AWS published on-demand rates for {region} (Catalog updated 2026).",
        "Estimates exclude local taxes, custom KMS key charges ($1/month/key), and granular CloudWatch metrics ($0.30/metric).",
        "Does not constitute an official contractual quote from Amazon Web Services.",
        "Spot Instances or 1/3-year AWS Savings Plans can reduce compute expenditures by 40% - 72%."
    ]

    return CostEstimationResponse(
        region=region,
        currency="USD",
        pricing_date="2026-10-24",
        data_source=f"CloudForge AWS Reference Catalog ({region})",
        total_monthly_usd=total_monthly,
        total_annual_usd=total_annual,
        items=items,
        comparisons=comparisons,
        disclaimers=disclaimers,
        is_live_aws_quote=False
    )

def calculate_multi_cloud_costs(req: CostEstimationRequest) -> MultiCloudCostComparison:
    # 1. AWS
    aws_resp = calculate_costs(req)
    aws_comp_items = [i for i in aws_resp.items if i.category == "compute"]
    aws_stor_items = [i for i in aws_resp.items if i.category == "storage"]
    aws_db_items = [i for i in aws_resp.items if i.category == "database"]
    aws_net_items = [i for i in aws_resp.items if i.category == "networking"]

    aws_breakdown = ProviderCostBreakdown(
        provider="aws",
        provider_name="Amazon Web Services (AWS)",
        region_name=req.region,
        monthly_compute_usd=round(sum(i.monthly_cost_usd for i in aws_comp_items), 2),
        monthly_storage_usd=round(sum(i.monthly_cost_usd for i in aws_stor_items), 2),
        monthly_database_usd=round(sum(i.monthly_cost_usd for i in aws_db_items), 2),
        monthly_networking_usd=round(sum(i.monthly_cost_usd for i in aws_net_items), 2),
        total_monthly_usd=aws_resp.total_monthly_usd,
        total_annual_usd=aws_resp.total_annual_usd,
        items=aws_resp.items
    )

    # 2. Azure Calculation
    az_catalog = AZURE_CATALOG.get("us-east-1", AZURE_CATALOG["us-east-1"])
    az_vm_name, az_vm_rate = az_catalog["compute"].get(req.compute_instance_type, ("Standard_B2s", 0.0416))
    az_compute_m = round(az_vm_rate * HOURS_PER_MONTH * req.compute_count, 2)
    az_disk_m = round(az_catalog["disk_ssd_per_gb_month"] * req.storage_gb * req.compute_count, 2)
    az_blob_m = round(az_catalog["blob_hot_per_gb_month"] * req.s3_storage_gb, 2)
    
    az_db_m = 0.0
    az_db_name, az_db_rate = az_catalog["db"].get(req.db_instance_class, ("Burstable B1ms", 0.018))
    if req.db_enabled:
        if req.db_multi_az:
            az_db_rate *= az_catalog["db"]["ha_multiplier"]
        az_db_compute = az_db_rate * HOURS_PER_MONTH
        az_db_storage = az_catalog["db"]["storage_per_gb_month"] * req.db_storage_gb * (2.0 if req.db_multi_az else 1.0)
        az_db_m = round(az_db_compute + az_db_storage, 2)

    az_nat_m = 0.0
    if req.nat_gateway_count > 0:
        az_nat_m = round((az_catalog["nat_gateway_per_hour"] * HOURS_PER_MONTH * req.nat_gateway_count) + (az_catalog["nat_gateway_data_per_gb"] * req.bandwidth_gb), 2)
    az_egress_m = round(max(0, req.bandwidth_gb - 100) * az_catalog["data_transfer_out_per_gb"], 2)
    az_net_m = round(az_nat_m + az_egress_m, 2)
    az_total_m = round(az_compute_m + az_disk_m + az_blob_m + az_db_m + az_net_m, 2)

    az_items = [
        CostItem(category="compute", resource_name=f"Azure VM ({az_vm_name}) x {req.compute_count}", unit="Hours", unit_price_usd=az_vm_rate, quantity=HOURS_PER_MONTH*req.compute_count, monthly_cost_usd=az_compute_m, assumptions=f"Azure B/D series equivalent in {az_catalog['region_name']}."),
        CostItem(category="storage", resource_name=f"Azure Managed Disk Standard SSD ({req.storage_gb} GB)", unit="GB-mo", unit_price_usd=az_catalog["disk_ssd_per_gb_month"], quantity=float(req.storage_gb*req.compute_count), monthly_cost_usd=az_disk_m, assumptions="LRS Standard SSD block storage."),
        CostItem(category="storage", resource_name=f"Azure Blob Storage Hot ({req.s3_storage_gb} GB)", unit="GB-mo", unit_price_usd=az_catalog["blob_hot_per_gb_month"], quantity=float(req.s3_storage_gb), monthly_cost_usd=az_blob_m, assumptions="Hot tier LRS storage."),
        CostItem(category="database", resource_name=f"Azure Database for PostgreSQL ({az_db_name})", unit="Hours + Storage", unit_price_usd=az_db_rate, quantity=float(HOURS_PER_MONTH), monthly_cost_usd=az_db_m, assumptions="PostgreSQL Flexible Server with automated daily backups."),
        CostItem(category="networking", resource_name=f"Azure NAT Gateway + Egress ({req.bandwidth_gb} GB)", unit="Hourly + Egress", unit_price_usd=az_catalog["nat_gateway_per_hour"], quantity=float(HOURS_PER_MONTH), monthly_cost_usd=az_net_m, assumptions="Virtual Network NAT gateway plus outbound internet traffic.")
    ]

    azure_breakdown = ProviderCostBreakdown(
        provider="azure",
        provider_name="Microsoft Azure",
        region_name=az_catalog["region_name"],
        monthly_compute_usd=az_compute_m,
        monthly_storage_usd=round(az_disk_m + az_blob_m, 2),
        monthly_database_usd=az_db_m,
        monthly_networking_usd=az_net_m,
        total_monthly_usd=az_total_m,
        total_annual_usd=round(az_total_m * 12, 2),
        items=az_items
    )

    # 3. GCP Calculation
    gcp_catalog = GCP_CATALOG.get("us-east-1", GCP_CATALOG["us-east-1"])
    gcp_vm_name, gcp_vm_rate = gcp_catalog["compute"].get(req.compute_instance_type, ("e2-standard-2", 0.0410))
    gcp_compute_m = round(gcp_vm_rate * HOURS_PER_MONTH * req.compute_count, 2)
    gcp_disk_m = round(gcp_catalog["disk_balanced_per_gb_month"] * req.storage_gb * req.compute_count, 2)
    gcp_gcs_m = round(gcp_catalog["gcs_standard_per_gb_month"] * req.s3_storage_gb, 2)

    gcp_db_m = 0.0
    gcp_db_name, gcp_db_rate = gcp_catalog["db"].get(req.db_instance_class, ("Cloud SQL db-f1-micro", 0.015))
    if req.db_enabled:
        if req.db_multi_az:
            gcp_db_rate *= gcp_catalog["db"]["ha_multiplier"]
        gcp_db_compute = gcp_db_rate * HOURS_PER_MONTH
        gcp_db_storage = gcp_catalog["db"]["storage_per_gb_month"] * req.db_storage_gb * (2.0 if req.db_multi_az else 1.0)
        gcp_db_m = round(gcp_db_compute + gcp_db_storage, 2)

    gcp_nat_m = 0.0
    if req.nat_gateway_count > 0:
        gcp_nat_m = round((gcp_catalog["cloud_nat_per_hour"] * HOURS_PER_MONTH * req.nat_gateway_count) + (gcp_catalog["cloud_nat_data_per_gb"] * req.bandwidth_gb), 2)
    gcp_egress_m = round(max(0, req.bandwidth_gb - 100) * gcp_catalog["data_transfer_out_per_gb"], 2)
    gcp_net_m = round(gcp_nat_m + gcp_egress_m, 2)
    gcp_total_m = round(gcp_compute_m + gcp_disk_m + gcp_gcs_m + gcp_db_m + gcp_net_m, 2)

    gcp_items = [
        CostItem(category="compute", resource_name=f"GCP Compute Engine ({gcp_vm_name}) x {req.compute_count}", unit="Hours", unit_price_usd=gcp_vm_rate, quantity=HOURS_PER_MONTH*req.compute_count, monthly_cost_usd=gcp_compute_m, assumptions=f"Google E2/N2 instance equivalent in {gcp_catalog['region_name']}."),
        CostItem(category="storage", resource_name=f"GCP Persistent Disk Balanced ({req.storage_gb} GB)", unit="GB-mo", unit_price_usd=gcp_catalog["disk_balanced_per_gb_month"], quantity=float(req.storage_gb*req.compute_count), monthly_cost_usd=gcp_disk_m, assumptions="Zonal pd-balanced SSD-backed block storage."),
        CostItem(category="storage", resource_name=f"GCP Cloud Storage Standard ({req.s3_storage_gb} GB)", unit="GB-mo", unit_price_usd=gcp_catalog["gcs_standard_per_gb_month"], quantity=float(req.s3_storage_gb), monthly_cost_usd=gcp_gcs_m, assumptions="Standard multi-region object storage."),
        CostItem(category="database", resource_name=f"GCP Cloud SQL for PostgreSQL ({gcp_db_name})", unit="Hours + Storage", unit_price_usd=gcp_db_rate, quantity=float(HOURS_PER_MONTH), monthly_cost_usd=gcp_db_m, assumptions="Fully managed Cloud SQL instance with point-in-time recovery."),
        CostItem(category="networking", resource_name=f"GCP Cloud NAT + Premium Egress ({req.bandwidth_gb} GB)", unit="Hourly + Egress", unit_price_usd=gcp_catalog["cloud_nat_per_hour"], quantity=float(HOURS_PER_MONTH), monthly_cost_usd=gcp_net_m, assumptions="Google Cloud NAT gateway plus premium tier internet egress.")
    ]

    gcp_breakdown = ProviderCostBreakdown(
        provider="gcp",
        provider_name="Google Cloud Platform (GCP)",
        region_name=gcp_catalog["region_name"],
        monthly_compute_usd=gcp_compute_m,
        monthly_storage_usd=round(gcp_disk_m + gcp_gcs_m, 2),
        monthly_database_usd=gcp_db_m,
        monthly_networking_usd=gcp_net_m,
        total_monthly_usd=gcp_total_m,
        total_annual_usd=round(gcp_total_m * 12, 2),
        items=gcp_items
    )

    totals = {
        "AWS": aws_resp.total_monthly_usd,
        "Azure": az_total_m,
        "GCP": gcp_total_m
    }
    sorted_providers = sorted(totals.items(), key=lambda x: x[1])
    cheapest = sorted_providers[0][0]
    most_expensive = sorted_providers[-1][0]
    savings_m = round(sorted_providers[-1][1] - sorted_providers[0][1], 2)
    savings_a = round(savings_m * 12, 2)

    insights = [
        f"**{cheapest}** offers the lowest total baseline on-demand cost for this workload (${sorted_providers[0][1]:.2f}/mo).",
        f"Choosing **{cheapest}** instead of **{most_expensive}** saves **${savings_m:.2f}/month** (or **${savings_a:.2f}/year**).",
        "**Azure Blob Storage** is ~21% cheaper per GB than Amazon S3 Standard ($0.018 vs $0.023/GB-mo).",
        "**Google Cloud E2 instances** offer competitive entry pricing due to resource overcommitment, while AWS EC2 provides more granular burstable credits via t3 unlimited.",
        "Committed Use Discounts (GCP 1/3-yr CUD) or AWS Savings Plans reduce compute costs by an additional 38% - 57%."
    ]

    return MultiCloudCostComparison(
        currency="USD",
        pricing_date="2026-10-24",
        data_source="CloudForge Multi-Cloud Reference Matrix (AWS / Azure / GCP)",
        providers={
            "aws": aws_breakdown,
            "azure": azure_breakdown,
            "gcp": gcp_breakdown
        },
        cheapest_provider=cheapest,
        most_expensive_provider=most_expensive,
        monthly_arbitrage_savings_usd=savings_m,
        annual_arbitrage_savings_usd=savings_a,
        arbitrage_insights=insights
    )
