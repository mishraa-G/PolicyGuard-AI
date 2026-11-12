"""Unit and integration tests for LangGraph State Machine Workflow."""

import pytest
from src.graph.workflow import execute_compliance_check

def test_workflow_approved_claim():
    res = execute_compliance_check("Can I expense an $80 dinner in Chicago with an itemized receipt?")
    assert res["verdict"] == "APPROVED"
    assert len(res["citations"]) > 0
    assert res["total_latency_ms"] < 800.0

def test_workflow_violation_claim():
    res = execute_compliance_check("Can I expense a $95 dinner in Austin without manager escalation?")
    assert res["verdict"] == "VIOLATION"
    assert res["total_latency_ms"] < 800.0

def test_workflow_missing_receipt():
    res = execute_compliance_check("Can I claim a $60 dinner in New York without an itemized receipt?")
    assert res["verdict"] == "VIOLATION"

def test_workflow_critical_sla_pass():
    res = execute_compliance_check("Does a 36-hour remediation plan for a Critical SQL injection vulnerability meet the SLA?")
    assert res["verdict"] == "APPROVED"

def test_workflow_latency_budget():
    res = execute_compliance_check("What is the mandatory retention timeline for customer audit logs?")
    assert res["total_latency_ms"] < 800.0

