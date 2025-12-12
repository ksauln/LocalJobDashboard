import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app  # noqa: F401  # ensure project root is on sys.path
from app.app import ensure_agents
from src.storage.sqlite import list_resumes
from src.tools.parsing import strip_html

ensure_agents()

st.title("Match & Rank")
resumes = list_resumes()
resume_map = {r["resume_id"]: r for r in resumes}
resume_ids = list(resume_map.keys())
if not resume_ids:
    st.info("Upload a resume first from the Resumes page.")
    st.stop()

selected = st.selectbox(
    "Select resume",
    resume_ids,
    format_func=lambda rid: resume_map[rid]["filename"] or rid,
)
top_k = st.slider("Top K", 5, 50, 25)
use_llm = st.checkbox("Use LLM explanations", value=True)

if st.button("Rank") and selected:
    results = st.session_state.agents["match"].rank(selected, top_k=top_k, use_llm_rerank=use_llm)
    st.session_state.match_results = results

if not st.session_state.get("match_results"):
    st.info("No matches yet. Make sure jobs are ingested and try ranking.")

for job in st.session_state.get("match_results", []):
    st.subheader(f"{job['title']} at {job['company']} ({job.get('source')})")
    cols = st.columns(3)
    cols[0].metric("Hybrid score", f"{job.get('hybrid_score', 0):.1f}")
    cols[1].metric("Vector distance", f"{job.get('distance', 0):.3f}")
    if job.get("match"):
        cols[2].metric("LLM score", f"{job['match'].get('score_0_to_100', 0):.1f}")
    desc = strip_html(job.get("description", ""))[:800]
    st.write(desc)
    if job.get("match"):
        match = job["match"]
        if match.get("strengths"):
            st.write("**Strengths:** " + "; ".join(match["strengths"]))
        if match.get("gaps"):
            st.write("**Gaps:** " + "; ".join(match["gaps"]))
        if match.get("short_reason"):
            st.write(f"**Why:** {match['short_reason']}")
    st.markdown(f"[Link]({job.get('url')})")
    if hasattr(st, "divider"):
        st.divider()
    else:  # older Streamlit fallback
        st.markdown("---")
