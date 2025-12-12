import os
import tempfile

from src.storage.sqlite import init_db, insert_resume, list_resumes, insert_job, list_jobs
from src.models import Job
import src.config as config


def test_init_and_insert(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(config, "SQLITE_PATH", str(db_path))
    init_db()
    insert_resume("r1", "file.pdf", "now")
    resumes = list_resumes()
    assert resumes[0]["resume_id"] == "r1"

    job = Job(job_id="j1", title="t", company="c", location=None, url="u", source="s", posted_at=None, description="d")
    insert_job(job)
    jobs = list_jobs()
    assert jobs[0]["job_id"] == "j1"
