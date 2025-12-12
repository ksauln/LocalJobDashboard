import json
import logging
import re
import uuid
from datetime import datetime
from typing import List, Optional

from ..llm import ollama_client
from ..storage import vectordb
from ..storage.sqlite import log_match_run
from ..tools.parsing import strip_html
from ..tools.scoring import distance_to_score, hybrid_score, keyword_overlap

logger = logging.getLogger(__name__)


class MatchRankAgent:
    def __init__(self, resume_collection, job_collection):
        self.resume_collection = resume_collection
        self.job_collection = job_collection
        self.max_embed_chars = 4000
        self.max_llm_resume_chars = 4000
        self.max_llm_job_chars = 1200

    def _resume_query_text(self, resume_id: str, top_n: int = 3) -> str:
        res = vectordb.get(self.resume_collection, where_filter={"resume_id": resume_id}, limit=top_n)
        docs = res.get("documents", [])
        return "\n".join(docs)

    def _llm_rerank(self, resume_text: str, jobs: List[dict]) -> dict:
        base_prompt = (
            "You are a ranking function. Return only a JSON array (no code fences, no prose) with up to 10 items. "
            "Use this shape exactly: "
            '[{"job_id": "string", "score_0_to_100": 0-100 integer, "strengths": ["string"], '
            '"gaps": ["string"], "short_reason": "string"}]. If there are no matches, return [].'
        )
        prompts = [
            base_prompt,
            base_prompt + " Respond ONLY with the JSON array. Begin with '[' and end with ']'.",
        ]
        trimmed_jobs = []
        for job in jobs:
            trimmed_jobs.append(
                {
                    **job,
                    "description": (job.get("description") or "")[: self.max_llm_job_chars],
                }
        )
        parsed = None
        last_raw = ""
        for prompt in prompts:
            messages = [
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": json.dumps({"resume": resume_text[: self.max_llm_resume_chars], "jobs": trimmed_jobs}),
                },
            ]
            last_raw = ollama_client.chat(messages)
            parsed = self._parse_llm_json(last_raw)
            if parsed is not None:
                break
        if parsed is None:  # pragma: no cover - resiliency for non-JSON model output
            logger.warning("LLM rerank parse failed after retries: %s", last_raw)
            return {}
        return {item["job_id"]: item for item in parsed if item.get("job_id")}

    @staticmethod
    def _parse_llm_json(raw: str) -> Optional[List[dict]]:
        """Best-effort extraction of a JSON array from the model output."""
        cleaned = raw.strip().strip("`")
        if not cleaned:
            return []
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"(\[.*\])", cleaned, flags=re.S)
            if not match:
                return None
            try:
                data = json.loads(match.group(1))
            except json.JSONDecodeError:
                return None
        return data if isinstance(data, list) else None

    def rank(self, resume_id: str, top_k: int = 25, use_llm_rerank: bool = True):
        run_id = str(uuid.uuid4())
        started = datetime.utcnow().isoformat()
        resume_text = self._resume_query_text(resume_id)
        try:
            query_embedding = ollama_client.embed(resume_text[: self.max_embed_chars])
        except ollama_client.OllamaError as exc:
            logger.error("Embedding resume failed: %s", exc)
            raise
        if not query_embedding:
            logger.warning("Empty embedding returned for resume %s; skipping match", resume_id)
            return []
        try:
            results = vectordb.query(self.job_collection, query_embedding, n_results=top_k)
        except IndexError:
            logger.warning("Vector DB query failed (likely empty index); skipping match")
            return []
        if not results.get("ids") or not results["ids"][0]:
            logger.info("No jobs in vector DB to match against")
            return []
        jobs = []
        for idx, job_id in enumerate(results.get("ids", [[]])[0]):
            meta = results.get("metadatas", [[]])[0][idx]
            distance = results.get("distances", [[]])[0][idx]
            doc_text = strip_html(results.get("documents", [[]])[0][idx])
            desc = strip_html(meta.get("description", ""))
            distance_score = distance_to_score(distance)
            keyword_score = keyword_overlap(resume_text, doc_text)
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
                    "description": desc or doc_text,
                    "keyword_score": keyword_score,
                    "distance_score": distance_score,
                }
            )
        llm_matches = {}
        if use_llm_rerank and jobs:
            try:
                llm_matches = self._llm_rerank(resume_text, jobs)
            except ollama_client.OllamaError as exc:
                logger.warning("LLM rerank skipped due to Ollama error: %s", exc)
                llm_matches = {}
            for job in jobs:
                if job["job_id"] in llm_matches:
                    job["match"] = llm_matches[job["job_id"]]
        jobs.sort(
            key=lambda j: j.get("match", {}).get("score_0_to_100", j.get("hybrid_score", 0)),
            reverse=True,
        )
        finished = datetime.utcnow().isoformat()
        log_match_run(run_id, resume_id, started, finished, top_k, "llm" if use_llm_rerank else "no-llm")
        logger.info("Match rank run %s completed", run_id)
        return jobs
