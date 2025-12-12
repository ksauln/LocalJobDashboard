import sys
from pathlib import Path
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:  # ensure src package is importable when run via Streamlit
    sys.path.insert(0, str(PROJECT_ROOT))

cache_resource = getattr(st, "cache_resource", st.experimental_singleton)

from src import config
from src.logging_config import setup_logging
from src.storage.sqlite import init_db, list_jobs, list_resumes
from src.storage.vectordb import get_chroma_client, get_or_create_collection
from src.agents.resume_ingest import ResumeIngestAgent
from src.agents.job_scout import JobScoutAgent
from src.agents.match_rank import MatchRankAgent
from src.tools.job_sources import get_sources_from_env
from src.llm import ollama_client

setup_logging()


@cache_resource
def load_collections():
    jobs_client = get_chroma_client(config.VDB_JOBS_DIR)
    resumes_client = get_chroma_client(config.VDB_RESUMES_DIR)
    return (
        get_or_create_collection(jobs_client, "jobs"),
        get_or_create_collection(resumes_client, "resumes"),
    )


def ensure_agents():
    if "agents" not in st.session_state:
        jobs_col, resumes_col = load_collections()
        st.session_state.agents = {
            "resume": ResumeIngestAgent(resumes_col),
            "jobs": JobScoutAgent(jobs_col),
            "match": MatchRankAgent(resumes_col, jobs_col),
        }


def sidebar_status():
    st.sidebar.header("System Status")
    try:
        ollama_client.embed("ping")
        st.sidebar.success("Ollama reachable")
    except Exception as exc:  # pragma: no cover
        st.sidebar.error(f"Ollama issue: {exc}")
    st.sidebar.write(f"Resumes: {len(list_resumes())}")
    st.sidebar.write(f"Jobs: {len(list_jobs())}")
    st.sidebar.write(f"Sources: {[s.name for s in get_sources_from_env()]}")


def main():
    st.set_page_config(page_title="Local Job Dashboard", page_icon="🧭", layout="wide")
    st.title("Local Agentic Job Dashboard")
    init_db()
    ensure_agents()
    sidebar_status()
    st.write("Use the sidebar to navigate pages: Resumes, Job Search, Match & Rank, Settings & Logs.")


if __name__ == "__main__":
    main()
