import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app  # noqa: F401  # ensure project root is on sys.path
from app.app import ensure_agents
from src.storage.sqlite import list_jobs

ensure_agents()

st.title("Job Search")
query = st.text_input("Search query")
limit = st.slider("Limit per source", 5, 100, 20)
if st.button("Run JobScout") and query:
    summary = st.session_state.agents["jobs"].run_search(query, limit_per_source=limit)
    st.success(summary)

jobs = list_jobs()
st.dataframe(jobs)
