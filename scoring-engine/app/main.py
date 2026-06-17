"""Scoring engine HTTP API — thin FastAPI wrapper around the Affinitree library.

Exposes the scoring engine and anomaly detector as HTTP endpoints so they can
be called directly without going through an axis service. Useful for testing,
CI, and interactive exploration of the scoring logic.
"""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from affinitree import StartupProfile, detect, score
from affinitree.scorer import SCORE_CONFIGS

app = FastAPI(title="Affinitree Scoring Engine", version="0.1.0")

VALID_SCORES = list(SCORE_CONFIGS.keys())


class ScoreRequest(BaseModel):
    profile: dict[str, Any]
    score_name: str


class AnomalyRequest(BaseModel):
    profile: dict[str, Any]


@app.get("/health")
def health():
    return {"status": "ok", "service": "scoring-engine", "scores": VALID_SCORES}


@app.post("/score")
def compute_score(req: ScoreRequest):
    if req.score_name not in VALID_SCORES:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown score '{req.score_name}'. Valid: {VALID_SCORES}",
        )
    profile = StartupProfile(**req.profile)
    result = score(profile, req.score_name)
    return {
        "score_name": req.score_name,
        "score": result.score,
        "explanation": result.explanation_tree(),
        "missing_fields": result.missing_fields,
    }


@app.post("/score/all")
def compute_all_scores(profile_data: dict[str, Any]):
    profile = StartupProfile(**profile_data)
    return {
        name: {
            "score": (r := score(profile, name)).score,
            "missing_fields": r.missing_fields,
        }
        for name in VALID_SCORES
    }


@app.post("/detect")
def detect_anomalies(req: AnomalyRequest):
    profile = StartupProfile(**req.profile)
    anomalies = detect(profile)
    return {"anomalies": [a.to_dict() for a in anomalies], "count": len(anomalies)}
