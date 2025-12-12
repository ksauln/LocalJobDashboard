from src.tools.dedupe import stable_job_id, normalize_url, is_duplicate
from src.models import Job


def test_stable_job_id_deterministic():
    id1 = stable_job_id("Title", "Company", "Remote", "https://example.com")
    id2 = stable_job_id("Title", "Company", "Remote", "https://example.com")
    assert id1 == id2


def test_normalize_url_removes_query():
    url = "https://example.com/role?utm=123"
    assert normalize_url(url) == "https://example.com/role"


def test_is_duplicate():
    j = Job(job_id="1", title="t", company="c", location=None, url="https://example.com/a?x=1", source="s", posted_at=None, description="d")
    seen = set()
    assert not is_duplicate(seen, j)
    assert is_duplicate(seen, j)
