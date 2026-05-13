# Risk Dashboard and Notifications

## Dashboard Principles

The dashboard should help users quickly answer:

- Which suppliers are risky right now?
- Why did the risk score change?
- What decision or action is pending?
- Which risks need human attention?
- Which suppliers may deteriorate in the future?

## Dashboard Screens

### 1. Executive Risk Overview

- Total suppliers
- High-risk suppliers
- Suppliers under review
- Critical open alerts
- Pending onboarding approvals
- Risk trend by month
- Risk distribution by category
- Top risk movements

### 2. Supplier 360 Profile

- Supplier identity and legal profile
- Parent, subsidiary, branch, director, and UBO relationships
- Composite risk score
- Category-wise risk scores
- Risk evidence summary
- Source credibility and confidence scores
- Submitted documents and authenticity status
- Sanctions/watchlist results
- News, legal, regulatory, ESG, and logistics timeline
- Open cases and mitigation actions

### 3. Pre-Onboarding Review

- AI recommendation
- Composite score and category score breakdown
- Evidence list with source references
- Missing or expired documents
- Authenticity warnings
- Clarification requests
- Approve, reject, defer, or enhanced due diligence actions
- Decision comments and audit trail

### 4. Dynamic Risk Monitoring

- Current score versus previous score
- Explanation of score movement
- Material events detected
- Severity and priority
- Assigned risk owner
- Recommended mitigation
- Open investigation status

### 5. Risk Heatmap

- Risk by geography
- Risk by commodity/category
- Risk by supplier tier
- Risk by business unit
- Risk by ESG, compliance, operational, financial, cyber, and reputation category

### 6. Predictive Analytics

- Suppliers likely to become high risk
- 3, 6, and 12 month risk trend
- Peer group comparison
- Suppliers matching previous failure patterns
- Region and category clusters with rising risk
- What-if simulations

## Notification Triggers

| Trigger | Severity Example | Action |
|---|---|---|
| Supplier appears on sanctions/watchlist | Critical | Alert compliance and block onboarding |
| Negative news spike | Medium/High | Notify risk owner and refresh score |
| Litigation or regulatory notice | High | Open investigation case |
| Certificate expired | Medium | Request updated document |
| Financial distress signal | High | Notify finance analyst |
| Ownership/director/address change | Medium/High | Trigger entity verification |
| Shipment activity drops suddenly | Medium | Notify supplier relationship manager |
| ESG controversy detected | Medium/High | Route to ESG analyst |
| Document authenticity issue | High/Critical | Pause onboarding and open case |
| Risk score crosses threshold | High/Critical | Escalate to approver |

## Notification Channels

- In-app notifications
- Email
- Slack or Microsoft Teams
- SMS for critical events
- Webhooks to procurement, ERP, or GRC systems
- Case/task creation in ServiceNow, Jira, or internal workflow tools

## Alert Routing

| Risk Type | Primary Owner |
|---|---|
| Sanctions / Watchlist | Compliance Officer |
| Financial Risk | Finance Analyst |
| ESG Risk | ESG Analyst |
| Cyber Risk | Cyber Risk Analyst |
| Operational Risk | Supplier Relationship Manager |
| Reputational Risk | Risk Analyst |
| Critical Composite Risk | Risk Committee / Approver |

