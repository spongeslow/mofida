#!/usr/bin/env bash
# Run every evaluation tier and print a consolidated summary.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${PY:-$ROOT/scoring-engine/.venv/bin/python}"
rc=0

echo "==================== Tier 2 -- Affinitree ===================="
"$PY" "$ROOT/eval/tier2-affinitree/run_eval.py" --determinism --anomaly --text-stability || rc=1

echo
echo "==================== Tier 1 -- Maturity (Axis 01) ===================="
if [ -f "$ROOT/eval/tier1-maturity/run_eval.py" ]; then
  "$PY" "$ROOT/eval/tier1-maturity/run_eval.py" || rc=1
else
  echo "SKIPPED -- tier1 runner not present yet (Phase 2)."
fi

echo
echo "==================== Tier 3 -- RAG retrieval ===================="
if [ -f "$ROOT/eval/tier3-rag/run_eval.py" ]; then
  "$PY" "$ROOT/eval/tier3-rag/run_eval.py" || rc=1
else
  echo "SKIPPED -- tier3 runner not present yet (Phase 3)."
fi

echo
[ $rc -eq 0 ] && echo "ALL PRESENT TIERS PASSED" || echo "ONE OR MORE TIERS FAILED"
exit $rc
