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

const demoUsers = [
  "buyer@example.com",
  "supplier@example.com",
  "risk@example.com",
  "approver@example.com",
  "srm@example.com",
  "admin@example.com",
  "auditor@example.com"
];

export function SupplierRiskWorkspace() {
  const [token, setToken] = useState(() => localStorage.getItem("riskBeaconToken") ?? "");
  const [user, setUser] = useState<User | null>(null);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selected, setSelected] = useState<Supplier | null>(null);
  const [agentRuns, setAgentRuns] = useState<AgentRun[]>([]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const authHeaders = useMemo(() => ({ Authorization: `Bearer ${token}`, "Content-Type": "application/json" }), [token]);

  useEffect(() => {
    if (!token) return;
    void bootstrap();
  }, [token]);

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
      setSuppliers(list);
      const nextId = selectedId ?? list[0]?.id ?? null;
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
    setSelected(null);
  }

  async function refreshSupplier(id = selectedId) {
    const list = await request<Supplier[]>("/suppliers");
    setSuppliers(list);
    if (id) setSelected(await request<Supplier>(`/suppliers/${id}`));
    if (id) setAgentRuns(await request<AgentRun[]>(`/agents/runs?supplier_id=${id}`));
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

  async function addDocument() {
    if (!selected) return;
    const document_type = window.prompt("Document type", "business_registration");
    const file_name = window.prompt("File name", "document.pdf");
    if (!document_type || !file_name) return;
    const updated = await request<Supplier>(`/suppliers/${selected.id}/documents`, {
      method: "POST",
      body: JSON.stringify({ document_type, file_name })
    });
    setSelected(updated);
    await refreshSupplier(updated.id);
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

  if (!token || !user) {
    return <LoginScreen loading={loading} message={message} onLogin={login} />;
  }

  const roles = user.roles.join(", ");
  const canCreate = user.roles.includes("Procurement Buyer") || user.roles.includes("System Administrator");
  const canAssess = user.roles.some((role) => ["Procurement Buyer", "Risk Analyst", "System Administrator"].includes(role));
  const canDecide = user.roles.includes("Approver / Risk Committee") || user.roles.includes("System Administrator");
  const canUpload = user.roles.some((role) => ["Supplier Admin", "Procurement Buyer", "System Administrator"].includes(role));
  const canEditProfile = user.roles.some((role) => ["Supplier Admin", "Procurement Buyer", "System Administrator"].includes(role));

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
            <button className="rb-icon" onClick={() => void bootstrap()} title="Refresh">
              <Database size={18} />
            </button>
          </div>
        </header>

        {message ? <div className="rb-message">{message}</div> : null}

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
                    {canUpload ? <button onClick={addDocument}><FileText size={16} /> Add document</button> : null}
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
                        <strong>{signal.category} · {signal.severity}</strong>
                        <span>{signal.signal}</span>
                        <small>{Math.round(signal.confidence * 100)}% confidence · {signal.recommended_action}</small>
                      </div>
                    )) : <p className="rb-empty">No active risk signals yet.</p>}
                  </Panel>
                  <Panel title="Documents">
                    {selected.documents?.map((document) => (
                      <div className="rb-item" key={document.id}>
                        <strong>{document.document_type}</strong>
                        <span>{document.file_name}</span>
                        <small>{document.status}</small>
                      </div>
                    ))}
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
    commodity_category: "",
    supplier_tier: "Tier 2"
  });

  async function submit(event: FormEvent) {
    event.preventDefault();
    await onCreate(form);
    setOpen(false);
    setForm({ legal_name: "", country: "IN", supplier_contact_name: "", supplier_contact_email: "", commodity_category: "", supplier_tier: "Tier 2" });
  }

  return (
    <div className="rb-create">
      <button className="rb-primary" onClick={() => setOpen((value) => !value)}><Plus size={16} /> New supplier</button>
      {open ? (
        <form className="rb-popover" onSubmit={submit}>
          <input placeholder="Legal name" value={form.legal_name} onChange={(event) => setForm({ ...form, legal_name: event.target.value })} required />
          <input placeholder="Country code" value={form.country} onChange={(event) => setForm({ ...form, country: event.target.value })} required />
          <input placeholder="Supplier contact name" value={form.supplier_contact_name} onChange={(event) => setForm({ ...form, supplier_contact_name: event.target.value })} />
          <input placeholder="Supplier contact email" value={form.supplier_contact_email} onChange={(event) => setForm({ ...form, supplier_contact_email: event.target.value })} />
          <input placeholder="Category" value={form.commodity_category} onChange={(event) => setForm({ ...form, commodity_category: event.target.value })} />
          <button>Create onboarding</button>
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
          <input value={form.country} onChange={(event) => setForm({ ...form, country: event.target.value })} required />
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
          <input value={form.industry} onChange={(event) => setForm({ ...form, industry: event.target.value })} />
        </label>
        <label>
          Category
          <input value={form.commodity_category} onChange={(event) => setForm({ ...form, commodity_category: event.target.value })} />
        </label>
        <label>
          Supplier tier
          <input value={form.supplier_tier} onChange={(event) => setForm({ ...form, supplier_tier: event.target.value })} />
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
