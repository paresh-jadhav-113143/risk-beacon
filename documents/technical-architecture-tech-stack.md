# Technical Architecture and Tech Stack

## Target Architecture

```mermaid
flowchart LR
    A["External and internal sources"] --> B["Ingestion layer"]
    B --> C["Document AI and OCR"]
    B --> D["API and stream connectors"]

    C --> E["Risk enrichment agents"]
    D --> E

    E --> F["Entity resolution"]
    F --> G["Supplier knowledge graph"]

    E --> H["Risk signal store"]
    G --> I["Risk scoring engine"]
    H --> I

    I --> J["Decision workflow"]
    J --> K["Human review"]
    K --> L["Supplier decision"]

    I --> M["Dashboard"]
    I --> N["Notification engine"]

    O["Event stream"] --> P["Continuous monitoring"]
    P --> E
    P --> Q["Case management"]
```

## Recommended Tech Stack

| Layer | Recommended Options |
|---|---|
| Frontend | React / Next.js, TypeScript, Tailwind CSS, shadcn/ui |
| Charts and Visualization | Recharts, Apache ECharts, D3.js for graph-heavy views |
| Backend APIs | Python FastAPI or Node.js/NestJS |
| Agent Orchestration | OpenAI Agents SDK, LangGraph, Semantic Kernel |
| Workflow Engine | Temporal for durable onboarding, review, and escalation workflows |
| Event Streaming | Kafka, Redpanda, AWS MSK, Azure Event Hubs |
| Async Processing | Temporal workers, Celery, BullMQ |
| LLM Layer | OpenAI models with tool calling, structured outputs, and guardrails |
| OCR and Document AI | Azure Document Intelligence, AWS Textract, Google Document AI, Tesseract fallback |
| Transactional Database | SQLite for MVP; PostgreSQL later when concurrency, scale, or deployment needs require it |
| Vector Search | SQLite FTS or application-level search for MVP; pgvector, Pinecone, Weaviate, or OpenSearch vector search later |
| Graph Database | Neo4j or Amazon Neptune |
| Search | OpenSearch / Elasticsearch |
| Object Storage | S3, Azure Blob Storage, Google Cloud Storage |
| Rules and Policy Engine | JSONLogic, Drools, Open Policy Agent, custom scoring service |
| BI and Reporting | Superset, Metabase, Power BI integration |
| Observability | OpenTelemetry, Prometheus, Grafana, model tracing |
| Security | Email/password login for MVP, password hashing, RBAC, supplier-scoped visibility, encryption, secrets manager, audit logs; SSO/SAML/OIDC later |

## Core Services

| Service | Purpose |
|---|---|
| Supplier Service | Supplier master profile, status, ownership, business metadata |
| Document Service | Uploads, OCR status, extraction results, authenticity checks |
| Enrichment Service | External source ingestion and normalized risk signals |
| Entity Resolution Service | Identity matching, aliases, UBOs, relationship mapping |
| Scoring Service | Risk score computation, thresholds, score history |
| Workflow Service | Human review, approvals, escalations, reassessments |
| Monitoring Service | Continuous monitoring jobs and event subscriptions |
| Notification Service | In-app, email, Teams/Slack, webhook, SMS alerts |
| Case Management Service | Investigation, remediation, SLA, closure |
| Audit Service | Immutable decision and evidence trail |

## Data Stores

| Store | Data |
|---|---|
| SQLite | MVP transactional store for supplier profiles, users, cases, decisions, scores, audit events, evidence metadata, and agent outputs |
| Object Storage | Raw documents, extracted files, evidence snapshots |
| Vector Database | Embeddings for document search and semantic retrieval |
| Graph Database | Supplier relationships, UBO links, parent/subsidiary mapping |
| Search Index | News, documents, evidence, investigation notes |
| Event Store | Risk events, score changes, alert history |

## MVP SQLite Guidance

Use SQLite for the first MVP to minimize local setup and infrastructure dependency.

SQLite should be configured with:

```sql
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=5000;
PRAGMA foreign_keys=ON;
```

Recommended MVP rules:

- Store the database as a local file, for example `./data/risk_beacon.db`.
- Use SQLModel or SQLAlchemy so the domain model can migrate to PostgreSQL later.
- Keep write transactions short.
- Allow agents to run extraction and enrichment work in parallel, but persist validated outputs through a controlled repository or persistence service.
- Retry briefly on `database is locked` errors.
- Do not use SQLite as a shared database file across multiple app servers.

Migration to PostgreSQL should be considered when the product needs multiple app servers, high write concurrency, heavy dashboard workloads, or enterprise-scale audit/event volume.
