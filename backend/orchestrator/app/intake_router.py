"""Adaptive-intake endpoints.

Primary surface is the **Computerized Adaptive Testing (CAT)** engine
(``/intake/next``): a genuinely adaptive questionnaire driven by Item Response
Theory — each next question maximises Fisher information about the founder's
latent maturity, so no two founders necessarily see the same questions and the
intake converges in far fewer items than a fixed form.

The flow is fully stateless: the client replays the ``responses`` history each
turn (matching the rest of the orchestrator). The legacy fixed-branch endpoints
(``/intake/start`` and ``/intake/answer``) are retained for backward
compatibility but are no longer used by the app.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from .cat import session as cat_session
from .intake.questionnaire import AdaptiveQuestionnaire

router = APIRouter(prefix="/intake")


# ---------------------------------------------------------------------------
# CAT (adaptive) — primary
# ---------------------------------------------------------------------------

class CatResponse(BaseModel):
    item_id: str
    # Graded response credit in [0, 1] for select items (drives the EAP update);
    # None for free-text items, which gather evidence but don't move the estimate.
    credit: float | None = None
    # The answer mapped into the StartupProfile (option value or free text).
    value: Any | None = None


class NextRequest(BaseModel):
    language: str = "fr"
    responses: list[CatResponse] = []


@router.post("/next")
def intake_next(req: NextRequest):
    """Return the next adaptive question (with the live stage posterior) given
    the answers so far, or the completion payload + profile patch when done."""
    responses = [r.model_dump() for r in req.responses]
    return cat_session.next_question(responses, req.language)


# ---------------------------------------------------------------------------
# Legacy fixed-branch questionnaire — kept for backward compatibility
# ---------------------------------------------------------------------------

class StartRequest(BaseModel):
    language: str = "fr"


class AnswerRequest(BaseModel):
    language: str = "fr"
    answers: dict[str, Any] = {}


@router.post("/start")
def intake_start(req: StartRequest):
    """[legacy] Return the first question of the fixed-branch questionnaire."""
    return AdaptiveQuestionnaire(req.language).start()


@router.post("/answer")
def intake_answer(req: AnswerRequest):
    """[legacy] Given answers gathered so far, return the next fixed-branch
    question or the merged StartupProfile patch."""
    q = AdaptiveQuestionnaire(req.language)
    nxt = q.resume(req.answers)
    if nxt is None:
        return {"done": True, "profile_patch": q.merge_to_profile(req.answers)}
    return {"done": False, "question": nxt}
