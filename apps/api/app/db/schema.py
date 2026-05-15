from __future__ import annotations

import json
from datetime import datetime, timezone

from app.db.sqlite import db_session
from app.security.auth import hash_password


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  email TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  name TEXT NOT NULL,
  status TEXT NOT NULL,
  last_login_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT,
  UNIQUE(tenant_id, email)
);

CREATE TABLE IF NOT EXISTS roles (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(tenant_id, name)
);

CREATE TABLE IF NOT EXISTS user_roles (
  user_id TEXT NOT NULL REFERENCES users(id),
  role_id TEXT NOT NULL REFERENCES roles(id),
  assigned_at TEXT NOT NULL,
  assigned_by TEXT,
  PRIMARY KEY(user_id, role_id)
);

CREATE TABLE IF NOT EXISTS suppliers (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  legal_name TEXT NOT NULL,
  country TEXT NOT NULL,
  tax_id TEXT,
  registration_number TEXT,
  website TEXT,
  industry TEXT,
  commodity_category TEXT,
  supplier_tier TEXT,
  status TEXT NOT NULL,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS supplier_contacts (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  supplier_id TEXT NOT NULL REFERENCES suppliers(id),
  name TEXT NOT NULL,
  email TEXT,
  phone TEXT,
  role TEXT,
  is_primary INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS supplier_user_access (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  supplier_id TEXT NOT NULL REFERENCES suppliers(id),
  user_id TEXT NOT NULL REFERENCES users(id),
  supplier_contact_id TEXT REFERENCES supplier_contacts(id),
  access_role TEXT NOT NULL,
  status TEXT NOT NULL,
  invited_by TEXT,
  invited_at TEXT,
  accepted_at TEXT,
  revoked_at TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(tenant_id, supplier_id, user_id)
);

CREATE TABLE IF NOT EXISTS buyer_supplier_access (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  supplier_id TEXT NOT NULL REFERENCES suppliers(id),
  user_id TEXT NOT NULL REFERENCES users(id),
  access_level TEXT NOT NULL,
  status TEXT NOT NULL,
  assigned_by TEXT,
  assigned_at TEXT NOT NULL,
  revoked_at TEXT,
  UNIQUE(tenant_id, supplier_id, user_id)
);

CREATE TABLE IF NOT EXISTS onboarding_requests (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  supplier_id TEXT NOT NULL REFERENCES suppliers(id),
  requester_id TEXT NOT NULL REFERENCES users(id),
  status TEXT NOT NULL,
  submitted_at TEXT,
  decided_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS documents (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  supplier_id TEXT NOT NULL REFERENCES suppliers(id),
  onboarding_request_id TEXT REFERENCES onboarding_requests(id),
  document_type TEXT NOT NULL,
  file_name TEXT NOT NULL,
  storage_key TEXT NOT NULL,
  status TEXT NOT NULL,
  authenticity_status TEXT NOT NULL DEFAULT 'not_checked',
  uploaded_by TEXT NOT NULL REFERENCES users(id),
  uploaded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS extracted_fields (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  supplier_id TEXT NOT NULL REFERENCES suppliers(id),
  document_id TEXT NOT NULL REFERENCES documents(id),
  agent_run_id TEXT REFERENCES agent_runs(id),
  field_name TEXT NOT NULL,
  field_value TEXT,
  confidence REAL NOT NULL,
  source_text TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_runs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  agent_name TEXT NOT NULL,
  supplier_id TEXT REFERENCES suppliers(id),
  onboarding_request_id TEXT REFERENCES onboarding_requests(id),
  correlation_id TEXT NOT NULL,
  status TEXT NOT NULL,
  input_json TEXT NOT NULL,
  output_json TEXT,
  started_at TEXT NOT NULL,
  completed_at TEXT,
  error_json TEXT
);

CREATE TABLE IF NOT EXISTS evidence_sources (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  supplier_id TEXT NOT NULL REFERENCES suppliers(id),
  agent_run_id TEXT REFERENCES agent_runs(id),
  source_type TEXT NOT NULL,
  name TEXT NOT NULL,
  url TEXT,
  retrieved_at TEXT NOT NULL,
  credibility_score REAL NOT NULL,
  snapshot_storage_key TEXT,
  metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS risk_signals (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  supplier_id TEXT NOT NULL REFERENCES suppliers(id),
  agent_run_id TEXT REFERENCES agent_runs(id),
  category TEXT NOT NULL,
  signal TEXT NOT NULL,
  severity TEXT NOT NULL,
  confidence REAL NOT NULL,
  interpretation TEXT NOT NULL,
  recommended_action TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS risk_scores (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  supplier_id TEXT NOT NULL REFERENCES suppliers(id),
  onboarding_request_id TEXT REFERENCES onboarding_requests(id),
  agent_run_id TEXT REFERENCES agent_runs(id),
  composite_score INTEGER NOT NULL,
  risk_level TEXT NOT NULL,
  calculated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS score_components (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  risk_score_id TEXT NOT NULL REFERENCES risk_scores(id),
  category TEXT NOT NULL,
  score INTEGER NOT NULL,
  weight REAL NOT NULL,
  explanation TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS recommendations (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  supplier_id TEXT NOT NULL REFERENCES suppliers(id),
  onboarding_request_id TEXT REFERENCES onboarding_requests(id),
  agent_run_id TEXT REFERENCES agent_runs(id),
  risk_score_id TEXT REFERENCES risk_scores(id),
  recommended_action TEXT NOT NULL,
  recommended_owner_role TEXT,
  summary TEXT NOT NULL,
  rationale_json TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS review_queue_items (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  supplier_id TEXT NOT NULL REFERENCES suppliers(id),
  onboarding_request_id TEXT REFERENCES onboarding_requests(id),
  assigned_role TEXT NOT NULL,
  assigned_user_id TEXT,
  priority TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS decisions (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  supplier_id TEXT NOT NULL REFERENCES suppliers(id),
  onboarding_request_id TEXT REFERENCES onboarding_requests(id),
  decision TEXT NOT NULL,
  reason TEXT NOT NULL,
  decided_by TEXT NOT NULL REFERENCES users(id),
  decided_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notifications (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  recipient_id TEXT NOT NULL REFERENCES users(id),
  supplier_id TEXT REFERENCES suppliers(id),
  type TEXT NOT NULL,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  status TEXT NOT NULL,
  severity TEXT NOT NULL,
  created_at TEXT NOT NULL,
  read_at TEXT
);

CREATE TABLE IF NOT EXISTS audit_events (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  correlation_id TEXT NOT NULL,
  actor_type TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  action TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  before_json TEXT,
  after_json TEXT,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
  token TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id),
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_suppliers_tenant_status ON suppliers(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_buyer_access_user ON buyer_supplier_access(tenant_id, user_id, status);
CREATE INDEX IF NOT EXISTS idx_supplier_access_user ON supplier_user_access(tenant_id, user_id, status);
CREATE INDEX IF NOT EXISTS idx_extracted_fields_document ON extracted_fields(tenant_id, document_id, field_name);
CREATE INDEX IF NOT EXISTS idx_extracted_fields_supplier ON extracted_fields(tenant_id, supplier_id, field_name);
CREATE INDEX IF NOT EXISTS idx_risk_signals_supplier ON risk_signals(tenant_id, supplier_id, category);
CREATE INDEX IF NOT EXISTS idx_scores_supplier ON risk_scores(tenant_id, supplier_id, calculated_at);
CREATE INDEX IF NOT EXISTS idx_review_queue ON review_queue_items(tenant_id, status, assigned_role);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_events(tenant_id, entity_type, entity_id, created_at);
"""


ROLES = [
    ("role_supplier_admin", "Supplier Admin"),
    ("role_procurement_buyer", "Procurement Buyer"),
    ("role_risk_analyst", "Risk Analyst"),
    ("role_supplier_relationship_manager", "Supplier Relationship Manager"),
    ("role_approver", "Approver / Risk Committee"),
    ("role_system_admin", "System Administrator"),
    ("role_auditor", "Auditor"),
]


USERS = [
    ("usr_buyer", "buyer@example.com", "Mira Buyer", "role_procurement_buyer"),
    ("usr_supplier", "supplier@example.com", "Priya Supplier", "role_supplier_admin"),
    ("usr_risk", "risk@example.com", "Aarav Risk", "role_risk_analyst"),
    ("usr_approver", "approver@example.com", "Nisha Approver", "role_approver"),
    ("usr_srm", "srm@example.com", "Daniel SRM", "role_supplier_relationship_manager"),
    ("usr_admin", "admin@example.com", "System Admin", "role_system_admin"),
    ("usr_auditor", "auditor@example.com", "Audit User", "role_auditor"),
]


def initialize_database() -> None:
    with db_session() as conn:
        conn.executescript(SCHEMA)
        timestamp = now()
        for role_id, name in ROLES:
            conn.execute(
                "INSERT OR IGNORE INTO roles(id, tenant_id, name, description, created_at) VALUES (?, ?, ?, ?, ?)",
                (role_id, "TEN-001", name, f"{name} role", timestamp),
            )
        for user_id, email, name, role_id in USERS:
            conn.execute(
                """
                INSERT OR IGNORE INTO users(id, tenant_id, email, password_hash, name, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, "TEN-001", email, hash_password("Password123!"), name, "active", timestamp),
            )
            conn.execute(
                "INSERT OR IGNORE INTO user_roles(user_id, role_id, assigned_at, assigned_by) VALUES (?, ?, ?, ?)",
                (user_id, role_id, timestamp, "system"),
            )
        _seed_supplier(conn, timestamp)


def _seed_supplier(conn, timestamp: str) -> None:
    exists = conn.execute("SELECT id FROM suppliers WHERE id = ?", ("SUP-001",)).fetchone()
    if exists:
        return
    conn.execute(
        """
        INSERT INTO suppliers(id, tenant_id, legal_name, country, tax_id, registration_number, website,
          industry, commodity_category, supplier_tier, status, metadata_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "SUP-001",
            "TEN-001",
            "Aster Components Pvt Ltd",
            "IN",
            "29ABCDE1234F1Z5",
            "U12345MH2020PTC123456",
            "https://aster.example",
            "Electronic Components",
            "Electronic assemblies",
            "Tier 1",
            "pending_review",
            json.dumps({"annual_spend_estimate": 2500000, "currency": "USD"}),
            timestamp,
        ),
    )
    conn.execute(
        """
        INSERT INTO onboarding_requests(id, tenant_id, supplier_id, requester_id, status, submitted_at, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        ("ONB-001", "TEN-001", "SUP-001", "usr_buyer", "in_review", timestamp, timestamp),
    )
    conn.execute(
        """
        INSERT INTO buyer_supplier_access(id, tenant_id, supplier_id, user_id, access_level, status, assigned_by, assigned_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("BSA-001", "TEN-001", "SUP-001", "usr_buyer", "manage_onboarding", "active", "usr_admin", timestamp),
    )
    conn.execute(
        """
        INSERT INTO supplier_user_access(id, tenant_id, supplier_id, user_id, access_role, status, invited_by, invited_at, accepted_at, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("SUA-001", "TEN-001", "SUP-001", "usr_supplier", "supplier_admin", "active", "usr_buyer", timestamp, timestamp, timestamp),
    )
    documents = [
        ("DOC-001", "business_registration", "Business registration.pdf", "extracted"),
        ("DOC-002", "tax_certificate", "Tax certificate.pdf", "extracted"),
        ("DOC-003", "bank_letter", "Bank letter.pdf", "uploaded"),
    ]
    for doc_id, doc_type, file_name, status in documents:
        conn.execute(
            """
            INSERT INTO documents(id, tenant_id, supplier_id, onboarding_request_id, document_type, file_name,
              storage_key, status, uploaded_by, uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (doc_id, "TEN-001", "SUP-001", "ONB-001", doc_type, file_name, f"documents/{doc_id}.pdf", status, "usr_supplier", timestamp),
        )
