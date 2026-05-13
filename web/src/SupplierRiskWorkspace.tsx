import {
  AlertTriangle,
  Archive,
  Bell,
  Building2,
  Check,
  ChevronRight,
  CircleAlert,
  ClipboardCheck,
  Clock3,
  FileCheck2,
  FileSearch,
  Gauge,
  History,
  Inbox,
  LayoutDashboard,
  Mail,
  MessageSquareText,
  MoreHorizontal,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  UserCheck,
  UsersRound,
  X
} from "lucide-react";
import type { ComponentType, CSSProperties } from "react";
import { useMemo, useState } from "react";

type RiskLevel = "Low" | "Medium" | "High" | "Critical";
type ViewKey = "overview" | "intake" | "documents" | "risk" | "review" | "audit";

type Supplier = {
  id: string;
  name: string;
  country: string;
  category: string;
  tier: string;
  owner: string;
  buyer: string;
  status: string;
  stage: string;
  risk: RiskLevel;
  score: number;
  delta: number;
  submitted: string;
  due: string;
  documents: {
    complete: number;
    total: number;
    items: DocumentItem[];
  };
  categories: RiskCategory[];
  signals: RiskSignal[];
  audit: AuditEvent[];
  notifications: NotificationItem[];
};

type RiskCategory = {
  name: string;
  score: number;
  level: RiskLevel;
  reviewer: string;
};

type RiskSignal = {
  category: string;
  severity: RiskLevel;
  confidence: number;
  source: string;
  summary: string;
  action: string;
};

type DocumentItem = {
  name: string;
  type: string;
  status: "Verified" | "Extracting" | "Needs replacement" | "Missing";
  confidence: number;
  updated: string;
};

type AuditEvent = {
  actor: string;
  action: string;
  time: string;
  entity: string;
};

type NotificationItem = {
  title: string;
  channel: "In-app" | "Email";
  status: "Queued" | "Sent" | "Read";
  time: string;
};

const views: Array<{ key: ViewKey; label: string; icon: ComponentType<{ size?: number }> }> = [
  { key: "overview", label: "Overview", icon: LayoutDashboard },
  { key: "intake", label: "Intake", icon: Inbox },
  { key: "documents", label: "Documents", icon: FileSearch },
  { key: "risk", label: "Risk", icon: Gauge },
  { key: "review", label: "Review", icon: ClipboardCheck },
  { key: "audit", label: "Audit", icon: History }
];

const suppliers: Supplier[] = [
  {
    id: "SUP-001",
    name: "Aster Components Pvt Ltd",
    country: "India",
    category: "Electronic assemblies",
    tier: "Tier 1",
    owner: "Mira Shah",
    buyer: "Procurement Buyer",
    status: "Review required",
    stage: "Compliance review",
    risk: "High",
    score: 76,
    delta: 12,
    submitted: "13 May 2026",
    due: "16 May 2026",
    documents: {
      complete: 5,
      total: 7,
      items: [
        { name: "Business registration", type: "Legal", status: "Verified", confidence: 94, updated: "Today" },
        { name: "Tax certificate", type: "Financial", status: "Verified", confidence: 91, updated: "Today" },
        { name: "Bank letter", type: "Financial", status: "Extracting", confidence: 68, updated: "8 min ago" },
        { name: "ISO 27001 certificate", type: "Cyber", status: "Needs replacement", confidence: 41, updated: "Yesterday" },
        { name: "ESG declaration", type: "ESG", status: "Missing", confidence: 0, updated: "Pending" }
      ]
    },
    categories: [
      { name: "Compliance", score: 82, level: "High", reviewer: "Compliance Officer" },
      { name: "Financial", score: 58, level: "Medium", reviewer: "Finance Analyst" },
      { name: "ESG", score: 36, level: "Low", reviewer: "ESG Analyst" },
      { name: "Cyber", score: 71, level: "High", reviewer: "Cyber Risk Analyst" }
    ],
    signals: [
      {
        category: "Compliance",
        severity: "High",
        confidence: 91,
        source: "Regulatory notice database",
        summary: "A supplier alias appears in an adverse regulatory notice from the past 18 months.",
        action: "Route to compliance officer for enhanced due diligence."
      },
      {
        category: "Cyber",
        severity: "High",
        confidence: 78,
        source: "Certificate metadata extraction",
        summary: "Security certificate metadata does not match the declared issuing date.",
        action: "Request replacement certificate and reviewer validation."
      },
      {
        category: "Financial",
        severity: "Medium",
        confidence: 73,
        source: "Financial filing extract",
        summary: "Working capital ratio declined compared with the previous filing period.",
        action: "Assign finance analyst review before approval."
      }
    ],
    audit: [
      { actor: "System", action: "Calculated composite score 76", time: "10:42 AM", entity: "Risk score" },
      { actor: "Document Intelligence Agent", action: "Flagged ISO certificate metadata mismatch", time: "10:36 AM", entity: "Document" },
      { actor: "Mira Shah", action: "Assigned compliance review", time: "10:28 AM", entity: "Workflow" },
      { actor: "Supplier Admin", action: "Submitted onboarding package", time: "10:11 AM", entity: "Onboarding" }
    ],
    notifications: [
      { title: "Compliance review assigned", channel: "In-app", status: "Read", time: "10:29 AM" },
      { title: "Certificate replacement requested", channel: "Email", status: "Queued", time: "10:37 AM" },
      { title: "High-risk score threshold crossed", channel: "In-app", status: "Sent", time: "10:42 AM" }
    ]
  },
  {
    id: "SUP-002",
    name: "Northstar Packaging LLC",
    country: "United States",
    category: "Sustainable packaging",
    tier: "Tier 2",
    owner: "Daniel Reed",
    buyer: "Procurement Buyer",
    status: "Ready for approval",
    stage: "Approver queue",
    risk: "Medium",
    score: 47,
    delta: -4,
    submitted: "12 May 2026",
    due: "15 May 2026",
    documents: {
      complete: 6,
      total: 6,
      items: [
        { name: "Business registration", type: "Legal", status: "Verified", confidence: 97, updated: "Yesterday" },
        { name: "Tax certificate", type: "Financial", status: "Verified", confidence: 93, updated: "Yesterday" },
        { name: "Bank letter", type: "Financial", status: "Verified", confidence: 89, updated: "Yesterday" },
        { name: "ESG declaration", type: "ESG", status: "Verified", confidence: 86, updated: "Yesterday" }
      ]
    },
    categories: [
      { name: "Compliance", score: 21, level: "Low", reviewer: "Compliance Officer" },
      { name: "Financial", score: 49, level: "Medium", reviewer: "Finance Analyst" },
      { name: "ESG", score: 54, level: "Medium", reviewer: "ESG Analyst" },
      { name: "Cyber", score: 34, level: "Low", reviewer: "Cyber Risk Analyst" }
    ],
    signals: [
      {
        category: "ESG",
        severity: "Medium",
        confidence: 76,
        source: "News and reputation scan",
        summary: "Recent labor complaint mentions a facility in the supplier network.",
        action: "Ask ESG analyst to validate relevance before final approval."
      }
    ],
    audit: [
      { actor: "Finance Analyst", action: "Confirmed financial signal is non-blocking", time: "09:58 AM", entity: "Risk signal" },
      { actor: "System", action: "Generated approval recommendation", time: "09:41 AM", entity: "Recommendation" },
      { actor: "Supplier Admin", action: "Completed required documents", time: "09:22 AM", entity: "Document" }
    ],
    notifications: [
      { title: "Approval packet ready", channel: "In-app", status: "Sent", time: "09:42 AM" },
      { title: "Buyer notified of review completion", channel: "Email", status: "Sent", time: "09:43 AM" }
    ]
  },
  {
    id: "SUP-003",
    name: "Marula Logistics SA",
    country: "South Africa",
    category: "Regional freight",
    tier: "Tier 1",
    owner: "Priya Menon",
    buyer: "Procurement Buyer",
    status: "Enhanced due diligence",
    stage: "Risk committee",
    risk: "Critical",
    score: 88,
    delta: 18,
    submitted: "11 May 2026",
    due: "14 May 2026",
    documents: {
      complete: 4,
      total: 8,
      items: [
        { name: "Business registration", type: "Legal", status: "Verified", confidence: 92, updated: "11 May" },
        { name: "Ownership declaration", type: "Legal", status: "Needs replacement", confidence: 39, updated: "Today" },
        { name: "Trade license", type: "Compliance", status: "Extracting", confidence: 62, updated: "12 min ago" },
        { name: "Insurance certificate", type: "Logistics", status: "Missing", confidence: 0, updated: "Pending" }
      ]
    },
    categories: [
      { name: "Compliance", score: 91, level: "Critical", reviewer: "Compliance Officer" },
      { name: "Financial", score: 67, level: "Medium", reviewer: "Finance Analyst" },
      { name: "ESG", score: 61, level: "Medium", reviewer: "ESG Analyst" },
      { name: "Cyber", score: 42, level: "Medium", reviewer: "Cyber Risk Analyst" }
    ],
    signals: [
      {
        category: "Compliance",
        severity: "Critical",
        confidence: 93,
        source: "Watchlist screening",
        summary: "Potential UBO match to a restricted-party watchlist requires human validation.",
        action: "Block approval until compliance officer completes enhanced due diligence."
      },
      {
        category: "Entity resolution",
        severity: "High",
        confidence: 84,
        source: "Ownership declaration extraction",
        summary: "Declared ownership differs from registry-linked parent entity.",
        action: "Request updated ownership documentation."
      }
    ],
    audit: [
      { actor: "Entity Resolution Agent", action: "Found UBO match candidate", time: "10:18 AM", entity: "Entity match" },
      { actor: "System", action: "Escalated to risk committee", time: "10:19 AM", entity: "Workflow" },
      { actor: "Compliance Officer", action: "Opened enhanced due diligence review", time: "10:21 AM", entity: "Decision" }
    ],
    notifications: [
      { title: "Critical risk threshold crossed", channel: "In-app", status: "Sent", time: "10:19 AM" },
      { title: "Risk committee review required", channel: "Email", status: "Sent", time: "10:20 AM" }
    ]
  },
  {
    id: "SUP-004",
    name: "Evergreen Textiles GmbH",
    country: "Germany",
    category: "Technical fabric",
    tier: "Tier 2",
    owner: "Lena Ortiz",
    buyer: "Procurement Buyer",
    status: "Supplier clarification",
    stage: "Waiting on supplier",
    risk: "Medium",
    score: 63,
    delta: 7,
    submitted: "10 May 2026",
    due: "17 May 2026",
    documents: {
      complete: 3,
      total: 7,
      items: [
        { name: "Business registration", type: "Legal", status: "Verified", confidence: 95, updated: "10 May" },
        { name: "Labor policy", type: "ESG", status: "Needs replacement", confidence: 45, updated: "Today" },
        { name: "Environmental certificate", type: "ESG", status: "Missing", confidence: 0, updated: "Pending" }
      ]
    },
    categories: [
      { name: "Compliance", score: 28, level: "Low", reviewer: "Compliance Officer" },
      { name: "Financial", score: 44, level: "Medium", reviewer: "Finance Analyst" },
      { name: "ESG", score: 69, level: "Medium", reviewer: "ESG Analyst" },
      { name: "Cyber", score: 31, level: "Low", reviewer: "Cyber Risk Analyst" }
    ],
    signals: [
      {
        category: "ESG",
        severity: "Medium",
        confidence: 72,
        source: "Document extraction",
        summary: "Labor policy text is incomplete and omits supplier subcontractor commitments.",
        action: "Request policy replacement from supplier admin."
      }
    ],
    audit: [
      { actor: "ESG Analyst", action: "Requested replacement labor policy", time: "08:57 AM", entity: "Clarification" },
      { actor: "System", action: "Paused final approval until response", time: "08:58 AM", entity: "Workflow" }
    ],
    notifications: [
      { title: "Supplier clarification sent", channel: "Email", status: "Sent", time: "08:59 AM" },
      { title: "Waiting on replacement document", channel: "In-app", status: "Read", time: "09:00 AM" }
    ]
  }
];

const riskFilters: Array<RiskLevel | "All"> = ["All", "Low", "Medium", "High", "Critical"];

export function SupplierRiskWorkspace() {
  const [activeView, setActiveView] = useState<ViewKey>("overview");
  const [selectedSupplierId, setSelectedSupplierId] = useState(suppliers[0].id);
  const [query, setQuery] = useState("");
  const [riskFilter, setRiskFilter] = useState<RiskLevel | "All">("All");

  const filteredSuppliers = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return suppliers.filter((supplier) => {
      const matchesQuery =
        !normalizedQuery ||
        supplier.name.toLowerCase().includes(normalizedQuery) ||
        supplier.id.toLowerCase().includes(normalizedQuery) ||
        supplier.country.toLowerCase().includes(normalizedQuery);
      const matchesRisk = riskFilter === "All" || supplier.risk === riskFilter;

      return matchesQuery && matchesRisk;
    });
  }, [query, riskFilter]);

  const selectedSupplier =
    suppliers.find((supplier) => supplier.id === selectedSupplierId) ?? suppliers[0];

  const highPriorityCount = suppliers.filter(
    (supplier) => supplier.risk === "High" || supplier.risk === "Critical"
  ).length;
  const pendingDocuments = suppliers.reduce(
    (sum, supplier) => sum + (supplier.documents.total - supplier.documents.complete),
    0
  );

  return (
    <main className="app-shell">
      <aside className="sidebar" aria-label="Primary navigation">
        <div className="brand-lockup">
          <div className="brand-mark">S;</div>
          <div>
            <p className="eyebrow">Semicolon</p>
            <h1>Supplier Risk</h1>
          </div>
        </div>

        <nav className="nav-list">
          {views.map((view) => {
            const Icon = view.icon;
            return (
              <button
                className={`nav-item ${activeView === view.key ? "active" : ""}`}
                key={view.key}
                onClick={() => setActiveView(view.key)}
                type="button"
              >
                <Icon size={18} />
                <span>{view.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="sidebar-panel">
          <p className="panel-label">MVP scope</p>
          <div className="scope-row">
            <ShieldCheck size={17} />
            <span>Human final decisions</span>
          </div>
          <div className="scope-row">
            <FileCheck2 size={17} />
            <span>Evidence-backed AI</span>
          </div>
          <div className="scope-row">
            <History size={17} />
            <span>Complete audit trail</span>
          </div>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Pre-onboarding command center</p>
            <h2>{viewLabel(activeView)}</h2>
          </div>
          <div className="topbar-actions">
            <button className="icon-button" aria-label="Notifications" type="button">
              <Bell size={18} />
            </button>
            <button className="primary-action" type="button">
              <Building2 size={18} />
              <span>New supplier</span>
            </button>
          </div>
        </header>

        <section className="metric-strip" aria-label="Supplier risk summary">
          <Metric title="Suppliers in review" value="18" detail="6 due this week" icon={UsersRound} />
          <Metric title="High priority" value={String(highPriorityCount)} detail="Needs human review" icon={CircleAlert} tone="hot" />
          <Metric title="Pending documents" value={String(pendingDocuments)} detail="Across active requests" icon={FileSearch} tone="amber" />
          <Metric title="SLA health" value="92%" detail="On-time review rate" icon={Clock3} tone="green" />
        </section>

        <section className="main-grid">
          <section className="supplier-panel" aria-label="Supplier list">
            <div className="panel-header">
              <div>
                <p className="panel-label">Review queue</p>
                <h3>Active suppliers</h3>
              </div>
              <button className="icon-button small" aria-label="Filter queue" type="button">
                <SlidersHorizontal size={16} />
              </button>
            </div>

            <label className="search-field">
              <Search size={17} />
              <input
                aria-label="Search suppliers"
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search supplier, ID, country"
                value={query}
              />
            </label>

            <div className="segmented" aria-label="Risk filter">
              {riskFilters.map((filter) => (
                <button
                  className={riskFilter === filter ? "active" : ""}
                  key={filter}
                  onClick={() => setRiskFilter(filter)}
                  type="button"
                >
                  {filter}
                </button>
              ))}
            </div>

            <div className="supplier-list">
              {filteredSuppliers.map((supplier) => (
                <button
                  className={`supplier-row ${selectedSupplier.id === supplier.id ? "selected" : ""}`}
                  key={supplier.id}
                  onClick={() => setSelectedSupplierId(supplier.id)}
                  type="button"
                >
                  <div className="supplier-row-top">
                    <span className="supplier-name">{supplier.name}</span>
                    <RiskPill level={supplier.risk} />
                  </div>
                  <div className="supplier-meta">
                    <span>{supplier.id}</span>
                    <span>{supplier.country}</span>
                    <span>{supplier.tier}</span>
                  </div>
                  <div className="queue-progress">
                    <div>
                      <span className="queue-stage">{supplier.stage}</span>
                      <span className="queue-owner">{supplier.owner}</span>
                    </div>
                    <ChevronRight size={17} />
                  </div>
                </button>
              ))}
            </div>
          </section>

          <section className="detail-panel" aria-label="Supplier detail">
            <SupplierHeader supplier={selectedSupplier} />
            {activeView === "overview" && <OverviewScreen supplier={selectedSupplier} />}
            {activeView === "intake" && <IntakeScreen supplier={selectedSupplier} />}
            {activeView === "documents" && <DocumentsScreen supplier={selectedSupplier} />}
            {activeView === "risk" && <RiskScreen supplier={selectedSupplier} />}
            {activeView === "review" && <ReviewScreen supplier={selectedSupplier} />}
            {activeView === "audit" && <AuditScreen supplier={selectedSupplier} />}
          </section>
        </section>
      </section>
    </main>
  );
}

function Metric({
  title,
  value,
  detail,
  icon: Icon,
  tone = "blue"
}: {
  title: string;
  value: string;
  detail: string;
  icon: ComponentType<{ size?: number }>;
  tone?: "blue" | "hot" | "amber" | "green";
}) {
  return (
    <div className={`metric metric-${tone}`}>
      <div>
        <p>{title}</p>
        <strong>{value}</strong>
        <span>{detail}</span>
      </div>
      <Icon size={20} />
    </div>
  );
}

function SupplierHeader({ supplier }: { supplier: Supplier }) {
  return (
    <header className="supplier-header">
      <div>
        <div className="supplier-title-line">
          <span className="id-chip">{supplier.id}</span>
          <RiskPill level={supplier.risk} />
        </div>
        <h3>{supplier.name}</h3>
        <p>
          {supplier.category} - {supplier.country} - {supplier.status}
        </p>
      </div>
      <div className="header-actions">
        <button className="secondary-action" type="button">
          <Mail size={17} />
          <span>Request info</span>
        </button>
        <button className="icon-button" aria-label="More actions" type="button">
          <MoreHorizontal size={18} />
        </button>
      </div>
    </header>
  );
}

function OverviewScreen({ supplier }: { supplier: Supplier }) {
  return (
    <div className="screen-grid">
      <section className="score-surface">
        <div className="section-heading">
          <div>
            <p className="panel-label">Composite score</p>
            <h4>{supplier.risk} risk</h4>
          </div>
          <span className={`delta ${supplier.delta >= 0 ? "up" : "down"}`}>
            {supplier.delta >= 0 ? "+" : ""}
            {supplier.delta}
          </span>
        </div>
        <div className="score-layout">
          <div
            className={`score-ring risk-${supplier.risk.toLowerCase()}`}
            style={{ "--score": supplier.score } as CSSProperties}
            aria-label={`Composite risk score ${supplier.score}`}
          >
            <strong>{supplier.score}</strong>
            <span>of 100</span>
          </div>
          <div className="decision-band">
            <div>
              <p>Recommended action</p>
              <strong>{recommendationFor(supplier.risk)}</strong>
            </div>
            <button className="primary-action" type="button">
              <UserCheck size={17} />
              <span>Open review</span>
            </button>
          </div>
        </div>
      </section>

      <section className="category-surface">
        <div className="section-heading">
          <div>
            <p className="panel-label">Category scoring</p>
            <h4>Reviewer split</h4>
          </div>
          <Sparkles size={18} />
        </div>
        <div className="category-list">
          {supplier.categories.map((category) => (
            <CategoryBar category={category} key={category.name} />
          ))}
        </div>
      </section>

      <section className="wide-surface">
        <div className="section-heading">
          <div>
            <p className="panel-label">Entity resolution</p>
            <h4>Relationship map</h4>
          </div>
          <span className="confidence-chip">84% confidence</span>
        </div>
        <div className="entity-map" aria-label="Supplier relationship map">
          <div className="entity-node primary">{supplier.name}</div>
          <div className="entity-line" />
          <div className="entity-node">Parent entity</div>
          <div className="entity-line muted" />
          <div className="entity-node warning">UBO candidate</div>
          <div className="entity-line" />
          <div className="entity-node">Registered branch</div>
        </div>
      </section>
    </div>
  );
}

function IntakeScreen({ supplier }: { supplier: Supplier }) {
  const profileRows = [
    ["Legal name", supplier.name],
    ["Country", supplier.country],
    ["Category", supplier.category],
    ["Tier", supplier.tier],
    ["Buyer", supplier.buyer],
    ["Risk owner", supplier.owner],
    ["Submitted", supplier.submitted],
    ["Review due", supplier.due]
  ];

  return (
    <div className="screen-grid">
      <section className="wide-surface">
        <div className="section-heading">
          <div>
            <p className="panel-label">Supplier profile</p>
            <h4>Intake record</h4>
          </div>
          <button className="secondary-action compact" type="button">
            <Check size={16} />
            <span>Validate</span>
          </button>
        </div>
        <div className="profile-grid">
          {profileRows.map(([label, value]) => (
            <div className="profile-field" key={label}>
              <span>{label}</span>
              <strong>{value}</strong>
            </div>
          ))}
        </div>
      </section>

      <section className="category-surface">
        <div className="section-heading">
          <div>
            <p className="panel-label">Workflow</p>
            <h4>Status path</h4>
          </div>
        </div>
        <div className="status-path">
          {["Created", "Submitted", "Extracted", "Scored", "Review", "Decision"].map((step, index) => (
            <div className={`path-step ${index < 4 ? "done" : index === 4 ? "current" : ""}`} key={step}>
              <span>{index + 1}</span>
              <p>{step}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="score-surface">
        <div className="section-heading">
          <div>
            <p className="panel-label">Clarifications</p>
            <h4>Open requests</h4>
          </div>
          <MessageSquareText size={18} />
        </div>
        <div className="clarification-box">
          <strong>{supplier.documents.total - supplier.documents.complete} pending items</strong>
          <p>Missing or low-confidence documents are waiting for supplier response.</p>
          <button className="primary-action" type="button">
            <Mail size={17} />
            <span>Send request</span>
          </button>
        </div>
      </section>
    </div>
  );
}

function DocumentsScreen({ supplier }: { supplier: Supplier }) {
  return (
    <div className="screen-grid">
      <section className="wide-surface">
        <div className="section-heading">
          <div>
            <p className="panel-label">Document checklist</p>
            <h4>
              {supplier.documents.complete} of {supplier.documents.total} complete
            </h4>
          </div>
          <button className="primary-action" type="button">
            <FileCheck2 size={17} />
            <span>Upload</span>
          </button>
        </div>
        <div className="document-table">
          <div className="table-head">
            <span>Document</span>
            <span>Type</span>
            <span>Status</span>
            <span>Confidence</span>
            <span>Updated</span>
          </div>
          {supplier.documents.items.map((document) => (
            <div className="table-row" key={document.name}>
              <span>{document.name}</span>
              <span>{document.type}</span>
              <StatusBadge status={document.status} />
              <span>{document.confidence ? `${document.confidence}%` : "-"}</span>
              <span>{document.updated}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="score-surface">
        <div className="section-heading">
          <div>
            <p className="panel-label">Extraction queue</p>
            <h4>Worker state</h4>
          </div>
          <Clock3 size={18} />
        </div>
        <div className="worker-list">
          <WorkerRow label="OCR extraction" value="Running" tone="blue" />
          <WorkerRow label="Field confidence" value="Ready" tone="green" />
          <WorkerRow label="Authenticity checks" value="Queued" tone="amber" />
        </div>
      </section>

      <section className="category-surface">
        <div className="section-heading">
          <div>
            <p className="panel-label">Document actions</p>
            <h4>Review controls</h4>
          </div>
        </div>
        <div className="action-grid">
          <button type="button">
            <Check size={17} />
            <span>Verify</span>
          </button>
          <button type="button">
            <X size={17} />
            <span>Reject</span>
          </button>
          <button type="button">
            <Archive size={17} />
            <span>Archive</span>
          </button>
        </div>
      </section>
    </div>
  );
}

function RiskScreen({ supplier }: { supplier: Supplier }) {
  return (
    <div className="screen-grid">
      <section className="wide-surface">
        <div className="section-heading">
          <div>
            <p className="panel-label">AI evidence summary</p>
            <h4>Material findings</h4>
          </div>
          <span className="confidence-chip">Source required</span>
        </div>
        <div className="signal-list">
          {supplier.signals.map((signal) => (
            <article className="signal-row" key={`${signal.category}-${signal.source}`}>
              <div className="signal-icon">
                <AlertTriangle size={18} />
              </div>
              <div>
                <div className="signal-heading">
                  <strong>{signal.category}</strong>
                  <RiskPill level={signal.severity} />
                  <span>{signal.confidence}% confidence</span>
                </div>
                <p>{signal.summary}</p>
                <div className="source-line">
                  <span>{signal.source}</span>
                  <span>{signal.action}</span>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="score-surface">
        <div className="section-heading">
          <div>
            <p className="panel-label">Score components</p>
            <h4>Rule output</h4>
          </div>
        </div>
        <div className="category-list compact-list">
          {supplier.categories.map((category) => (
            <CategoryBar category={category} key={category.name} />
          ))}
        </div>
      </section>

      <section className="category-surface">
        <div className="section-heading">
          <div>
            <p className="panel-label">Guardrails</p>
            <h4>Decision policy</h4>
          </div>
          <ShieldCheck size={18} />
        </div>
        <div className="policy-list">
          <PolicyRow text="Source attribution required" />
          <PolicyRow text="Facts separated from interpretation" />
          <PolicyRow text="Human final approval required" />
          <PolicyRow text="Overrides require reason" />
        </div>
      </section>
    </div>
  );
}

function ReviewScreen({ supplier }: { supplier: Supplier }) {
  return (
    <div className="screen-grid">
      <section className="wide-surface">
        <div className="section-heading">
          <div>
            <p className="panel-label">Decision workflow</p>
            <h4>{supplier.stage}</h4>
          </div>
          <RiskPill level={supplier.risk} />
        </div>
        <div className="decision-grid">
          <button className="decision approve" type="button">
            <Check size={18} />
            <span>Approve</span>
          </button>
          <button className="decision defer" type="button">
            <Clock3 size={18} />
            <span>Defer</span>
          </button>
          <button className="decision request" type="button">
            <Mail size={18} />
            <span>Request info</span>
          </button>
          <button className="decision reject" type="button">
            <X size={18} />
            <span>Reject</span>
          </button>
        </div>
        <div className="review-note">
          <label htmlFor="decision-reason">Decision reason</label>
          <textarea id="decision-reason" placeholder="Required for final decision or score override" />
        </div>
      </section>

      <section className="score-surface">
        <div className="section-heading">
          <div>
            <p className="panel-label">Assigned reviewers</p>
            <h4>Ownership</h4>
          </div>
        </div>
        <div className="reviewer-list">
          {supplier.categories.map((category) => (
            <div className="reviewer-row" key={category.name}>
              <span>{category.reviewer}</span>
              <strong>{category.name}</strong>
              <RiskPill level={category.level} />
            </div>
          ))}
        </div>
      </section>

      <section className="category-surface">
        <div className="section-heading">
          <div>
            <p className="panel-label">Recommendation</p>
            <h4>{recommendationFor(supplier.risk)}</h4>
          </div>
        </div>
        <p className="summary-copy">
          AI recommendation is advisory. Final onboarding, rejection, suspension, or critical risk
          acceptance remains with authorized human users.
        </p>
      </section>
    </div>
  );
}

function AuditScreen({ supplier }: { supplier: Supplier }) {
  return (
    <div className="screen-grid">
      <section className="wide-surface">
        <div className="section-heading">
          <div>
            <p className="panel-label">Audit trail</p>
            <h4>Recent activity</h4>
          </div>
          <button className="secondary-action compact" type="button">
            <Archive size={16} />
            <span>Export</span>
          </button>
        </div>
        <div className="audit-list">
          {supplier.audit.map((event) => (
            <div className="audit-row" key={`${event.actor}-${event.time}-${event.action}`}>
              <span className="audit-dot" />
              <div>
                <strong>{event.action}</strong>
                <p>
                  {event.actor} - {event.entity}
                </p>
              </div>
              <time>{event.time}</time>
            </div>
          ))}
        </div>
      </section>

      <section className="score-surface">
        <div className="section-heading">
          <div>
            <p className="panel-label">Notifications</p>
            <h4>Delivery state</h4>
          </div>
          <Bell size={18} />
        </div>
        <div className="notification-list">
          {supplier.notifications.map((notification) => (
            <div className="notification-row" key={`${notification.title}-${notification.time}`}>
              <div>
                <strong>{notification.title}</strong>
                <p>
                  {notification.channel} - {notification.time}
                </p>
              </div>
              <span className={`status-dot ${notification.status.toLowerCase()}`}>{notification.status}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="category-surface">
        <div className="section-heading">
          <div>
            <p className="panel-label">Audit coverage</p>
            <h4>Captured actions</h4>
          </div>
        </div>
        <div className="policy-list">
          <PolicyRow text="Supplier profile changes" />
          <PolicyRow text="Document replacements" />
          <PolicyRow text="Score calculations and overrides" />
          <PolicyRow text="Human decisions and approvals" />
        </div>
      </section>
    </div>
  );
}

function CategoryBar({ category }: { category: RiskCategory }) {
  return (
    <div className="category-row">
      <div className="category-text">
        <strong>{category.name}</strong>
        <span>{category.reviewer}</span>
      </div>
      <div className="bar-track" aria-label={`${category.name} score ${category.score}`}>
        <span
          className={`bar-fill risk-${category.level.toLowerCase()}`}
          style={{ width: `${category.score}%` }}
        />
      </div>
      <span className="category-score">{category.score}</span>
    </div>
  );
}

function RiskPill({ level }: { level: RiskLevel }) {
  return <span className={`risk-pill risk-${level.toLowerCase()}`}>{level}</span>;
}

function StatusBadge({ status }: { status: DocumentItem["status"] }) {
  return <span className={`doc-status ${status.toLowerCase().replace(" ", "-")}`}>{status}</span>;
}

function WorkerRow({ label, value, tone }: { label: string; value: string; tone: string }) {
  return (
    <div className="worker-row">
      <span>{label}</span>
      <strong className={`worker-${tone}`}>{value}</strong>
    </div>
  );
}

function PolicyRow({ text }: { text: string }) {
  return (
    <div className="policy-row">
      <Check size={16} />
      <span>{text}</span>
    </div>
  );
}

function viewLabel(view: ViewKey) {
  return views.find((item) => item.key === view)?.label ?? "Overview";
}

function recommendationFor(level: RiskLevel) {
  if (level === "Low") return "Recommend onboarding";
  if (level === "Medium") return "Human review";
  if (level === "High") return "Enhanced due diligence";
  return "Reject, block, or executive approval";
}
