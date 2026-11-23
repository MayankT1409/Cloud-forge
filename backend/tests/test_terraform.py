import time
import pytest
from app.schemas.provisioning import ProvisioningDraft, VPCConfig, EC2Config, S3Config, RDSConfig
from app.services.terraform_service import (
    render_terraform_hcl,
    generate_plan,
    run_apply,
    run_destroy,
    get_operation_status
)
from app.core.security import redact_secrets

def test_hcl_rendering_and_sanitization():
    draft = ProvisioningDraft(
        environment="staging",
        region="us-east-1",
        vpc=VPCConfig(name="test-vpc", cidr_block="10.10.0.0/16"),
        ec2=EC2Config(name="test-app", instance_type="t3.small"),
        s3=S3Config(bucket_name_prefix="test-bucket"),
        rds=RDSConfig(enabled=True, db_identifier="test-db")
    )
    hcl = render_terraform_hcl(draft)
    
    assert 'resource "aws_vpc" "main"' in hcl
    assert 'cidr_block           = "10.10.0.0/16"' in hcl
    assert 'resource "aws_instance" "app"' in hcl
    assert 'resource "aws_s3_bucket" "storage"' in hcl
    assert 'resource "aws_db_instance" "database"' in hcl

def test_plan_generation():
    draft = ProvisioningDraft()
    plan = generate_plan(draft)
    
    assert plan.plan_id.startswith("plan-")
    assert plan.is_valid is True
    assert plan.resources_to_add > 0
    assert len(plan.resource_changes) > 0
    assert plan.has_destructive_actions is False

def test_apply_requires_explicit_confirmation():
    draft = ProvisioningDraft()
    plan = generate_plan(draft)
    
    with pytest.raises(ValueError, match="Explicit confirmation required"):
        run_apply(plan.plan_id, confirmation="maybe")

def test_apply_and_destroy_flow():
    draft = ProvisioningDraft()
    plan = generate_plan(draft)
    
    apply_res = run_apply(plan.plan_id, confirmation="CONFIRM")
    assert apply_res.operation_id.startswith("op-apply-")
    assert apply_res.status == "queued"
    
    time.sleep(0.5)
    status = get_operation_status(apply_res.operation_id)
    assert status.status in ("running", "succeeded")
    
    with pytest.raises(ValueError, match="DESTROY"):
        run_destroy(plan.plan_id, confirmation="no")

    destroy_res = run_destroy(plan.plan_id, confirmation="DESTROY")
    assert destroy_res.operation_id.startswith("op-destr-")

def test_secret_redaction():
    raw_log = "Error connecting: aws_secret_access_key='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY' and AKIAIOSFODNN7EXAMPLE"
    redacted = redact_secrets(raw_log)
    
    assert "wJalrXUtnFEMI" not in redacted
    assert "AKIAIOSFODNN7EXAMPLE" not in redacted
    assert "AKIA****************" in redacted
