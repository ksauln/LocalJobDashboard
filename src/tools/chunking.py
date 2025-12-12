from typing import List


def chunk_text(text: str, max_chars: int = 1200, overlap: int = 150) -> List[str]:
    cleaned = "\n".join(line.strip() for line in text.strip().splitlines())
    cleaned = "\n".join([line for line in cleaned.splitlines() if line.strip()])
    chunks: List[str] = []
    start = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + max_chars)
        chunk = cleaned[start:end]
        chunks.append(chunk.strip())
        start = end - overlap
        if start < 0:
            start = 0
        if end == len(cleaned):
            break
    return [c for c in chunks if c]
