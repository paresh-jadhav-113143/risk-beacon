# Roles and Permissions

## Role Model

The platform should use role-based access control with audit logging for all risk decisions, score overrides, document changes, and approval actions.

| Role | Responsibilities |
|---|---|
| Supplier Admin | Submit supplier profile data, upload documents, respond to clarification requests |
| Procurement Buyer | Initiate onboarding, track supplier status, view recommended decision |
| Risk Analyst | Review AI findings, validate evidence, open investigations, recommend actions |
| Compliance Officer | Review sanctions, regulatory, legal, and policy risks |
| ESG Analyst | Review sustainability, labor, environmental, and governance risks |
| Finance Analyst | Review financial filings, credit signals, bankruptcy indicators, and financial distress |
| Cyber Risk Analyst | Review cybersecurity exposure, breach signals, and security certifications |
| Supplier Relationship Manager | Monitor onboarded supplier health and remediation progress |
| Approver / Risk Committee | Make final approve, reject, suspend, or continue decisions |
| System Administrator | Manage users, roles, integrations, thresholds, workflows, and policies |
| Auditor | Review historical decisions, evidence, overrides, and approval trails |

## Permission Areas

| Permission Area | Example Capabilities |
|---|---|
| Supplier Profile | Create, view, edit, archive supplier records |
| Documents | Upload, classify, extract, verify, request replacement |
| Risk Evidence | View source evidence, confidence score, credibility score |
| Risk Score | View score, recalculate, override with reason |
| Decisions | Approve, reject, defer, request more information |
| Cases | Create investigation, assign owner, update status, close case |
| Monitoring | Configure thresholds, subscribe to alerts, pause monitoring |
| Configuration | Manage scoring weights, source connectors, notification policies |
| Audit | Export decision history, evidence trail, score movement, user actions |

## Human-in-the-Loop Governance

AI should assist with extraction, enrichment, scoring, summarization, and recommendations. Final decisions for onboarding, rejection, suspension, or critical risk acceptance should remain with authorized human users.

