"""Deterministic Rules Engine.
Executes parameterized SQL queries against structured compliance tables to provide
ground-truth validation, eliminate numerical hallucinations, and enforce hard limits.
"""

from typing import Dict, Any, Optional, Tuple, List
from src.sql_engine.database import get_connection

class DeterministicRulesEngine:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def check_spending(
        self,
        expense_type: str,
        amount: float,
        is_tier1_city: bool = False,
        has_receipt: bool = True
    ) -> Dict[str, Any]:
        """Evaluates an expense claim against deterministic spending limits."""
        tier = "Tier-1 Metro" if is_tier1_city else "Standard"
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM spending_limits WHERE expense_type = ? AND tier = ?",
            (expense_type, tier)
        )
        row = cursor.fetchone()

        if not row:
            # Fallback to Global tier
            cursor.execute(
                "SELECT * FROM spending_limits WHERE expense_type = ? AND tier = 'Global'",
                (expense_type,)
            )
            row = cursor.fetchone()

        conn.close()

        if not row:
            return {
                "evaluated": False,
                "compliant": True,
                "reason": f"No deterministic spending limit found for expense type '{expense_type}'."
            }

        cap = float(row["amount_cap_usd"])
        receipt_threshold = float(row["receipt_mandatory_threshold"])
        authority = row["approval_authority"]

        violations = []
        if cap > 0 and amount > cap:
            violations.append(
                f"Amount ${amount:.2f} exceeds allowable cap of ${cap:.2f} for {tier} {expense_type}. Requires {authority} escalation."
            )

        if not has_receipt and amount > receipt_threshold:
            violations.append(
                f"Expense of ${amount:.2f} exceeds ${receipt_threshold:.2f} itemized receipt threshold. Missing receipt violation."
            )

        is_compliant = len(violations) == 0
        return {
            "evaluated": True,
            "compliant": is_compliant,
            "expense_type": expense_type,
            "claimed_amount": amount,
            "allowable_cap": cap,
            "receipt_mandatory_threshold": receipt_threshold,
            "required_approval_authority": authority,
            "violations": violations,
            "deterministic_rule": row["condition_notes"]
        }

    def check_sla(self, sla_name: str, proposed_duration_hours: float) -> Dict[str, Any]:
        """Validates SLA durations (remediation, breach reporting) against statutory standards."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM compliance_slas WHERE sla_name = ?",
            (sla_name,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return {
                "evaluated": False,
                "compliant": True,
                "reason": f"No deterministic SLA found for '{sla_name}'."
            }

        max_hours = int(row["max_duration_hours"])
        is_compliant = proposed_duration_hours <= max_hours

        return {
            "evaluated": True,
            "compliant": is_compliant,
            "sla_name": sla_name,
            "proposed_hours": proposed_duration_hours,
            "statutory_limit_hours": max_hours,
            "statutory_reference": row["statutory_reference"],
            "violation": None if is_compliant else f"Proposed duration {proposed_duration_hours}h exceeds maximum statutory SLA of {max_hours}h ({row['statutory_reference']})."
        }

    def check_procurement_threshold(
        self,
        contract_amount: float,
        competitive_bids_count: int = 1,
        approver_role: str = ""
    ) -> Dict[str, Any]:
        """Evaluates contract value against procurement matrix requirements."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM procurement_approval_matrix 
            WHERE ? >= min_amount_usd AND ? <= max_amount_usd
            """,
            (contract_amount, contract_amount)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return {"evaluated": False, "compliant": True}

        required_role = row["required_role"]
        required_bids = int(row["competitive_bids_count"])
        rfp_mandatory = bool(row["rfp_mandatory"])

        violations = []
        if competitive_bids_count < required_bids:
            violations.append(
                f"Procurement value ${contract_amount:,.2f} requires at least {required_bids} competitive bids (provided: {competitive_bids_count})."
            )
        if rfp_mandatory and competitive_bids_count < 3:
            violations.append(f"Spend exceeding ${row['min_amount_usd']:,.2f} strictly mandates a formal RFP process.")

        return {
            "evaluated": True,
            "compliant": len(violations) == 0,
            "contract_amount": contract_amount,
            "required_role": required_role,
            "required_competitive_bids": required_bids,
            "rfp_mandatory": rfp_mandatory,
            "violations": violations
        }

    def query_policy_rules(self, key_query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Queries structured policy constraints by keyword or rule key."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT policy_id, category, rule_key, rule_value, rule_value_str, description, jurisdiction, version
            FROM policy_rules
            WHERE rule_key LIKE ? OR category LIKE ? OR description LIKE ?
            LIMIT ?
            """,
            (f"%{key_query}%", f"%{key_query}%", f"%{key_query}%", limit)
        )
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def cross_check_candidate_facts(self, candidate_facts: Dict[str, Any]) -> List[str]:
        """Cross-checks synthesized facts against deterministic SQL constraints.
        Returns a list of contradiction warnings / hallucination flags.
        """
        contradictions = []

        # Check expense amount vs allowable cap
        if "expense_type" in candidate_facts and "claimed_amount" in candidate_facts:
            exp_type = candidate_facts["expense_type"]
            amount = float(candidate_facts["claimed_amount"])
            is_tier1 = candidate_facts.get("is_tier1_city", False)
            res = self.check_spending(exp_type, amount, is_tier1_city=is_tier1)
            if res.get("evaluated") and not res.get("compliant"):
                contradictions.extend(res.get("violations", []))

        # Check SLA
        if "sla_name" in candidate_facts and "proposed_hours" in candidate_facts:
            sla_name = candidate_facts["sla_name"]
            hours = float(candidate_facts["proposed_hours"])
            res = self.check_sla(sla_name, hours)
            if res.get("evaluated") and not res.get("compliant"):
                contradictions.append(res["violation"])

        # Check procurement
        if "contract_amount" in candidate_facts:
            amount = float(candidate_facts["contract_amount"])
            bids = int(candidate_facts.get("bids_count", 1))
            res = self.check_procurement_threshold(amount, competitive_bids_count=bids)
            if res.get("evaluated") and not res.get("compliant"):
                contradictions.extend(res.get("violations", []))

        return contradictions

