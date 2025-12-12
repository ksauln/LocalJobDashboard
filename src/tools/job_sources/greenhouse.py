import logging
from datetime import datetime
from typing import List

import requests

from ...config import GREENHOUSE_BOARDS
from ...models import Job
from .base import BaseJobSource
from ..dedupe import stable_job_id

logger = logging.getLogger(__name__)


class GreenhouseSource(BaseJobSource):
    name = "greenhouse"

    def search(self, query: str, limit: int = 50) -> List[Job]:
        jobs: List[Job] = []
        for board in GREENHOUSE_BOARDS:
            url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
            try:
                resp = requests.get(url, timeout=15)
                resp.raise_for_status()
                data = resp.json().get("jobs", [])
            except Exception as exc:  # pragma: no cover - network
                logger.warning("Greenhouse fetch failed: %s", exc)
                continue
            for entry in data:
                if len(jobs) >= limit:
                    break
                desc = entry.get("content", "")
                if query.lower() not in desc.lower() and query.lower() not in entry.get("title", "").lower():
                    continue
                job_id = entry.get("id") or stable_job_id(entry.get("title", ""), board, entry.get("location", {}).get("name", ""), entry.get("absolute_url", ""))
                jobs.append(
                    Job(
                        job_id=str(job_id),
                        title=entry.get("title", ""),
                        company=board,
                        location=entry.get("location", {}).get("name"),
                        url=entry.get("absolute_url", ""),
                        source=self.name,
                        posted_at=entry.get("updated_at", datetime.utcnow().isoformat()),
                        description=desc,
                    )
                )
        return jobs
