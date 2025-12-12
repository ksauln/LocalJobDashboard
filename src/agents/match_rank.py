import json
import logging
import uuid
from datetime import datetime
from typing import List

from ..llm import ollama_client
from ..storage import vectordb
from ..storage.sqlite import log_match_run
from ..tools.scoring import distance_to_score, hybrid_score, keyword_overlap

logger = logging.getLogger(__name__)


class MatchRankAgent:
    def __init__(self, resume_collection, job_collection):
        self.resume_collection = resume_collection
        self.job_collection = job_collection

    def _resume_query_text(self, resume_id: str, top_n: int = 3) -> str:
        res = vectordb.get(self.resume_collection, where_filter={"resume_id": resume_id}, limit=top_n)
        docs = res.get("documents", [])
        return "\n".join(docs)

    def _llm_rerank(self, resume_text: str, jobs: List[dict]) -> dict:
        prompt = (
            "Given the resume text and job postings, return a JSON list (no code fences) "
            "with up to 10 items. Each item has job_id, score_0_to_100, strengths (list), gaps (list), short_reason."
        )
        messages = [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": json.dumps({"resume": resume_text, "jobs": jobs}),
            },
        ]
        raw = ollama_client.chat(messages)
        try:
            cleaned = raw.strip().strip("`")
            return {item["job_id"]: item for item in json.loads(cleaned)}
        except Exception:  # pragma: no cover
            logger.warning("LLM rerank parse failed: %s", raw)
            return {}

    def rank(self, resume_id: str, top_k: int = 25, use_llm_rerank: bool = True):
        run_id = str(uuid.uuid4())
        started = datetime.utcnow().isoformat()
        resume_text = self._resume_query_text(resume_id)
        query_embedding = ollama_client.embed(resume_text)
        results = vectordb.query(self.job_collection, query_embedding, n_results=top_k)
        jobs = []
        for idx, job_id in enumerate(results.get("ids", [[]])[0]):
            meta = results.get("metadatas", [[]])[0][idx]
            distance = results.get("distances", [[]])[0][idx]
            distance_score = distance_to_score(distance)
            keyword_score = keyword_overlap(resume_text, results.get("documents", [[]])[0][idx])
            final_score = hybrid_score(distance_score, keyword_score)
            jobs.append(
                {
                    "job_id": job_id,
                    "title": meta.get("title"),
                    "company": meta.get("company"),
                    "url": meta.get("url"),
                    "source": meta.get("source"),
                    "posted_at": meta.get("posted_at"),
                    "distance": distance,
                    "hybrid_score": final_score,
                    "description": meta.get("description", ""),
                }
            )
        llm_matches = {}
        if use_llm_rerank and jobs:
            llm_matches = self._llm_rerank(resume_text, jobs)
            for job in jobs:
                if job["job_id"] in llm_matches:
                    job["match"] = llm_matches[job["job_id"]]
        finished = datetime.utcnow().isoformat()
        log_match_run(run_id, resume_id, started, finished, top_k, "llm" if use_llm_rerank else "no-llm")
        logger.info("Match rank run %s completed", run_id)
        return jobs
