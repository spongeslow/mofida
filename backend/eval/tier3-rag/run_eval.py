#!/usr/bin/env python3
"""Tier 3 RAG evaluation — Recall@3 and MRR.

Usage:
    python eval/tier3-rag/run_eval.py [--rag-url http://localhost:8300]

Pass thresholds:
    Recall@3 >= 0.80
    MRR      >= 0.70
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import httpx

QUERY_PAIRS = pathlib.Path(__file__).parent / "query_pairs.json"
DEFAULT_RAG_URL = "http://localhost:8300"
TOP_K = 3
RECALL_THRESHOLD = 0.80
MRR_THRESHOLD = 0.70


def _recall_at_k(retrieved: list[str], expected: list[str], k: int) -> float:
    top_k = retrieved[:k]
    hits = sum(1 for e in expected if e in top_k)
    return hits / max(len(expected), 1)


def _rr(retrieved: list[str], expected: list[str]) -> float:
    for rank, rid in enumerate(retrieved, start=1):
        if rid in expected:
            return 1.0 / rank
    return 0.0


def run_eval(rag_url: str) -> dict:
    pairs = json.loads(QUERY_PAIRS.read_text())
    total_recall = 0.0
    total_rr = 0.0
    results: list[dict] = []

    for pair in pairs:
        query = pair["query"]
        stage = pair.get("stage")
        dims = pair.get("dimensions", [])
        sector = pair.get("sector")
        expected = pair["expected_resource_ids"]

        try:
            resp = httpx.post(
                f"{rag_url}/retrieve",
                json={"query": query, "stage": stage, "dimensions": dims, "sector": sector, "top_k": TOP_K},
                timeout=60.0,
            )
            resp.raise_for_status()
            retrieved_ids = [r["resource_id"] for r in resp.json().get("results", [])]
        except Exception as exc:
            print(f"[FAIL] query='{query[:50]}...' error={exc}", file=sys.stderr)
            retrieved_ids = []

        recall = _recall_at_k(retrieved_ids, expected, TOP_K)
        rr = _rr(retrieved_ids, expected)
        total_recall += recall
        total_rr += rr

        results.append({
            "query": query[:60],
            "expected": expected,
            "retrieved": retrieved_ids,
            "recall_at_3": round(recall, 3),
            "rr": round(rr, 3),
        })

    n = len(pairs)
    mean_recall = total_recall / n if n else 0.0
    mrr = total_rr / n if n else 0.0

    return {
        "n": n,
        "recall_at_3": round(mean_recall, 4),
        "mrr": round(mrr, 4),
        "pass": mean_recall >= RECALL_THRESHOLD and mrr >= MRR_THRESHOLD,
        "thresholds": {"recall_at_3": RECALL_THRESHOLD, "mrr": MRR_THRESHOLD},
        "per_query": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Tier 3 RAG evaluation")
    parser.add_argument("--rag-url", default=DEFAULT_RAG_URL)
    args = parser.parse_args()

    report = run_eval(args.rag_url)
    print(json.dumps({k: v for k, v in report.items() if k != "per_query"}, indent=2))
    print(f"\nPer-query breakdown:")
    for r in report["per_query"]:
        status = "✓" if r["recall_at_3"] > 0 else "✗"
        print(f"  {status} Recall@3={r['recall_at_3']} MRR={r['rr']}  {r['query']}")
    print()
    if report["pass"]:
        print("PASS — Recall@3 and MRR meet thresholds.")
        sys.exit(0)
    else:
        print(
            f"FAIL — Recall@3={report['recall_at_3']} (need {RECALL_THRESHOLD})  "
            f"MRR={report['mrr']} (need {MRR_THRESHOLD})"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
