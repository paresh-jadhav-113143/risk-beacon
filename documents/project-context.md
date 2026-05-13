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
| [agentic-ai-architecture.md](agentic-ai-architecture.md) | Defines the specialized agent catalog, agent workflow, output contract, and AI guardrails. |
| [implementation-plan.md](implementation-plan.md) | Converts the strategy documents into phased delivery work, MVP backlog, data model draft, API surface, and first two sprints. |

## Recommended Reading Order

1. Start with [project-context.md](project-context.md) for the high-level map.
2. Read [feature-roadmap.md](feature-roadmap.md) to understand product scope and phase boundaries.
3. Read [application-workflow.md](application-workflow.md) to understand the user and decision workflows.
4. Read [roles-and-permissions.md](roles-and-permissions.md) to understand responsibility and access boundaries.
5. Read [agentic-ai-architecture.md](agentic-ai-architecture.md) to understand AI responsibilities and output constraints.
6. Read [technical-architecture-tech-stack.md](technical-architecture-tech-stack.md) to understand platform architecture options.
7. Use [implementation-plan.md](implementation-plan.md) as the active build plan.

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
- PostgreSQL for transactional data.
- S3-compatible object storage for documents.
- Structured background workers for OCR, enrichment, scoring, and notifications.
- Specialized AI agent modules with schema-validated outputs.
- Deterministic scoring rules for final score calculation.
- RBAC and audit logging from the foundation phase.

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
- Add database migration setup.
- Create user, role, permission, supplier, and audit foundations.
- Build the first supplier list and supplier detail screens.

