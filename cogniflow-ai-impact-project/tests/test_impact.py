"""
Automated Verification Suite for CogniFlow AI Impact Pipeline.
"""
import pytest
from pathlib import Path
from pipeline.schemas import SeverityLevel
from pipeline.triage_engine import analyze_incident
from pipeline.runner import run_pipeline

def test_sev1_critical_classification():
    raw_sev1 = {
        "id": "INC-TEST-01",
        "service": "database-cluster",
        "raw_logs": "FATAL: PostgreSQL connection limit exceeded (max_connections=500). Deadlock detected.",
        "customer_tier": "enterprise",
        "affected_users": 5000
    }
    res = analyze_incident(raw_sev1)
    assert res.severity == SeverityLevel.SEV1
    assert res.sla_response_minutes == 15
    assert "connection" in res.root_cause_summary.lower()
    assert res.confidence_score >= 0.95
    assert len(res.external_customer_update) > 20

def test_sev2_webhook_latency_classification():
    raw_sev2 = {
        "id": "INC-TEST-02",
        "service": "billing-gateway",
        "raw_logs": "ERROR: upstream Stripe webhook timeout after 10000ms. 42 concurrent requests hanging.",
        "customer_tier": "enterprise",
        "affected_users": 150
    }
    res = analyze_incident(raw_sev2)
    assert res.severity == SeverityLevel.SEV2
    assert res.sla_response_minutes == 30
    assert "webhook" in res.root_cause_summary.lower()

def test_routine_maintenance_info():
    raw_info = {
        "id": "INC-TEST-03",
        "service": "api-gateway",
        "raw_logs": "INFO: Routine SSL certificate auto-renewal successful.",
        "customer_tier": "system",
        "affected_users": 0
    }
    res = analyze_incident(raw_info)
    assert res.severity == SeverityLevel.INFO
    assert res.sla_response_minutes == 1440

def test_end_to_end_pipeline_and_roi():
    report = run_pipeline()
    assert report.total_incidents_processed == 5
    assert report.sev1_count == 1
    assert report.sev2_count == 2
    assert report.hours_saved > 3.0
    assert report.annual_roi_projected_usd >= 40000.0
    
    assert Path("output/triage_report.json").exists()
    assert Path("output/dashboard.html").exists()
