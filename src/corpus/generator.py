"""Enterprise Policy Corpus Generator.
Generates 200+ realistic, multi-page, multi-section enterprise compliance policy documents
with strict numerical rules, approval hierarchies, and structured metadata.
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from src.config import settings

VERTICALS = {
    "infosec": {
        "prefix": "INF-POL",
        "name": "Information Security & Data Protection",
        "authorizer": "Chief Information Security Officer",
        "topics": [
            ("Data Retention and Archival Standard", "retention_period_years", 7, "All customer audit logs, transaction records, and compliance artifacts must be retained for exactly 7 years."),
            ("Cryptographic Key Management Standard", "min_key_length_rsa", 3072, "Asymmetric encryption keys must utilize minimum RSA-3072 or ECC-384 bit curves. AES-256 is mandatory for data-at-rest."),
            ("Vulnerability Remediation SLAs", "critical_sla_hours", 48, "Critical severity vulnerabilities (CVSS 9.0+) must be remediated or mitigated within 48 hours. High severity (CVSS 7.0-8.9) within 14 days."),
            ("Access Control and MFA Mandate", "session_timeout_minutes", 15, "Privileged administrative sessions must enforce hardware MFA (FIDO2) and automatically terminate after 15 minutes of inactivity."),
            ("Data Classification and Handling", "max_sharing_level", 2, "Confidential and Restricted data requires mandatory end-to-end encryption and watermarking before external transmission."),
            ("Incident Response & Breach Notification", "breach_notice_hours", 24, "Material security incidents must be escalated to legal and CISO within 4 hours; regulatory notifications executed within 72 hours (GDPR) or 24 hours (SEC)."),
            ("Endpoint Security & Mobile Device Management", "encryption_type", "BitLocker/FileVault", "All laptops and portable devices must enforce full disk encryption (XTS-AES 256) and EDR agent compliance."),
            ("Third-Party Vendor Security Assessment", "tier1_assessment_frequency_months", 12, "Tier-1 SaaS and infrastructure vendors holding customer PII require annual SOC 2 Type II audits and penetration tests."),
            ("Cloud Security & IAM Least Privilege", "inactive_account_deprovision_days", 30, "IAM accounts inactive for more than 30 consecutive days must be automatically disabled; rotated credentials every 90 days."),
            ("Disaster Recovery and Backup Verification", "rpo_hours", 4, "Core database clusters must guarantee an RPO (Recovery Point Objective) under 4 hours and RTO under 8 hours with quarterly failover tests.")
        ]
    },
    "travel_expense": {
        "prefix": "TRV-POL",
        "name": "Corporate Travel & Expense Management",
        "authorizer": "Chief Financial Officer & VP Global Controller",
        "topics": [
            ("Daily Meal Allowance & Per Diem Caps", "daily_meal_limit_usd", 85, "Standard daily domestic meal allowance is capped at $85/day. High-cost Tier-1 cities (NYC, SF, London, Tokyo) allow up to $120/day."),
            ("Air Travel Booking & Cabin Class Policy", "intl_flight_hours_for_business", 6, "Domestic flights must be booked in Economy. International flights with continuous flight duration exceeding 6 hours qualify for Business Class."),
            ("Hotel & Lodging Rate Ceiling", "hotel_nightly_cap_usd", 250, "Standard domestic hotel rate cap is $250/night before taxes. Tier-1 metropolitan markets have an authorized ceiling of $375/night."),
            ("Ground Transportation & Rideshare Policy", "rental_car_approval_threshold_days", 3, "Rideshare (Uber/Lyft Standard) is preferred for transit under 3 days. Rental cars require Director pre-approval for assignments exceeding 3 days."),
            ("Client Entertainment & Hospitality", "per_head_dinner_cap_usd", 150, "Client dinners exceeding $150 per attendee require VP pre-approval. Alcohol expense must not exceed 35% of the total dining bill."),
            ("Receipt Requirement and Itemization Threshold", "receipt_mandatory_threshold_usd", 25, "Itemized receipts are legally mandatory for any expense exceeding $25.00. Missing receipt declarations are capped at 2 per calendar year."),
            ("Conference and Event Travel Guidelines", "conference_ticket_limit_usd", 2000, "Individual industry conference registrations exceeding $2,000 require Department Head approval and at least 30 days advance booking."),
            ("Currency Conversion and Foreign Travel Advances", "max_cash_advance_usd", 500, "Corporate card must be used for foreign transactions. Foreign currency emergency cash advances are strictly capped at $500 with Finance signoff."),
            ("Mileage Reimbursement for Personal Vehicles", "mileage_rate_cents", 67, "Personal vehicle business use is reimbursed at standard IRS rate of 67 cents per mile; commuting distance is strictly non-reimbursable."),
            ("Non-Reimbursable Personal Expenses", "personal_expense_threshold", 0, "Hotel mini-bar, in-flight WiFi under 2 hours, personal grooming, spousal travel, and traffic violation fines are strictly non-reimbursable.")
        ]
    },
    "hr_compliance": {
        "prefix": "HRC-POL",
        "name": "Human Resources & Workforce Compliance",
        "authorizer": "Chief People Officer & General Counsel",
        "topics": [
            ("Remote Work & Home Office Equipment Stipend", "home_office_stipend_usd", 1000, "Eligible remote employees receive a one-time home office equipment stipend of $1,000 and a monthly internet subsidy of $75."),
            ("Parental & Family Bonding Leave", "paid_parental_leave_weeks", 16, "Primary and secondary caregivers with at least 6 months continuous service receive 16 consecutive weeks of 100% paid parental leave."),
            ("Outside Business Activities & Moonlighting", "approval_authority", "Legal & Ethics Committee", "Any outside consulting, board memberships, or secondary commercial employment strictly requires prior written approval from the Legal & Ethics Committee."),
            ("Equal Opportunity, Anti-Harassment & Non-Discrimination", "investigation_initiation_hours", 48, "Zero tolerance for workplace discrimination or harassment. Formal complaints must trigger formal investigation within 48 hours."),
            ("Performance Improvement Plans (PIP) Guidelines", "pip_duration_days", 45, "Formal performance remediation plans must span a minimum duration of 30 days and maximum 60 days, benchmarked by measurable weekly KPIs."),
            ("Bereavement & Compassionate Care Leave", "bereavement_days", 5, "Employees are granted up to 5 consecutive paid days off for immediate family bereavement, and 3 paid days for extended family."),
            ("Relocation Assistance & Clawback Terms", "clawback_months", 24, "Corporate relocation packages exceeding $10,000 are subject to a 24-month pro-rated repayment clawback if the employee voluntarily resigns."),
            ("Paid Time Off (PTO) Carryover and Payout", "max_pto_carryover_days", 10, "A maximum of 10 unused PTO days may be carried forward into the subsequent calendar year. Unused surplus beyond 10 days expires December 31."),
            ("Jury Duty and Civic Engagement Leave", "paid_jury_duty_days", 10, "Up to 10 days of paid jury duty leave per calendar year is provided upon submission of summons or court clerk certification."),
            ("Employee Grievance & Retaliation Safeguards", "ombudsperson_access", "Confidential", "Confidential channels to external Ombudsperson are maintained. Any retaliatory act against reporting employees results in immediate termination.")
        ]
    },
    "procurement": {
        "prefix": "PRO-POL",
        "name": "Corporate Procurement & Vendor Governance",
        "authorizer": "Head of Global Strategic Sourcing",
        "topics": [
            ("Purchase Order Thresholds and Signing Authority", "director_approval_ceiling_usd", 25000, "Contracts up to $5,000 require Manager signoff. $5,001-$25,000 requires Director approval. Contracts above $100,000 require VP, Legal, and CFO signoff."),
            ("Competitive Bidding and RFP Requirements", "rfp_mandatory_threshold_usd", 50000, "Procurement engagements exceeding $50,000 mandate an RFP process with at least 3 formal, independent competitive vendor proposals."),
            ("Sole-Source Vendor Justification Standard", "cfo_exception_required", "True", "Bypassing competitive RFP via Sole-Source requires demonstrated proprietary technical exclusivity and joint signoff from VP Sourcing and CFO."),
            ("Software SaaS Subscription Purchasing", "infosec_preclearance_required", "True", "Any software license or cloud SaaS subscription handling company data requires mandatory InfoSec & Legal privacy review prior to contract signature."),
            ("Payment Terms & Early Payment Discounts", "default_payment_terms_days", 60, "Standard corporate purchase terms are Net 60 days. Shorter terms (Net 30 or Net 15) require 2% early settlement discount or Controller approval."),
            ("Emergency Procurement Procedures", "emergency_spend_ceiling_usd", 50000, "In verified operational emergencies threatening revenue or safety, emergency spending up to $50,000 is authorized with post-hoc ratification within 5 business days."),
            ("Capital Expenditure (CapEx) Authorization Matrix", "board_capex_threshold_usd", 500000, "Capital asset investments exceeding $250,000 require Executive Committee approval; CapEx over $500,000 requires Board of Directors authorization."),
            ("Vendor Code of Conduct & ESG Standards", "esg_audit_rights", "Mandatory", "All suppliers must contractually agree to the Vendor ESG Charter, modern slavery prohibitions, and grant annual supply-chain audit rights."),
            ("Independent Contractor & Contingent Worker Sourcing", "max_contingent_tenure_months", 18, "Independent contractors and agency staff cannot exceed a continuous engagement tenure of 18 months without a mandatory 6-month break-in-service."),
            ("Procurement Card (P-Card) Usage Limits", "pcard_single_transaction_limit_usd", 2500, "Corporate P-Cards have a strict per-transaction ceiling of $2,500 and monthly aggregate limit of $10,000. Capital equipment and software are blocked.")
        ]
    },
    "code_of_conduct": {
        "prefix": "ETH-POL",
        "name": "Business Conduct, Ethics & Regulatory Compliance",
        "authorizer": "Chief Compliance Officer & Audit Committee",
        "topics": [
            ("Gift Acceptance and Corporate Entertainment Limits", "max_gift_value_usd", 100, "Employees may not accept gifts, favors, or hospitality exceeding $100 in cumulative annual value from any single vendor or counterparty. Cash or cash equivalents are strictly prohibited."),
            ("Anti-Bribery and Foreign Corrupt Practices Act (FCPA)", "facilitation_payments_prohibited", "True", "Strict prohibition on giving, offering, or authorizing bribes or facilitation payments to foreign officials, regardless of local customary business practice."),
            ("Insider Trading and Pre-Clearance Windows", "blackout_window_weeks", 2, "Covered employees are barred from trading company securities during quarterly blackout windows starting 2 weeks prior to quarter-end until 48 hours post-earnings release."),
            ("Whistleblower Protection & Anonymous Reporting Hotline", "retaliation_penalty", "Immediate Termination", "Anonymous 24/7 compliance reporting hotline operated by an independent third party. Retaliation against whistleblowers results in immediate termination and legal action."),
            ("Conflict of Interest Disclosures and Recusal", "annual_disclosure_required", "True", "Annual conflict of interest disclosure is mandatory for all managerial personnel. Any personal interest in a vendor or competitor requires immediate recusal."),
            ("Political Contributions and Corporate Lobbying", "corporate_fund_use", "Prohibited", "Company funds, facilities, or resources may not be contributed to political campaigns, parties, or PACs without unanimous Board approval."),
            ("Social Media and Public Communication Protocols", "authorized_spokesperson_only", "True", "Only designated corporate spokespersons may comment publicly or on social media regarding company operations, financial results, or legal matters."),
            ("Trade Sanctions and Export Control Compliance", "sanctions_screening_required", "True", "All international transactions and counterparties must undergo automated screening against OFAC, EU, and UN Consolidated Sanctions Lists prior to fulfillment."),
            ("Intellectual Property & Confidentiality Obligations", "survival_post_employment_years", "Indefinite", "All patents, code, trade secrets, and proprietary documentation created during employment remain sole company property and confidentiality obligations survive indefinitely."),
            ("Fair Competition and Antitrust Compliance", "competitor_discussion_prohibited", "True", "Employees are strictly forbidden from discussing pricing, market allocation, customer segmentation, or bidding strategies with competitors.")
        ]
    }
}

JURISDICTIONS = ["Global", "North America (US/CA)", "European Union (GDPR)", "APAC (Singapore/Japan)"]
VERSIONS = ["v2.4", "v3.1", "v4.0", "v1.8"]

def generate_policy_markdown(
    doc_id: str,
    title: str,
    vertical_key: str,
    vertical_name: str,
    authorizer: str,
    topic_data: tuple,
    jurisdiction: str,
    version: str,
    variation_idx: int
) -> str:
    metric_key, metric_val, core_rule = topic_data[1], topic_data[2], topic_data[3]

    doc_text = f"""---
document_id: "{doc_id}"
title: "{title} - Standard Operating Procedure"
category: "{vertical_key}"
category_name: "{vertical_name}"
jurisdiction: "{jurisdiction}"
version: "{version}"
effective_date: "2024-01-15"
authorizer: "{authorizer}"
classification: "Enterprise Internal / Compliance Bound"
status: "active"
---

# {doc_id}: {title}

## Section 1: Executive Purpose & Enterprise Scope
This document articulates the mandatory enterprise-wide compliance framework governing {title.lower()} within {jurisdiction}. 
All business units, permanent personnel, contingent contractors, and executive officers are legally and contractually obligated 
to adhere to the provisions established herein. 

Compliance with this policy is subject to continuous automated monitoring and periodic independent audit by the Internal Audit Committee 
and external regulatory compliance assessors. Non-compliance compromises enterprise regulatory posture, exposing the organization 
to substantial financial penalties, civil liability, and reputational injury.

## Section 2: Statutory Authority & Regulatory Mapping
This policy aligns directly with international statutory frameworks including:
- ISO/IEC 27001:2022 Information Security Management Standards
- AICPA SOC 2 Type II Trust Services Criteria (Security, Availability, Confidentiality)
- Sarbanes-Oxley Act (SOX) Section 404 Financial Internal Controls
- EU General Data Protection Regulation (GDPR) Regulation (EU) 2016/679
- Foreign Corrupt Practices Act (15 U.S.C. § 78dd-1) and UK Bribery Act 2010

## Section 3: Core Compliance Mandates & Operational Rules
### 3.1 Primary Requirement
{core_rule}

### 3.2 Key Quantifiable Metric & Bound
- Parameter: `{metric_key}`
- Formal Threshold / Value: **{metric_val}**
- Scope of Application: Regional operations across {jurisdiction} under version {version}.
- Enforcement Mechanism: Automated deterministic checking and mandatory management approval hierarchy.

### 3.3 Multi-Tier Authorization Matrix
1. **Tier 1 (Operational)**: Requests within standard limits require immediate supervisor or operational unit lead approval.
2. **Tier 2 (Managerial)**: Any deviation or threshold variance between standard baseline and 1.5x limit requires Director or VP signoff.
3. **Tier 3 (Executive / Exceptional)**: Variances exceeding established ceilings require written authorization from {authorizer}.

## Section 4: Operational Implementation & Daily Procedures
Personnel must follow standardized workflows when initiating transactions or operations governed by this policy:
1. Complete formal pre-authorization documentation via enterprise workflow software at least 5 business days prior to commitment.
2. Maintain complete evidentiary records, including itemized invoices, tamper-evident audit logs, and counterparty confirmations.
3. Submit all reconciliation artifacts within 14 calendar days of transaction completion.
4. Flag any anomalies or potential conflicts of interest immediately to the compliance monitoring office.

## Section 5: Exceptions, Exemption Waivers & Emergency Protocols
No informal or verbal waivers of this policy are permissible. Exceptional business circumstances warranting an exemption require:
- Formal submission of Exemption Request Form (ERF) detailing commercial necessity and compensatory risk controls.
- Quantitative risk assessment conducted by the Risk Management Department.
- Explicit, timestamped digital signature from {authorizer}.
- Exemption validity is strictly time-bounded to a maximum of 90 calendar days, requiring re-certification thereafter.

## Section 6: Audit Evidentiary Standards, Logging & Sanctions
All transactions, approvals, and access logs governed by this standard are streamed to tamper-proof, append-only centralized audit infrastructure. 
Audit logs are retained for the statutory retention period and are subject to unannounced quarterly compliance inspection.

Failure to comply with these provisions, intentional falsification of compliance records, or evasion of approval hierarchies 
constitutes gross misconduct resulting in disciplinary consequences up to and including termination of employment, revocation of privileges, 
and referral to civil or criminal law enforcement authorities where appropriate.
"""
    return doc_text

def build_corpus() -> List[Dict[str, Any]]:
    """Builds 210 distinct multi-page enterprise policy documents."""
    generated_docs = []
    doc_counter = 1

    for vert_key, vert_info in VERTICALS.items():
        prefix = vert_info["prefix"]
        topics = vert_info["topics"]

        # Generate 42 documents per vertical = 210 total documents
        for i in range(42):
            topic_idx = i % len(topics)
            topic_tuple = topics[topic_idx]
            topic_title = topic_tuple[0]
            jurisdiction = JURISDICTIONS[i % len(JURISDICTIONS)]
            version = VERSIONS[i % len(VERSIONS)]
            variation_idx = (i // len(topics)) + 1

            doc_id = f"{prefix}-{(i + 1):03d}"
            title = f"{topic_title} ({jurisdiction} Amendment {variation_idx})"

            content = generate_policy_markdown(
                doc_id=doc_id,
                title=title,
                vertical_key=vert_key,
                vertical_name=vert_info["name"],
                authorizer=vert_info["authorizer"],
                topic_data=topic_tuple,
                jurisdiction=jurisdiction,
                version=version,
                variation_idx=variation_idx
            )

            dir_path = settings.raw_policies_dir / vert_key
            dir_path.mkdir(parents=True, exist_ok=True)
            file_path = dir_path / f"{doc_id}.md"

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            generated_docs.append({
                "doc_id": doc_id,
                "title": title,
                "category": vert_key,
                "category_name": vert_info["name"],
                "jurisdiction": jurisdiction,
                "version": version,
                "authorizer": vert_info["authorizer"],
                "rule_key": topic_tuple[1],
                "rule_value": topic_tuple[2],
                "core_rule": topic_tuple[3],
                "file_path": str(file_path),
                "content": content
            })

            doc_counter += 1

    return generated_docs

if __name__ == "__main__":
    print(f"Generating enterprise policy documents in {settings.raw_policies_dir}...")
    docs = build_corpus()
    print(f"Successfully generated {len(docs)} multi-page enterprise compliance policy documents!")
