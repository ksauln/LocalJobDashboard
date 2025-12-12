import logging
from datetime import datetime
from typing import List

import requests

from ...config import REMOTIVE_CATEGORY
from ...models import Job
from .base import BaseJobSource
from ..dedupe import stable_job_id

logger = logging.getLogger(__name__)


class RemotiveSource(BaseJobSource):
    name = "remotive"

    def search(self, query: str, limit: int = 50) -> List[Job]:
        params = {"search": query}
        if REMOTIVE_CATEGORY:
            params["category"] = REMOTIVE_CATEGORY
        try:
            resp = requests.get("https://remotive.com/api/remote-jobs", params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json().get("jobs", [])
        except Exception as exc:  # pragma: no cover - network
            logger.warning("Remotive fetch failed: %s", exc)
            return []
        jobs: List[Job] = []
        for entry in data[:limit]:
            desc = entry.get("description", "")
            job_id = entry.get("id") or stable_job_id(
                entry.get("title", ""), entry.get("company_name", ""), entry.get("candidate_required_location", ""), entry.get("url", "")
            )
            jobs.append(
                Job(
                    job_id=str(job_id),
                    title=entry.get("title", ""),
                    company=entry.get("company_name", ""),
                    location=entry.get("candidate_required_location"),
                    url=entry.get("url", ""),
                    source=self.name,
                    posted_at=entry.get("publication_date", datetime.utcnow().isoformat()),
                    description=desc,
                )
            )
        return jobs
