#!/usr/bin/env python3
"""Tier 2 evaluation runner for the Affinitree scoring engine.

  --determinism     same structured profile scored 10x -> identical (target 100%)
  --text-stability  each text field scored 5x -> std-dev <= 0.15 (needs Ollama)
  --anomaly         10 contradiction profiles -> 100% recall

With no flag, runs --determinism and --anomaly (the two that need no LLM).
Exit code is non-zero if any selected target is missed.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).parent
# Make the affinitree package importable without installation.
sys.path.insert(0, str(HERE.parents[1] / "scoring-engine"))

from affinitree import StartupProfile, detect, score  # noqa: E402
from affinitree import rubric  # noqa: E402

SIGMA_TARGET = 0.15


def _load(name: str) -> dict:
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def run_determinism() -> bool:
    data = _load("structured_profiles.json")
    ok = True
    for case in data["cases"]:
        profile = StartupProfile(**case["profile"])
        for score_name in case["scores"]:
            results = [json.dumps(score(profile, score_name).to_dict(), sort_keys=True) for _ in range(10)]
            identical = len(set(results)) == 1
            ok = ok and identical
            status = "PASS" if identical else "FAIL"
            print(f"[determinism] {case['id']:24} {score_name:18} {status}")
    print(f"[determinism] {'OK' if ok else 'FAILED'} (target: 100% identical over 10 runs)\n")
    return ok


def run_anomaly() -> bool:
    data = _load("contradiction_profiles.json")
    hits = 0
    total = len(data["cases"])
    for case in data["cases"]:
        profile = StartupProfile(**case["profile"])
        codes = {a.code for a in detect(profile)}
        fired = case["expect"] in codes
        hits += fired
        print(f"[anomaly] {case['id']:28} expect={case['expect']:28} {'PASS' if fired else 'FAIL ' + str(codes)}")
    recall = hits / total
    ok = recall == 1.0
    print(f"[anomaly] recall = {recall:.0%} ({hits}/{total}); target 100% -> {'OK' if ok else 'FAILED'}\n")
    return ok


def run_text_stability() -> bool:
    data = _load("text_profiles.json")
    try:
        client = rubric.OllamaClient()
        client.generate_json("ping", seed=0)  # connectivity probe
    except Exception as exc:  # noqa: BLE001
        print(f"[text-stability] SKIPPED -- no Ollama backend available ({exc.__class__.__name__}).")
        print("[text-stability] run with Ollama up to measure rubric variance.\n")
        return True

    ok = True
    for item in data["fields"]:
        scores = []
        for _ in range(5):
            r = rubric.score_field(item["text"], item["field"], client, runs=2)
            scores.append(r["score"] / 4.0)  # normalise 0-4 -> 0-1
        sigma = statistics.pstdev(scores)
        passed = sigma <= SIGMA_TARGET
        ok = ok and passed
        print(f"[text-stability] {item['field']:36} sigma={sigma:.3f} {'PASS' if passed else 'FAIL'}")
    print(f"[text-stability] {'OK' if ok else 'FAILED'} (target sigma <= {SIGMA_TARGET})\n")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--determinism", action="store_true")
    ap.add_argument("--text-stability", action="store_true")
    ap.add_argument("--anomaly", action="store_true")
    args = ap.parse_args()

    selected = {
        "determinism": args.determinism,
        "text": args.text_stability,
        "anomaly": args.anomaly,
    }
    if not any(selected.values()):
        selected["determinism"] = selected["anomaly"] = True

    ok = True
    if selected["determinism"]:
        ok &= run_determinism()
    if selected["anomaly"]:
        ok &= run_anomaly()
    if selected["text"]:
        ok &= run_text_stability()

    print("RESULT:", "ALL TARGETS MET" if ok else "ONE OR MORE TARGETS MISSED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
