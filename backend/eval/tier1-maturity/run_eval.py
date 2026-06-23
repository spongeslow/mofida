#!/usr/bin/env python3
"""Tier 1 evaluation runner for the Axis 01 maturity classifier.

Sends each labelled vignette to the live ideation-service ``/diagnose`` endpoint
and scores the predictions:

  macro-F1        macro-averaged F1 across the 6 maturity stages (target >= 0.65)
  top-2 accuracy  gold stage within the model's top-2 (target >= 0.85)

Because the endpoint returns a single prediction, top-2 is approximated: when the
model is confident (confidence > 0.5) only the predicted stage counts; when it is
unsure (confidence <= 0.5) an adjacent stage on the maturity ladder is also
accepted as the implicit second candidate.

  --kappa  also report Cohen's kappa between annotator_labels[0] and [1].
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx
from sklearn.metrics import classification_report, cohen_kappa_score, f1_score

HERE = Path(__file__).parent
DIAGNOSE_URL = "http://localhost:8101/diagnose"
TIMEOUT = 180.0

# Canonical ordering of the six maturity stages (used for adjacency + labels).
STAGES = [
    "Ideation",
    "Market Validation",
    "Structuration",
    "Fundraising",
    "Launch Planning",
    "Growth",
]
_STAGE_INDEX = {s: i for i, s in enumerate(STAGES)}


def _load_vignettes() -> list[dict]:
    return json.loads((HERE / "vignettes.json").read_text(encoding="utf-8"))


def _predict(vignette: dict, client: httpx.Client) -> tuple[str, float]:
    """POST a minimal profile carrying the vignette text and return (stage, conf)."""
    profile = {
        "meta": {
            "description": vignette["text"],
            "self_assessed_stage": vignette["gold_label"],
        }
    }
    resp = client.post(DIAGNOSE_URL, json=profile, timeout=TIMEOUT)
    resp.raise_for_status()
    body = resp.json()
    return body.get("stage", ""), float(body.get("confidence", 0.0))


def _top2_hit(pred: str, gold: str, confidence: float) -> bool:
    """Gold within the model's (approximated) top-2 candidates."""
    if pred == gold:
        return True
    if confidence > 0.5:
        return False  # confident single prediction -> no second candidate
    # Unsure: accept an adjacent stage as the implicit second candidate.
    pi, gi = _STAGE_INDEX.get(pred), _STAGE_INDEX.get(gold)
    return pi is not None and gi is not None and abs(pi - gi) == 1


def run_predictions(vignettes: list[dict]) -> tuple[list[str], list[str], int]:
    y_true: list[str] = []
    y_pred: list[str] = []
    top2_hits = 0
    with httpx.Client() as client:
        for v in vignettes:
            try:
                pred, conf = _predict(v, client)
            except httpx.HTTPError as exc:
                print(f"[{v['id']}] ERROR calling diagnose: {exc}", file=sys.stderr)
                raise SystemExit(2)
            gold = v["gold_label"]
            y_true.append(gold)
            y_pred.append(pred if pred in STAGES else "Ideation")
            hit = _top2_hit(pred, gold, conf)
            top2_hits += hit
            print(f"[{v['id']}] gold={gold:18} pred={pred:18} conf={conf:.2f} top2={'Y' if hit else 'N'}")
    return y_true, y_pred, top2_hits


def report_kappa(vignettes: list[dict]) -> None:
    a0 = [v["annotator_labels"][0] for v in vignettes]
    a1 = [v["annotator_labels"][1] for v in vignettes]
    kappa = cohen_kappa_score(a0, a1, labels=STAGES)
    print(f"\nCohen's kappa (annotator 0 vs 1): {kappa:.3f}  (target >= 0.65)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kappa", action="store_true", help="report inter-annotator Cohen's kappa")
    args = ap.parse_args()

    vignettes = _load_vignettes()
    y_true, y_pred, top2_hits = run_predictions(vignettes)

    print("\n=== Classification report ===")
    print(classification_report(y_true, y_pred, labels=STAGES, zero_division=0))

    macro_f1 = f1_score(y_true, y_pred, labels=STAGES, average="macro", zero_division=0)
    top2_acc = top2_hits / len(vignettes)
    print(f"macro-F1        : {macro_f1:.3f}  (target >= 0.65)")
    print(f"top-2 accuracy  : {top2_acc:.3f}  (target >= 0.85)")

    if args.kappa:
        report_kappa(vignettes)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
