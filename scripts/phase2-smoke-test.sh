#!/usr/bin/env bash
# Phase 2 end-to-end smoke test.
#
# Verifies the orchestrator + axis services come up, then drives the full
# STATE_EXISTING path: create project -> adaptive intake -> diagnostic pass,
# and asserts the aggregated result has the expected shape.
#
#   Usage:  bash scripts/phase2-smoke-test.sh
#   Run after:  docker compose up -d
set -uo pipefail

ORCH="http://localhost:8001"
HEALTH_PORTS=(8001 8101 8102 8103 8104 8105 8106 8109 8300)
RETRIES=60
SLEEP=2

red()  { printf '\033[31m%s\033[0m\n' "$1"; }
green() { printf '\033[32m%s\033[0m\n' "$1"; }

fail() { red "FAIL: $1"; exit 1; }

# ---------------------------------------------------------------------------
# 1. Wait for every required service to report healthy.
# ---------------------------------------------------------------------------
echo ">> Waiting for services to become healthy..."
for port in "${HEALTH_PORTS[@]}"; do
  ok=0
  for _ in $(seq 1 "$RETRIES"); do
    if curl -fsS "http://localhost:${port}/health" >/dev/null 2>&1; then
      ok=1; break
    fi
    sleep "$SLEEP"
  done
  if [ "$ok" -eq 1 ]; then
    green "   :${port}/health ok"
  else
    fail "service on :${port} did not become healthy within $((RETRIES * SLEEP))s"
  fi
done

# ---------------------------------------------------------------------------
# 1b. Warm up the Axis 01 maturity model.
#     The first LLM call loads the model into memory and can exceed the
#     diagnostic runner's 30s per-axis timeout; warming it first keeps the
#     diagnostic call fast. Harmless (and skipped) if no LLM is available.
# ---------------------------------------------------------------------------
echo ">> Warming up the maturity model (first call loads it; may take a minute)..."
if curl -fsS --max-time 180 -X POST "http://localhost:8101/diagnose" \
     -H 'content-type: application/json' -d '{"profile":{"sector":"agri-food"}}' >/dev/null 2>&1; then
  green "   model warm"
else
  echo "   (warmup skipped — LLM unavailable; Axis 01 will use its fallback)"
fi

# ---------------------------------------------------------------------------
# 2. Create a new project.
# ---------------------------------------------------------------------------
echo ">> Creating project (POST /api/v1/project/new)..."
CREATE_RESP=$(curl -fsS -X POST "${ORCH}/api/v1/project/new" \
  -H 'content-type: application/json' \
  -d '{"sector":"agri-food","language":"fr"}') || fail "project/new request failed"

PROJECT_ID=$(printf '%s' "$CREATE_RESP" | python3 -c 'import sys,json; print(json.load(sys.stdin)["project_id"])') \
  || fail "could not parse project_id from: $CREATE_RESP"
green "   project_id=${PROJECT_ID}"

# ---------------------------------------------------------------------------
# 3. Drive the adaptive intake flow with hardcoded answers.
#    agri-food / Market Validation / 5 interviews / team of 3 / SARL.
# ---------------------------------------------------------------------------
echo ">> Running intake flow (POST /api/v1/intake/start + /answer)..."
curl -fsS -X POST "${ORCH}/api/v1/intake/start" \
  -H 'content-type: application/json' -d '{"language":"fr"}' >/dev/null \
  || fail "intake/start failed"

read -r -d '' ANSWERS <<'JSON'
{
  "q_sector": "agri-food",
  "q_certifications": "HACCP, bio",
  "q_revenue": false,
  "q_interviews": 5,
  "q_self_stage": "Market Validation",
  "q_team": 3,
  "q_legal": "SARL",
  "q_prototype": true,
  "q_fundraising": "pre-seed"
}
JSON

INTAKE_RESP=$(curl -fsS -X POST "${ORCH}/api/v1/intake/answer" \
  -H 'content-type: application/json' \
  -d "{\"language\":\"fr\",\"answers\":${ANSWERS}}") || fail "intake/answer failed"

INTAKE_RESP="$INTAKE_RESP" python3 <<'PY' || fail "intake did not complete"
import os, sys, json
d = json.loads(os.environ["INTAKE_RESP"])
if not d.get("done"):
    print("intake not done, next:", d.get("question", {}).get("id"))
    sys.exit(1)
print("   intake complete; profile_patch =", json.dumps(d.get("profile_patch", {}), ensure_ascii=False))
PY
green "   intake flow completed"

# ---------------------------------------------------------------------------
# 4. Run the diagnostic pass.
# ---------------------------------------------------------------------------
echo ">> Running diagnostic (POST /api/v1/project/${PROJECT_ID}/run-diagnostic)..."
DIAG_RESP=$(curl -fsS -X POST "${ORCH}/api/v1/project/${PROJECT_ID}/run-diagnostic") \
  || fail "run-diagnostic request failed"

# ---------------------------------------------------------------------------
# 5. Assert the aggregated result shape.
# ---------------------------------------------------------------------------
echo ">> Validating diagnostic response..."
DIAG_RESP="$DIAG_RESP" python3 <<'PY'
import os, sys, json
d = json.loads(os.environ["DIAG_RESP"])
print("---- diagnostic response ----")
print(json.dumps(d, indent=2, ensure_ascii=False))
print("-----------------------------")

errs = []
if not d.get("maturity_stage"):
    errs.append("maturity_stage is null/missing")

scores = d.get("scores") or {}
for k in ("market", "commercial_offer", "innovation", "scalability", "green"):
    if k not in scores:
        errs.append(f"scores missing key: {k}")

if not isinstance(d.get("blockers"), list):
    errs.append("blockers is not a list")

if "perception_gap" not in d:
    errs.append("perception_gap field missing")

if errs:
    print("\nASSERTION FAILURES:")
    for e in errs:
        print("  -", e)
    sys.exit(1)
print("\nall assertions passed")
PY
RESULT=$?

echo
if [ "$RESULT" -eq 0 ]; then
  green "PASS — Phase 2 smoke test succeeded."
  exit 0
else
  red "FAIL — diagnostic response did not meet expectations."
  exit 1
fi
