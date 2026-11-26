import re
from pathlib import Path
from fastapi import HTTPException, status

AWS_ACCOUNT_ID_PATTERN = re.compile(r"^\d{12}$")
AWS_ROLE_ARN_PATTERN = re.compile(r"^arn:aws:iam::\d{12}:role/[\w+=,.@-]+$")
AWS_REGION_PATTERN = re.compile(r"^[a-z]{2}-[a-z]+-\d{1}$")
AZURE_REGION_PATTERN = re.compile(r"^[a-z0-9]{3,30}$")
GCP_REGION_PATTERN = re.compile(r"^[a-z]+-[a-z]+\d+$")
AWS_ACCESS_KEY_PATTERN = re.compile(r"^[A-Z0-9]{16,128}$")
RESOURCE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9-_]{2,64}$")
CIDR_PATTERN = re.compile(r"^([0-9]{1,3}\.){3}[0-9]{1,3}/([0-9]|[1-2][0-9]|3[0-2])$")

def sanitize_resource_name(name: str) -> str:
    cleaned = name.strip()
    if not RESOURCE_NAME_PATTERN.match(cleaned):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid resource name '{name}'. Must be 2-64 characters alphanumeric, hyphen, or underscore."
        )
    return cleaned

def validate_aws_account_id(account_id: str) -> str:
    cleaned = account_id.strip()
    if not AWS_ACCOUNT_ID_PATTERN.match(cleaned):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid AWS Account ID '{account_id}'. Must be exactly 12 digits."
        )
    return cleaned

def validate_role_arn(role_arn: str) -> str:
    cleaned = role_arn.strip()
    if not AWS_ROLE_ARN_PATTERN.match(cleaned):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid AWS Role ARN '{role_arn}'. Format: arn:aws:iam::<account-id>:role/<role-name>"
        )
    return cleaned

def validate_aws_region(region: str) -> str:
    cleaned = region.strip().lower()
    if not AWS_REGION_PATTERN.match(cleaned):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid AWS region '{region}'. Format: e.g. us-east-1, eu-west-1"
        )
    return cleaned

def validate_cloud_region(provider: str, region: str) -> str:
    cleaned = region.strip().lower()
    if provider == "aws":
        return validate_aws_region(cleaned)
    if provider == "azure":
        if not AZURE_REGION_PATTERN.match(cleaned):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid Azure region '{region}'. Format: e.g. eastus, westeurope, centralindia"
            )
        return cleaned
    if provider == "gcp":
        if not GCP_REGION_PATTERN.match(cleaned):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid GCP region '{region}'. Format: e.g. us-central1, europe-west1, asia-south1"
            )
        return cleaned
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported cloud provider '{provider}'."
    )

def validate_access_key_id(access_key_id: str) -> str:
    cleaned = access_key_id.strip()
    if not AWS_ACCESS_KEY_PATTERN.match(cleaned):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid AWS Access Key ID format. Must be 16-128 uppercase alphanumeric characters (e.g. AKIA...)."
        )
    return cleaned

def validate_cidr_block(cidr: str) -> str:
    cleaned = cidr.strip()
    if not CIDR_PATTERN.match(cleaned):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid CIDR block '{cidr}'. Format: e.g. 10.0.0.0/16"
        )
    return cleaned

def redact_secrets(text: str) -> str:
    if not text:
        return ""
    redacted = text
    redacted = re.sub(r"AKIA[0-9A-Z]{16}", "AKIA****************", redacted)
    redacted = re.sub(r"ASIA[0-9A-Z]{16}", "ASIA****************", redacted)
    redacted = re.sub(
        r"(?i)(password|secret|secret_key|token|access_key)\s*[:=]\s*['\"]?([a-zA-Z0-9/+=_~.-]{6,})['\"]?",
        r'\1: "********"',
        redacted
    )
    redacted = re.sub(r"(?<![A-Za-z0-9/+=])[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])", "****************************************", redacted)
    return redacted

def safe_workspace_path(base_dir: Path, requested_dir_name: str) -> Path:
    if ".." in requested_dir_name or "/" in requested_dir_name or "\\" in requested_dir_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Illegal directory path access detected."
        )
    target = (base_dir / requested_dir_name).resolve()
    if not target.is_relative_to(base_dir.resolve()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Illegal directory traversal attempted."
        )
    return target
