import json
import logging
import time
from typing import List, Optional

import requests

from ..config import OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL, OLLAMA_MODEL

logger = logging.getLogger(__name__)


class OllamaError(RuntimeError):
    pass


def _post_with_retry(
    endpoint: str, payload: dict, retries: int = 2, timeout: int = 30, base_url: Optional[str] = None
) -> requests.Response:
    url = f"{base_url or OLLAMA_BASE_URL}{endpoint}"
    for attempt in range(retries + 1):
        try:
            resp = requests.post(url, json=payload, timeout=timeout)
            resp.raise_for_status()
            return resp
        except (requests.ConnectionError, requests.Timeout) as exc:  # pragma: no cover
            if attempt >= retries:
                raise OllamaError("Ollama is not reachable; ensure it is running") from exc
            time.sleep(1.5)
        except requests.HTTPError as exc:  # pragma: no cover
            raise OllamaError(f"Ollama error: {resp.text}") from exc
    raise OllamaError("Unknown error contacting Ollama")


def embed(text: str, base_url: Optional[str] = None, embed_model: Optional[str] = None) -> List[float]:
    payload = {"model": embed_model or OLLAMA_EMBED_MODEL, "prompt": text}
    resp = _post_with_retry("/api/embeddings", payload, base_url=base_url)
    data = resp.json()
    return data.get("embedding", [])


def chat(
    messages: List[dict],
    model: Optional[str] = None,
    format: Optional[str] = None,
    base_url: Optional[str] = None,
) -> str:
    payload = {"model": model or OLLAMA_MODEL, "messages": messages, "stream": False}
    if format:
        payload["format"] = format
    resp = _post_with_retry("/api/chat", payload, base_url=base_url)
    data = resp.json()
    return data.get("message", {}).get("content", "")
