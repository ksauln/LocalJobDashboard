# Scoring

This is how jobs are ranked for a selected resume.

## Embedding similarity
- Chroma uses cosine distance (lower is better).  
- We map distance to a 0–100 score so it is easy to read: `distance_score = 100 / (1 + distance)`. Small distances stay close to 100; large distances drop toward 0.

## Keyword overlap
- Tokenize resume text and job text, drop simple stopwords, compute intersection-over-union.  
- Scale to 0–100: `keyword_score = overlap_ratio * 100`. This rewards shared terms even if embeddings are noisy.

## Hybrid score (default sort)
- Combine both views: `hybrid_score = 0.7 * distance_score + 0.3 * keyword_score`.  
- Rationale: embeddings carry most of the signal; keywords help guard against odd embeddings or very short texts.

## Optional LLM rerank
- If enabled, we send the resume and top jobs to Ollama chat.  
- Model returns JSON with `score_0_to_100`, `strengths`, `gaps`, `short_reason`.  
- UI shows this detail alongside the hybrid score; hybrid remains the primary ordering to keep results stable even if LLM replies vary.

## Tuning tips
- Want faster/cheaper? Disable LLM explanations.  
- Want stricter exact-match bias? Increase the keyword weight.  
- Need more jobs per run? Raise `Top K` in the Match page or `--top_k` in `scripts/match.py`.
