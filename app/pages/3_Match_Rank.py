import streamlit as st

from src.storage.sqlite import list_resumes
from src.app import ensure_agents

ensure_agents()

st.title("Match & Rank")
resumes = list_resumes()
resume_ids = [r["resume_id"] for r in resumes]
selected = st.selectbox("Select resume", resume_ids)
top_k = st.slider("Top K", 5, 50, 25)
use_llm = st.checkbox("Use LLM explanations", value=True)

if st.button("Rank") and selected:
    results = st.session_state.agents["match"].rank(selected, top_k=top_k, use_llm_rerank=use_llm)
    st.session_state.match_results = results

for job in st.session_state.get("match_results", []):
    st.subheader(f"{job['title']} at {job['company']} ({job.get('source')})")
    st.write(f"Score: {job.get('hybrid_score')} Distance: {job.get('distance')}")
    st.write(job.get("description", "")[:500])
    if job.get("match"):
        st.write(job["match"])
    st.markdown(f"[Link]({job.get('url')})")
