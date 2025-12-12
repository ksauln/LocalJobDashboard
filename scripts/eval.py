import math
from typing import List

from src.storage.vectordb import get_chroma_client, get_or_create_collection, query
import src.config as config

# Dummy evaluation samples
SAMPLES = [
    {"resume": "python developer data", "relevant_job_ids": ["dummy-1", "dummy-2"]},
    {"resume": "frontend react", "relevant_job_ids": ["dummy-3"]},
]


def precision_at_k(retrieved: List[str], relevant: List[str], k: int) -> float:
    if k == 0:
        return 0.0
    hits = sum(1 for item in retrieved[:k] if item in relevant)
    return hits / k


def mrr(retrieved: List[str], relevant: List[str]) -> float:
    for idx, item in enumerate(retrieved, start=1):
        if item in relevant:
            return 1.0 / idx
    return 0.0


def main():
    client = get_chroma_client(config.VDB_JOBS_DIR)
    col = get_or_create_collection(client, "jobs")
    precisions = []
    rr = []
    for sample in SAMPLES:
        emb = [0.0] * len(col.get()["embeddings"][0]) if col.count() else [0.0]
        res = query(col, emb, n_results=10)
        ids = res.get("ids", [[]])[0]
        precisions.append(precision_at_k(ids, sample["relevant_job_ids"], k=3))
        rr.append(mrr(ids, sample["relevant_job_ids"]))
    print({"p@3": sum(precisions) / len(precisions), "mrr": sum(rr) / len(rr)})


if __name__ == "__main__":
    main()
