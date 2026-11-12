"""Automated Ragas-Style Compliance Evaluation Metrics.
Calculates Context Recall, Faithfulness / Hallucination Rate, Context Precision,
and Ground-Truth Verdict Accuracy across benchmark edge cases.
"""

import re
from typing import List, Dict, Any, Optional

class ComplianceMetricsEvaluator:
    def evaluate_context_recall(
        self,
        retrieved_chunks: List[Dict[str, Any]],
        ground_truth_facts: List[str],
        sql_rules: Optional[List[Dict[str, Any]]] = None
    ) -> float:
        """Calculates Context Recall: Proportion of ground truth facts present in retrieved chunks + SQL rules."""
        if not ground_truth_facts:
            return 1.0

        all_context = " ".join([
            c["payload"].get("text", "").lower() for c in retrieved_chunks
        ])
        if sql_rules:
            all_context += " " + " ".join([str(r).lower() for r in sql_rules])

        hits = 0
        for fact in ground_truth_facts:
            fact_tokens = [w.lower() for w in re.findall(r"\b[\$a-z0-9\.-]+\b", fact)]
            meaningful = [
                t for t in fact_tokens 
                if t not in {"the", "a", "an", "for", "in", "on", "is", "are", "to", "and", "or", "of", "with", "without", "at", "by"}
            ]

            if not meaningful:
                hits += 1
                continue

            matching = sum(1 for t in meaningful if t in all_context)
            if (matching / len(meaningful)) >= 0.28:
                hits += 1

        return hits / len(ground_truth_facts)

    def evaluate_context_precision(
        self,
        retrieved_chunks: List[Dict[str, Any]],
        expected_policy_id: str,
        category: str
    ) -> float:
        """Calculates Context Precision: Precision of top-ranked relevant chunks."""
        if not retrieved_chunks:
            return 0.0

        relevant_ranks = []
        for idx, chunk in enumerate(retrieved_chunks):
            payload = chunk["payload"]
            is_relevant = (
                payload.get("document_id", "") == expected_policy_id or
                payload.get("category", "") == category
            )
            if is_relevant:
                relevant_ranks.append(idx + 1)

        if not relevant_ranks:
            return 0.0

        score = sum(
            (i + 1) / rank for i, rank in enumerate(relevant_ranks)
        ) / len(relevant_ranks)

        return min(1.0, score)

    def evaluate_hallucination_and_faithfulness(
        self,
        reasoning: str,
        verdict: str,
        sql_verification_result: Dict[str, Any],
        ground_truth_verdict: str,
        ground_truth_facts: List[str]
    ) -> Dict[str, Any]:
        """Calculates Faithfulness and Hallucination Rate.
        Flags any synthesized claims that contradict deterministic SQL truth or ground truth.
        """
        hallucination_reasons = []

        if verdict != ground_truth_verdict:
            hallucination_reasons.append(
                f"Verdict mismatch: Predicted '{verdict}' vs Ground Truth '{ground_truth_verdict}'"
            )

        if sql_verification_result.get("evaluated") and not sql_verification_result.get("compliant"):
            if verdict == "APPROVED":
                hallucination_reasons.append(
                    "Deterministic SQL violation bypassed: synthesized approval on forbidden spend/SLA."
                )

        total_claims = max(1, len(ground_truth_facts) + 1)
        contradictory_claims = len(hallucination_reasons)

        hallucination_rate = min(1.0, contradictory_claims / total_claims)
        faithfulness = 1.0 - hallucination_rate

        return {
            "is_hallucination": len(hallucination_reasons) > 0,
            "hallucination_rate": hallucination_rate,
            "faithfulness": faithfulness,
            "reasons": hallucination_reasons
        }
