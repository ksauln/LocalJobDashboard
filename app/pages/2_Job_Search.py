import streamlit as st

from src.storage.sqlite import list_jobs
from src.app import ensure_agents

ensure_agents()

st.title("Job Search")
query = st.text_input("Search query")
limit = st.slider("Limit per source", 5, 100, 20)
if st.button("Run JobScout") and query:
    summary = st.session_state.agents["jobs"].run_search(query, limit_per_source=limit)
    st.success(summary)

jobs = list_jobs()
st.dataframe(jobs)
