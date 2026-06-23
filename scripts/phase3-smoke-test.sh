#!/usr/bin/env bash
# Phase 3 (C) smoke test — validates the continuous-update and roadmap-engine
# endpoints introduced in Phases B and C.
#
# Requires Phase 2 stack to be running (docker compose up -d).
# Expects phase2-smoke-test.sh to have passed at least once (creates the DB schema).
#
# Usage:  bash scripts/phase3-smoke-test.sh
set -uo pipefail

ORCH="http://localhost:8001"
RETRIES=30
SLEEP=2

red()    { printf '\033[31m%s\033[0m\n' "$1"; }
green()  { printf '\033[32m%s\033[0m\n' "$1"; }
yellow() { printf '\033[33m%s\033[0m\n' "$1"; }
fail()   { red "FAIL: $1"; exit 1; }

check_field() {
  local resp="$1" field="$2" label="$3"
  if echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); assert '$field' in d, '$field missing'" 2>/dev/null; then
    green "   ok  $label"
  else
    fail "$label — field '$field' missing in: $resp"
  fi
}

# ---------------------------------------------------------------------------
# 0. Wait for orchestrator.
# ---------------------------------------------------------------------------
echo ">> Waiting for orchestrator..."
for _ in $(seq 1 $RETRIES); do
  if curl -fsS "${ORCH}/health" >/dev/null 2>&1; then break; fi
  sleep $SLEEP
done
curl -fsS "${ORCH}/health" >/dev/null 2>&1 || fail "orchestrator not healthy"
green "   orchestrator ok"

# ---------------------------------------------------------------------------
# 1. Create a fresh project in CREATION mode.
# ---------------------------------------------------------------------------
echo ">> Creating test project..."
CREATE=$(curl -fsS -X POST "${ORCH}/api/v1/project/new" \
  -H 'content-type: application/json' \
  -d '{"sector":"agri-food","language":"fr","profile":{}}') || fail "POST /project/new"
PID=$(echo "$CREATE" | python3 -c "import sys,json; print(json.load(sys.stdin)['project_id'])") \
  || fail "project_id missing in create response"
green "   project_id = $PID"

# ---------------------------------------------------------------------------
# 2. Plan sections — generation loop (ideation only for speed).
# ---------------------------------------------------------------------------
echo ">> Generation loop (ideation axis)..."
GEN=$(curl -fsS -X POST "${ORCH}/api/v1/project/${PID}/generate/ideation" \
  -H 'content-type: application/json' \
  -d '{"constraints":null}') || fail "POST /generate/ideation"
check_field "$GEN" "content"    "generate/ideation → content"
check_field "$GEN" "summary"    "generate/ideation → summary"
check_field "$GEN" "assumptions" "generate/ideation → assumptions"

APPROVE=$(curl -fsS -X POST "${ORCH}/api/v1/project/${PID}/generate/ideation/approve" \
  -H 'content-type: application/json' \
  -d "{\"content\": $(echo "$GEN" | python3 -c 'import sys,json; print(json.dumps(json.load(sys.stdin)["content"]))'), \"summary\":\"smoke test\"}") \
  || fail "POST /generate/ideation/approve"
check_field "$APPROVE" "version" "approve/ideation → version"

# ---------------------------------------------------------------------------
# 3. Plan document — GET plan.
# ---------------------------------------------------------------------------
echo ">> Plan document..."
PLAN=$(curl -fsS "${ORCH}/api/v1/project/${PID}/plan") || fail "GET /plan"
check_field "$PLAN" "sections" "GET /plan → sections"

# ---------------------------------------------------------------------------
# 4. Events feed — listing and filtering.
# ---------------------------------------------------------------------------
echo ">> Events feed..."
EVENTS=$(curl -fsS "${ORCH}/api/v1/project/${PID}/events") || fail "GET /events"
check_field "$EVENTS" "events" "GET /events → events"

EVENTS_FILTERED=$(curl -fsS "${ORCH}/api/v1/project/${PID}/events?source=manual&limit=10") \
  || fail "GET /events?source=manual"
check_field "$EVENTS_FILTERED" "events" "GET /events filtered → events"

# ---------------------------------------------------------------------------
# 5. Manual section edit → creates an event.
# ---------------------------------------------------------------------------
echo ">> Manual section edit..."
CONTENT_JSON=$(echo "$GEN" | python3 -c 'import sys,json; print(json.dumps(json.load(sys.stdin)["content"]))')
EDIT=$(curl -fsS -X POST "${ORCH}/api/v1/project/${PID}/section/ideation" \
  -H 'content-type: application/json' \
  -d "{\"content\": $CONTENT_JSON, \"summary\":\"smoke edit\"}") || fail "POST /section/ideation"
check_field "$EDIT"    "event_id"         "section edit → event_id"
check_field "$EDIT"    "downstream_axes"  "section edit → downstream_axes"
EVENT_ID=$(echo "$EDIT" | python3 -c "import sys,json; print(json.load(sys.stdin)['event_id'])")
green "   event_id = $EVENT_ID"

# ---------------------------------------------------------------------------
# 6. Event actions — ignore the event.
# ---------------------------------------------------------------------------
echo ">> Event actions (ignore)..."
IGN=$(curl -fsS -X POST "${ORCH}/api/v1/event/${EVENT_ID}/ignore") || fail "POST /event/ignore"
check_field "$IGN" "status" "ignore → status"
STATUS=$(echo "$IGN" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
[ "$STATUS" = "ignored" ] || fail "ignore status expected 'ignored', got '$STATUS'"
green "   ignore ok"

# Re-event: mark manual
EDIT2=$(curl -fsS -X POST "${ORCH}/api/v1/project/${PID}/section/ideation" \
  -H 'content-type: application/json' \
  -d "{\"content\": $CONTENT_JSON, \"summary\":\"smoke edit 2\"}") || fail "POST /section/ideation (2)"
EVENT_ID2=$(echo "$EDIT2" | python3 -c "import sys,json; print(json.load(sys.stdin)['event_id'])")
MAN=$(curl -fsS -X POST "${ORCH}/api/v1/event/${EVENT_ID2}/manual") || fail "POST /event/manual"
check_field "$MAN" "status" "manual → status"
green "   manual ok"

# ---------------------------------------------------------------------------
# 7. Event diff.
# ---------------------------------------------------------------------------
echo ">> Event diff..."
DIFF=$(curl -fsS "${ORCH}/api/v1/event/${EVENT_ID}/diff") || fail "GET /event/diff"
check_field "$DIFF" "diff" "GET /event/diff → diff"

# ---------------------------------------------------------------------------
# 8. What's new summary.
# ---------------------------------------------------------------------------
echo ">> What's new..."
WN=$(curl -fsS "${ORCH}/api/v1/project/${PID}/whats-new?language=fr") || fail "GET /whats-new"
check_field "$WN" "events" "GET /whats-new → events"

# ---------------------------------------------------------------------------
# 9. Knowledge base — add entry.
# ---------------------------------------------------------------------------
echo ">> KB add entry..."
KB=$(curl -fsS -X POST "${ORCH}/api/v1/project/${PID}/kb" \
  -H 'content-type: application/json' \
  -d '{"content":"Test knowledge base entry for smoke testing.","title":"Smoke entry"}') \
  || fail "POST /kb"
check_field "$KB" "kb_id"      "POST /kb → kb_id"
check_field "$KB" "kb_version" "POST /kb → kb_version"

# ---------------------------------------------------------------------------
# 10. Roadmap provenance.
# ---------------------------------------------------------------------------
echo ">> Roadmap provenance..."
PROV=$(curl -fsS "${ORCH}/api/v1/project/${PID}/roadmap/provenance") || fail "GET /roadmap/provenance"
check_field "$PROV" "stale" "GET /roadmap/provenance → stale"

# ---------------------------------------------------------------------------
# 11. Projects list — project appears in list.
# ---------------------------------------------------------------------------
echo ">> Projects list..."
PROJECTS=$(curl -fsS "${ORCH}/api/v1/projects") || fail "GET /projects"
check_field "$PROJECTS" "projects" "GET /projects → projects"
FOUND=$(echo "$PROJECTS" | python3 -c "
import sys, json
projects = json.load(sys.stdin)['projects']
print(any(p['project_id'] == '$PID' for p in projects))
")
[ "$FOUND" = "True" ] || yellow "   warn: project not yet in projects list (may be filtered)"

# ---------------------------------------------------------------------------
# 12. Delete project.
# ---------------------------------------------------------------------------
echo ">> Delete project..."
DEL=$(curl -fsS -X DELETE "${ORCH}/api/v1/project/${PID}") || fail "DELETE /project"
check_field "$DEL" "deleted" "DELETE /project → deleted"
DELETED=$(echo "$DEL" | python3 -c "import sys,json; print(json.load(sys.stdin)['deleted'])")
[ "$DELETED" = "True" ] || fail "deleted flag expected True, got $DELETED"

green "
>> All Phase 3 smoke tests passed."
