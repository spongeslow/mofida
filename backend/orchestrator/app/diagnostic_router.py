"""Diagnostic endpoint: run the STATE_EXISTING pass, persist it, stream events.

Also hosts the per-axis Debate chat and the PDF document upload endpoint.
"""
from __future__ import annotations

import io
import json
import logging
import os

import asyncpg
import httpx
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from . import axis_registry, sse
from .axis_registry import AXES
from .cbm.scorer import run_cbm_for_axes
from .diagnostic.aggregator import aggregate_results
from .diagnostic.runner import run_diagnostic_pass
from .state_router import get_pool

_OLLAMA_BASE  = os.environ.get("OLLAMA_BASE_URL",  "http://ollama:11434")
_OLLAMA_MODEL = os.environ.get("OLLAMA_CHAT_MODEL", os.environ.get("OLLAMA_MODEL", "llama3.1:8b"))

try:
    from toolkit import ToolManager as _ToolManager
    _tool_manager = _ToolManager()
except ImportError:
    _tool_manager = None

router = APIRouter()
logger = logging.getLogger("moufida.diagnostic_router")


async def _persist(conn: asyncpg.Connection, project_id: str, ideation: dict, agg: dict) -> None:
    """Write one diagnostic_history row plus a score_snapshots row per score."""
    await conn.execute(
        """
        INSERT INTO diagnostic_history
            (project_id, maturity_stage, self_assessed, perception_gap,
             confidence, evidence, blockers, anomalies)
        VALUES ($1::uuid, $2, $3, $4, $5, $6::jsonb, $7::jsonb, $8::jsonb)
        """,
        project_id,
        agg["maturity_stage"],
        agg["self_assessed_stage"],
        "yes" if agg["perception_gap"] else "no",
        ideation.get("confidence"),
        json.dumps(ideation.get("evidence", [])),
        json.dumps(agg["blockers"]),
        json.dumps(agg["anomalies"]),
    )
    for name, score in agg["scores"].items():
        await conn.execute(
            """
            INSERT INTO score_snapshots (project_id, score_name, score, breakdown)
            VALUES ($1::uuid, $2, $3, $4::jsonb)
            """,
            project_id,
            name,
            float(score),
            json.dumps(agg["score_breakdowns"].get(name) or {}),
        )


async def _persist_concept_scores(
    conn: asyncpg.Connection, project_id: str, cbm_results: dict
) -> None:
    """Write one concept_scores row per axis (Concept Bottleneck layer)."""
    for axis, data in cbm_results.items():
        await conn.execute(
            """
            INSERT INTO concept_scores
                (project_id, axis, concepts, cbm_score, actual_score, bottleneck, calibrated)
            VALUES ($1::uuid, $2, $3::jsonb, $4, $5, $6::jsonb, $7)
            """,
            project_id,
            axis,
            json.dumps(data.get("concepts") or {}),
            data.get("cbm_score"),
            data.get("actual_score"),
            json.dumps(data.get("bottleneck")) if data.get("bottleneck") else None,
            bool(data.get("calibrated", False)),
        )


async def _run_concept_bottleneck(profile: dict, agg: dict) -> dict:
    """Run the concept-bottleneck pass for all network axes (best-effort).

    Maps each axis's owned composite score (if any) to its ridge-calibration
    target so future ``/cbm/calibrate`` calls can learn data-driven weights.
    """
    actual_scores: dict[str, float | None] = {}
    for axis in axis_registry.NETWORK_AXES:
        score_name = AXES.get(axis, {}).get("score")
        actual_scores[axis] = agg["scores"].get(score_name) if score_name else None
    try:
        return await run_cbm_for_axes(profile, axis_registry.NETWORK_AXES, actual_scores)
    except Exception as exc:  # noqa: BLE001 — never break the diagnostic
        logger.warning("concept-bottleneck pass failed project-level: %s", exc)
        return {}


async def _persist_roadmap(
    conn: asyncpg.Connection, project_id: str, roadmap: dict
) -> None:
    version = await conn.fetchval(
        "SELECT COALESCE(MAX(version), 0) + 1 FROM roadmap_versions WHERE project_id = $1::uuid",
        project_id,
    )
    await conn.execute(
        """
        INSERT INTO roadmap_versions (project_id, version, roadmap, trigger)
        VALUES ($1::uuid, $2, $3::jsonb, 'diagnostic')
        """,
        project_id,
        version,
        json.dumps(roadmap),
    )


async def _call_roadmap(
    project_id: str,
    stage: str,
    sector: str,
    language: str,
    blockers: list[dict],
    scores: dict,
    profile: dict,
) -> dict | None:
    gtm_host = axis_registry.axis_host("gtm")
    try:
        async with httpx.AsyncClient(timeout=180.0) as http:
            resp = await http.post(
                f"{gtm_host}/roadmap",
                json={
                    "project_id": project_id,
                    "stage": stage or "ideation",
                    "sector": str(profile.get("sector", "cross-sector")),
                    "language": language or "fr",
                    "blockers": blockers,
                    "scores": scores,
                    "profile": profile,
                },
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("roadmap generation failed for project=%s: %s", project_id, exc)
        return None


@router.post("/project/{project_id}/run-diagnostic")
async def run_diagnostic(project_id: str, quick: bool = False):
    """Run the diagnostic pass. ``quick=true`` skips the slow Axis 10 roadmap
    generation (RAG + LLM) for an abbreviated run; scores, maturity, blockers and
    recommendations are still produced."""
    pool = await get_pool()

    # 1. Load the profile.
    try:
        row = await pool.fetchrow(
            "SELECT id, profile FROM profiles WHERE id = $1::uuid", project_id
        )
    except (asyncpg.DataError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"invalid project_id: {exc}")
    if row is None:
        raise HTTPException(status_code=404, detail="project not found")

    profile = row["profile"]
    if isinstance(profile, str):
        profile = json.loads(profile or "{}")

    # 2. Pull tools enrich the profile with live external data before scoring.
    if _tool_manager is not None:
        try:
            profile = await _tool_manager.enrich_profile(pool, profile)
        except Exception as exc:
            logger.warning("tool profile enrichment failed: %s", exc)

    # 3. Fan out to the axes and aggregate.
    axis_outputs = await run_diagnostic_pass(project_id, profile, axis_registry)
    agg = aggregate_results(profile, axis_outputs)

    # 4. Persist diagnostic history + score snapshots atomically.
    ideation = axis_outputs.get("ideation") or {}
    async with pool.acquire() as conn:
        async with conn.transaction():
            await _persist(conn, project_id, ideation, agg)

    # 5. Fire score/maturity SSE events.
    for name, score in agg["scores"].items():
        await sse.push_event(project_id, "score_update", {"score_name": name, "score": score})
    await sse.push_event(
        project_id,
        "maturity_update",
        {
            "maturity_stage": agg["maturity_stage"],
            "self_assessed_stage": agg["self_assessed_stage"],
            "perception_gap": agg["perception_gap"],
        },
    )

    # 5b. Concept Bottleneck layer: decompose each axis score into named concepts
    #     and identify the bottleneck. Skipped in quick mode (adds LLM calls).
    cbm_results: dict = {}
    if not quick:
        cbm_results = await _run_concept_bottleneck(profile, agg)
        if cbm_results:
            try:
                async with pool.acquire() as conn:
                    async with conn.transaction():
                        await _persist_concept_scores(conn, project_id, cbm_results)
            except Exception as exc:
                logger.warning("concept_scores persist failed project=%s: %s", project_id, exc)
            await sse.push_event(project_id, "concept_update", {
                "axes": list(cbm_results.keys()),
                "bottlenecks": {
                    axis: data.get("bottleneck")
                    for axis, data in cbm_results.items()
                    if data.get("bottleneck")
                },
            })

    # 6. Generate Axis 10 roadmap (post-wave, non-blocking). Skipped in quick mode.
    roadmap_result: dict | None = None
    language = profile.get("language", "fr")
    if not quick:
        roadmap_result = await _call_roadmap(
            project_id=project_id,
            stage=agg.get("maturity_stage") or "ideation",
            sector=str(profile.get("sector", "cross-sector")),
            language=language,
            blockers=agg["blockers"],
            scores=agg["scores"],
            profile=profile,
        )

    # 7. Persist roadmap and push SSE event.
    if roadmap_result:
        try:
            async with pool.acquire() as conn:
                async with conn.transaction():
                    await _persist_roadmap(conn, project_id, roadmap_result)
        except Exception as exc:
            logger.warning("roadmap persist failed project=%s: %s", project_id, exc)

        await sse.push_event(project_id, "roadmap_update", {
            "stage": roadmap_result.get("stage"),
            "gaps": roadmap_result.get("gaps", []),
            "resources_used": roadmap_result.get("resources_used", 0),
        })

    # 8. Fan out push-tool notifications (Slack, Notion, Sheets) asynchronously.
    if _tool_manager is not None:
        try:
            await _tool_manager.dispatch_diagnostic(
                pool,
                project_id,
                profile,
                agg["scores"],
                agg["blockers"],
                roadmap_result,
            )
        except Exception as exc:
            logger.warning("tool dispatch_diagnostic failed: %s", exc)

    # 9. Return the full aggregated result including roadmap.
    #    confidence/evidence live on the ideation axis output (same source as
    #    _persist); surface them at the top level so the dashboard MaturityCard
    #    can render the confidence % and evidence bullets without a second fetch.
    response = {
        "project_id": project_id,
        "confidence": ideation.get("confidence"),
        "evidence": ideation.get("evidence", []),
        **agg,
        "axis_outputs": axis_outputs,
    }
    if cbm_results:
        response["concept_scores"] = cbm_results
    if roadmap_result:
        response["roadmap"] = roadmap_result
    return response


# ---------------------------------------------------------------------------
# Document upload — PDF → text extraction → knowledge_base
# ---------------------------------------------------------------------------

@router.post("/project/{project_id}/documents")
async def upload_document(project_id: str, file: UploadFile = File(...)):
    """Upload a PDF, extract its text, and persist it to knowledge_base for RAG.

    Text-based PDFs only — scanned PDFs surface a warning (OCR is out of scope).
    """
    pool = await get_pool()

    raw = await file.read()
    filename = file.filename or "upload.pdf"
    extracted_text = ""
    warning = None

    lower = filename.lower()
    content_type = (file.content_type or "").lower()
    is_text = (
        lower.endswith((".txt", ".md", ".markdown", ".csv"))
        or content_type.startswith("text/")
        or content_type in ("application/markdown", "application/json")
    )

    if is_text:
        # Plain-text / markdown: decode directly (no PDF parsing).
        try:
            extracted_text = raw.decode("utf-8", errors="replace").strip()
            if not extracted_text:
                warning = "no_extractable_text"
        except Exception as exc:
            logger.warning("text decode failed file=%s: %s", filename, exc)
            warning = "extraction_failed"
    else:
        try:
            import pypdf  # lazy import so import errors fail loudly at call time, not startup
            reader = pypdf.PdfReader(io.BytesIO(raw))
            parts = []
            for page in reader.pages:
                text = page.extract_text() or ""
                parts.append(text)
            extracted_text = "\n".join(parts).strip()
            if not extracted_text:
                warning = "no_extractable_text"
        except Exception as exc:
            logger.warning("pypdf extraction failed file=%s: %s", filename, exc)
            warning = "extraction_failed"

    char_count = len(extracted_text)

    # `persisted` reflects whether the row actually landed in knowledge_base —
    # not merely whether text was extracted. The CHECK constraint on `source`
    # only allows seed/tool/upload/manual/feed, so the filename goes in `title`.
    persisted = False
    if extracted_text:
        try:
            kb_version = await pool.fetchval(
                "SELECT COALESCE(MAX(kb_version), 0) + 1 FROM knowledge_base WHERE project_id = $1::uuid",
                project_id,
            )
            await pool.execute(
                """
                INSERT INTO knowledge_base (project_id, source, title, content, kb_version)
                VALUES ($1::uuid, 'upload', $2, $3, $4)
                """,
                project_id,
                filename,
                extracted_text,
                kb_version,
            )
            persisted = True
        except Exception as exc:
            logger.warning("knowledge_base insert failed project=%s: %s", project_id, exc)
            warning = warning or "persist_failed"

    return {
        "project_id":     project_id,
        "filename":       filename,
        "char_count":     char_count,
        "persisted":      persisted,
        "warning":        warning,
    }


# ---------------------------------------------------------------------------
# List a project's uploaded documents (for the KB browser panel)
# ---------------------------------------------------------------------------

@router.get("/project/{project_id}/documents")
async def list_documents(project_id: str):
    """Return the documents the founder has uploaded into this project's KB."""
    pool = await get_pool()
    try:
        rows = await pool.fetch(
            """
            SELECT id, title, char_length(content) AS char_count, kb_version, created_at
            FROM knowledge_base
            WHERE project_id = $1::uuid AND source = 'upload'
            ORDER BY created_at DESC
            """,
            project_id,
        )
    except Exception as exc:
        logger.warning("list documents failed project=%s: %s", project_id, exc)
        raise HTTPException(status_code=400, detail="invalid_project") from exc

    return {
        "project_id": project_id,
        "documents": [
            {
                "id":         str(r["id"]),
                "title":      r["title"],
                "char_count": r["char_count"],
                "kb_version": r["kb_version"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            }
            for r in rows
        ],
    }


# ---------------------------------------------------------------------------
# Per-axis Debate — argue the score, recompute if convinced
# ---------------------------------------------------------------------------

class DebateRequest(BaseModel):
    language: str = "fr"
    message: str
    history: list[dict] = []


@router.post("/project/{project_id}/axis/{axis}/debate")
async def debate_axis(project_id: str, axis: str, req: DebateRequest):
    """Let the founder argue their axis score. Recomputes + locks if convinced.

    Returns reply, whether score changed, new_score (if changed), rationale.
    """
    if axis not in axis_registry.NETWORK_AXES:
        raise HTTPException(status_code=404, detail=f"unknown axis: {axis}")

    pool = await get_pool()

    # Load latest score for this axis.
    score_row = await pool.fetchrow(
        """
        SELECT DISTINCT ON (score_name) score_name, score, breakdown
          FROM score_snapshots
         WHERE project_id = $1::uuid
           AND score_name LIKE $2
         ORDER BY score_name, created_at DESC
        """,
        project_id,
        f"%{axis.replace('-', '_')}%",
    )

    current_score = score_row["score"] if score_row else None
    current_breakdown = score_row["breakdown"] if score_row else {}
    if isinstance(current_breakdown, str):
        try:
            current_breakdown = json.loads(current_breakdown)
        except Exception:
            current_breakdown = {}

    # Check if this axis is already locked (event with source=chat and status=acted).
    locked_row = await pool.fetchrow(
        """
        SELECT id FROM events
         WHERE project_id = $1::uuid
           AND source = 'chat'
           AND status = 'acted'
           AND $2 = ANY(axes_affected)
         LIMIT 1
        """,
        project_id,
        axis,
    )
    if locked_row:
        return {
            "reply": "Ce score a déjà été verrouillé suite à une discussion précédente.",
            "score_changed": False,
            "new_score": current_score,
            "locked": True,
            "rationale": "Score locked by previous debate.",
        }

    # Build conversation for Ollama.
    history_msgs = [
        {"role": m.get("role", "user"), "content": m.get("content", "")}
        for m in req.history
    ]

    system_prompt = (
        f"You are Moufida, an AI startup advisor. A founder is debating their {axis} score.\n"
        f"Current score: {current_score}/5. Breakdown: {json.dumps(current_breakdown, ensure_ascii=False)}\n\n"
        "If the founder provides convincing NEW evidence or a valid counter-argument "
        "that changes the facts (not just opinion), update the score and explain why.\n"
        "If not convinced, explain why the current score stands.\n\n"
        "Respond ONLY with this JSON:\n"
        '{"reply": "...", "score_changed": false, "new_score": null, '
        '"rationale": "...", "convinced": false}\n\n'
        f"Respond in {req.language}."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        *history_msgs,
        {"role": "user", "content": req.message},
    ]

    reply_text = "Je prends note de votre argument."
    score_changed = False
    new_score = current_score
    rationale = ""
    convinced = False

    try:
        async with httpx.AsyncClient(timeout=120.0) as http:
            resp = await http.post(
                f"{_OLLAMA_BASE}/api/chat",
                json={
                    "model":  _OLLAMA_MODEL,
                    "messages": messages,
                    "stream": False,
                },
            )
            resp.raise_for_status()
            raw = resp.json().get("message", {}).get("content", "")
            # Parse JSON from response.
            s, e = raw.find("{"), raw.rfind("}")
            if s != -1 and e > s:
                try:
                    parsed = json.loads(raw[s:e + 1])
                    reply_text   = parsed.get("reply", reply_text)
                    score_changed = bool(parsed.get("score_changed", False))
                    new_score    = parsed.get("new_score") or current_score
                    rationale    = parsed.get("rationale", "")
                    convinced    = bool(parsed.get("convinced", False))
                except Exception:
                    reply_text = raw
    except Exception as exc:
        logger.warning("debate LLM call failed project=%s axis=%s: %s", project_id, axis, exc)

    locked = False
    if score_changed and new_score is not None and new_score != current_score:
        try:
            score_name = score_row["score_name"] if score_row else axis.replace("-", "_")
            await pool.execute(
                """
                INSERT INTO score_snapshots (project_id, score_name, score, breakdown)
                VALUES ($1::uuid, $2, $3, $4::jsonb)
                """,
                project_id,
                score_name,
                float(new_score),
                json.dumps({"debate_rationale": rationale}),
            )
            # Log event so this axis is locked for future auto-changes.
            await pool.execute(
                """
                INSERT INTO events
                    (project_id, source, type, severity, summary, axes_affected, status)
                VALUES ($1::uuid, 'chat', 'debate_score_update', 'info', $2, $3, 'acted')
                """,
                project_id,
                f"Score {axis} updated via debate: {current_score} → {new_score}",
                [axis],
            )
            locked = True
            await sse.push_event(project_id, "score_update", {
                "score_name": score_name,
                "score": float(new_score),
                "source": "debate",
            })
        except Exception as exc:
            logger.warning("debate score persist failed: %s", exc)

    return {
        "reply":         reply_text,
        "score_changed": score_changed and locked,
        "new_score":     new_score,
        "locked":        locked,
        "rationale":     rationale,
    }
