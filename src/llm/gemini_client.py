"""Google Gemini Client for PolicyGuard Compliance Synthesis.
Integrates Gemini 1.5 Flash / 2.0 Flash via direct high-performance REST calls
with automatic JSON structured output and fallback guardrails.
"""

import json
import time
import re
from typing import Dict, Any, List, Optional
import httpx
from src.config import settings

GEMINI_API_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

SYSTEM_INSTRUCTION = """You are PolicyGuard, an elite enterprise compliance intelligence officer.
Your task is to analyze employee inquiries against authoritative enterprise policy provisions and deterministic SQL bounds.

You must output strictly valid JSON adhering to this schema:
{
  "verdict": "APPROVED" | "VIOLATION" | "CONDITIONAL_APPROVAL",
  "summary": "Concise 1-sentence compliance determination",
  "detailed_reasoning": "Detailed factual justification explaining allowable caps, conditions, and requirements",
  "citations": ["DOC-ID (Section Name)"]
}

Rules:
1. Deterministic SQL Constraints take absolute precedence over model assumptions.
2. If an expense exceeds allowable caps or lacks a mandatory itemized receipt, the verdict must be VIOLATION.
3. If cash gifts, facilitation payments, or gifts from RFP bidders are mentioned, verdict must be VIOLATION.
4. Output ONLY raw JSON without conversational filler or markdown wrappers.
"""

class GeminiComplianceClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.gemini_api_key
        self.model = model or settings.gemini_model
        self.timeout = 8.0

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 10)

    def generate_compliance_verdict(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        sql_verification: Dict[str, Any],
        sql_rules: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Calls Google Gemini API to synthesize policy reasoning and compliance verdict."""
        if not self.is_available():
            return None

        # Build prompt
        context_blocks = []
        for c in retrieved_chunks[:4]:
            payload = c["payload"]
            doc_id = payload.get("document_id", "DOC")
            section = payload.get("section", "Section")
            context_blocks.append(f"[{doc_id} | {section}]\n{payload.get('text', '')}")

        combined_context = "\n\n---\n\n".join(context_blocks)
        sql_summary = json.dumps(sql_verification, indent=2)

        prompt_text = f"""Employee Query:
"{query}"

Deterministic SQL Rules & Mathematical Validation:
{sql_summary}

Authoritative Policy Context (Top Retrieved Sections):
{combined_context}

Provide your structured compliance verdict in raw JSON:
"""

        models_to_try = [self.model, "gemini-2.5-flash-lite"] if self.model != "gemini-2.5-flash-lite" else [self.model]

        for model_name in models_to_try:
            url = GEMINI_API_ENDPOINT.format(model=model_name) + f"?key={self.api_key}"
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": prompt_text}]
                    }
                ],
                "systemInstruction": {
                    "parts": [{"text": SYSTEM_INSTRUCTION}]
                },
                "generationConfig": {
                    "temperature": 0.1,
                    "responseMimeType": "application/json"
                }
            }

            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(url, json=payload)
                    if resp.status_code != 200:
                        continue

                    data = resp.json()
                    candidate_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()

                    # Clean markdown wrapper if present
                    clean_json = re.sub(r"^```json\s*|\s*```$", "", candidate_text, flags=re.MULTILINE).strip()
                    parsed = json.loads(clean_json)

                    # Ensure required keys exist
                    if "verdict" in parsed and "detailed_reasoning" in parsed:
                        return parsed
            except Exception:
                continue

        return None

