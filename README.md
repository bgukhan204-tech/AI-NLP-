# Enterprise RAG with RBAC

Secure enterprise knowledge assistant using document RAG, Qdrant, Groq, and role-based access control.

## Architecture

Documents -> extraction/chunking -> Sentence Transformer embeddings -> Qdrant -> RBAC metadata filter -> authorized context -> Groq LLM -> answer + sources.

Authentication uses PBKDF2 password hashes and short-lived JWTs. Roles and department permissions are defined in `config/rbac.yaml`. Document indexing is restricted to `hr_admin` in the demo UI.

## Run locally

1. Create `.env` from `.env.example`.
2. Set a strong `JWT_SECRET` and a valid `GROQ_API_KEY`.
3. For Qdrant Cloud, set `QDRANT_URL` and `QDRANT_API_KEY`; otherwise local storage is used at `QDRANT_PATH`.
4. Install dependencies: `pip install -r requirements.txt`.
5. Start: `streamlit run app.py`.

## Demo accounts

The repository contains PBKDF2 hashes for demo accounts only. Replace them before any real deployment. Do not store real passwords or API keys in Git.

## Security model

Authorization is enforced at vector retrieval using Qdrant payload filtering. Only chunks whose `department` is in the authenticated user's role permissions are passed to the LLM. The LLM is instructed to answer only from the authorized context.

For a high-compliance production deployment, move users/roles from YAML to a managed database/identity provider and use a dedicated API service behind HTTPS, with centralized audit logging, rate limiting, secret management, and monitoring.
