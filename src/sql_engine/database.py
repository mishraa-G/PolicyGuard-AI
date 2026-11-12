"""Deterministic SQL Policy Database for PolicyGuard.
Provides relational storage for strict compliance bounds, numerical thresholds,
approval matrices, and statutory SLAs.
"""

import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional
from src.config import settings

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS policy_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_id TEXT NOT NULL,
    category TEXT NOT NULL,
    rule_key TEXT NOT NULL,
    rule_value REAL,
    rule_value_str TEXT,
    description TEXT NOT NULL,
    jurisdiction TEXT NOT NULL,
    version TEXT NOT NULL,
    UNIQUE(policy_id, rule_key, jurisdiction, version)
);

CREATE TABLE IF NOT EXISTS spending_limits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_type TEXT NOT NULL,
    tier TEXT NOT NULL,
    amount_cap_usd REAL NOT NULL,
    receipt_mandatory_threshold REAL NOT NULL,
    approval_authority TEXT NOT NULL,
    condition_notes TEXT
);

CREATE TABLE IF NOT EXISTS compliance_slas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain TEXT NOT NULL,
    sla_name TEXT NOT NULL,
    max_duration_hours INTEGER NOT NULL,
    statutory_reference TEXT NOT NULL,
    consequence_of_breach TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS procurement_approval_matrix (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    min_amount_usd REAL NOT NULL,
    max_amount_usd REAL NOT NULL,
    required_role TEXT NOT NULL,
    competitive_bids_count INTEGER NOT NULL,
    rfp_mandatory BOOLEAN NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_policy_rules_key ON policy_rules(rule_key, jurisdiction);
CREATE INDEX IF NOT EXISTS idx_spending_limits_type ON spending_limits(expense_type, tier);
CREATE INDEX IF NOT EXISTS idx_compliance_slas_name ON compliance_slas(sla_name);
"""

def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Returns a SQLite connection with dict-like row factory."""
    path = db_path or settings.sqlite_db_path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: Optional[str] = None):
    """Initializes tables and seeds baseline deterministic compliance data."""
    conn = get_connection(db_path)
    with conn:
        conn.executescript(SCHEMA_SQL)
        seed_deterministic_rules(conn)
    conn.close()

def seed_deterministic_rules(conn: sqlite3.Connection):
    """Seeds deterministic ground-truth rules matching enterprise policies."""
    # 1. Spending limits
    spending_data = [
        ("meal", "Standard", 85.0, 25.0, "Manager", "Domestic daily meal allowance"),
        ("meal", "Tier-1 Metro", 120.0, 25.0, "Manager", "High-cost cities: NYC, SF, Tokyo, London"),
        ("hotel", "Standard", 250.0, 0.0, "Manager", "Standard nightly lodging cap before taxes"),
        ("hotel", "Tier-1 Metro", 375.0, 0.0, "Director", "High-cost metro lodging ceiling"),
        ("flight_business", "International", 0.0, 0.0, "VP", "Authorized only if continuous flight > 6 hours"),
        ("gift_acceptance", "Global", 100.0, 0.0, "Ethics Committee", "Annual cumulative limit per vendor; cash prohibited"),
        ("home_office", "Remote", 1000.0, 0.0, "People Ops", "One-time equipment stipend; $75/mo internet subsidy"),
        ("client_dinner_per_head", "Global", 150.0, 25.0, "VP", "Client entertainment max per person; alcohol <= 35%"),
        ("pcard_single_tx", "Global", 2500.0, 0.0, "Finance", "Corporate procurement card single purchase ceiling")
    ]
    conn.executemany("""
        INSERT OR REPLACE INTO spending_limits 
        (id, expense_type, tier, amount_cap_usd, receipt_mandatory_threshold, approval_authority, condition_notes)
        VALUES ((SELECT id FROM spending_limits WHERE expense_type=? AND tier=?), ?, ?, ?, ?, ?, ?)
    """, [(d[0], d[1], d[0], d[1], d[2], d[3], d[4], d[5]) for d in spending_data])

    # 2. Compliance SLAs
    sla_data = [
        ("infosec", "critical_vuln_remediation", 48, "SOC 2 Type II / ISO 27001", "Severe security audit finding / escalation"),
        ("infosec", "high_vuln_remediation", 336, "SOC 2 Type II", "14 days SLA standard"),
        ("infosec", "data_breach_ciso_escalation", 4, "Enterprise Incident Policy", "Internal escalation to legal & executive team"),
        ("infosec", "data_breach_regulatory_notice", 72, "GDPR Article 33 / SEC Rule", "Statutory breach reporting window"),
        ("infosec", "audit_log_retention_years", 61320, "SOX Sec 404 / SOC 2", "7 years continuous immutable retention"),
        ("hr", "harassment_investigation_start", 48, "Equal Opportunity Mandate", "Mandatory formal HR inquiry kickoff"),
        ("hr", "paid_parental_leave_weeks", 2688, "Global Benefits Charter", "16 weeks 100% paid leave for caregivers")
    ]
    conn.executemany("""
        INSERT OR REPLACE INTO compliance_slas
        (id, domain, sla_name, max_duration_hours, statutory_reference, consequence_of_breach)
        VALUES ((SELECT id FROM compliance_slas WHERE sla_name=?), ?, ?, ?, ?, ?)
    """, [(d[1], d[0], d[1], d[2], d[3], d[4]) for d in sla_data])

    # 3. Procurement matrix
    procurement_data = [
        (0.0, 5000.0, "Manager", 1, False),
        (5000.01, 25000.0, "Director", 3, False),
        (25000.01, 50000.0, "Senior Director", 3, False),
        (50000.01, 100000.0, "Vice President", 3, True),
        (100000.01, 10000000.0, "CFO & Legal & VP", 3, True)
    ]
    conn.executemany("""
        INSERT OR REPLACE INTO procurement_approval_matrix
        (id, min_amount_usd, max_amount_usd, required_role, competitive_bids_count, rfp_mandatory)
        VALUES ((SELECT id FROM procurement_approval_matrix WHERE min_amount_usd=? AND max_amount_usd=?), ?, ?, ?, ?, ?)
    """, [(d[0], d[1], d[0], d[1], d[2], d[3], d[4]) for d in procurement_data])

if __name__ == "__main__":
    init_db()
    print(f"Initialized PolicyGuard SQLite Database at {settings.sqlite_db_path} successfully.")
