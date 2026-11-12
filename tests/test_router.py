"""Unit tests for query analyzer and entity router."""

import pytest
from src.graph.nodes import node_analyze_and_route
from src.graph.state import PolicyGuardState

def test_expense_entity_extraction():
    state: PolicyGuardState = {
        "query": "Can I expense an $85 dinner in Chicago with an itemized receipt?",
        "session_id": "test_1",
        "intent_type": "",
        "extracted_entities": {},
        "route": "",
        "retrieved_chunks": [],
        "sql_rules": [],
        "sql_verification_result": {},
        "verdict": "",
        "summary": "",
        "detailed_reasoning": "",
        "citations": [],
        "guardrail_passed": True,
        "hallucination_flags": [],
        "guardrail_corrected": False,
        "latency_breakdown_ms": {},
        "total_latency_ms": 0.0
    }

    res = node_analyze_and_route(state)
    assert res["intent_type"] == "EXPENSE"
    assert res["extracted_entities"]["amount"] == 85.0
    assert res["extracted_entities"]["has_receipt"] is True
    assert res["extracted_entities"]["is_tier1_city"] is False
    assert res["route"] == "HYBRID"

def test_missing_receipt_detection():
    state: PolicyGuardState = {
        "query": "Can I claim a $50 lunch without an itemized receipt?",
        "session_id": "test_2",
        "intent_type": "",
        "extracted_entities": {},
        "route": "",
        "retrieved_chunks": [],
        "sql_rules": [],
        "sql_verification_result": {},
        "verdict": "",
        "summary": "",
        "detailed_reasoning": "",
        "citations": [],
        "guardrail_passed": True,
        "hallucination_flags": [],
        "guardrail_corrected": False,
        "latency_breakdown_ms": {},
        "total_latency_ms": 0.0
    }

    res = node_analyze_and_route(state)
    assert res["extracted_entities"]["has_receipt"] is False

def test_tier1_city_detection():
    state: PolicyGuardState = {
        "query": "Can I expense a $115 meal in Tokyo?",
        "session_id": "test_3",
        "intent_type": "",
        "extracted_entities": {},
        "route": "",
        "retrieved_chunks": [],
        "sql_rules": [],
        "sql_verification_result": {},
        "verdict": "",
        "summary": "",
        "detailed_reasoning": "",
        "citations": [],
        "guardrail_passed": True,
        "hallucination_flags": [],
        "guardrail_corrected": False,
        "latency_breakdown_ms": {},
        "total_latency_ms": 0.0
    }

    res = node_analyze_and_route(state)
    assert res["extracted_entities"]["is_tier1_city"] is True

