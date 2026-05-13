# Application Workflow

## Objective

The application evaluates supplier risk before onboarding and continuously monitors onboarded suppliers after approval. The core capability is the Risk Data Enrichment Module, supported by agentic AI and human-in-the-loop decisioning.

## Pre-Onboarding Workflow

```mermaid
flowchart TD
    A["Supplier onboarding request"] --> B["Supplier profile creation"]
    B --> C["Document and data collection"]
    C --> D["Risk data enrichment agents"]
    D --> E["Entity resolution and relationship mapping"]
    E --> F["Risk signal extraction"]
    F --> G["Risk scoring engine"]
    G --> H{"Risk threshold"}

    H -->|Low risk| I["Recommend onboarding"]
    H -->|Medium risk| J["Human review required"]
    H -->|High risk| K["Enhanced due diligence / reject recommendation"]

    I --> L["Final human approval"]
    J --> L
    K --> L

    L --> M{"Decision"}
    M -->|Approve| N["Supplier onboarded"]
    M -->|Reject| O["Supplier rejected or deferred"]
    M -->|Need more data| P["Supplier clarification request"]
    P --> C
```

## Post-Onboarding Dynamic Risk Workflow

```mermaid
flowchart TD
    A["Onboarded supplier"] --> B["Continuous risk monitoring"]
    B --> C["New risk event detected"]
    C --> D["Risk enrichment refresh"]
    D --> E["Risk score recalculation"]
    E --> F{"Material change?"}

    F -->|No| B
    F -->|Yes| G["Generate explanation"]
    G --> H["Notify risk owner"]
    H --> I["Open investigation case"]
    I --> J["Recommend mitigation actions"]
    J --> K["Human decision"]
    K --> L["Update supplier posture"]
    L --> B
```

## Key Decision Points

| Stage | AI Responsibility | Human Responsibility |
|---|---|---|
| Intake | Extract supplier information from forms and documents | Validate missing or unclear details |
| Enrichment | Gather signals from internal and external sources | Confirm source relevance for critical findings |
| Scoring | Calculate category and composite risk scores | Challenge or override with justification |
| Recommendation | Recommend approve, review, reject, or enhanced due diligence | Make final onboarding decision |
| Monitoring | Detect meaningful risk changes | Decide mitigation, suspension, or continuation |

## Risk Decision Thresholds

| Score | Risk Level | Recommended Action |
|---|---|---|
| 0-39 | Low | Recommend onboarding |
| 40-69 | Medium | Human review |
| 70-84 | High | Enhanced due diligence |
| 85-100 | Critical | Reject, block, or executive approval |

