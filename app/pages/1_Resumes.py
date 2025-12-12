import streamlit as st

from src.storage.sqlite import list_resumes
from src.storage import vectordb
from src.app import ensure_agents, load_collections


ensure_agents()
resumes_col = load_collections()[1]


st.title("Resumes")
uploaded = st.file_uploader("Upload resume", type=["pdf", "docx", "txt"])
if uploaded and st.button("Ingest"):
    path = f"/tmp/{uploaded.name}"
    with open(path, "wb") as f:
        f.write(uploaded.getbuffer())
    resume_id = st.session_state.agents["resume"].ingest(path)
    st.success(f"Ingested resume {resume_id}")

resumes = list_resumes()
resume_ids = [r["resume_id"] for r in resumes]
selected = st.selectbox("Select resume", resume_ids)
if selected:
    chunks = vectordb.get(resumes_col, where_filter={"resume_id": selected})
    st.write(f"Chunks: {len(chunks.get('ids', []))}")
