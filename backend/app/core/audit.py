import json
from datetime import datetime, timezone
from typing import Any
from app.core.config import AUDIT_LOG_FILE
from app.core.security import redact_secrets

def record_audit_event(
    action: str,
    user: str,
    resource: str,
    status: str,
    details: dict[str, Any] | None = None
) -> dict[str, Any]:
    timestamp = datetime.now(timezone.utc).isoformat()
    clean_details = {}
    if details:
        for k, v in details.items():
            if isinstance(v, str):
                clean_details[k] = redact_secrets(v)
            else:
                clean_details[k] = v

    entry = {
        "timestamp": timestamp,
        "action": action,
        "user": user,
        "resource": resource,
        "status": status,
        "details": clean_details,
    }

    try:
        with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"Warning: Failed to write audit event: {e}")

    return entry

def get_recent_audit_events(limit: int = 50) -> list[dict[str, Any]]:
    if not AUDIT_LOG_FILE.exists():
        return []
    events = []
    try:
        with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in reversed(lines[-limit:]):
                try:
                    events.append(json.loads(line.strip()))
                except Exception:
                    continue
    except Exception as e:
        print(f"Warning: Failed to read audit events: {e}")
    return events
