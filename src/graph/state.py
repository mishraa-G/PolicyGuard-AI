"""LangGraph State Definition for PolicyGuard Enterprise Compliance RAG."""

from typing import TypedDict, List, Dict, Any, Optional

class PolicyGuardState(TypedDict):
    # Input
    query: str
    session_id: str

    # Query Analysis & Routing
    intent_type: str  # EXPENSE | INFODEC_SLA | PROCUREMENT | HR_POLICY | GENERAL_COMPLIANCE
    extracted_entities: Dict[str, Any]
    route: str  # HYBRID | SQL_DETERMINISTIC | SEMANTIC

    # Context & Evidence
    retrieved_chunks: List[Dict[str, Any]]
    sql_rules: List[Dict[str, Any]]
    sql_verification_result: Dict[str, Any]

    # Synthesis & Verdict
    verdict: str  # APPROVED | VIOLATION | CONDITIONAL_APPROVAL | ESCALATION_REQUIRED
    summary: str
    detailed_reasoning: str
    citations: List[str]

    # Guardrails & Hallucination Defense
    guardrail_passed: bool
    hallucination_flags: List[str]
    guardrail_corrected: bool

    # Latency Telemetry (sub-800ms accelerator monitoring)
    latency_breakdown_ms: Dict[str, float]
    total_latency_ms: float

