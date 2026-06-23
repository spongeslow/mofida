"""Shared evidence helpers for creation-mode axis services.

The orchestrator gathers per-axis evidence (curated KB hits + live web results)
and passes it in the /generate request body under `evidence`. Each axis service
uses these helpers to (1) render an evidence block for the LLM prompt and
(2) build the `citations` list echoed back in the response, so the UI can show
clickable sources.

Evidence shape (from the orchestrator):
    {
      "kb":  [{"title", "url", "provider", "matched_chunk", ...}, ...],
      "web": [{"title", "url", "snippet", "source": "web"}, ...],
    }
"""
from __future__ import annotations

from typing import Any


def format_evidence_block(evidence: dict[str, Any] | None) -> str:
    """Render KB + web evidence as a numbered list for the LLM prompt.

    Returns an empty string when there is no evidence (prompt stays unchanged).
    """
    if not evidence:
        return ""
    kb = evidence.get("kb") or []
    web = evidence.get("web") or []
    if not kb and not web:
        return ""

    # NOTE: the numbering here is continuous (kb first, then web) and matches the
    # order of build_citations() exactly, so an inline "[n]" the model emits maps
    # to citations[n-1] on the frontend.
    lines: list[str] = []
    idx = 1
    for r in kb:
        title = r.get("title", "")
        url = r.get("url", "")
        provider = r.get("provider", "")
        excerpt = (r.get("matched_chunk") or "")[:200]
        lines.append(f"[{idx}] (KB) {title} — {provider} — {url}\n   {excerpt}")
        idx += 1
    for r in web:
        title = r.get("title", "")
        url = r.get("url", "")
        excerpt = (r.get("snippet") or "")[:200]
        lines.append(f"[{idx}] (web) {title} — {url}\n   {excerpt}")
        idx += 1

    # Trailing blank line so callers can prepend this to their prompt directly:
    #     prompt = format_evidence_block(req.evidence) + prompt
    return (
        "SOURCES — ground your answer in these. When a statement draws on a "
        "source, cite it inline using its bracketed number (e.g. [1], [2]). "
        "Do NOT invent sources, URLs, or numbers beyond this list:\n"
        + "\n".join(lines)
        + "\n\n"
    )


def build_citations(evidence: dict[str, Any] | None) -> list[dict]:
    """Flatten evidence into a citations list for the /generate response."""
    if not evidence:
        return []
    citations: list[dict] = []
    for r in evidence.get("kb") or []:
        if r.get("url") or r.get("title"):
            citations.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "provider": r.get("provider", ""),
                "source": "kb",
            })
    for r in evidence.get("web") or []:
        if r.get("url") or r.get("title"):
            citations.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "provider": "",
                "source": "web",
            })
    return citations
