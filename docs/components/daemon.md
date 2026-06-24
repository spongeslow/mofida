# Go Daemon

**Location:** `daemon/` | **Stack:** Go 1.22, redis/go-redis/v9  
No HTTP server — outbound-only.

The daemon is the "always alive" component. It runs 24/7 inside Docker, watching the world for the focused startup even when the app is closed. It is the system's connection to the real world: competitor pages, grant databases, legal feeds, market trends, and project budgets.

---

## Architectural Principles

**No project ID at startup.** The daemon boots without knowing what to watch. It learns by polling `GET /daemon/control` on the orchestrator (which reads the single-row `daemon_control` table). When the focused project changes in the UI, the daemon detects the change on its next heartbeat.

**Hot-swap without restart.** When focus changes, the supervisor cancels the current watcher batch (`context.CancelFunc` + `sync.WaitGroup`), refreshes watch targets, and starts a fresh batch — all in-process.

**Adaptive watch targets.** Before starting each project's watchers, the daemon calls `POST /project/{id}/watch-targets/refresh`. The orchestrator uses the full profile to LLM-derive niche-specific feeds, keywords, and competitor URLs. Cached by profile hash — recomputed only when the profile changes.

---

## Supervisor Loop

```go
for {
    heartbeat()                           // POST /daemon/heartbeat
    newFocus := pollFocusedProject()      // GET /daemon/control

    if newFocus != currentFocus {
        cancelCurrentWatchers()           // context cancel + WaitGroup drain
        targets = refreshTargets(newFocus)
        startProjectWatchers(newFocus, targets)
        currentFocus = newFocus
    }
    time.Sleep(30 * time.Second)
}
```

The `daemon_control` table has a single row (`id=TRUE`) carrying `paused`, `focus_project_id`, `last_beat`, `updated_at`. Pause is a flag — it stops the work but keeps goroutines alive so the UI can distinguish "paused" from "offline."

---

## Watcher Tiers

### Process-Lifetime Watchers (survive focus changes)

**KB Staleness** — nightly: checks RAG service for resources with `last_verified` > 90 days, publishes `needs_review` signal.

**Composio Poller** — every 5 min: polls `POST /integrations/poll` for inbound Composio triggers. Provides NAT-friendly webhook fallback for desktops behind home/office routers.

### Project-Scoped Watchers (restart on focus change)

| Watcher | Frequency | Signal published | Dashboard surface |
|---|---|---|---|
| **Budget** | 6h | `budget_alert` → business-model axis | Event Feed |
| **Competitor** | 12h | `POST /competitor/observe` → LLM extraction + SWOT | Competitor Board |
| **Legal** | 24h | `legal_update` → legal axis | Event Feed |
| **Milestone** | 24h | `milestone` → ideation axis | Event Feed |
| **Trend** | 7 days | `trend_spike` → market axis | Event Feed / "What's new?" |
| **Grant** | 24h | `POST /opportunity/observe` → LLM match scoring | Opportunity Radar |

### Competitor Watcher Detail

For each competitor URL from profile + watch targets:
1. Fetch the page with HTTP client
2. MD5-hash the visible text content
3. Diff against saved hash → if changed: `POST /project/{id}/competitor/observe`
4. Also scan RSS feeds from watch targets for news mentions using profile-derived keywords

State persisted to JSON files in `DAEMON_STATE_DIR` (default `/tmp/moufida-daemon-state`) keyed by project ID.

### Grant Watcher Feeds

Polls: StartupAct/APII announcements, BFPME programme calls, Wamda ecosystem grants, EU Horizon calls, AfricArena competitions, impact investor announcements.

### Signal Flow to Orchestrator

```
Daemon → Redis PUBLISH moufida:signals { type, project_id, axis, data }
       → Orchestrator redis_consumer.py → axis /metric_update endpoint

Daemon → HTTP POST /competitor/observe   (for rich structured observations)
       → HTTP POST /opportunity/observe
```

---

## Why Go?

- A Go binary with 6 goroutines uses < 30 MB RAM vs. ~200 MB for a Python equivalent
- `context.Context` cancellation makes the hot-swap pattern race-free
- Compiles to a single static binary on a scratch base image
- `sync.WaitGroup` ensures watcher goroutines drain cleanly before the new batch starts
