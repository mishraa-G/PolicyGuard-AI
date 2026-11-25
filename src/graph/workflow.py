"""LangGraph Workflow Compilation for PolicyGuard.
Builds the state graph connecting routing, Qdrant hybrid retrieval,
SQL validation, synthesis, and self-correction guardrails.
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, START, END

from src.graph.state import PolicyGuardState
from src.graph.nodes import (
    node_analyze_and_route,
    node_retrieve_qdrant,
    node_evaluate_sql,
    node_synthesize_compliance,
    node_validate_guardrail
)

def qdrant_next_step(state: PolicyGuardState) -> str:
    """Conditional edge router after retrieval: bypasses SQL for purely qualitative inquiries."""
    route = state.get("route", "HYBRID")
    if route == "SEMANTIC":
        return "synthesize_compliance"
    return "evaluate_sql"

def create_policyguard_graph():
    """Constructs and compiles the PolicyGuard LangGraph state machine."""
    workflow = StateGraph(PolicyGuardState)

    # Register nodes
    workflow.add_node("analyze_and_route", node_analyze_and_route)
    workflow.add_node("retrieve_qdrant", node_retrieve_qdrant)
    workflow.add_node("evaluate_sql", node_evaluate_sql)
    workflow.add_node("synthesize_compliance", node_synthesize_compliance)
    workflow.add_node("validate_guardrail", node_validate_guardrail)

    # Connect nodes
    workflow.add_edge(START, "analyze_and_route")
    workflow.add_edge("analyze_and_route", "retrieve_qdrant")

    # Dynamic branch after retrieval:
    # If purely qualitative (SEMANTIC), skip SQL evaluation and go straight to synthesis.
    # If quantitative (HYBRID), execute SQL deterministic check.
    workflow.add_conditional_edges(
        "retrieve_qdrant",
        qdrant_next_step,
        {
            "synthesize_compliance": "synthesize_compliance",
            "evaluate_sql": "evaluate_sql"
        }
    )

    workflow.add_edge("evaluate_sql", "synthesize_compliance")
    workflow.add_edge("synthesize_compliance", "validate_guardrail")
    workflow.add_edge("validate_guardrail", END)

    return workflow.compile()

# Singleton graph app instance
app_graph = create_policyguard_graph()

def execute_compliance_check(query: str, session_id: str = "default_session") -> PolicyGuardState:
    """Convenience helper to invoke the compiled LangGraph pipeline."""
    initial_state: PolicyGuardState = {
        "query": query,
        "session_id": session_id,
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

    result = app_graph.invoke(initial_state)
    return result

if __name__ == "__main__":
    sample_query = "Can I expense a $110 dinner in San Francisco without an itemized receipt?"
    print(f"Executing Query: '{sample_query}'")
    out = execute_compliance_check(sample_query)
    print(f"Verdict: {out['verdict']}")
    print(f"Reasoning:\n{out['detailed_reasoning']}")
    print(f"Latency: {out['total_latency_ms']} ms")
    print(f"Citations: {out['citations']}")

