"""Unit tests for deterministic SQL compliance engine."""

import pytest
from src.sql_engine.rules_engine import DeterministicRulesEngine

@pytest.fixture
def engine():
    return DeterministicRulesEngine()

def test_meal_standard_city_within_cap(engine):
    res = engine.check_spending("meal", 80.0, is_tier1_city=False, has_receipt=True)
    assert res["evaluated"] is True
    assert res["compliant"] is True
    assert res["allowable_cap"] == 85.0

def test_meal_standard_city_exceeds_cap(engine):
    res = engine.check_spending("meal", 95.0, is_tier1_city=False, has_receipt=True)
    assert res["evaluated"] is True
    assert res["compliant"] is False
    assert len(res["violations"]) > 0

def test_tier1_city_cap(engine):
    # Tier-1 allows up to $120
    res = engine.check_spending("meal", 115.0, is_tier1_city=True, has_receipt=True)
    assert res["compliant"] is True
    assert res["allowable_cap"] == 120.0

def test_receipt_threshold_violation(engine):
    # Over $25 requires receipt
    res = engine.check_spending("meal", 45.0, is_tier1_city=False, has_receipt=False)
    assert res["compliant"] is False
    assert any("itemized receipt" in v for v in res["violations"])

def test_critical_sla_compliance(engine):
    # Critical SLA max is 48 hours
    res_pass = engine.check_sla("critical_vuln_remediation", 36.0)
    assert res_pass["compliant"] is True

    res_fail = engine.check_sla("critical_vuln_remediation", 72.0)
    assert res_fail["compliant"] is False

def test_procurement_rfp_requirement(engine):
    # Over $50,000 requires RFP and 3 bids
    res = engine.check_procurement_threshold(85000.0, competitive_bids_count=1)
    assert res["compliant"] is False
    assert res["rfp_mandatory"] is True

