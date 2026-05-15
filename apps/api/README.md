# Risk Beacon API

## Local Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --app-dir apps/api
```

Seed users all use the password:

```text
Password123!
```

Example users:

```text
buyer@example.com
supplier@example.com
risk@example.com
approver@example.com
admin@example.com
auditor@example.com
```
