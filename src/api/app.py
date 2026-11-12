"""FastAPI Enterprise Compliance Service for PolicyGuard.
Provides REST endpoints for compliance evaluation, latency telemetry, and policy search.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import time

from src.graph.workflow import execute_compliance_check
from src.corpus.loader import load_all_policies
from src.config import settings

app = FastAPI(
    title="PolicyGuard Enterprise Compliance RAG API",
    description="Enterprise compliance accelerator with LangGraph, Qdrant hybrid retrieval, and deterministic SQL guardrails.",
    version="1.0.0"
)

class ComplianceRequest(BaseModel):
    query: str = Field(..., example="Can I expense a $110 dinner in New York City with an itemized receipt?")
    session_id: Optional[str] = Field(default="session_default")

class ComplianceResponse(BaseModel):
    query: str
    verdict: str
    summary: str
    detailed_reasoning: str
    citations: List[str]
    guardrail_passed: bool
    guardrail_corrected: bool
    latency_breakdown_ms: Dict[str, float]
    total_latency_ms: float

@app.get("/")
def root():
    return {
        "service": "PolicyGuard Enterprise Compliance RAG",
        "version": "1.0.0",
        "status": "operational",
        "docs_url": "/docs"
    }

@app.get("/api/v1/health")
def health():
    return {
        "status": "healthy",
        "qdrant_collection": settings.qdrant_collection,
        "sqlite_db": settings.sqlite_db_path,
        "timestamp": time.time()
    }

@app.post("/api/v1/compliance/check", response_model=ComplianceResponse)
def check_compliance(req: ComplianceRequest):
    try:
        res = execute_compliance_check(req.query, session_id=req.session_id)
        return ComplianceResponse(
            query=res["query"],
            verdict=res["verdict"],
            summary=res["summary"],
            detailed_reasoning=res["detailed_reasoning"],
            citations=res["citations"],
            guardrail_passed=res["guardrail_passed"],
            guardrail_corrected=res["guardrail_corrected"],
            latency_breakdown_ms=res["latency_breakdown_ms"],
            total_latency_ms=res["total_latency_ms"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/policies")
def list_policies(limit: int = 20):
    policies = load_all_policies()
    return {
        "total_policies_count": len(policies),
        "returned_count": min(limit, len(policies)),
        "policies": [
            {
                "document_id": p.get("document_id"),
                "title": p.get("title"),
                "category": p.get("category"),
                "jurisdiction": p.get("jurisdiction"),
                "version": p.get("version"),
                "authorizer": p.get("authorizer")
            }
            for p in policies[:limit]
        ]
    }

@app.get("/api/v1/metrics")
def get_metrics():
    import json
    from pathlib import Path
    eval_path = Path("evaluation/eval_report.json")
    bench_path = Path("benchmarks/latency_summary.json")

    eval_data = {}
    bench_data = {}

    if eval_path.exists():
        with open(eval_path) as f:
            eval_data = json.load(f)

    if bench_path.exists():
        with open(bench_path) as f:
            bench_data = json.load(f)

    return {
        "evaluation_benchmarks": eval_data.get("metrics", {}),
        "latency_telemetry": bench_data
    }

