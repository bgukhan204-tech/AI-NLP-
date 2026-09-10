import os
import time
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from src.auth import decode_token, issue_token
from src.rag import EnterpriseRAG
from src.rbac import authenticate, session_from_claims

st.set_page_config(page_title="Enterprise RAG", page_icon="🔐")

@st.cache_resource
def get_rag() -> EnterpriseRAG:
    return EnterpriseRAG()


def login() -> None:
    st.title("🔐 Enterprise AI Knowledge Assistant")
    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", type="primary")
    if submitted:
        now = time.time()
        attempts = st.session_state.get("login_attempts", [])
        attempts = [t for t in attempts if now - t < 300]
        if len(attempts) >= 5:
            st.error("Too many failed login attempts. Try again later.")
            return
        try:
            session = authenticate(username.strip(), password)
            st.session_state["access_token"] = issue_token(session)
            st.session_state["session"] = session
            st.rerun()
        except ValueError:
            attempts.append(now)
            st.session_state["login_attempts"] = attempts
            st.error("Invalid username or password")


if "access_token" not in st.session_state:
    login()
    st.stop()

try:
    claims = decode_token(st.session_state["access_token"])
    session = session_from_claims(claims)
except Exception:
    st.session_state.pop("access_token", None)
    st.session_state.pop("session", None)
    st.error("Your session has expired. Please sign in again.")
    st.stop()

with st.sidebar:
    st.header("Authenticated user")
    st.write(f"**{session['username']}**")
    st.write(f"Role: **{session['role']}**")
    st.write("Allowed departments:")
    st.write(session["allowed_departments"])
    if st.button("Sign out"):
        st.session_state.clear()
        st.rerun()

st.title("Enterprise AI Knowledge Assistant")
st.caption("RAG retrieval is filtered by the authenticated user's RBAC permissions before LLM generation.")

st.subheader("Ask the company knowledge base")
question = st.text_input("Question", placeholder="What is our leave policy?")

if st.button("Ask AI", type="primary") and question.strip():
    with st.spinner("Searching authorized documents..."):
        result = get_rag().ask(question.strip(), session["allowed_departments"])
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
        with st.spinner("Chunking, embedding and indexing..."):
            count = get_rag().index_document(tmp_path, department)
        os.unlink(tmp_path)
        st.success(f"Indexed {count} chunks from {uploaded.name}.")
