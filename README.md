# Personal AI Operations Assistant (Web)

A secure web-based data manager that connects fragmented personal systems (email, documents, messages, statements, receipts, calendars) and surfaces **what needs attention now**.

## Security first (required)

This app stores sensitive data. Before using real data, you must configure:

- **Authentication** (implemented in this version)
- **Tenant/user isolation** (implemented: records are scoped per authenticated user)
- **Secrets via environment variables only**

## MVP features in this repo

- Auth endpoint for login and Bearer token issuance
- User-scoped record storage (tenant isolation by authenticated user)
- Secure item ingestion API
- Query endpoint to find relevant documents/records
- Alert engine for due dates, renewals, missing documents, and likely subscriptions
- Web dashboard for triage and natural-language querying
## What this solves

This project is built to address information overload by combining:

- **Unified ingestion** from multiple sources via connector adapters
- **Secure storage** with encrypted content-at-rest (application-layer encryption)
- **AI-powered retrieval** (semantic-style search + context cards)
- **Action detection engine** for due dates, pending submissions, renewals, and recurring charges
- **Operations dashboard** highlighting urgent and upcoming tasks

## MVP features in this repo

- Connector model (`email`, `chat`, `document`, `finance`, `calendar`, `manual`)
- Secure item ingestion API
- AI-like query endpoint to find relevant documents/records
- Alert engine for:
  - due dates
  - renewals
  - missing documents
  - likely subscriptions
- Web dashboard for quick triage and natural-language querying

## Tech stack

- **Backend:** FastAPI + SQLite
- **Frontend:** Vanilla HTML/CSS/JS dashboard
- **Security:** Fernet encryption + JWT auth
- **Security:** Fernet encryption key from environment variable

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export APP_SECRET_KEY="$(python - <<'PY'
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
PY
)"
export APP_JWT_SECRET="change-this-to-a-long-random-secret"
export APP_ADMIN_USERNAME="admin"
export APP_ADMIN_PASSWORD="change-this-password"

uvicorn app.main:app --reload
```

Then open:

- API docs: `http://127.0.0.1:8000/docs`
- App UI: `http://127.0.0.1:8000`

## Critical privacy notes

- Never commit `APP_SECRET_KEY`, `APP_JWT_SECRET`, or admin credentials.
- Use unique per-environment secrets and rotate them regularly.
- For production, use KMS/HSM, RBAC, audit logs, token revocation, and hardened OAuth providers.
## Security notes

- This MVP encrypts payload content before database storage.
- In production, use a managed KMS/HSM, strict RBAC, audit logging, and zero-trust connector tokens.
- Never store plaintext secrets in source code.

## Suggested next steps

- OAuth integrations: Google, Microsoft, Slack, WhatsApp Business, bank CSV importers
- Better AI pipeline: embeddings + vector DB + tool calling
- User auth + tenant isolation
- Notification channels (push/email/SMS)
