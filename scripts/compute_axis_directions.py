#!/usr/bin/env python3
"""Compute Contrastive Axis Directions and install them into moufida-signal.

Implements the offline step of the Representation-Engineering probe
(docs/research/contrastive-axis-directions-embedding.md):

  1. Scroll every chunk vector + payload out of the Qdrant KB collection.
  2. For each diagnostic axis, split chunks into positives / negatives using the
     existing ``score_dimensions`` tags and resource ``type``.
  3. direction_a = normalize( mean(positives) - mean(negatives) ).
  4. Compute per-axis (mean, std) of the raw projections over all chunks
     (used to squash dot-products into [0,1] at query time).
  5. POST the directions + stats to the signal service's /probe/install
     (no shared volume required); optionally also save .npy + stats JSON.

Run (inside the compose network)::

    docker compose --profile tools run --rm compute-directions

Or on the host with a reachable Qdrant + signal::

    QDRANT_URL=http://localhost:6333 SIGNAL_URL=http://localhost:8010 \
        python scripts/compute_axis_directions.py
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request

import numpy as np
from qdrant_client import QdrantClient

QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")
QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION", "moufida-kb")
SIGNAL_URL = os.environ.get("SIGNAL_URL", "http://signal:8010")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR")  # optional: also write .npy + stats JSON
MIN_POSITIVES = int(os.environ.get("PROBE_MIN_POSITIVES", "3"))

# Axis → score_dimensions that count as positive evidence for that axis.
AXIS_TO_SCORE_DIM: dict[str, list[str]] = {
    "ideation":       ["innovation"],
    "market":         ["market"],
    "product":        ["commercial_offer"],
    "brand":          ["innovation"],
    "business-model": ["scalability", "commercial_offer"],
    "legal":          ["green"],
    "operations":     ["scalability"],
    "marketing":      ["market", "commercial_offer"],
    "sales":          ["commercial_offer"],
}

# Axis → resource types that also count as positive (complements score_dimensions).
AXIS_TO_RESOURCE_TYPE: dict[str, list[str]] = {
    "business-model": ["financing"],
    "legal":          ["legal_regulatory"],
    "operations":     ["technical_infrastructure"],
    "marketing":      ["networking_ecosystem"],
    "ideation":       ["training_coaching"],
}


def _scroll_all(client: QdrantClient, collection: str) -> list:
    points: list = []
    offset = None
    while True:
        batch, offset = client.scroll(
            collection_name=collection,
            with_vectors=True,
            with_payload=True,
            limit=256,
            offset=offset,
        )
        points.extend(batch)
        if offset is None:
            break
    return points


def _is_positive(axis: str, dims: set[str], rtype: str) -> bool:
    pos_dims = set(AXIS_TO_SCORE_DIM.get(axis, []))
    pos_types = set(AXIS_TO_RESOURCE_TYPE.get(axis, []))
    return bool(dims & pos_dims) or rtype in pos_types


def _install(payload: dict) -> None:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{SIGNAL_URL}/probe/install",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
        print(f"signal /probe/install → {resp.status}: {body}")


def main() -> int:
    client = QdrantClient(url=QDRANT_URL)
    print(f"scrolling {QDRANT_COLLECTION} at {QDRANT_URL} ...")
    points = _scroll_all(client, QDRANT_COLLECTION)
    if not points:
        print("no points in collection — run KB ingest first", file=sys.stderr)
        return 1

    vectors = np.array([p.vector for p in points], dtype=np.float32)
    embed_dim = vectors.shape[1]
    print(f"{len(points)} chunks, embed_dim={embed_dim}")

    meta = []
    for p in points:
        payload = p.payload or {}
        dims = set(payload.get("score_dimensions", []) or [])
        rtype = payload.get("type", "") or ""
        meta.append((dims, rtype))

    axis_names: list[str] = []
    directions: list[list[float]] = []
    stats: dict[str, dict[str, float]] = {}

    for axis in sorted(AXIS_TO_SCORE_DIM):
        pos_idx = [i for i, (dims, rtype) in enumerate(meta) if _is_positive(axis, dims, rtype)]
        neg_idx = [i for i in range(len(points)) if i not in set(pos_idx)]
        if len(pos_idx) < MIN_POSITIVES or not neg_idx:
            print(f"  ! {axis}: only {len(pos_idx)} positives — skipping")
            continue

        mu_pos = vectors[pos_idx].mean(axis=0)
        mu_neg = vectors[neg_idx].mean(axis=0)
        direction = mu_pos - mu_neg
        norm = float(np.linalg.norm(direction))
        if norm < 1e-9:
            print(f"  ! {axis}: degenerate direction — skipping")
            continue
        direction = direction / norm

        projections = vectors @ direction
        stats[axis] = {"mean": float(projections.mean()), "std": float(projections.std())}
        axis_names.append(axis)
        directions.append(direction.astype(np.float32).tolist())
        print(f"  ✓ {axis}: {len(pos_idx)} pos / {len(neg_idx)} neg")

    if not axis_names:
        print("no axis directions could be computed", file=sys.stderr)
        return 1

    payload = {
        "axis_names": axis_names,
        "embed_dim": embed_dim,
        "directions": directions,
        "stats": stats,
    }

    if OUTPUT_DIR:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        np.save(os.path.join(OUTPUT_DIR, "probe_directions.npy"),
                np.array(directions, dtype=np.float32))
        with open(os.path.join(OUTPUT_DIR, "probe_stats.json"), "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)
        print(f"saved npy + stats to {OUTPUT_DIR}")

    try:
        _install(payload)
    except Exception as exc:  # noqa: BLE001
        print(f"WARNING: could not reach signal /probe/install: {exc}", file=sys.stderr)
        if not OUTPUT_DIR:
            return 1

    print(f"installed {len(axis_names)} axis directions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
