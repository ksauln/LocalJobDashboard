import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app  # noqa: F401  # ensure project root is on sys.path
from app.app import ensure_agents, load_collections
from src import config
from src.llm import get_active_config, set_runtime_llm_config
from src.storage.sqlite import get_conn, wipe_jobs, wipe_resumes
from src.storage.vectordb import clear_collection

ensure_agents()
jobs_collection, resumes_collection = load_collections()

st.title("Settings & Logs")
st.header("LLM Provider")
active_cfg = get_active_config()
with st.form("llm-config"):
    provider = st.selectbox("Provider", ["ollama", "openai"], index=0 if active_cfg.provider == "ollama" else 1)
    base_url = st.text_input(
        "Base URL",
        value=active_cfg.base_url,
        help="For Ollama, include protocol and port. For OpenAI-compatible APIs, include the version path.",
    )
    col_a, col_b = st.columns(2)
    with col_a:
        model = st.text_input("Chat/Completion model", value=active_cfg.model)
    with col_b:
        embed_model = st.text_input("Embedding model", value=active_cfg.embed_model)
    api_key = st.text_input("API key (OpenAI-compatible)", value=active_cfg.api_key, type="password")
    submitted = st.form_submit_button("Save runtime settings")
    if submitted:
        set_runtime_llm_config(
            provider=provider,
            base_url=base_url,
            model=model,
            embed_model=embed_model,
            api_key=api_key,
        )
        st.success("LLM settings updated for this session.")

st.subheader("Current configuration (environment defaults)")
st.json(
    {
        "LLM_PROVIDER": config.LLM_PROVIDER,
        "OLLAMA_BASE_URL": config.OLLAMA_BASE_URL,
        "OLLAMA_MODEL": config.OLLAMA_MODEL,
        "OLLAMA_EMBED_MODEL": config.OLLAMA_EMBED_MODEL,
        "OPENAI_BASE_URL": config.OPENAI_BASE_URL,
        "OPENAI_MODEL": config.OPENAI_MODEL,
        "OPENAI_EMBED_MODEL": config.OPENAI_EMBED_MODEL,
        "SQLITE_PATH": config.SQLITE_PATH,
        "VDB_JOBS_DIR": config.VDB_JOBS_DIR,
        "VDB_RESUMES_DIR": config.VDB_RESUMES_DIR,
        "JOB_SOURCES": config.JOB_SOURCES,
    }
)

conn = get_conn()
st.subheader("Recent Job Runs")
st.dataframe(conn.execute("SELECT * FROM job_runs ORDER BY started_at DESC LIMIT 20").fetchall())

st.subheader("Recent Match Runs")
st.dataframe(conn.execute("SELECT * FROM match_runs ORDER BY started_at DESC LIMIT 20").fetchall())
conn.close()

st.subheader("Data Management")
st.caption("Danger zone: permanently delete stored records and vector embeddings.")
col1, col2 = st.columns(2)
with col1:
    if st.button("Clear jobs (SQLite + vectors)"):
        wipe_jobs()
        clear_collection(jobs_collection)
        st.success("Cleared jobs and job run logs; job vectors removed.")
with col2:
    if st.button("Clear resumes (SQLite + vectors)"):
        wipe_resumes()
        clear_collection(resumes_collection)
        st.success("Cleared resumes, match logs, and resume vectors.")
