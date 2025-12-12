import hashlib
from urllib.parse import urlparse

from ..models import Job


def stable_job_id(title: str, company: str, location: str, url: str) -> str:
    norm = f"{title.lower().strip()}|{company.lower().strip()}|{(location or '').lower().strip()}|{normalize_url(url)}"
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed._replace(query="", fragment="").geturl()


def is_duplicate(existing_urls_set: set, job: Job) -> bool:
    norm_url = normalize_url(job.url)
    if norm_url in existing_urls_set:
        return True
    existing_urls_set.add(norm_url)
    return False
