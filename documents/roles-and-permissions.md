# Roles and Permissions

## Role Model

The platform should use role-based access control with audit logging for all risk decisions, score overrides, document changes, and approval actions.

For the MVP, login should be kept simple with email and password. Enterprise SSO can be added later, but the first build should use users, password hashes, roles, permissions, and supplier-scoped access records.

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

## Supplier Visibility by Role

Every supplier-facing query should enforce tenant scope and role-based supplier visibility. Users must only see suppliers they are permitted to access.

| Role | Supplier Visibility |
|---|---|
| Supplier Admin | Can only see supplier records explicitly linked to the user through supplier access mapping. Cannot see other suppliers. |
| Procurement Buyer | Can only see suppliers linked to that buyer through onboarding ownership, buyer-supplier assignment, or explicit supplier access mapping. |
| Risk Analyst | Can see suppliers assigned to the analyst, suppliers in the analyst's review queue, or suppliers visible through configured risk team scope. |
| Compliance Officer | Can see suppliers with assigned compliance reviews, sanctions/watchlist findings, regulatory findings, or configured compliance team scope. |
| ESG Analyst | Can see suppliers with assigned ESG reviews, ESG findings, or configured ESG team scope. |
| Finance Analyst | Can see suppliers with assigned financial reviews, financial findings, or configured finance team scope. |
| Cyber Risk Analyst | Can see suppliers with assigned cyber reviews, cyber findings, or configured cyber team scope. |
| Supplier Relationship Manager | Can see onboarded suppliers assigned to that relationship manager or configured supplier portfolio. |
| Approver / Risk Committee | Can see suppliers routed to their approval queue or committee scope. |
| System Administrator | Can see and manage supplier records according to tenant administrator permissions. |
| Auditor | Can see supplier records only through read-only audit, decision, evidence, and history views allowed by audit permissions. |

Supplier visibility should be implemented through explicit mapping tables rather than UI-only filtering. Backend APIs must enforce the same visibility rules.

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
