import argparse

from src.storage.vectordb import get_chroma_client, get_or_create_collection
from src.storage.sqlite import init_db
from src.agents.resume_ingest import ResumeIngestAgent
import src.config as config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    args = parser.parse_args()
    init_db()
    client = get_chroma_client(config.VDB_RESUMES_DIR)
    collection = get_or_create_collection(client, "resumes")
    agent = ResumeIngestAgent(collection)
    resume_id = agent.ingest(args.file)
    print(f"Ingested {resume_id}")


if __name__ == "__main__":
    main()
