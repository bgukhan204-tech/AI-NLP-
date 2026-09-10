# Enterprise RAG with RBAC

A secure enterprise knowledge assistant using document RAG, Qdrant, Groq, PostgreSQL, JWT authentication, optional enterprise OIDC SSO, and centralized audit logging.

## Production architecture

```text
User
  -> Password login OR OIDC SSO
  -> PostgreSQL user + role lookup
  -> Short-lived JWT
  -> Question
  -> Sentence Transformer embedding
  -> Qdrant vector search + department filter
  -> Authorized document chunks only
  -> Groq LLM
  -> Answer + source attribution
  -> Audit event in PostgreSQL
```

## Implemented production features

- PDF/TXT/CSV/Excel ingestion and chunking
- Sentence Transformer embeddings
- Qdrant vector storage and semantic retrieval
- RBAC enforcement in the Qdrant retrieval filter
- Groq LLM generation with grounded-answer prompt
- PBKDF2-SHA256 password verification
- Short-lived JWT access tokens
- PostgreSQL-backed application users
- Active-user and role validation on every token refresh/use
- Login failure/rate-limit protection in the Streamlit UI
- HR admin-only document indexing
- Centralized audit events for login, logout, queries, indexing and denied SSO access
- Automated unit tests and PostgreSQL integration tests
- GitHub Actions CI with a PostgreSQL service
- Optional OpenID Connect / enterprise SSO bridge
- Docker image and Render deployment blueprint
- Environment-based secret configuration; no real secrets belong in Git

## Production setup

### 1. Configure PostgreSQL

Set `DATABASE_URL`, install dependencies, then run:

```bash
python scripts/init_db.py
```

For new production users, prefer the secure provisioning CLI:

```bash
python scripts/create_user.py
```

The application roles and department permissions remain in `config/rbac.yaml`; user credentials are stored in PostgreSQL.

### 2. Configure secrets

Copy `.env.example` to `.env` locally and set:

- `DATABASE_URL`
- `JWT_SECRET` (use a long random value)
- `GROQ_API_KEY`
- `QDRANT_URL` and `QDRANT_API_KEY` for Qdrant Cloud

Never commit `.env`, passwords, JWT secrets, or API keys.

### 3. Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

### 4. Run tests

```bash
pytest -q
```

The CI workflow automatically starts PostgreSQL and runs both unit and integration tests.

## Enterprise SSO

Set `OIDC_ENABLED=true` and configure Streamlit's OIDC secrets for the selected provider. The identity provider authenticates the person; PostgreSQL must still contain an active provisioned user with the required application role.

Example `.streamlit/secrets.toml` structure:

```toml
[auth]
redirect_uri = "https://YOUR-DOMAIN/oauth2callback"
cookie_secret = "GENERATE_A_LONG_RANDOM_VALUE"
client_id = "YOUR_OIDC_CLIENT_ID"
client_secret = "YOUR_OIDC_CLIENT_SECRET"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

For Microsoft Entra ID, Okta, Auth0, or another enterprise IdP, use that provider's OIDC discovery URL and register the exact production redirect URI.

Do not commit `secrets.toml`.

## Deployment

`render.yaml` provisions a Render web service and PostgreSQL database. Before deploying, provide the external Qdrant and Groq secrets in the hosting platform. The application can then be deployed from the repository.

Production hardening should also include HTTPS at the hosting edge, managed secrets, backups/retention policies for PostgreSQL, centralized log/alert monitoring, and regular dependency/security scanning.

## Security model

Authorization is enforced before LLM generation. Qdrant receives the authenticated user's allowed departments as a metadata filter, so unauthorized chunks are not returned to the application or sent to the LLM. PostgreSQL is the source of truth for active users and roles, while the YAML file defines the application's role-to-department policy.
