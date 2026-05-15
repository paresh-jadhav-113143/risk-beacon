# Risk Beacon

Supplier risk intelligence MVP with React, FastAPI, and SQLite.

## Local Run

Start the API:

```bash
python3 -m pip install -r apps/api/requirements.txt
env PYTHONPATH=apps/api python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Start the web app:

```bash
cd web
npm install
npm run dev
```

The web app proxies API calls to `http://localhost:8000`.
By default the React app also uses `http://127.0.0.1:8000` directly unless `VITE_API_BASE_URL` is set.

## Demo Accounts

All seeded demo users use:

```text
Password123!
```

Accounts:

```text
buyer@example.com
supplier@example.com
risk@example.com
approver@example.com
srm@example.com
admin@example.com
auditor@example.com
```

## MVP Coverage

- Email/password login.
- SQLite-backed users, roles, supplier visibility, suppliers, documents, agent runs, risk signals, scores, recommendations, decisions, notifications, and audit events.
- Buyer-scoped supplier visibility.
- Supplier-scoped supplier user access.
- Risk Analyst review ownership for compliance, financial, ESG, cyber, operational, reputation, authenticity, and anomaly findings.
- Agent pipeline scaffold with persisted runs, risk signals, scoring, recommendations, and review queue creation.
- React dashboard, supplier detail, document metadata entry, assessment execution, and approver decision actions.

## Optional Live Integrations

The app runs locally without external keys by using explicit fallback adapters. Configure these environment variables to enable live integrations:

```text
OPENAI_API_KEY         Enables LangChain + OpenAI evidence summarization and structured extraction.
OPENAI_MODEL           Model used by LangChain ChatOpenAI.
TAVILY_API_KEY         Enables Tavily web search for news/ESG enrichment.
SERPAPI_API_KEY        Alternative web search provider.
NEWS_API_KEY           Enables NewsAPI article search.
SEC_USER_AGENT         Required user agent for SEC EDGAR filing lookup.
SANCTIONS_PROVIDER_*   Enables a configured sanctions screening provider.
```

OCR behavior:

- PDF extraction uses `pypdf` when local files exist in storage.
- Image OCR uses `pytesseract` and `Pillow` when installed and when the Tesseract binary is available on the machine.
- If files or OCR dependencies are missing, the agent records a metadata-only fallback result instead of failing the workflow.
