"""Stateless adaptive-intake endpoints.

The client carries all state: it sends ``answers`` (keyed by question id) on each
turn and the server replays the branch graph to return the next question or the
final ``profile_patch``.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from .intake.questionnaire import AdaptiveQuestionnaire

router = APIRouter(prefix="/intake")


class StartRequest(BaseModel):
    language: str = "fr"


class AnswerRequest(BaseModel):
    language: str = "fr"
    answers: dict[str, Any] = {}


@router.post("/start")
def intake_start(req: StartRequest):
    """Return the first question in the requested language."""
    return AdaptiveQuestionnaire(req.language).start()


@router.post("/answer")
def intake_answer(req: AnswerRequest):
    """Given the answers gathered so far, return the next question or, when the
    flow is complete, the merged StartupProfile patch."""
    q = AdaptiveQuestionnaire(req.language)
    nxt = q.resume(req.answers)
    if nxt is None:
        return {"done": True, "profile_patch": q.merge_to_profile(req.answers)}
    return {"done": False, "question": nxt}
