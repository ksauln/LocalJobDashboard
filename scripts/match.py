import argparse

from src.storage.vectordb import get_chroma_client, get_or_create_collection
from src.storage.sqlite import init_db
from src.agents.match_rank import MatchRankAgent
import src.config as config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume_id", required=True)
    parser.add_argument("--top_k", type=int, default=25)
    parser.add_argument("--no_llm", action="store_true")
    args = parser.parse_args()
    init_db()
    resumes_client = get_chroma_client(config.VDB_RESUMES_DIR)
    jobs_client = get_chroma_client(config.VDB_JOBS_DIR)
    resume_col = get_or_create_collection(resumes_client, "resumes")
    job_col = get_or_create_collection(jobs_client, "jobs")
    agent = MatchRankAgent(resume_col, job_col)
    results = agent.rank(args.resume_id, top_k=args.top_k, use_llm_rerank=not args.no_llm)
    print(results)


if __name__ == "__main__":
    main()
