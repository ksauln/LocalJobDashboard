import streamlit as st

from src.storage.sqlite import get_conn
from src import config
from src.app import ensure_agents

ensure_agents()

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
