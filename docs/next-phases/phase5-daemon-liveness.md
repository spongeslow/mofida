# Phase 5 — Go Daemon & Liveness

> 📍 Plan order: needs axis `metric_update` logic (depends on Phase 2b axes being correct) and the RAG admin endpoint (Phase 3). Can run in parallel with Phase 4. See [README](./README.md).

**Goal:** The system updates scores and alerts autonomously without any user action. The Go daemon's five watchers perform real scraping/checking and publish structured messages to Redis. The orchestrator's Redis consumer routes those messages to the correct axis services.

**Prerequisites:**
- Phase 2 complete (axis `metric_update` endpoints exist)
- Phase 3 complete (RAG admin endpoint exists for KB staleness flagging)
- Phase 4 SSE consumer working (alerts need somewhere to display)

---

## Current State

| Component | File | Status |
|---|---|---|
| Budget watcher | `daemon/internal/watchers/watchers.go` | ⏳ Heartbeat only |
| Competitor watcher | `daemon/internal/watchers/watchers.go` | ⏳ Heartbeat only |
| Legal radar | `daemon/internal/watchers/watchers.go` | ⏳ Heartbeat only |
| Milestone checker | `daemon/internal/watchers/watchers.go` | ⏳ Heartbeat only |
| Trend scanner | `daemon/internal/watchers/watchers.go` | ⏳ Heartbeat only |
| KB staleness checker | `daemon/internal/kbstaleness/checker.go` | ⏳ Heartbeat only |
| Redis publisher | `daemon/internal/redis/publisher.go` | ⏳ Logs instead of publishing |
| Orchestrator consumer | `orchestrator/app/redis_consumer.py` | ❌ Not built |

---

## Step 1 — Wire Real Redis into the Go Daemon

**File:** `daemon/go.mod` + `daemon/internal/redis/publisher.go`

Add `go-redis` as the only external dependency:

```bash
cd daemon
go get github.com/redis/go-redis/v9
```

Update `publisher.go` to use a real Redis client:

```go
package redis

import (
    "context"
    "encoding/json"
    "log"
    "time"

    goredis "github.com/redis/go-redis/v9"
)

type Publisher struct {
    client  *goredis.Client
    channel string
}

func NewPublisher(url, channel string) (*Publisher, error) {
    opt, err := goredis.ParseURL(url)
    if err != nil {
        return nil, fmt.Errorf("invalid REDIS_URL %q: %w", url, err)
    }
    client := goredis.NewClient(opt)
    if err := client.Ping(context.Background()).Err(); err != nil {
        return nil, fmt.Errorf("redis ping failed: %w", err)
    }
    log.Printf("[redis] connected to %s channel=%s", url, channel)
    return &Publisher{client: client, channel: channel}, nil
}

func (p *Publisher) Publish(ctx context.Context, projectID, metricType string, value any) error {
    m := Metric{
        ProjectID: projectID,
        Type:      metricType,
        Value:     value,
        Timestamp: time.Now().UTC().Format(time.RFC3339),
    }
    b, _ := json.Marshal(m)
    return p.client.Publish(ctx, p.channel, string(b)).Err()
}
```

Update `daemon/cmd/main.go` to handle the `error` return from `NewPublisher` and to pass `context.Background()` to watchers.

---

## Step 2 — Budget Watcher

**New file:** `daemon/internal/watchers/budget.go`

**Cadence:** Every 6 hours.

**Logic:**
1. Call `GET http://{ORCHESTRATOR_URL}/api/v1/project/{project_id}` to read the project profile.
2. Extract `finance.burn_rate_usd` (monthly spend) and `finance.runway_months`.
3. Derive a virtual "budget percentage used" as `1 - (runway_months / initial_runway_months)`. Since we don't have a starting runway reference, a simpler heuristic: if `runway_months < 6` → warning, if `runway_months < 3` → critical.
4. Publish thresholds:
   - `runway_months < 6` → `type: "budget", value: {"runway_months": N, "severity": "warning"}`
   - `runway_months < 3` → `type: "budget", value: {"runway_months": N, "severity": "critical"}`
   - `runway_months < 1` → `type: "budget", value: {"runway_months": N, "severity": "fatal"}`

```go
type BudgetWatcher struct {
    base
    orchestratorURL string
    projectID       string
}

func (w *BudgetWatcher) tick(ctx context.Context) {
    profile, err := fetchProfile(ctx, w.orchestratorURL, w.projectID)
    if err != nil { log.Printf("[budget] fetch error: %v", err); return }
    
    runway := profile["finance"].(map[string]any)["runway_months"]
    // ... classify severity and publish
}
```

**Important:** The watcher must read `project_id` from Redis or from an env var. For Phase 5, use an env var `MOUFIDA_PROJECT_ID` as a simple single-project mode. Multi-project support is Phase 6.

---

## Step 3 — Competitor Watcher

**New file:** `daemon/internal/watchers/competitor.go`

**Cadence:** Every 12 hours.

**Logic:**
1. Read competitor list from the project profile (`market.competitors` — a list of `{name, url}` objects). If the profile has no competitors, log a skip.
2. For each competitor URL, fetch its homepage or RSS feed and compute an MD5 hash of the response body.
3. Compare with the previously stored hash (stored in a local JSON file: `daemon/state/competitor_hashes.json`).
4. On change: publish `type: "competitor", value: {name, url, event: "page_changed"}`.
5. Update stored hashes.

**RSS feeds to always monitor** (sector-agnostic):
- `https://www.wamda.com/feed` — Arab startup news
- `https://technewsafrica.com/feed` — Africa tech
- `https://www.africanews.com/rss` — General Africa

For each RSS item, check if any `market.competitor_names` appears in the title. If yes, publish `type: "competitor", value: {name: ..., event: "news_mention", headline: ...}`.

```go
type CompetitorWatcher struct {
    base
    stateFile string
}

type competitorState struct {
    Hashes map[string]string `json:"hashes"`
    LastRun string            `json:"last_run"`
}
```

---

## Step 4 — Legal Radar

**New file:** `daemon/internal/watchers/legal.go`

**Cadence:** Daily.

**Feeds to monitor:**
- Tunisian Official Journal (JORT): `http://www.iort.gov.tn/WD120AWP/WD120Awp.exe/CONNECT/IORT_INTERNET` — scrape latest publications
- EUR-Lex (AI Act / GDPR updates): `https://eur-lex.europa.eu/legal-content/FR/LSU/?uri=CELEX:32016R0679` (RSS)
- INNORPI news: scrape `https://www.innorpi.tn`

**Keyword filter:** `["RGPD", "GDPR", "AI Act", "Startup Act", "loi organique", "protection des données", "propriété intellectuelle", "financement startup"]`

**Logic:**
1. Fetch each feed URL.
2. For each item, check if any keyword appears in title or summary.
3. If new (not seen in `daemon/state/legal_seen.json`): publish `type: "legal", value: {source, title, url, keywords_matched}`.
4. Store seen item IDs.

---

## Step 5 — Milestone Checker

**New file:** `daemon/internal/watchers/milestone.go`

**Cadence:** Daily.

**Logic:**
1. Read project milestones from `GET /api/v1/project/{id}` profile field `milestones: [{name, deadline_date, completed}]`.
2. For each incomplete milestone, compute `days_left = deadline_date - today`.
3. At `days_left ∈ {14, 7, 1, 0}`: publish `type: "milestone", value: {name, deadline_date, days_left}`.
4. Avoid re-publishing the same threshold: store published thresholds in `daemon/state/milestone_alerts.json`.

**Date parsing:** Use Go's `time.Parse("2006-01-02", deadline)`.

---

## Step 6 — Trend Scanner

**New file:** `daemon/internal/watchers/trend.go`

**Cadence:** Weekly.

**Logic:**
1. Read the project's sector and key topics from profile (`sector`, `market.keywords` — a list of strings the founder cares about).
2. Fetch RSS from TechCrunch (`https://techcrunch.com/feed`), Wamda (`https://www.wamda.com/feed`), AfricArena (`https://africarena.com/feed`).
3. Count occurrences of each keyword across all item titles + summaries.
4. Compare with counts from the previous week (stored in `daemon/state/trend_counts.json`).
5. If a keyword frequency changed by > 50%: publish `type: "trend", value: {keyword, previous_count, current_count, change_pct, direction}`.
6. Update stored counts with current week's data.

---

## Step 7 — KB Staleness Checker

**File:** `daemon/internal/kbstaleness/checker.go`

**Cadence:** Daily.

**Logic:**
1. Call `GET http://{RAG_URL}/admin/resources` (add this endpoint to RAG service — returns all resources with their `id`, `url`, `last_verified`).
2. For each resource where `last_verified` is older than 90 days:
   - Fetch `resource.url`.
   - Compute MD5 hash of response body.
   - Compare with stored hash (`daemon/state/kb_hashes.json`).
   - If hash changed: call `POST {RAG_URL}/admin/flag/{resource_id}` → marks `needs_review = true` in Qdrant.
3. Update stored hashes and `last_checked` timestamps.

**New RAG admin endpoint needed:**
```python
@app.get("/admin/resources")
def list_resources():
    """Returns all resource IDs, URLs, and last_verified dates."""
    # Read from knowledge-base/resources/*.json
    resources = load_all_resources()
    return [{"id": r["id"], "url": r["url"], "last_verified": r["last_verified"]} for r in resources]
```

---

## Step 8 — Orchestrator Redis Consumer

**File:** `orchestrator/app/redis_consumer.py`

**What it does:** Long-running async task that subscribes to `moufida:metrics` and forwards each message to the correct axis service's `/metric_update` endpoint.

```python
import asyncio
import json
import logging

import httpx
import redis.asyncio as aioredis

from .axis_registry import METRIC_ROUTES, axis_host

logger = logging.getLogger("moufida.redis_consumer")

REDIS_URL = os.environ["REDIS_URL"]
REDIS_CHANNEL = os.environ["REDIS_METRICS_CHANNEL"]


async def consume():
    """Subscribe to moufida:metrics and fan out to axis metric_update endpoints."""
    client = aioredis.from_url(REDIS_URL)
    pubsub = client.pubsub()
    await pubsub.subscribe(REDIS_CHANNEL)
    logger.info("Redis consumer started, listening on %s", REDIS_CHANNEL)

    async for message in pubsub.listen():
        if message["type"] != "message":
            continue
        try:
            data = json.loads(message["data"])
        except (json.JSONDecodeError, TypeError):
            continue

        metric_type = data.get("type")
        target_slugs = METRIC_ROUTES.get(metric_type, [])
        if not target_slugs:
            logger.debug("No route for metric type %r", metric_type)
            continue

        async with httpx.AsyncClient(timeout=10.0) as http:
            for slug in target_slugs:
                url = f"{axis_host(slug)}/metric_update"
                try:
                    resp = await http.post(url, json=data)
                    logger.info("metric_update %s -> %s: %d", metric_type, slug, resp.status_code)
                except httpx.HTTPError as exc:
                    logger.warning("metric_update failed for %s: %s", slug, exc)
```

**Wire into orchestrator lifespan in `main.py`:**
```python
from contextlib import asynccontextmanager
import asyncio
from . import redis_consumer as _redis_consumer

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_redis_consumer.consume())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(title="Moufida Orchestrator", lifespan=lifespan)
```

---

## Step 9 — Watcher Restructuring (Separate Files)

The current `watchers.go` has a single `base` struct for all watchers. In Phase 5, split into individual files:

```
daemon/internal/watchers/
├── base.go        # shared Watcher interface + base tick loop
├── budget.go      # BudgetWatcher
├── competitor.go  # CompetitorWatcher
├── legal.go       # LegalWatcher
├── milestone.go   # MilestoneWatcher
└── trend.go       # TrendWatcher
```

Each watcher gets its own struct with its specific config (URLs, state file path, etc.) and implements the `tick(ctx context.Context)` method called by the base loop.

---

## Daemon State Files

Create `daemon/state/` directory (gitignored):
```
daemon/state/
├── competitor_hashes.json   # {url: md5_hash}
├── legal_seen.json          # [item_id, ...]
├── milestone_alerts.json    # {milestone_name: [thresholds_already_published]}
├── trend_counts.json        # {week_start: {keyword: count}}
└── kb_hashes.json           # {resource_id: md5_hash}
```

Add to `.gitignore`:
```
daemon/state/
```

---

## Environment Variables Added

Add to `.env` and `.env.example`:
```
MOUFIDA_PROJECT_ID=       # default project UUID for single-project daemon mode
ORCHESTRATOR_URL=         # already exists
RAG_URL=                  # already exists
```

---

## Metric_Update Logic in Axis Services

Once the Redis consumer is routing messages, the axis services need to do something on `metric_update`. Currently they all return `{"status": "not_implemented"}`.

**Axis 02 — Market (`competitor` signal):**
```python
@app.post("/metric_update")
async def metric_update(payload: dict):
    # Re-run Affinitree market score with updated competitor context
    # If score drops > 0.5: push SSE alert (via orchestrator SSE endpoint)
    # Return new score
```

**Axis 05 — Business Model (`budget` signal):**
```python
@app.post("/metric_update")
async def metric_update(payload: dict):
    runway = payload["value"]["runway_months"]
    # Re-run Affinitree scalability score
    # If runway < 3 months: severity = "critical"
    # Push SSE alert
```

**Axis 06 — Legal (`legal` signal):**
```python
@app.post("/metric_update")
async def metric_update(payload: dict):
    # Update the compliance checklist based on new regulation
    # Re-run Affinitree green score
    # Push SSE alert if new blocker introduced
```

These SSE pushes use `POST /api/v1/sse/push/{project_id}` — add this internal endpoint to the orchestrator that calls `sse.push_event()`.

---

## Completion Criteria

- [ ] `docker compose logs daemon` shows real published messages, not "logging only"
- [ ] `redis-cli -u $REDIS_URL subscribe moufida:metrics` receives JSON messages from the daemon
- [ ] `docker compose logs orchestrator` shows "metric_update competitor -> market: 200" when a competitor event fires
- [ ] Sending a test message via `redis-cli publish moufida:metrics '{"project_id":"...","type":"budget","value":{"runway_months":2},"timestamp":"..."}'` → AlertFeed shows a critical budget alert within 5 seconds
- [ ] KB staleness checker flags a resource `needs_review=true` in Qdrant when a test URL's hash changes
- [ ] `GET http://localhost:8200/health` still returns ok after 24 hours of daemon running (no memory leaks)
