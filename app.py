import os
import time
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from src.audit import audit_event
from src.auth import decode_token, issue_token
from src.database import Database
from src.rag import EnterpriseRAG
from src.rbac import authenticate, session_from_claims
from src.sso import session_from_oidc_user

st.set_page_config(page_title="Enterprise RAG", page_icon="🔐")

@st.cache_resource
def get_rag() -> EnterpriseRAG:
    return EnterpriseRAG()

@st.cache_resource
def init_database() -> bool:
    Database().initialize()
    return True

try:
    init_database()
except Exception:
    st.error("Database is not configured or unavailable. Set DATABASE_URL and run scripts/init_db.py.")
    st.stop()


def oidc_provider_from_user(oidc_user: dict) -> str:
    issuer = str(oidc_user.get("iss", "")).lower()
    if "accounts.google.com" in issuer:
        return "google"
    if "microsoftonline.com" in issuer or "microsoft.com" in issuer:
        return "microsoft"
    return "oidc"


def complete_oidc_login() -> None:
    user = dict(st.user)
    provider = oidc_provider_from_user(user)
    try:
        session = session_from_oidc_user(user)
        st.session_state["access_token"] = issue_token(session)
        st.session_state["session"] = session
        st.session_state["auth_method"] = provider
        audit_event(
            "login_success",
            username=session["username"],
            role=session["role"],
            details={"method": provider},
        )
        st.rerun()
    except ValueError as exc:
        audit_event("sso_user_denied", details={"provider": provider, "reason": str(exc)})
        st.error("Your SSO account is not provisioned for this application.")
        st.stop()


def regular_login() -> None:
    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", type="primary")
    if submitted:
        now = time.time()
        attempts = [t for t in st.session_state.get("login_attempts", []) if now - t < 300]
        if len(attempts) >= 5:
            audit_event("login_rate_limited", username=username.strip() or None)
            st.error("Too many failed login attempts. Try again later.")
            return
        try:
            session = authenticate(username.strip(), password)
            st.session_state["access_token"] = issue_token(session)
            st.session_state["session"] = session
            st.session_state["auth_method"] = "password"
            st.session_state["login_attempts"] = []
            audit_event("login_success", username=session["username"], role=session["role"], details={"method": "password"})
            st.rerun()
        except ValueError:
            attempts.append(now)
            st.session_state["login_attempts"] = attempts
            audit_event("login_failure", username=username.strip() or None, details={"method": "password"})
            st.error("Invalid username or password")


def login() -> None:
    st.title("🔐 Enterprise AI Knowledge Assistant")
    oidc_enabled = os.getenv("OIDC_ENABLED", "true").lower() == "true"
    google_enabled = bool(os.getenv("GOOGLE_CLIENT_ID", "").strip() and os.getenv("GOOGLE_CLIENT_SECRET", "").strip())
    microsoft_enabled = bool(
        os.getenv("MICROSOFT_CLIENT_ID", "").strip()
        and os.getenv("MICROSOFT_CLIENT_SECRET", "").strip()
        and os.getenv("MICROSOFT_TENANT_ID", "").strip()
    )

    if oidc_enabled and (google_enabled or microsoft_enabled):
        st.subheader("Enterprise SSO")
        if google_enabled and st.button("Sign in with Google", type="primary"):
            st.login("google")
        if microsoft_enabled and st.button("Sign in with Microsoft"):
            st.login("microsoft")

        if getattr(st.user, "is_logged_in", False):
            complete_oidc_login()
        st.divider()

    st.subheader("Password login")
    regular_login()


if "access_token" not in st.session_state:
    login()
    st.stop()

try:
    claims = decode_token(st.session_state["access_token"])
    session = session_from_claims(claims)
except Exception:
    st.session_state.pop("access_token", None)
    st.session_state.pop("session", None)
    audit_event("session_expired")
    st.error("Your session has expired. Please sign in again.")
    st.stop()

with st.sidebar:
    st.header("Authenticated user")
    st.write(f"**{session['username']}**")
    st.write(f"Role: **{session['role']}**")
    st.write(f"Auth: **{st.session_state.get('auth_method', 'password')}**")
    st.write("Allowed departments:")
    st.write(session["allowed_departments"])
    if st.button("Sign out"):
        audit_event("logout", username=session["username"], role=session["role"])
        if st.session_state.get("auth_method") in {"google", "microsoft", "oidc"} and getattr(st.user, "is_logged_in", False):
            st.logout()
        st.session_state.clear()
        st.rerun()

st.title("Enterprise AI Knowledge Assistant")
st.caption("RAG retrieval is filtered by the authenticated user's RBAC permissions before LLM generation.")

st.subheader("Ask the company knowledge base")
question = st.text_input("Question", placeholder="What is our leave policy?")

if st.button("Ask AI", type="primary") and question.strip():
    with st.spinner("Searching authorized documents..."):
        result = get_rag().ask(question.strip(), session["allowed_departments"])
    audit_event(
        "rag_query",
        username=session["username"],
        role=session["role"],
        details={"question_length": len(question.strip()), "source_count": len(result["sources"])},
    )
    st.markdown("### Answer")
    st.write(result["answer"])
    if result["sources"]:
        st.markdown("### Retrieved sources")
        for source in result["sources"]:
            st.write(f"- {source['source']} · {source['department']} · score={source['score']:.3f}")

if session["role"] == "hr_admin":
    st.divider()
    st.subheader("Document administration")
    uploaded = st.file_uploader("PDF, TXT, CSV or Excel", type=["pdf", "txt", "csv", "xlsx", "xls"])
    department = st.selectbox("Department", ["general", "engineering", "hr_public", "finance", "management", "hr_private"])
    if uploaded and st.button("Index document"):
        import tempfile
        from pathlib import Path
        suffix = Path(uploaded.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded.getvalue())
            tmp_path = tmp.name
        try:
            with st.spinner("Chunking, embedding and indexing..."):
                count = get_rag().index_document(tmp_path, department)
            audit_event(
                "document_indexed",
                username=session["username"],
                role=session["role"],
                details={"filename": uploaded.name, "department": department, "chunks": count},
            )
            st.success(f"Indexed {count} chunks from {uploaded.name}.")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
