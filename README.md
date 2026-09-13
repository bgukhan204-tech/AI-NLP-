# Enterprise RAG with RBAC

A production-oriented enterprise knowledge assistant using document RAG, Qdrant, Groq, PostgreSQL, JWT authentication, optional Google/Microsoft OIDC SSO, and centralized audit logging.

## Architecture

```text
User
  -> Password login OR Google/Microsoft SSO
  -> PostgreSQL user + role lookup
  -> Short-lived application JWT
  -> Question
  -> Embedding model (loaded lazily)
  -> Qdrant semantic search + department RBAC filter
  -> Authorized document chunks only
  -> Groq LLM
  -> Grounded answer + source attribution
  -> Audit event in PostgreSQL
```

## Implemented features

- PDF/TXT/CSV/Excel ingestion and chunking
- Sentence Transformer embeddings with lazy first-use loading
- Qdrant vector storage and semantic retrieval
- RBAC enforcement inside the vector-search filter
- Groq grounded generation with source attribution
- PBKDF2-SHA256 password verification
- Short-lived JWT access tokens
- PostgreSQL-backed users and active-role validation
- Login failure/rate-limit protection
- HR-admin-only document indexing
- HR-admin document inventory and document deletion
- HR-admin audit-log dashboard
- Audit events for login, logout, queries, indexing, deletion and denied SSO access
- Google and Microsoft OIDC bridge with PostgreSQL provisioning
- Unit/integration tests and GitHub Actions CI
- Docker + Render deployment support
- Environment-based secrets; no real credentials in Git

## Local setup

### 1. Configure PostgreSQL

Set `DATABASE_URL`, install dependencies, then initialize the schema:

```bash
python scripts/init_db.py
```

Create production users with:

```bash
python scripts/create_user.py
```

Roles and department permissions are defined in `config/rbac.yaml`.

### 2. Configure environment variables

Copy `.env.example` to `.env` and set at minimum:

- `DATABASE_URL`
- `JWT_SECRET`
- `GROQ_API_KEY`
- `QDRANT_URL`
- `QDRANT_API_KEY`

For SSO, also configure the Google/Microsoft OIDC variables documented in `.env.example`.

Never commit `.env`, passwords, JWT secrets, OAuth secrets or API keys.

### 3. Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

The embedding model is intentionally loaded only when the first document is indexed or the first question is asked. This keeps the initial Streamlit/Render startup lighter.

### 4. Test

```bash
pytest -q
```

GitHub Actions also starts PostgreSQL, checks imports, compiles the application, runs tests and builds the Docker image.

## Enterprise SSO

The application uses Streamlit's OIDC support for the identity-provider login, then maps the authenticated identity to an active PostgreSQL user. Authentication by Google or Microsoft alone does **not** grant application access; the account must be provisioned with an application role.

The production callback URI is:

```text
https://YOUR-RENDER-SERVICE.onrender.com/oauth2callback
```

Configure that exact URI in the selected identity provider and set the corresponding Render environment variables. `scripts/generate_oidc_secrets.py` creates the runtime Streamlit OIDC configuration from those environment variables.

## Deployment

The included Dockerfile binds Streamlit to `0.0.0.0` and Render's `$PORT`. This is important for Render's reverse proxy and avoids the common 502 caused by a service listening on the wrong port.

Render still requires external credentials for PostgreSQL, Groq, Qdrant and any enabled SSO provider. Keep all secrets in Render environment variables rather than Git.

## Security model

Authorization is enforced before LLM generation. Qdrant receives the authenticated user's allowed departments as a metadata filter, so unauthorized chunks are not returned to the application or sent to the LLM. PostgreSQL is the source of truth for active users and roles, while `config/rbac.yaml` defines the application's role-to-department policy.

Audit logs intentionally store metadata such as question length and source count rather than the full user question by default.

## Current production checklist

- [x] RAG pipeline
- [x] Qdrant integration
- [x] PostgreSQL user store
- [x] RBAC enforcement
- [x] Password + JWT authentication
- [x] Google/Microsoft OIDC integration
- [x] Document administration
- [x] Audit dashboard
- [x] Docker/Render port configuration
- [x] CI/test automation
- [ ] Configure production Qdrant credentials
- [ ] Configure production Google/Microsoft credentials if SSO is needed
- [ ] Provision real application users
- [ ] Run end-to-end production tests after Render redeploy
- [ ] Add production backups, monitoring/alerts and dependency/security scanning
