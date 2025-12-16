import logging
from dataclasses import dataclass
from typing import List, Optional

import requests

from .. import config
from . import ollama_client

logger = logging.getLogger(__name__)


class LLMProviderError(RuntimeError):
    pass


@dataclass
class LLMConfig:
    provider: str = config.LLM_PROVIDER
    api_key: Optional[str] = config.OPENAI_API_KEY
    base_url: Optional[str] = None
    model: Optional[str] = None
    embed_model: Optional[str] = None


_runtime_config: Optional[LLMConfig] = None


def set_runtime_llm_config(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    embed_model: Optional[str] = None,
) -> None:
    """Override LLM settings for the current process/session."""

    global _runtime_config
    _runtime_config = LLMConfig(
        provider=provider or config.LLM_PROVIDER,
        api_key=api_key if api_key is not None else config.OPENAI_API_KEY,
        base_url=base_url,
        model=model,
        embed_model=embed_model,
    )


def clear_runtime_llm_config() -> None:
    global _runtime_config
    _runtime_config = None


def get_active_config() -> LLMConfig:
    cfg = _runtime_config or LLMConfig()
    provider = (cfg.provider or config.LLM_PROVIDER).lower()
    if provider not in {"ollama", "openai"}:
        logger.warning("Unknown LLM provider '%s', falling back to Ollama", provider)
        provider = "ollama"
    base_url = cfg.base_url
    model = cfg.model
    embed_model = cfg.embed_model
    if provider == "openai":
        base_url = base_url or config.OPENAI_BASE_URL
        model = model or config.OPENAI_MODEL
        embed_model = embed_model or config.OPENAI_EMBED_MODEL
    else:
        base_url = base_url or config.OLLAMA_BASE_URL
        model = model or config.OLLAMA_MODEL
        embed_model = embed_model or config.OLLAMA_EMBED_MODEL
    return LLMConfig(
        provider=provider,
        api_key=cfg.api_key or config.OPENAI_API_KEY,
        base_url=base_url,
        model=model,
        embed_model=embed_model,
    )


def embed(text: str, model: Optional[str] = None) -> List[float]:
    cfg = get_active_config()
    if cfg.provider == "openai":
        return _openai_embed(text, model or cfg.embed_model, cfg)
    return ollama_client.embed(text, base_url=cfg.base_url, embed_model=model or cfg.embed_model)


def chat(messages: List[dict], model: Optional[str] = None, format: Optional[str] = None) -> str:
    cfg = get_active_config()
    if cfg.provider == "openai":
        return _openai_chat(messages, model or cfg.model, format, cfg)
    return ollama_client.chat(messages, model=model or cfg.model, format=format, base_url=cfg.base_url)


def _openai_post(path: str, payload: dict, cfg: LLMConfig) -> requests.Response:
    url = f"{cfg.base_url.rstrip('/')}{path}"
    headers = {"Content-Type": "application/json"}
    if cfg.api_key:
        headers["Authorization"] = f"Bearer {cfg.api_key}"
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
    except (requests.ConnectionError, requests.Timeout) as exc:  # pragma: no cover - network
        raise LLMProviderError("OpenAI is not reachable; check base URL and connectivity") from exc
    except requests.HTTPError as exc:  # pragma: no cover - passthrough for debugging
        raise LLMProviderError(f"OpenAI error: {resp.text}") from exc
    return resp


def _openai_embed(text: str, model: str, cfg: LLMConfig) -> List[float]:
    payload = {"model": model, "input": text}
    resp = _openai_post("/embeddings", payload, cfg)
    data = resp.json()
    embedding = (data.get("data") or [{}])[0].get("embedding")
    return embedding or []


def _openai_chat(messages: List[dict], model: str, format: Optional[str], cfg: LLMConfig) -> str:
    payload = {"model": model, "messages": messages}
    if format == "json":
        payload["response_format"] = {"type": "json_object"}
    resp = _openai_post("/chat/completions", payload, cfg)
    data = resp.json()
    return (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
