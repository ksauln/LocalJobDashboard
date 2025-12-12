import logging
import uuid
from datetime import datetime
from typing import Any
from pathlib import Path

from ..llm import ollama_client
from ..storage import vectordb
from ..storage.sqlite import insert_resume
from ..tools.chunking import chunk_text
from ..tools.parsing import extract_text

logger = logging.getLogger(__name__)


class ResumeIngestAgent:
    def __init__(self, resume_collection):
        self.resume_collection = resume_collection

    def ingest(self, filepath: str) -> str:
        text = extract_text(filepath)
        if not text.strip():
            raise ValueError("Extracted text is empty")
        chunks = chunk_text(text)
        resume_id = str(uuid.uuid4())
        display_name = Path(filepath).name
        embeddings = [ollama_client.embed(chunk) for chunk in chunks]
        ids = [f"{resume_id}:{i}" for i in range(len(chunks))]
        metadatas: list[dict[str, Any]] = [
            {"resume_id": resume_id, "chunk_index": i, "source_file": filepath}
            for i in range(len(chunks))
        ]
        vectordb.add_documents(
            self.resume_collection,
            ids=ids,
            documents=chunks,
            metadatas=metadatas,
            embeddings=embeddings,
        )
        insert_resume(resume_id, display_name, datetime.utcnow().isoformat())
        logger.info("Ingested resume %s (%s) with %s chunks", resume_id, display_name, len(chunks))
        return resume_id
