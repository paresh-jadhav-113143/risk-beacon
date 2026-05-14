# Project Context

## Project

Semicolon is a supplier risk intelligence platform for pre-onboarding assessment, human-in-the-loop decisioning, and continuous post-onboarding monitoring.

The core product evaluates supplier risk by combining supplier-submitted data, document intelligence, external enrichment, entity resolution, category-wise scoring, AI-assisted evidence summaries, and final human approval workflows.

## Documents in This Project

| Document | Purpose |
|---|---|
| [technical-architecture-tech-stack.md](technical-architecture-tech-stack.md) | Defines the target architecture, recommended technology options, core services, and data stores. |
| [roles-and-permissions.md](roles-and-permissions.md) | Defines role-based access control, permission areas, and human-in-the-loop governance. |
| [feature-roadmap.md](feature-roadmap.md) | Defines the MVP and later product phases from continuous monitoring through enterprise integrations. |
| [application-workflow.md](application-workflow.md) | Defines pre-onboarding and post-onboarding workflows, decision points, and risk thresholds. |
| [supplier-onboarding-sequence-flows.md](supplier-onboarding-sequence-flows.md) | Defines actor-by-actor onboarding event sequences, next actionable owners, and alternate onboarding scenarios. |
| [agentic-ai-architecture.md](agentic-ai-architecture.md) | Defines the specialized agent catalog, agent workflow, output contract, and AI guardrails. |
| [agents-workflow.md](agents-workflow.md) | Defines production-ready low-level agent instructions, JSON input and output contracts, tools, persistence, and operational guardrails. |
| [project-structure-and-database-design.md](project-structure-and-database-design.md) | Defines the production-ready backend project structure, agent module layout, SQLite table design, indexes, and persistence rules. |
| [implementation-plan.md](implementation-plan.md) | Converts the strategy documents into phased delivery work, MVP backlog, data model draft, API surface, and first two sprints. |

## Recommended Reading Order

1. Start with [project-context.md](project-context.md) for the high-level map.
2. Read [feature-roadmap.md](feature-roadmap.md) to understand product scope and phase boundaries.
3. Read [application-workflow.md](application-workflow.md) to understand the user and decision workflows.
4. Read [supplier-onboarding-sequence-flows.md](supplier-onboarding-sequence-flows.md) to understand actor-by-actor handoffs and scenarios.
5. Read [roles-and-permissions.md](roles-and-permissions.md) to understand responsibility and access boundaries.
6. Read [agentic-ai-architecture.md](agentic-ai-architecture.md) to understand AI responsibilities and output constraints.
7. Read [agents-workflow.md](agents-workflow.md) to understand production-ready low-level agent execution design.
8. Read [project-structure-and-database-design.md](project-structure-and-database-design.md) to understand implementation structure and SQLite persistence design.
9. Read [technical-architecture-tech-stack.md](technical-architecture-tech-stack.md) to understand platform architecture options.
10. Use [implementation-plan.md](implementation-plan.md) as the active build plan.

## Active Implementation Direction

The first build target is the MVP for pre-onboarding supplier risk assessment:

- Supplier onboarding request.
- Supplier profile management.
- Document upload and extraction.
- Basic enrichment and sanctions/compliance screening.
- Entity resolution.
- Category-wise and composite risk scoring.
- AI-generated evidence summary with source attribution.
- Human review and final decisioning.
- Audit trail.
- In-app and email notifications.

## Initial Technical Direction

Use the implementation plan defaults unless project constraints change:

- Next.js, TypeScript, Tailwind CSS, and shadcn/ui for the frontend.
- Python FastAPI for backend APIs.
- SQLite for MVP transactional data, with a migration path to PostgreSQL when scale or concurrency requires it.
- Simple email and password login for MVP, with hashed passwords and RBAC-backed supplier visibility.
- S3-compatible object storage for documents.
- Structured background workers for OCR, enrichment, scoring, and notifications.
- Specialized AI agent modules with schema-validated outputs.
- Deterministic scoring rules for final score calculation.
- RBAC and audit logging from the foundation phase.
- Buyers can only see suppliers linked to them through onboarding ownership, buyer-supplier assignment, or explicit supplier access mapping.

## Guardrails

- AI can assist with extraction, enrichment, scoring, summarization, and recommendations.
- AI must not make final approve, reject, suspend, or critical risk acceptance decisions.
- Material risk findings must include source attribution.
- Extracted facts must be separated from model interpretation.
- Risk scores must be explainable and reproducible.
- Human overrides must require a reason and be logged.
- Audit events must capture material user, system, document, score, and decision actions.

## Current Next Step

Begin Phase 0 and Sprint 1 from [implementation-plan.md](implementation-plan.md):

- Scaffold the frontend and backend.
- Add local development services.
- Add SQLite database and migration setup.
- Create user, role, permission, supplier, and audit foundations.
- Build the first supplier list and supplier detail screens.
