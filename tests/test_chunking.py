from src.tools.chunking import chunk_text


def test_chunking_overlap_and_size():
    text = "a" * 3000
    chunks = chunk_text(text, max_chars=1200, overlap=150)
    assert all(len(c) <= 1200 for c in chunks)
    assert len(chunks) > 1
    # overlap
    assert chunks[0][-150:] == text[1050:1200]
