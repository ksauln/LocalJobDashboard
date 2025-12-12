import streamlit as st

import app  # noqa: F401  # ensure project root is on sys.path
from src.storage.sqlite import get_conn, wipe_jobs, wipe_resumes
from src.storage.vectordb import clear_collection
from src import config
from app.app import ensure_agents, load_collections

ensure_agents()
jobs_collection, resumes_collection = load_collections()

st.title("Settings & Logs")
st.write("Configuration")
st.json({
    "OLLAMA_BASE_URL": config.OLLAMA_BASE_URL,
    "OLLAMA_MODEL": config.OLLAMA_MODEL,
    "OLLAMA_EMBED_MODEL": config.OLLAMA_EMBED_MODEL,
    "SQLITE_PATH": config.SQLITE_PATH,
    "VDB_JOBS_DIR": config.VDB_JOBS_DIR,
    "VDB_RESUMES_DIR": config.VDB_RESUMES_DIR,
    "JOB_SOURCES": config.JOB_SOURCES,
})

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
