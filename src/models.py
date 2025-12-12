from typing import List, Optional, Union
from pydantic import BaseModel


class ResumeMeta(BaseModel):
    resume_id: str
    filename: str
    added_at: str


class Job(BaseModel):
    job_id: str
    title: str
    company: str
    location: Optional[str] = None
    url: str
    source: str
    posted_at: Optional[str] = None
    description: str


class MatchResult(BaseModel):
    job_id: str
    score_0_to_100: int
    strengths: List[str]
    gaps: List[str]
    short_reason: str


class RankedJob(BaseModel):
    job: Union[Job, dict]
    distance: float
    match: Optional[MatchResult] = None

