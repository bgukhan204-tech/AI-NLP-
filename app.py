import streamlit as st

from src.rag import EnterpriseRAG
from src.rbac import authenticate

st.set_page_config(page_title="Enterprise RAG", page_icon="🔐")
st.title("🔐 Enterprise AI Knowledge Assistant")
st.caption("RAG retrieval is filtered by the authenticated user's allowed departments.")

@st.cache_resource
def get_rag() -> EnterpriseRAG:
    return EnterpriseRAG()

with st.sidebar:
    st.header("User")
    username = st.selectbox("Login as", ["employee1", "manager1", "hradmin"])
    try:
        session = authenticate(username)
        st.success(f"Role: {session['role']}")
        st.write("Allowed departments:")
        st.write(session["allowed_departments"])
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

st.subheader("Ask the company knowledge base")
question = st.text_input("Question", placeholder="What is our leave policy?")

if st.button("Ask AI", type="primary") and question.strip():
    with st.spinner("Searching authorized documents..."):
        result = get_rag().ask(
            question.strip(),
            session["allowed_departments"],
        )
    st.markdown("### Answer")
    st.write(result["answer"])

    if result["sources"]:
        st.markdown("### Retrieved sources")
        for source in result["sources"]:
            st.write(
                f"- {source['source']} · {source['department']} · "
                f"score={source['score']:.3f}"
            )

st.divider()
st.subheader("Index a document")
st.caption("Demo/admin indexing UI. Assign a department before indexing.")

uploaded = st.file_uploader("PDF, TXT, CSV or Excel", type=["pdf", "txt", "csv", "xlsx", "xls"])
department = st.selectbox(
    "Department",
    ["general", "engineering", "hr_public", "finance", "management", "hr_private"],
)

if uploaded and st.button("Index document"):
    import tempfile
    from pathlib import Path

    suffix = Path(uploaded.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.getvalue())
        tmp_path = tmp.name

    with st.spinner("Chunking, embedding and indexing..."):
        count = get_rag().index_document(tmp_path, department)

    st.success(f"Indexed {count} chunks from {uploaded.name}.")
