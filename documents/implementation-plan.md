# Implementation Plan

## Objective

Build the supplier risk platform in an incremental sequence, starting with a focused MVP for pre-onboarding risk assessment and human decisioning, then expanding into continuous monitoring, authenticity checks, predictive analytics, and enterprise integrations.

## Recommended Build Choices

The architecture documents list several valid options. To keep the first implementation cohesive, use these defaults unless a deployment constraint requires otherwise:

| Area | Initial Choice | Reason |
|---|---|---|
| Frontend | React.js, TypeScript, Tailwind CSS, shadcn/ui | Fast delivery of a polished workflow UI with strong typing |
| Backend API | Python FastAPI | Good fit for AI workflows, async jobs, OCR integrations, and typed contracts |
| Database | SQLite | Simple MVP transactional store for suppliers, users, decisions, cases, scores, audit data, evidence metadata, and agent outputs |
| Migrations | Alembic | Versioned database schema changes |
| Object Storage | S3-compatible storage, MinIO locally | Stores raw documents, extracted files, and evidence snapshots |
| Background Jobs | Celery or Temporal workers in MVP | Start with durable async processing; use Temporal when workflow durability becomes central |
| Agent Layer | Specialized service modules with structured outputs | Keeps agent responsibilities clear while avoiding premature distributed complexity |
| Search and Vector | SQLite FTS or application-level search first; pgvector later | Defer extra infrastructure until semantic evidence search is needed |
| Graph | SQLite relationship tables first, Neo4j/Neptune later | MVP needs relationship mapping, not full graph infrastructure on day one |
| Auth | Email/password login with RBAC tables | Keeps MVP simple; support enterprise SSO later without changing supplier visibility rules |
| Observability | Structured logs and audit logs first, OpenTelemetry later | Gives traceability immediately and leaves room for production-grade monitoring |

## Delivery Strategy

Implement a thin but complete vertical slice first:

1. Create a supplier onboarding request.
2. Upload required documents.
3. Extract and normalize basic supplier data.
4. Run initial enrichment and sanctions/compliance checks.
5. Resolve supplier identity.
6. Calculate category and composite risk scores.
7. Generate an evidence-backed AI summary.
8. Route to human review.
9. Record approve, reject, defer, or request-information decisions.
10. Persist a complete audit trail.

This slice proves the core product loop before adding broader monitoring and advanced intelligence.

## Phase 0: Product and Engineering Foundation

**Goal:** Establish the implementation baseline and remove early ambiguity.

### Scope

- Confirm the initial stack choices.
- Define environments: local, development, staging, production.
- Create repository structure.
- Add local development setup.
- Add CI checks for formatting, linting, type checking, and tests.
- Define API contract style.
- Define core domain language and status values.

### Deliverables

- Monorepo or coordinated app structure:
  - `apps/web` for Next.js.
  - `apps/api` for FastAPI.
  - `packages/contracts` or shared OpenAPI-generated clients if using a monorepo.
- Local SQLite database file, plus `docker-compose` only for object storage and worker dependencies when needed.
- Baseline CI pipeline.
- Initial OpenAPI contract.
- Architecture decision record for the selected stack.

### Acceptance Criteria

- A developer can run the web app, API, database, and worker locally.
- Health checks pass for frontend, backend, database, and worker.
- CI runs on every change.

### SQLite MVP Requirements

SQLite is the default database for the MVP. It avoids database server setup, network dependency, Docker dependency for the database, and corporate proxy or Zscaler complications.

Use these settings at application startup:

```sql
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=5000;
PRAGMA foreign_keys=ON;
```

Implementation rules:

- Store the database file at `./data/risk_beacon.db` for local development.
- Use SQLModel or SQLAlchemy with Alembic migrations.
- Keep the schema relational and portable so PostgreSQL migration remains straightforward.
- Keep write transactions short.
- Run agents in parallel for API calls, OCR, extraction, and enrichment, but persist validated outputs through a controlled persistence layer.
- Add retry handling for transient `database is locked` errors.
- Do not rely on SQLite for multi-server production deployment.

## Phase 1: Core Domain, RBAC, and Audit Foundation

**Goal:** Create the platform skeleton that all workflows depend on.

### Scope

- User, role, and permission model.
- Email and password login with secure password hashes.
- Supplier visibility mapping for buyer and supplier access.
- Supplier master profile.
- Supplier onboarding request.
- Audit log service.
- Decision status model.
- Basic app navigation and workspace shell.

### Core Roles

- Supplier Admin
- Procurement Buyer
- Risk Analyst
- Supplier Relationship Manager
- Approver / Risk Committee
- System Administrator
- Auditor

### Core Entities

| Entity | Purpose |
|---|---|
| User | Authenticated person using the platform with email/password credentials |
| Role | Named responsibility bundle |
| Permission | Granular capability gate |
| SupplierUserAccess | Maps supplier users to supplier records |
| BuyerSupplierAccess | Maps buyers to supplier records they can view or manage |
| Supplier | Supplier master profile |
| SupplierContact | Supplier contact details |
| OnboardingRequest | Intake workflow instance |
| Decision | Human decision and rationale |
| AuditEvent | Immutable action history |

### Acceptance Criteria

- Users can be assigned roles.
- Permissions gate key UI and API actions.
- Buyers can only see suppliers linked to them through onboarding ownership, buyer-supplier assignment, or explicit supplier access mapping.
- Supplier users can only see supplier records explicitly linked to them.
- Supplier records can be created, viewed, edited, and archived.
- Audit events are written for supplier changes, document actions, score overrides, and decisions.

## Phase 2: Supplier Intake and Document Handling

**Goal:** Let buyers and supplier admins collect the information needed for assessment.

### Scope

- Supplier onboarding form.
- Required document checklist.
- Document upload and storage.
- Document metadata capture.
- OCR and extraction job lifecycle.
- Clarification request workflow.

### User Workflows

- Procurement Buyer initiates onboarding.
- Supplier Admin completes profile details.
- Supplier Admin uploads required documents.
- Risk Analyst views submitted data and extraction status.
- Risk Analyst requests missing or unclear information.

### Core Entities

| Entity | Purpose |
|---|---|
| Document | Uploaded file record |
| DocumentVersion | Replacements and updates |
| ExtractionJob | OCR/extraction processing state |
| ExtractedField | Normalized extracted data with confidence |
| ClarificationRequest | Request for supplier-provided correction or additional data |

### Acceptance Criteria

- Users can upload, replace, and view documents.
- Raw files are stored outside the database.
- Extraction results include confidence values.
- Missing or low-confidence fields can be sent back as clarification requests.
- All document and clarification actions are audited.

## Phase 3: MVP Enrichment, Entity Resolution, and Scoring

**Goal:** Produce explainable risk results for a supplier before onboarding.

### Scope

- Intake Agent for normalizing form and document data.
- Document Intelligence Agent for extraction summaries.
- Entity Resolution Agent for legal name, aliases, parent, subsidiary, director, and UBO hints.
- Sanctions and Compliance Agent for initial screening.
- Basic Financial Risk Agent.
- Basic News and Reputation Agent.
- Scoring Agent with deterministic score calculation.
- Recommendation Agent.

### Agent Output Contract

All material agent outputs should use a structured shape with:

- `supplier_id`
- `risk_category`
- `signal`
- `severity`
- `confidence`
- `source`
- `evidence_summary`
- `recommended_action`
- extracted facts separated from model interpretation

### Core Entities

| Entity | Purpose |
|---|---|
| RiskSignal | Normalized finding from documents or enrichment |
| EvidenceSource | Source metadata and retrieval details |
| EntityMatch | Candidate identity or relationship match |
| RiskScore | Category and composite score |
| ScoreComponent | Explainable contribution to final score |
| Recommendation | AI-assisted suggested action |

### Scoring Rules

Start with configurable but deterministic rules:

| Score | Risk Level | Action |
|---|---|---|
| 0-39 | Low | Recommend onboarding |
| 40-69 | Medium | Human review |
| 70-84 | High | Enhanced due diligence |
| 85-100 | Critical | Reject, block, or executive approval |

### Acceptance Criteria

- A supplier can move from submitted intake to calculated risk assessment.
- Scores are reproducible from stored risk signals and policy rules.
- Each material risk finding has source attribution.
- AI summaries link back to evidence records.
- The system never makes final approval or rejection without a human decision.

## Phase 4: Human Review, Decisions, Notifications, and MVP Dashboard

**Goal:** Make the MVP operational for risk teams.

### Scope

- Review queue.
- Supplier risk profile page.
- Evidence summary page.
- Category-wise risk score display.
- Composite risk score display.
- Decision workflow.
- Score override with reason.
- In-app and email notifications.
- Audit export basics.

### User Workflows

- Risk Analyst reviews AI findings and evidence across compliance, financial, ESG, cyber, operational, reputation, authenticity, and anomaly categories.
- Approver makes final approve, reject, defer, or request-information decision.
- Auditor reviews historical decisions and evidence trails.

### Acceptance Criteria

- Reviewers can filter suppliers by status, risk level, category, and owner.
- Decision makers can approve, reject, defer, or request more information.
- Score overrides require a reason and are audited.
- Notifications are sent for assigned reviews, clarification requests, and final decisions.
- Audit history can reconstruct who saw, changed, recommended, and decided what.

## Phase 5: MVP Hardening and Pilot

**Goal:** Prepare the MVP for realistic pilot usage.

### Scope

- Security review for authorization, file access, and audit integrity.
- Input validation and file scanning hooks.
- Rate limiting and background job retry policies.
- Error handling for failed OCR and enrichment.
- Data retention defaults.
- Seed data and demo scenarios.
- End-to-end tests for the critical onboarding workflow.

### Acceptance Criteria

- End-to-end happy path passes from onboarding request to final decision.
- Failure paths are visible and recoverable.
- Unauthorized users cannot access restricted supplier, document, score, or decision data.
- Pilot users can operate the MVP without engineering intervention.

## Phase 6: Continuous Monitoring

**Goal:** Expand from pre-onboarding assessment to dynamic supplier risk management.

### Scope

- Monitoring subscriptions for onboarded suppliers.
- Scheduled and event-driven enrichment refresh.
- Score recalculation.
- Score movement explanations.
- Configurable thresholds.
- Risk owner assignment.
- Risk trend timeline.
- Investigation case management.
- Teams, Slack, and webhook notifications.

### Core Entities

| Entity | Purpose |
|---|---|
| MonitoringSubscription | Defines what to watch for a supplier |
| RiskEvent | New external or internal risk event |
| ScoreMovement | Before/after score and explanation |
| Case | Investigation or remediation workflow |
| CaseComment | Investigation notes |
| CaseTask | Assigned remediation action |

### Acceptance Criteria

- Onboarded suppliers are monitored on a configured cadence.
- Material score changes generate explanations.
- Threshold breaches notify the assigned risk owner.
- Investigation cases can be opened, assigned, updated, and closed.

## Phase 7: Trust, Authenticity, and Anomaly Intelligence

**Goal:** Improve fraud and hidden-risk detection.

### Scope

- Authenticity Agent.
- Anomaly Agent.
- Document forgery detection hooks.
- Certificate authenticity verification.
- Metadata inconsistency detection.
- Cross-source verification.
- Signature, stamp, logo, and template anomaly checks.
- Supplier behavior anomaly detection.
- Peer group comparison.

### Acceptance Criteria

- Suspicious documents are flagged with evidence and confidence.
- Reused or inconsistent templates are visible to reviewers.
- Ownership, contact, document, payment, and shipment anomalies can become risk signals.
- Reviewers can accept, reject, or dismiss anomaly findings with reasons.

## Phase 8: Predictive Analytics

**Goal:** Identify future supplier risk before failure occurs.

### Scope

- Temporal risk trajectories.
- 3, 6, and 12 month risk forecasts.
- Supplier deterioration prediction.
- Similarity analysis against previously failed suppliers.
- Cohort analysis by geography, industry, tier, commodity, and business unit.
- What-if simulation.
- Preventive audit recommendations.
- Automated mitigation recommendations.

### Acceptance Criteria

- Users can view historical risk movement by supplier.
- Forecasts include confidence and explanatory drivers.
- Predictions are advisory and do not replace human decisions.
- Model outputs are tracked for later performance review.

## Phase 9: Enterprise Integrations and Scale

**Goal:** Operationalize the platform across procurement, compliance, and supplier management systems.

### Scope

- SAP Ariba integration.
- Coupa integration.
- Oracle Procurement integration.
- Microsoft Dynamics integration.
- GRC integration.
- ServiceNow/Jira case integration.
- Enterprise SSO and RBAC.
- Advanced audit exports.
- Policy-as-code scoring configuration.
- Multi-region deployment.
- Data retention and privacy controls.

### Acceptance Criteria

- External procurement systems can create or update supplier records.
- Decisions and risk statuses can be synced back to enterprise systems.
- Enterprise identity and access controls are enforced.
- Audit exports satisfy compliance review needs.

## MVP Backlog

### Foundation

- Initialize frontend app.
- Initialize backend API.
- Add SQLite database migrations.
- Add local development services.
- Add baseline CI.
- Add shared API contract generation or typed client.

### Identity and Access

- Implement user model.
- Implement email/password login.
- Implement roles and permissions.
- Implement supplier visibility rules for buyers and supplier users.
- Add route and API authorization guards.
- Add system administrator role management screens.
- Add audit middleware or service hooks.

### Supplier Management

- Create supplier profile schema.
- Create supplier list page.
- Create supplier detail page.
- Add supplier status model.
- Add archive and restore behavior.

### Intake

- Create onboarding request schema.
- Build buyer onboarding initiation flow.
- Build supplier intake form.
- Add validation for required business metadata.
- Track submission status.

### Documents

- Add document upload API.
- Add object storage integration.
- Add document checklist UI.
- Add extraction job model.
- Add OCR adapter interface.
- Store extraction results with confidence.

### Agents and Enrichment

- Add agent execution framework.
- Add structured output validation.
- Implement Intake Agent.
- Implement Document Intelligence Agent.
- Implement Entity Resolution Agent.
- Implement Sanctions and Compliance Agent.
- Implement initial Financial Risk Agent.
- Implement initial News and Reputation Agent.
- Persist risk signals and evidence sources.

### Scoring and Recommendation

- Define scoring policy configuration.
- Implement category score calculation.
- Implement composite score calculation.
- Store score history.
- Generate recommendation based on thresholds.
- Add score recalculation endpoint and worker job.

### Review and Decisioning

- Build review queue.
- Build risk assessment page.
- Build evidence viewer.
- Implement approve, reject, defer, and request-information actions.
- Implement score override with reason.
- Add final decision audit trail.

### Notifications

- Add in-app notification model.
- Add email notification adapter.
- Notify assigned reviewers.
- Notify suppliers for clarification requests.
- Notify buyers and approvers of final decisions.

### Testing

- Unit test scoring rules.
- Unit test RBAC permission checks.
- Unit test agent output validation.
- Integration test document upload.
- Integration test risk assessment generation.
- End-to-end test onboarding to decision workflow.

## Initial Data Model Draft

| Table | Key Fields |
|---|---|
| users | id, email, password_hash, name, status, created_at |
| roles | id, name, description |
| permissions | id, area, action |
| user_roles | user_id, role_id |
| role_permissions | role_id, permission_id |
| supplier_user_access | id, user_id, supplier_id, supplier_contact_id, access_role, status, invited_by, invited_at, accepted_at, revoked_at |
| buyer_supplier_access | id, user_id, supplier_id, access_level, status, assigned_by, assigned_at, revoked_at |
| suppliers | id, legal_name, country, tax_id, status, created_at, updated_at |
| supplier_contacts | id, supplier_id, name, email, phone, role |
| onboarding_requests | id, supplier_id, requester_id, status, submitted_at, decided_at |
| documents | id, supplier_id, onboarding_request_id, type, storage_key, status, uploaded_by, uploaded_at |
| document_versions | id, document_id, storage_key, version, uploaded_by, uploaded_at |
| extraction_jobs | id, document_id, status, provider, started_at, completed_at, error |
| extracted_fields | id, document_id, field_name, value, confidence, source_location |
| evidence_sources | id, source_type, name, url, retrieved_at, credibility_score |
| risk_signals | id, supplier_id, category, signal, severity, confidence, evidence_source_id |
| entity_matches | id, supplier_id, match_type, matched_name, confidence, evidence_source_id |
| risk_scores | id, supplier_id, onboarding_request_id, composite_score, risk_level, calculated_at |
| score_components | id, risk_score_id, category, score, explanation |
| recommendations | id, supplier_id, recommended_action, summary, created_at |
| decisions | id, supplier_id, onboarding_request_id, decision, reason, decided_by, decided_at |
| audit_events | id, actor_id, action, entity_type, entity_id, before_json, after_json, created_at |
| notifications | id, recipient_id, type, title, body, status, created_at |

## API Surface Draft

| Area | Endpoints |
|---|---|
| Auth and Users | `POST /auth/login`, `POST /auth/logout`, `GET /me`, `GET /roles`, `POST /users/{id}/roles` |
| Suppliers | `POST /suppliers`, `GET /suppliers`, `GET /suppliers/{id}`, `PATCH /suppliers/{id}` |
| Onboarding | `POST /onboarding-requests`, `GET /onboarding-requests`, `POST /onboarding-requests/{id}/submit` |
| Documents | `POST /suppliers/{id}/documents`, `GET /documents/{id}`, `POST /documents/{id}/replace` |
| Extraction | `POST /documents/{id}/extract`, `GET /documents/{id}/extractions` |
| Enrichment | `POST /suppliers/{id}/enrichment-runs`, `GET /suppliers/{id}/risk-signals` |
| Scoring | `POST /suppliers/{id}/scores/recalculate`, `GET /suppliers/{id}/scores/latest`, `GET /suppliers/{id}/scores/history` |
| Review | `GET /review-queue`, `POST /suppliers/{id}/recommendations`, `POST /scores/{id}/override` |
| Decisions | `POST /onboarding-requests/{id}/decisions`, `GET /suppliers/{id}/decisions` |
| Clarifications | `POST /onboarding-requests/{id}/clarifications`, `POST /clarifications/{id}/responses` |
| Audit | `GET /audit-events`, `GET /suppliers/{id}/audit-events` |
| Notifications | `GET /notifications`, `POST /notifications/{id}/read` |

## First Two Sprints

### Sprint 1: Skeleton and Supplier Foundation

- Create frontend and backend app scaffolds.
- Add SQLite schema migration setup.
- Add user, role, permission, supplier, and audit tables.
- Build supplier list and supplier detail screens.
- Add API authorization placeholders.
- Add audit logging for supplier create and update.

### Sprint 2: Onboarding and Documents

- Add onboarding request model and workflow statuses.
- Build buyer onboarding initiation flow.
- Build supplier intake form.
- Add document upload and object storage integration.
- Add document checklist UI.
- Add extraction job model and placeholder worker.
- Add audit events for onboarding and document actions.

## Key Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Agent output is inconsistent | Enforce JSON schema validation and reject malformed outputs |
| AI findings lack defensible evidence | Require source attribution for all material findings |
| Scoring becomes opaque | Keep final scoring deterministic and store score components |
| Workflow state becomes hard to reason about | Use explicit status transitions and audit every transition |
| Document processing fails silently | Track extraction job state, retries, and visible errors |
| RBAC is added too late | Build authorization and audit into Phase 1 |
| Too much infrastructure too early | Start with SQLite-backed relationships and add PostgreSQL, graph, vector, or search infrastructure when justified |

## Definition of Done for MVP

- Supplier onboarding can be completed end to end.
- Documents can be uploaded, stored, processed, and reviewed.
- Risk signals are generated from at least one compliance source and one basic enrichment source.
- Category and composite scores are calculated and explainable.
- AI-generated summaries include evidence references.
- Human users make final decisions.
- Approve, reject, defer, and request-information actions are supported.
- Role permissions protect sensitive actions.
- Audit trail captures material user, system, score, document, and decision actions.
- In-app and email notifications work for the core workflow.
- Critical path tests pass in CI.
