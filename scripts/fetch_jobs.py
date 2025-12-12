import argparse

from src.storage.vectordb import get_chroma_client, get_or_create_collection
from src.storage.sqlite import init_db
from src.agents.job_scout import JobScoutAgent
import src.config as config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()
    init_db()
    client = get_chroma_client(config.VDB_JOBS_DIR)
    collection = get_or_create_collection(client, "jobs")
    agent = JobScoutAgent(collection)
    summary = agent.run_search(args.query, limit_per_source=args.limit)
    print(summary)


if __name__ == "__main__":
    main()
