import logging
from datetime import datetime
from typing import List

import requests

from ...config import LEVER_COMPANIES
from ...models import Job
from .base import BaseJobSource
from ..dedupe import stable_job_id

logger = logging.getLogger(__name__)


class LeverSource(BaseJobSource):
    name = "lever"

    def search(self, query: str, limit: int = 50) -> List[Job]:
        jobs: List[Job] = []
        for company in LEVER_COMPANIES:
            url = f"https://api.lever.co/v0/postings/{company}?mode=json"
            try:
                resp = requests.get(url, timeout=15)
                resp.raise_for_status()
                postings = resp.json()
            except Exception as exc:  # pragma: no cover - network
                logger.warning("Lever fetch failed: %s", exc)
                continue
            for entry in postings:
                if len(jobs) >= limit:
                    break
                desc = entry.get("description", "")
                if query.lower() not in desc.lower() and query.lower() not in entry.get("text", "").lower():
                    continue
                job_id = entry.get("id") or stable_job_id(entry.get("text", ""), company, entry.get("categories", {}).get("location", ""), entry.get("hostedUrl", ""))
                jobs.append(
                    Job(
                        job_id=str(job_id),
                        title=entry.get("text", ""),
                        company=company,
                        location=entry.get("categories", {}).get("location"),
                        url=entry.get("hostedUrl", ""),
                        source=self.name,
                        posted_at=entry.get("createdAt", datetime.utcnow().isoformat()),
                        description=desc,
                    )
                )
        return jobs
