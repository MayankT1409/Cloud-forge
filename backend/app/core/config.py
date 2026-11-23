import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent
WORKSPACE_DIR = BASE_DIR / "workspaces"
REPORTS_DIR = BASE_DIR / "generated_reports"
AUDIT_LOG_FILE = BASE_DIR / "audit.log"

WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseModel):
    PROJECT_NAME: str = "CloudForge"
    API_V1_STR: str = "/api/v1"
    DEMO_MODE: bool = os.getenv("CLOUDFORGE_DEMO_MODE", "true").lower() in ("true", "1", "yes")
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    AWS_DEFAULT_REGION: str = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    TERRAFORM_BINARY: str = os.getenv("TERRAFORM_BINARY", "terraform")
    MAX_PLAN_TIMEOUT_SECONDS: int = 120
    MAX_APPLY_TIMEOUT_SECONDS: int = 600
    WORKSPACE_DIR: Path = WORKSPACE_DIR
    REPORTS_DIR: Path = REPORTS_DIR

settings = Settings()
