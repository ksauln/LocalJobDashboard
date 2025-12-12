import logging
import uuid
from datetime import datetime
from typing import Dict

from ..storage import vectordb
from ..storage.sqlite import insert_job, log_job_run
from ..tools.dedupe import is_duplicate, stable_job_id
from ..tools.job_sources import get_sources_from_env
from ..tools.parsing import strip_html
from ..llm import ollama_client
from ..llm.ollama_client import OllamaError

logger = logging.getLogger(__name__)


class JobScoutAgent:
    def __init__(self, job_collection):
        self.job_collection = job_collection
        self.sources = get_sources_from_env()
        self.max_embed_chars = 8000  # avoid exceeding embed context

    def run_search(self, query: str, limit_per_source: int = 50) -> Dict[str, int]:
        run_id = str(uuid.uuid4())
        started = datetime.utcnow().isoformat()
        summary: Dict[str, int] = {}
        existing_urls: set = set()
        total_added = 0
        for source in self.sources:
            jobs = source.search(query, limit_per_source)
            added_here = 0
            for job in jobs:
                cleaned_desc = strip_html(job.description)
                if not job.job_id:
                    job.job_id = stable_job_id(job.title, job.company, job.location or "", job.url)
                if is_duplicate(existing_urls, job):
                    continue
                job.description = cleaned_desc
                meta = job.dict()
                meta["description"] = cleaned_desc
                insert_job(job)
                doc = f"{job.title} at {job.company} {job.location or ''}\n{cleaned_desc}"
                doc_for_embed = doc[: self.max_embed_chars]
                try:
                    embedding = ollama_client.embed(doc_for_embed)
                except OllamaError as exc:
                    logger.warning("Embedding failed for job %s: %s", job.job_id, exc)
                    continue
                vectordb.add_documents(
                    self.job_collection,
                    ids=[job.job_id],
                    documents=[doc_for_embed],
                    metadatas=[meta],
                    embeddings=[embedding],
                )
                added_here += 1
            summary[source.name] = added_here
            total_added += added_here
        finished = datetime.utcnow().isoformat()
        log_job_run(run_id, query, started, finished, total_added, str(summary))
        logger.info("Job scout run %s added %s jobs", run_id, total_added)
        return summary
