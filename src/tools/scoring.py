import re
from typing import Iterable, Set

STOPWORDS: Set[str] = {
    "and",
    "the",
    "a",
    "an",
    "to",
    "of",
    "in",
    "for",
    "on",
    "with",
    "at",
    "by",
    "from",
}


def distance_to_score(distance: float) -> int:
    distance = max(distance, 0.0)
    score = int(max(0, min(100, round(100 / (1 + distance)))))
    return score


def _tokens(text: str) -> Set[str]:
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {w for w in words if w not in STOPWORDS}


def keyword_overlap(resume_text: str, job_text: str) -> int:
    res_tokens = _tokens(resume_text)
    job_tokens = _tokens(job_text)
    if not res_tokens or not job_tokens:
        return 0
    overlap = len(res_tokens & job_tokens) / len(res_tokens | job_tokens)
    return int(round(overlap * 100))


def hybrid_score(distance_score: int, keyword_score: int, weights: tuple[float, float] = (0.7, 0.3)) -> int:
    final = distance_score * weights[0] + keyword_score * weights[1]
    return int(round(final))
