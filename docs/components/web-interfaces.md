# Web Interfaces

---

## Admin Observability Panel

**Location:** `admin/` | **Port:** 3002 | **Stack:** React 18, TypeScript, Vite

A standalone browser SPA that communicates with the orchestrator's `/api/admin/*` routes. Read-only — nothing here changes application state.

### Authentication

Optional `ADMIN_TOKEN` (set in `.env`). When set, the panel prompts for the token on first open. Leave empty for open local access.

### Pages

**Health** — live probes auto-polling every 10s: PostgreSQL, Redis, Qdrant, Ollama (models loaded), SearXNG, Signal (CBM weights loaded + probe calibrated), all 10 axis services (:8101–:8110). Latency shown in ms per service.

**Requests** — paginated HTTP request log from `api_requests`. Columns: method, path, status (colour-coded), duration, project_id, timestamp. Click **Trace →** on any row to see all LLM calls correlated via `request_id` — a distributed trace from one HTTP request to all its downstream Ollama calls.

**LLM Calls** — full log from `llm_calls`. Shows axis, model, prompt preview (280 chars), response preview, input/output token counts, duration. Useful for token usage analysis and prompt debugging.

**Daemon Activity** — log from `daemon_activities`: competitor pages checked, grant calls found, legal entries deduplicated, milestones notified. Verifies the daemon is working correctly without Docker log access.

**Logs** — live SSE stream from the orchestrator's ring-buffer. Colour-coded by level (DEBUG grey, INFO blue, WARNING orange, ERROR red). Tails live during a diagnostic run.

### Why It Matters

Moufida's admin panel demonstrates production-readiness: real observability infrastructure that traces every request end-to-end. During a hackathon demo, judges can watch a diagnosis run in real time, see each Ollama call, verify the daemon is active, and confirm all services are healthy — without any black-box trust.

---

## Landing Page

**Location:** `landing/` | **Stack:** Next.js 14 App Router, TypeScript, Tailwind CSS

Public-facing marketing and waitlist site. Runs independently — no Docker dependency.

**Sections:** Nav, Hero (with `PixelMoufida` component matching the desktop app), TrustBar, Problem, HowItWorks, DueDiligence, Features, AdvancedTools, Integrations, Testimonials, Pricing, FAQ, FinalCTA, Footer.

**API routes:**
- `POST /api/waitlist` — waitlist signup → Supabase
- `POST /api/track` — analytics event tracking

**SEO:** dynamic OG image generation (`opengraph-image.tsx`), `robots.ts`, `sitemap.ts`.

```bash
cd landing && npm install && npm run dev   # http://localhost:3000
```

## Static Marketing Page

**Location:** `marketing/index.html` — single standalone HTML file, no build step. For quick campaign landing pages or event-specific marketing where a full Next.js app would be overkill.
