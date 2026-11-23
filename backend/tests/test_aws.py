from app.services.aws_service import (
    get_connection_status,
    set_demo_mode,
    fetch_inventory,
    fetch_monitoring,
    get_least_privilege_policy_guide
)

def test_aws_demo_mode_status():
    set_demo_mode(True)
    status = get_connection_status()
    
    assert status.connected is True
    assert status.is_demo is True
    assert "Demo" in status.account_id

def test_inventory_demo_fixtures():
    set_demo_mode(True)
    inv = fetch_inventory("us-east-1")
    
    assert inv.is_demo is True
    assert inv.total_count >= 4
    assert inv.managed_count > 0
    assert any(r.resource_type == "ec2" for r in inv.resources)
    assert any(r.resource_type == "vpc" for r in inv.resources)

def test_monitoring_demo_metrics():
    set_demo_mode(True)
    mon = fetch_monitoring(hours=6)
    
    assert mon.is_demo is True
    assert mon.has_metrics_permission is True
    assert len(mon.metrics) >= 2
    assert mon.metrics[0].metric_name == "CPUUtilization"
    assert len(mon.metrics[0].data_points) > 0

def test_least_privilege_policy_generator():
    guide = get_least_privilege_policy_guide()
    
    assert guide.external_id.startswith("cloudforge-org-")
    assert "sts:AssumeRole" in str(guide.trust_policy)
    assert "AdministratorAccess" not in str(guide.provisioning_policy)
    assert "Condition" in guide.provisioning_policy["Statement"][0]
