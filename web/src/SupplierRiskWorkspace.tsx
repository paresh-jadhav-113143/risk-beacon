import {
  AlertCircle,
  Bell,
  CheckCircle2,
  Database,
  FileText,
  Gauge,
  LogOut,
  Play,
  Plus,
  Shield,
  UserRound,
  XCircle
} from "lucide-react";
import { FormEvent, ReactNode, useEffect, useMemo, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

type User = {
  id: string;
  email: string;
  name: string;
  roles: string[];
};

type Supplier = {
  id: string;
  legal_name: string;
  country: string;
  tax_id?: string;
  registration_number?: string;
  website?: string;
  industry?: string;
  status: string;
  commodity_category?: string;
  supplier_tier?: string;
  latest_score?: { composite_score: number; risk_level: string; calculated_at: string } | null;
  onboarding?: { id: string; status: string } | null;
  document_count: number;
  active_signal_count: number;
  documents?: DocumentRecord[];
  extracted_fields?: ExtractedField[];
  risk_signals?: RiskSignal[];
  scores?: RiskScore[];
  recommendations?: Recommendation[];
  audit_events?: AuditEvent[];
  invitation?: SupplierInvitation;
};

type SupplierInvitation = {
  status: string;
  supplier_user_id: string;
  email: string;
  role: string;
  supplier_id: string;
  password_delivery: string;
  default_password?: string;
};

type DocumentRecord = {
  id: string;
  document_type: string;
  file_name: string;
  status: string;
  uploaded_at: string;
};

type RiskSignal = {
  id: string;
  category: string;
  signal: string;
  severity: string;
  confidence: number;
  interpretation: string;
  recommended_action: string;
  status: string;
};

type ExtractedField = {
  id: string;
  document_id: string;
  field_name: string;
  field_value?: string;
  confidence: number;
  source_text?: string;
};

type RiskScore = {
  id: string;
  composite_score: number;
  risk_level: string;
  calculated_at: string;
};

type Recommendation = {
  id: string;
  recommended_action: string;
  summary: string;
  created_at: string;
};

type AuditEvent = {
  id: string;
  actor_type: string;
  action: string;
  entity_type: string;
  created_at: string;
};

type AgentRun = {
  id: string;
  agent_name: string;
  status: string;
  started_at: string;
  completed_at?: string;
};

type NotificationRecord = {
  id: string;
  supplier_id?: string;
  type: string;
  title: string;
  body: string;
  status: string;
  severity: string;
  created_at: string;
};

type NewSupplierForm = {
  legal_name: string;
  country: string;
  supplier_contact_name: string;
  supplier_contact_email: string;
  commodity_category: string;
  supplier_tier: string;
};

type SupplierProfileForm = {
  legal_name: string;
  country: string;
  tax_id: string;
  registration_number: string;
  website: string;
  industry: string;
  commodity_category: string;
  supplier_tier: string;
};

type DocumentForm = {
  document_type: string;
  file_name: string;
};

const demoUsers = [
  "buyer@example.com",
  "supplier@example.com",
  "risk@example.com",
  "approver@example.com",
  "srm@example.com",
  "admin@example.com",
  "auditor@example.com"
];

const countryOptions = [
  { value: "IN", label: "India" },
  { value: "US", label: "United States" },
  { value: "GB", label: "United Kingdom" },
  { value: "DE", label: "Germany" },
  { value: "SG", label: "Singapore" },
  { value: "AE", label: "United Arab Emirates" }
];

const industryOptions = [
  "Electronic Components",
  "Manufacturing",
  "Packaging",
  "Information Technology",
  "Logistics",
  "Professional Services",
  "Raw Materials",
  "Pharmaceuticals"
];

const categoryOptions = [
  "Electronic assemblies",
  "Semiconductors",
  "Packaging",
  "IT services",
  "Raw materials",
  "Logistics",
  "Professional services"
];

const tierOptions = ["Tier 1", "Tier 2", "Tier 3", "Strategic"];

const documentTypeOptions = [
  { value: "business_registration", label: "Business registration" },
  { value: "tax_certificate", label: "Tax certificate" },
  { value: "bank_letter", label: "Bank letter" },
  { value: "financial_statement", label: "Financial statement" },
  { value: "sustainability_certificate", label: "Sustainability certificate" },
  { value: "insurance_certificate", label: "Insurance certificate" },
  { value: "quality_certificate", label: "Quality certificate" }
];

export function SupplierRiskWorkspace() {
  const [token, setToken] = useState(() => localStorage.getItem("riskBeaconToken") ?? "");
  const [user, setUser] = useState<User | null>(null);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selected, setSelected] = useState<Supplier | null>(null);
  const [agentRuns, setAgentRuns] = useState<AgentRun[]>([]);
  const [notifications, setNotifications] = useState<NotificationRecord[]>([]);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const authHeaders = useMemo(() => ({ Authorization: `Bearer ${token}`, "Content-Type": "application/json" }), [token]);

  useEffect(() => {
    if (!token) return;
    void bootstrap();
  }, [token]);

  useEffect(() => {
    if (!message) return undefined;
    const timer = window.setTimeout(() => setMessage(""), 5500);
    return () => window.clearTimeout(timer);
  }, [message]);

  async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        ...(token ? authHeaders : { "Content-Type": "application/json" }),
        ...(options.headers ?? {})
      }
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(body.detail ?? "Request failed");
    }
    return response.json();
  }

  async function bootstrap() {
    try {
      setLoading(true);
      const me = await request<User>("/auth/me");
      setUser(me);
      const list = await request<Supplier[]>("/suppliers");
      setNotifications(await request<NotificationRecord[]>("/notifications"));
      setSuppliers(list);
      const nextId = selectedId && list.some((supplier) => supplier.id === selectedId) ? selectedId : list[0]?.id ?? null;
      setSelectedId(nextId);
      if (nextId) {
        setSelected(await request<Supplier>(`/suppliers/${nextId}`));
        setAgentRuns(await request<AgentRun[]>(`/agents/runs?supplier_id=${nextId}`));
      } else {
        setSelected(null);
        setAgentRuns([]);
      }
    } catch (error) {
      localStorage.removeItem("riskBeaconToken");
      setToken("");
      setMessage(error instanceof Error ? error.message : "Session expired");
    } finally {
      setLoading(false);
    }
  }

  async function login(email: string, password: string) {
    setLoading(true);
    setMessage("");
    try {
      const result = await request<{ token: string; user: User }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password })
      });
      localStorage.setItem("riskBeaconToken", result.token);
      setToken(result.token);
      setUser(result.user);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  async function logout() {
    if (token) {
      await fetch(`${API_BASE}/auth/logout`, { method: "POST", headers: authHeaders }).catch(() => undefined);
    }
    localStorage.removeItem("riskBeaconToken");
    setToken("");
    setUser(null);
    setSuppliers([]);
    setSelectedId(null);
    setSelected(null);
    setAgentRuns([]);
    setNotifications([]);
    setNotificationsOpen(false);
  }

  async function refreshSupplier(id = selectedId) {
    const list = await request<Supplier[]>("/suppliers");
    setNotifications(await request<NotificationRecord[]>("/notifications"));
    setSuppliers(list);
    const visibleId = id && list.some((supplier) => supplier.id === id) ? id : list[0]?.id;
    setSelectedId(visibleId ?? null);
    if (visibleId) {
      setSelected(await request<Supplier>(`/suppliers/${visibleId}`));
      setAgentRuns(await request<AgentRun[]>(`/agents/runs?supplier_id=${visibleId}`));
    } else {
      setSelected(null);
      setAgentRuns([]);
    }
  }

  async function createSupplier(payload: NewSupplierForm) {
    const created = await request<Supplier>("/suppliers", { method: "POST", body: JSON.stringify(payload) });
    setSelectedId(created.id);
    await refreshSupplier(created.id);
    if (created.invitation?.default_password) {
      setMessage(`Supplier created. Supplier login: ${created.invitation.email} / ${created.invitation.default_password}`);
    } else if (created.invitation) {
      setMessage(`Supplier created. Existing supplier user linked: ${created.invitation.email}`);
    } else {
      setMessage("Supplier onboarding request created.");
    }
  }

  async function markNotificationRead(notificationId: string) {
    await request<{ ok: boolean }>(`/notifications/${notificationId}/read`, { method: "POST" });
    setNotifications(await request<NotificationRecord[]>("/notifications"));
  }

  async function markAllNotificationsRead() {
    await request<{ ok: boolean }>("/notifications/read-all", { method: "POST" });
    setNotifications(await request<NotificationRecord[]>("/notifications"));
  }

  async function openNotification(notification: NotificationRecord) {
    if (notification.status === "unread") {
      await markNotificationRead(notification.id);
    }
    if (notification.supplier_id && suppliers.some((supplier) => supplier.id === notification.supplier_id)) {
      setSelectedId(notification.supplier_id);
      setSelected(await request<Supplier>(`/suppliers/${notification.supplier_id}`));
      setAgentRuns(await request<AgentRun[]>(`/agents/runs?supplier_id=${notification.supplier_id}`));
    }
    setNotificationsOpen(false);
  }

  async function runAssessment() {
    if (!selected) return;
    setLoading(true);
    try {
      const response = await request<{ supplier: Supplier }>(`/suppliers/${selected.id}/run-assessment`, { method: "POST" });
      setSelected(response.supplier);
      await refreshSupplier(response.supplier.id);
      setMessage("Assessment completed and routed to Risk Analyst.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Assessment failed");
    } finally {
      setLoading(false);
    }
  }

  async function decide(decision: string) {
    if (!selected) return;
    const reason = window.prompt(`Reason for ${decision}?`);
    if (!reason) return;
    const updated = await request<Supplier>(`/suppliers/${selected.id}/decisions`, {
      method: "POST",
      body: JSON.stringify({ decision, reason })
    });
    setSelected(updated);
    await refreshSupplier(updated.id);
    setMessage(`Decision saved: ${decision}`);
  }

  async function addDocument(payload: DocumentForm) {
    if (!selected) return;
    try {
      const updated = await request<Supplier>(`/suppliers/${selected.id}/documents`, {
        method: "POST",
        body: JSON.stringify(payload)
      });
      setSelected(updated);
      await refreshSupplier(updated.id);
      setMessage("Document added.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Document upload failed");
    }
  }

  async function downloadDocument(document: DocumentRecord) {
    if (!selected) return;
    try {
      const response = await fetch(`${API_BASE}/suppliers/${selected.id}/documents/${document.id}/download`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(body.detail ?? "Download failed");
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = window.document.createElement("a");
      anchor.href = url;
      anchor.download = document.file_name;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Download failed");
    }
  }

  async function updateProfile(payload: SupplierProfileForm) {
    if (!selected) return;
    const updated = await request<Supplier>(`/suppliers/${selected.id}`, {
      method: "PATCH",
      body: JSON.stringify(emptyStringsToNull(payload))
    });
    setSelected(updated);
    await refreshSupplier(updated.id);
    setMessage("Supplier profile updated.");
  }

  async function reviewFinding(signalId: string, action: "accept" | "dismiss" | "request_information") {
    if (!selected) return;
    const reason = window.prompt(`Reason to ${action.replace("_", " ")} this finding?`);
    if (!reason) return;
    const updated = await request<Supplier>(`/suppliers/${selected.id}/risk-signals/${signalId}/review`, {
      method: "POST",
      body: JSON.stringify({ action, reason })
    });
    setSelected(updated);
    await refreshSupplier(updated.id);
    const activeFindings = updated.risk_signals?.filter((signal) => signal.status === "active").length ?? 0;
    if (updated.status === "pending_approval" && activeFindings === 0) {
      setMessage("All findings reviewed by Risk Analyst. Supplier routed to Approver / Risk Committee for final approval.");
    } else {
      setMessage(`Finding ${action.replace("_", " ")} saved. ${activeFindings} active finding${activeFindings === 1 ? "" : "s"} remaining.`);
    }
  }

  if (!token || !user) {
    return <LoginScreen loading={loading} message={message} onLogin={login} />;
  }

  const roles = user.roles.join(", ");
  const canCreate = user.roles.includes("Procurement Buyer") || user.roles.includes("System Administrator");
  const canAssess = Boolean(selected) && selected?.status !== "approved" && selected?.status !== "rejected" && user.roles.some((role) => ["Procurement Buyer", "Risk Analyst", "System Administrator"].includes(role));
  const canDecide = Boolean(selected) && selected?.status === "pending_approval" && (user.roles.includes("Approver / Risk Committee") || user.roles.includes("System Administrator"));
  const canUpload = Boolean(selected) && ["pending_onboarding", "needs_information"].includes(selected?.status ?? "") && user.roles.some((role) => ["Supplier Admin", "System Administrator"].includes(role));
  const canEditProfile = Boolean(selected) && ["pending_onboarding", "needs_information"].includes(selected?.status ?? "") && user.roles.some((role) => ["Supplier Admin", "System Administrator"].includes(role));
  const canReviewFindings = Boolean(selected) && selected?.status === "pending_review" && user.roles.some((role) => ["Risk Analyst", "System Administrator"].includes(role));
  const canDownloadDocuments = user.roles.some((role) => ["Supplier Admin", "Risk Analyst", "Approver / Risk Committee", "System Administrator", "Auditor"].includes(role));
  const unreadNotificationCount = notifications.filter((notification) => notification.status === "unread").length;

  return (
    <div className="rb-shell">
      <aside className="rb-sidebar">
        <div className="rb-brand">
          <Shield size={28} />
          <div>
            <strong>Risk Beacon</strong>
            <span>Supplier intelligence</span>
          </div>
        </div>
        <div className="rb-user">
          <UserRound size={18} />
          <div>
            <strong>{user.name}</strong>
            <span>{roles}</span>
          </div>
        </div>
        <button className="rb-ghost" onClick={logout}>
          <LogOut size={16} /> Log out
        </button>
      </aside>

      <main className="rb-main">
        <header className="rb-topbar">
          <div>
            <p className="rb-eyebrow">Scoped supplier workspace</p>
            <h1>{firstScreenTitle(user.roles)}</h1>
          </div>
          <div className="rb-top-actions">
            {canCreate ? <CreateSupplierButton onCreate={createSupplier} /> : null}
            <NotificationBell
              notifications={notifications}
              open={notificationsOpen}
              unreadCount={unreadNotificationCount}
              onToggle={() => setNotificationsOpen((value) => !value)}
              onOpenNotification={openNotification}
              onMarkAllRead={markAllNotificationsRead}
            />
            <button className="rb-icon" onClick={() => void bootstrap()} title="Refresh">
              <Database size={18} />
            </button>
          </div>
        </header>

        {message ? (
          <div className="rb-message">
            <span>{message}</span>
            <button type="button" onClick={() => setMessage("")}>X</button>
          </div>
        ) : null}

        <section className="rb-grid">
          <div className="rb-panel rb-list-panel">
            <div className="rb-panel-head">
              <h2>Suppliers</h2>
              <span>{suppliers.length}</span>
            </div>
            <div className="rb-list">
              {suppliers.map((supplier) => (
                <button
                  key={supplier.id}
                  className={`rb-supplier-row ${supplier.id === selected?.id ? "active" : ""}`}
                  onClick={async () => {
                    setSelectedId(supplier.id);
                    setSelected(await request<Supplier>(`/suppliers/${supplier.id}`));
                    setAgentRuns(await request<AgentRun[]>(`/agents/runs?supplier_id=${supplier.id}`));
                  }}
                >
                  <strong>{supplier.legal_name}</strong>
                  <span>{supplier.country} · {supplier.status}</span>
                  <RiskPill level={supplier.latest_score?.risk_level ?? "unscored"} score={supplier.latest_score?.composite_score} />
                </button>
              ))}
              {!suppliers.length ? <p className="rb-empty">No suppliers visible for this role.</p> : null}
            </div>
          </div>

          <div className="rb-detail">
            {selected ? (
              <>
                <section className="rb-panel">
                  <div className="rb-detail-head">
                    <div>
                      <p className="rb-eyebrow">{selected.id}</p>
                      <h2>{selected.legal_name}</h2>
                      <p>{selected.country} · {selected.commodity_category ?? "Uncategorized"} · {selected.supplier_tier ?? "No tier"}</p>
                    </div>
                    <RiskPill level={selected.latest_score?.risk_level ?? "unscored"} score={selected.latest_score?.composite_score} large />
                  </div>
                  <div className="rb-actions">
                    {canUpload ? <AddDocumentButton documents={selected.documents ?? []} onAdd={addDocument} /> : null}
                    {canAssess ? <button onClick={runAssessment} disabled={loading}><Play size={16} /> Run assessment</button> : null}
                    {canDecide ? (
                      <>
                        <button onClick={() => void decide("approve")}><CheckCircle2 size={16} /> Approve</button>
                        <button onClick={() => void decide("reject")}><XCircle size={16} /> Reject</button>
                      </>
                    ) : null}
                  </div>
                </section>

                <section className="rb-metrics">
                  <Metric icon={<FileText />} label="Documents" value={selected.document_count} />
                  <Metric icon={<AlertCircle />} label="Active signals" value={selected.active_signal_count} />
                  <Metric icon={<Gauge />} label="Status" value={selected.status.replaceAll("_", " ")} />
                  <Metric icon={<Bell />} label="Onboarding" value={selected.onboarding?.status ?? "none"} />
                </section>

                {canEditProfile ? (
                  <SupplierProfilePanel supplier={selected} onSave={updateProfile} />
                ) : null}

                <section className="rb-columns">
                  <Panel title="Risk Signals">
                    {selected.risk_signals?.length ? selected.risk_signals.map((signal) => (
                      <div className="rb-item" key={signal.id}>
                        <strong>{signal.category} · {signal.severity} · {signal.status}</strong>
                        <span>{signal.signal}</span>
                        <small>{Math.round(signal.confidence * 100)}% confidence · {signal.recommended_action}</small>
                        {canReviewFindings && signal.status === "active" ? (
                          <div className="rb-inline-actions">
                            <button onClick={() => void reviewFinding(signal.id, "accept")}>Accept</button>
                            <button onClick={() => void reviewFinding(signal.id, "dismiss")}>Dismiss</button>
                            <button onClick={() => void reviewFinding(signal.id, "request_information")}>Need info</button>
                          </div>
                        ) : null}
                      </div>
                    )) : <p className="rb-empty">No active risk signals yet.</p>}
                  </Panel>
                  <Panel title="Documents">
                    {selected.documents?.map((document) => (
                      <div className="rb-item" key={document.id}>
                        <strong>{document.document_type}</strong>
                        <span>{document.file_name}</span>
                        <small>{document.status}</small>
                        {canDownloadDocuments ? (
                          <div className="rb-inline-actions">
                            <button onClick={() => void downloadDocument(document)}>Download</button>
                          </div>
                        ) : null}
                      </div>
                    ))}
                    {selected.extracted_fields?.length ? (
                      <div className="rb-extraction-list">
                        <strong>Extracted fields</strong>
                        {selected.extracted_fields.slice(0, 8).map((field) => (
                          <small key={field.id}>{field.field_name}: {field.field_value ?? "empty"} ({Math.round(field.confidence * 100)}%)</small>
                        ))}
                      </div>
                    ) : null}
                  </Panel>
                </section>

                <section className="rb-columns">
                  <Panel title="Agent Runs">
                    {agentRuns.length ? agentRuns.slice(0, 10).map((run) => (
                      <div className="rb-item" key={run.id}>
                        <strong>{run.agent_name}</strong>
                        <span>{run.status}</span>
                        <small>{new Date(run.started_at).toLocaleString()}</small>
                      </div>
                    )) : <p className="rb-empty">No agent runs yet.</p>}
                  </Panel>
                  <Panel title="Recommendations">
                    {selected.recommendations?.length ? selected.recommendations.map((recommendation) => (
                      <div className="rb-item" key={recommendation.id}>
                        <strong>{recommendation.recommended_action}</strong>
                        <span>{recommendation.summary}</span>
                      </div>
                    )) : <p className="rb-empty">No recommendation generated.</p>}
                  </Panel>
                </section>
                <section className="rb-columns">
                  <Panel title="Audit Trail">
                    {selected.audit_events?.slice(0, 8).map((event) => (
                      <div className="rb-item" key={event.id}>
                        <strong>{event.action}</strong>
                        <span>{event.actor_type} · {event.entity_type}</span>
                        <small>{new Date(event.created_at).toLocaleString()}</small>
                      </div>
                    ))}
                  </Panel>
                  <Panel title="Visibility Scope">
                    <div className="rb-item">
                      <strong>{user.roles.join(", ")}</strong>
                      <span>This view is filtered by backend role and supplier access mappings.</span>
                      <small>Buyer and supplier users only see linked suppliers.</small>
                    </div>
                  </Panel>
                </section>
              </>
            ) : (
              <section className="rb-panel rb-empty-state">
                <h2>Select a supplier</h2>
                <p>Your visible suppliers are controlled by role and supplier mapping.</p>
              </section>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

function LoginScreen({ loading, message, onLogin }: { loading: boolean; message: string; onLogin: (email: string, password: string) => Promise<void> }) {
  const [email, setEmail] = useState("buyer@example.com");
  const [password, setPassword] = useState("Password123!");

  async function submit(event: FormEvent) {
    event.preventDefault();
    await onLogin(email, password);
  }

  return (
    <main className="rb-login">
      <section className="rb-login-panel">
        <div className="rb-brand login">
          <Shield size={30} />
          <div>
            <strong>Risk Beacon</strong>
            <span>Supplier onboarding MVP</span>
          </div>
        </div>
        <form onSubmit={submit}>
          <label>
            Email
            <input value={email} onChange={(event) => setEmail(event.target.value)} />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
          </label>
          <button className="rb-primary" disabled={loading}>{loading ? "Signing in..." : "Sign in"}</button>
        </form>
        {message ? <div className="rb-message error">{message}</div> : null}
        <div className="rb-demo-users">
          <p>Demo users</p>
          {demoUsers.map((demo) => (
            <button key={demo} onClick={() => setEmail(demo)}>{demo}</button>
          ))}
        </div>
      </section>
    </main>
  );
}

function CreateSupplierButton({ onCreate }: { onCreate: (payload: NewSupplierForm) => Promise<void> }) {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<NewSupplierForm>({
    legal_name: "",
    country: "IN",
    supplier_contact_name: "",
    supplier_contact_email: "",
    commodity_category: "Packaging",
    supplier_tier: "Tier 2"
  });

  async function submit(event: FormEvent) {
    event.preventDefault();
    await onCreate(form);
    setOpen(false);
    setForm({ legal_name: "", country: "IN", supplier_contact_name: "", supplier_contact_email: "", commodity_category: "Packaging", supplier_tier: "Tier 2" });
  }

  return (
    <div className="rb-create">
      <button className="rb-primary" onClick={() => setOpen((value) => !value)}><Plus size={16} /> New supplier</button>
      {open ? (
        <form className="rb-popover" onSubmit={submit}>
          <input placeholder="Legal name" value={form.legal_name} onChange={(event) => setForm({ ...form, legal_name: event.target.value })} required />
          <select value={form.country} onChange={(event) => setForm({ ...form, country: event.target.value })} required>
            {countryOptions.map((country) => <option key={country.value} value={country.value}>{country.label}</option>)}
          </select>
          <input placeholder="Supplier contact name" value={form.supplier_contact_name} onChange={(event) => setForm({ ...form, supplier_contact_name: event.target.value })} />
          <input placeholder="Supplier contact email" value={form.supplier_contact_email} onChange={(event) => setForm({ ...form, supplier_contact_email: event.target.value })} />
          <select value={form.commodity_category} onChange={(event) => setForm({ ...form, commodity_category: event.target.value })} required>
            {categoryOptions.map((category) => <option key={category} value={category}>{category}</option>)}
          </select>
          <select value={form.supplier_tier} onChange={(event) => setForm({ ...form, supplier_tier: event.target.value })} required>
            {tierOptions.map((tier) => <option key={tier} value={tier}>{tier}</option>)}
          </select>
          <button>Create onboarding</button>
        </form>
      ) : null}
    </div>
  );
}

function NotificationBell({
  notifications,
  open,
  unreadCount,
  onToggle,
  onOpenNotification,
  onMarkAllRead
}: {
  notifications: NotificationRecord[];
  open: boolean;
  unreadCount: number;
  onToggle: () => void;
  onOpenNotification: (notification: NotificationRecord) => Promise<void>;
  onMarkAllRead: () => Promise<void>;
}) {
  return (
    <div className="rb-notifications">
      <button className="rb-icon rb-bell" onClick={onToggle} title="Notifications">
        <Bell size={18} />
        {unreadCount ? <span>{unreadCount}</span> : null}
      </button>
      {open ? (
        <section className="rb-notification-menu">
          <div className="rb-notification-head">
            <strong>Notifications</strong>
            {unreadCount ? <button onClick={() => void onMarkAllRead()}>Mark all read</button> : null}
          </div>
          <div className="rb-notification-list">
            {notifications.length ? notifications.slice(0, 8).map((notification) => (
              <button
                key={notification.id}
                className={`rb-notification ${notification.status === "unread" ? "unread" : ""}`}
                onClick={() => void onOpenNotification(notification)}
              >
                <strong>{notification.title}</strong>
                <span>{notification.body}</span>
                <small>{new Date(notification.created_at).toLocaleString()}</small>
              </button>
            )) : <p className="rb-empty">No notifications yet.</p>}
          </div>
        </section>
      ) : null}
    </div>
  );
}

function AddDocumentButton({ documents, onAdd }: { documents: DocumentRecord[]; onAdd: (payload: DocumentForm) => Promise<void> }) {
  const [open, setOpen] = useState(false);
  const availableDocumentTypes = documentTypeOptions.filter((documentType) => !documents.some((document) => document.document_type === documentType.value && !["replaced", "archived"].includes(document.status)));
  const defaultDocumentType = availableDocumentTypes[0]?.value ?? "";
  const [form, setForm] = useState<DocumentForm>({ document_type: defaultDocumentType, file_name: "" });

  useEffect(() => {
    if (!availableDocumentTypes.some((documentType) => documentType.value === form.document_type)) {
      setForm((current) => ({ ...current, document_type: defaultDocumentType }));
    }
  }, [defaultDocumentType, documents.length]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!form.document_type) return;
    await onAdd(form);
    setOpen(false);
    setForm({ document_type: defaultDocumentType, file_name: "" });
  }

  return (
    <div className="rb-create">
      <button type="button" onClick={() => setOpen((value) => !value)} disabled={!availableDocumentTypes.length}><FileText size={16} /> Add document</button>
      {open ? (
        <form className="rb-popover" onSubmit={submit}>
          <select value={form.document_type} onChange={(event) => setForm({ ...form, document_type: event.target.value })} required>
            {availableDocumentTypes.map((documentType) => <option key={documentType.value} value={documentType.value}>{documentType.label}</option>)}
          </select>
          <input placeholder="File name" value={form.file_name} onChange={(event) => setForm({ ...form, file_name: event.target.value })} required />
          <button>Add document</button>
        </form>
      ) : null}
    </div>
  );
}

function SupplierProfilePanel({ supplier, onSave }: { supplier: Supplier; onSave: (payload: SupplierProfileForm) => Promise<void> }) {
  const [form, setForm] = useState<SupplierProfileForm>(() => profileFromSupplier(supplier));
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setForm(profileFromSupplier(supplier));
  }, [supplier.id]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    try {
      await onSave(form);
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="rb-panel">
      <div className="rb-panel-head">
        <h2>Supplier Profile</h2>
      </div>
      <form className="rb-profile-form" onSubmit={submit}>
        <label>
          Legal name
          <input value={form.legal_name} onChange={(event) => setForm({ ...form, legal_name: event.target.value })} required />
        </label>
        <label>
          Country
          <select value={form.country} onChange={(event) => setForm({ ...form, country: event.target.value })} required>
            {countryOptions.map((country) => <option key={country.value} value={country.value}>{country.label}</option>)}
          </select>
        </label>
        <label>
          Tax ID
          <input value={form.tax_id} onChange={(event) => setForm({ ...form, tax_id: event.target.value })} />
        </label>
        <label>
          Registration number
          <input value={form.registration_number} onChange={(event) => setForm({ ...form, registration_number: event.target.value })} />
        </label>
        <label>
          Website
          <input value={form.website} onChange={(event) => setForm({ ...form, website: event.target.value })} />
        </label>
        <label>
          Industry
          <select value={form.industry} onChange={(event) => setForm({ ...form, industry: event.target.value })}>
            <option value="">Select industry</option>
            {optionsWithCurrent(industryOptions, form.industry).map((industry) => <option key={industry} value={industry}>{industry}</option>)}
          </select>
        </label>
        <label>
          Category
          <select value={form.commodity_category} onChange={(event) => setForm({ ...form, commodity_category: event.target.value })}>
            <option value="">Select category</option>
            {optionsWithCurrent(categoryOptions, form.commodity_category).map((category) => <option key={category} value={category}>{category}</option>)}
          </select>
        </label>
        <label>
          Supplier tier
          <select value={form.supplier_tier} onChange={(event) => setForm({ ...form, supplier_tier: event.target.value })}>
            <option value="">Select tier</option>
            {optionsWithCurrent(tierOptions, form.supplier_tier).map((tier) => <option key={tier} value={tier}>{tier}</option>)}
          </select>
        </label>
        <div className="rb-form-actions">
          <button className="rb-primary" disabled={saving}>{saving ? "Saving..." : "Save profile"}</button>
        </div>
      </form>
    </section>
  );
}

function profileFromSupplier(supplier: Supplier): SupplierProfileForm {
  return {
    legal_name: supplier.legal_name ?? "",
    country: supplier.country ?? "",
    tax_id: supplier.tax_id ?? "",
    registration_number: supplier.registration_number ?? "",
    website: supplier.website ?? "",
    industry: supplier.industry ?? "",
    commodity_category: supplier.commodity_category ?? "",
    supplier_tier: supplier.supplier_tier ?? ""
  };
}

function emptyStringsToNull(payload: SupplierProfileForm) {
  return Object.fromEntries(Object.entries(payload).map(([key, value]) => [key, value.trim() === "" ? null : value.trim()]));
}

function optionsWithCurrent(options: string[], current: string) {
  if (!current || options.includes(current)) return options;
  return [current, ...options];
}

function RiskPill({ level, score, large = false }: { level: string; score?: number; large?: boolean }) {
  return <span className={`rb-risk ${level.toLowerCase()} ${large ? "large" : ""}`}>{score ?? "--"} · {level}</span>;
}

function Metric({ icon, label, value }: { icon: JSX.Element; label: string; value: string | number }) {
  return <div className="rb-metric">{icon}<span>{label}</span><strong>{value}</strong></div>;
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return <section className="rb-panel"><div className="rb-panel-head"><h2>{title}</h2></div>{children}</section>;
}

function firstScreenTitle(roles: string[]) {
  if (roles.includes("Supplier Admin")) return "Supplier portal";
  if (roles.includes("Procurement Buyer")) return "Buyer dashboard";
  if (roles.includes("Risk Analyst")) return "Risk review queue";
  if (roles.includes("Approver / Risk Committee")) return "Approval queue";
  if (roles.includes("Auditor")) return "Audit console";
  return "Supplier risk workspace";
}
