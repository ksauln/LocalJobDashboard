from datetime import datetime
from typing import List

from ...models import Job
from .base import BaseJobSource


class DummySource(BaseJobSource):
    name = "dummy"

    def search(self, query: str, limit: int = 50) -> List[Job]:
        now = datetime.utcnow().isoformat()
        jobs = [
            Job(
                job_id=f"dummy-{i}",
                title=f"Sample Role {i}",
                company="Acme Corp",
                location="Remote",
                url=f"https://example.com/jobs/{i}",
                source=self.name,
                posted_at=now,
                description=f"Example job {i} description related to {query}",
            )
            for i in range(1, min(limit, 5) + 1)
        ]
        return jobs
