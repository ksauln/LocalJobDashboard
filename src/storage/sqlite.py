import os
import sqlite3
from typing import Any, Dict, List, Optional

from ..models import Job
from .. import config


def get_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(config.SQLITE_PATH), exist_ok=True)
    conn = sqlite3.connect(config.SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS resumes (
            resume_id TEXT PRIMARY KEY,
            filename TEXT,
            added_at TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            location TEXT,
            url TEXT UNIQUE,
            source TEXT,
            posted_at TEXT,
            description TEXT,
            added_at TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS job_runs (
            run_id TEXT PRIMARY KEY,
            query TEXT,
            started_at TEXT,
            finished_at TEXT,
            added_count INTEGER,
            source_summary TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS match_runs (
            run_id TEXT PRIMARY KEY,
            resume_id TEXT,
            started_at TEXT,
            finished_at TEXT,
            top_k INTEGER,
            notes TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def insert_resume(resume_id: str, filename: str, added_at: str) -> None:
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO resumes(resume_id, filename, added_at) VALUES (?, ?, ?)",
        (resume_id, filename, added_at),
    )
    conn.commit()
    conn.close()


def list_resumes() -> List[sqlite3.Row]:
    conn = get_conn()
    cur = conn.execute("SELECT resume_id, filename, added_at FROM resumes ORDER BY added_at DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


def insert_job(job: Job) -> None:
    conn = get_conn()
    conn.execute(
        """
        INSERT OR IGNORE INTO jobs(job_id, title, company, location, url, source, posted_at, description, added_at)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """,
        (
            job.job_id,
            job.title,
            job.company,
            job.location,
            job.url,
            job.source,
            job.posted_at,
            job.description,
        ),
    )
    conn.commit()
    conn.close()


def list_jobs(limit: int = 200, filters: Optional[Dict[str, Any]] = None) -> List[sqlite3.Row]:
    filters = filters or {}
    clauses: List[str] = []
    values: List[Any] = []
    if "source" in filters:
        clauses.append("source = ?")
        values.append(filters["source"])
    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    conn = get_conn()
    query = f"SELECT job_id, title, company, location, url, source, posted_at, added_at FROM jobs {where_clause} ORDER BY added_at DESC LIMIT ?"
    values.append(limit)
    cur = conn.execute(query, values)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_job(job_id: str) -> Optional[sqlite3.Row]:
    conn = get_conn()
    cur = conn.execute(
        "SELECT job_id, title, company, location, url, source, posted_at, added_at, description FROM jobs WHERE job_id = ?",
        (job_id,),
    )
    row = cur.fetchone()
    conn.close()
    return row


def log_job_run(
    run_id: str,
    query: str,
    started_at: str,
    finished_at: str,
    added_count: int,
    source_summary: str,
) -> None:
    conn = get_conn()
    conn.execute(
        """
        INSERT OR REPLACE INTO job_runs(run_id, query, started_at, finished_at, added_count, source_summary)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (run_id, query, started_at, finished_at, added_count, source_summary),
    )
    conn.commit()
    conn.close()


def log_match_run(
    run_id: str,
    resume_id: str,
    started_at: str,
    finished_at: str,
    top_k: int,
    notes: str,
) -> None:
    conn = get_conn()
    conn.execute(
        """
        INSERT OR REPLACE INTO match_runs(run_id, resume_id, started_at, finished_at, top_k, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (run_id, resume_id, started_at, finished_at, top_k, notes),
    )
    conn.commit()
    conn.close()


def wipe_jobs() -> None:
    """Delete all jobs and job run logs."""
    conn = get_conn()
    conn.execute("DELETE FROM jobs")
    conn.execute("DELETE FROM job_runs")
    conn.commit()
    conn.close()


def wipe_resumes() -> None:
    """Delete all resumes and match run logs."""
    conn = get_conn()
    conn.execute("DELETE FROM resumes")
    conn.execute("DELETE FROM match_runs")
    conn.commit()
    conn.close()
