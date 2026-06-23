"""Small shared helper for JSON-mode Ollama calls from the orchestrator.

The axis services have their own copy of this pattern (``format:"json"`` POST +
substring-fallback parse); the Phase-F daemon-path routers (competitor,
opportunity, watch-targets) reuse this single async version so the daemon's LLM
calls all share timeout/parse behaviour.
"""
from __future__ import annotations

import json as _json
import logging
import os

import httpx

logger = logging.getLogger("moufida.llm_json")

_OLLAMA_BASE  = os.environ.get("OLLAMA_BASE_URL",  "http://ollama:11434")
_OLLAMA_MODEL = os.environ.get("OLLAMA_CHAT_MODEL", os.environ.get("OLLAMA_MODEL", "llama3.1:8b"))
_OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "300"))


def parse_json(raw: str) -> dict:
    """Parse JSON, falling back to the outermost {...} substring."""
    try:
        return _json.loads(raw)
    except Exception:
        start, end = raw.find("{"), raw.rfind("}")
        if start != -1 and end > start:
            try:
                return _json.loads(raw[start:end + 1])
            except Exception:
                pass
    return {}


async def generate_json(prompt: str, *, temperature: float = 0.2, axis: str | None = None) -> dict:
    """Call Ollama in JSON mode and return the parsed object ({} on any error).

    ``axis`` tags the call in the telemetry ``llm_calls`` log (Phase H)."""
    import time as _time
    start = _time.perf_counter()
    raw_text = ""
    tokens_in = tokens_out = None
    try:
        async with httpx.AsyncClient(timeout=_OLLAMA_TIMEOUT) as http:
            resp = await http.post(
                f"{_OLLAMA_BASE}/api/generate",
                json={
                    "model": _OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": temperature},
                },
            )
            resp.raise_for_status()
            data = resp.json()
            raw_text = data.get("response", "")
            tokens_in = data.get("prompt_eval_count")
            tokens_out = data.get("eval_count")
            return parse_json(raw_text)
    except Exception as exc:
        logger.warning("generate_json failed: %s", exc)
        return {}
    finally:
        _record_llm_call(axis, prompt, raw_text, start, tokens_in, tokens_out)


def _record_llm_call(axis, prompt, raw_text, start, tokens_in, tokens_out) -> None:
    """Best-effort telemetry; never raises into the caller."""
    try:
        import asyncio
        import time as _time
        from . import telemetry
        duration_ms = int((_time.perf_counter() - start) * 1000)
        asyncio.create_task(telemetry.record_llm_call(
            axis=axis, model=_OLLAMA_MODEL, prompt=prompt, response=raw_text or None,
            duration_ms=duration_ms, tokens_in=tokens_in, tokens_out=tokens_out,
        ))
    except Exception:  # noqa: BLE001
        pass
