import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app  # noqa: F401  # ensure project root is on sys.path
from app.app import ensure_agents, load_collections
from src.storage import vectordb
from src.storage.sqlite import list_resumes


ensure_agents()
resumes_col = load_collections()[1]


st.title("Resumes")
uploaded = st.file_uploader("Upload resume", type=["pdf", "docx", "txt"])
if uploaded and st.button("Ingest"):
    path = f"/tmp/{uploaded.name}"
    with open(path, "wb") as f:
        f.write(uploaded.getbuffer())
    resume_id = st.session_state.agents["resume"].ingest(path)
    st.success(f"Ingested resume: {uploaded.name} ({resume_id})")

resumes = list_resumes()
resume_map = {r["resume_id"]: r for r in resumes}
resume_ids = list(resume_map.keys())
selected = st.selectbox(
    "Select resume",
    resume_ids,
    format_func=lambda rid: resume_map[rid]["filename"] or rid,
)
if selected:
    chunks = vectordb.get(resumes_col, where_filter={"resume_id": selected})
    st.write(f"Chunks: {len(chunks.get('ids', []))}")
