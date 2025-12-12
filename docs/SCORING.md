# Scoring

## Distance to Score
We convert Chroma cosine distances (smaller is better) into a 0–100 score using `score = 100 / (1 + distance)` to keep values bounded and monotonically decreasing with distance.

## Keyword Overlap
We compute token overlap between resume text and job text, ignoring a small stopword list. The overlap ratio of intersection over union is scaled to 0–100.

## Hybrid Score
`hybrid_score = 0.7 * distance_score + 0.3 * keyword_score` balances semantic proximity with simple keyword overlap. Higher scores indicate better matches.

## LLM Rerank
Optionally, the LLM returns JSON match details (score, strengths, gaps, reason). These enrich UI display without replacing the base hybrid ranking.
