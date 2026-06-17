# Phase 4 — Voice Pipeline & Frontend

> 📍 Plan order: after phases 2b/2/3 (the dashboard renders scores, blockers, and the roadmap — these must be *correct* first). See [README](./README.md).

**Goal:** The Tauri desktop app is fully interactive. The user can start a project or diagnose an existing one via voice or UI, see their scores and roadmap on a live dashboard, review history in "Mon Parcours", and receive real-time alerts from the Go daemon.

**Prerequisites:**
- Phase 2 complete (orchestrator API returns diagnostic results, SSE stream is live)
- Phase 3 complete (roadmap endpoint returns actionable results)
- Model checkpoints downloaded: `whisper.bin`, `piper-fr.onnx`, `kokoro/model_quantized.onnx`, `af_heart.bin`, `ff_siwis.bin`, Porcupine access key

---

## Current State

All frontend files are empty stubs. The app builds and shows a minimal shell (title + language toggle). None of the following work yet:

- No API calls to the orchestrator
- No SSE event consumption
- No voice pipeline
- No dashboard, no Mon Parcours, no HUD overlay
- Tauri tray handlers are all TODO stubs

---

## Architecture

```
┌────────────────────────────────────────────────┐
│  Tauri Shell (main.rs)                         │
│  - System tray + menu handlers                 │
│  - Window lifecycle management                 │
│  - IPC bridge (invoke / emit)                  │
└──────────────┬─────────────────────────────────┘
               │ React (Vite + TypeScript)
┌──────────────▼─────────────────────────────────┐
│  App.tsx — Router                              │
│  ├── HUD overlay  (voice + alerts + review)    │
│  ├── Dashboard    (maturity, scores, roadmap)  │
│  └── Mon Parcours (history, score chart)       │
└────────────────────────────────────────────────┘
               │ HTTP / SSE
    localhost:8001 (orchestrator)
```

---

## Step 1 — App Routing & Layout

**File:** `frontend/src/App.tsx`

Replace the minimal scaffold with a router:

```tsx
import { useState } from "react";
import { Dashboard } from "./components/dashboard";
import { HUD } from "./components/hud";
import { MonParcours } from "./components/mon-parcours";
import { SSEConsumer } from "./sse/consumer";

type View = "dashboard" | "hud" | "parcours";

export default function App() {
  const [view, setView] = useState<View>("dashboard");
  const [projectId, setProjectId] = useState<string | null>(null);
  const [lang, setLang] = useState<"fr" | "en">("fr");

  return (
    <div lang={lang}>
      <SSEConsumer projectId={projectId} />
      <nav>...</nav>
      {view === "dashboard" && <Dashboard projectId={projectId} lang={lang} />}
      {view === "hud" && <HUD projectId={projectId} lang={lang} />}
      {view === "parcours" && <MonParcours projectId={projectId} lang={lang} />}
    </div>
  );
}
```

Add packages:
```bash
cd frontend
npm install recharts react-router-dom @tauri-apps/api
```

---

## Step 2 — SSE Consumer

**File:** `frontend/src/sse/consumer.ts`

Connects to `GET http://localhost:8001/api/v1/project/{project_id}/events` and dispatches events to a global state store (React context or Zustand).

```typescript
// Event types from orchestrator/app/sse.py:
// score_update  → {score_name: string, score: number}
// alert         → {severity: string, title: string, body: string}
// roadmap_update → {roadmap: object}
// review_ready  → {axis: string, output: object}
// maturity_update → {maturity_stage: string, perception_gap: boolean}

export function SSEConsumer({ projectId }: { projectId: string | null }) {
  useEffect(() => {
    if (!projectId) return;
    const es = new EventSource(`http://localhost:8001/api/v1/project/${projectId}/events`);
    es.addEventListener("score_update", (e) => store.dispatch(parseScoreUpdate(e.data)));
    es.addEventListener("alert", (e) => store.dispatch(parseAlert(e.data)));
    es.addEventListener("roadmap_update", (e) => store.dispatch(parseRoadmap(e.data)));
    es.addEventListener("review_ready", (e) => store.dispatch(parseReview(e.data)));
    es.addEventListener("maturity_update", (e) => store.dispatch(parseMaturity(e.data)));
    return () => es.close();
  }, [projectId]);
  return null;
}
```

Use a `Zustand` store (or React Context) to hold the global diagnostic state that all components read from.

---

## Step 3 — Dashboard Components

### 3.1 MaturityCard

**File:** `frontend/src/components/dashboard/MaturityCard.tsx`

**Data source:** `GET /api/v1/project/{id}` (current maturity stage) or SSE `maturity_update` event.

**Renders:**
- Stage badge (coloured chip): Ideation / Market Validation / Structuration / Fundraising / Launch Planning / Growth
- Confidence percentage
- Collapsible evidence list (bullet points, each citing a profile field)
- Perception gap warning if `self_assessed_stage !== maturity_stage`

```tsx
<MaturityCard
  stage="Market Validation"
  confidence={0.78}
  evidence={["5 customer interviews conducted", "MRR: $0"]}
  selfAssessed="Structuration"
  lang={lang}
/>
```

### 3.2 ScoreGauge

**File:** `frontend/src/components/dashboard/ScoreGauge.tsx`

**Data source:** SSE `score_update` events + initial load from `POST /api/v1/project/{id}/run-diagnostic`.

**Renders:**
- Large number showing `score/5` (coloured: green ≥ 3.5, yellow ≥ 2.0, red < 2.0)
- Score name label
- Expandable panel with the sub-dimension table:

| Sub-dimension | Weight | Value | Tier | Contribution |
|---|---|---|---|---|
| Customer validation | 30% | 0.0 | T1 | 0.00 |
| ...

- Natural-language justification text below the table
- "Améliorer" button that scrolls to the roadmap section filtered to this score

Render all 5 gauges side by side on desktop, stacked on small windows.

### 3.3 BlockerList

**File:** `frontend/src/components/dashboard/BlockerList.tsx`

**Data source:** Aggregator `blockers` array from diagnostic result.

**Renders:** Ranked list with severity badges:
- 🔴 **Critical** — e.g., "Runway < 3 months"
- 🟡 **Warning** — e.g., "No customer interviews documented"
- 🔵 **Info** — e.g., "Marketing readiness score low"

Each blocker shows: `axis` (which service flagged it), `description`, and a "Voir dans le roadmap" link.

### 3.4 RoadmapTimeline

**File:** `frontend/src/components/dashboard/RoadmapTimeline.tsx`

**Data source:** SSE `roadmap_update` event or `GET /api/v1/project/{id}` after diagnostic.

**Renders:** Three-column grid:

```
| Immédiat (0–2 sem.) | Court terme (1–3 mois) | Moyen terme (3–12 mois) |
|---------------------|------------------------|--------------------------|
| Action card         | Action card            | Action card              |
| [Rationale text]    | [Rationale text]       | [Rationale text]         |
| → Source link       | → Source link          | → Source link            |
```

Each action card has:
- Action title (bold)
- 1-line rationale
- Clickable source URL (opens in system browser via Tauri `open()`)

---

## Step 4 — HUD Overlay

### 4.1 ChatPanel

**File:** `frontend/src/components/hud/ChatPanel.tsx`

**Renders:**
- Transcript of the current voice conversation (voice input in grey, Moufida response in teal)
- Text fallback input (for non-voice use)
- Submit button

**API call:** `POST /api/v1/chat {"project_id": "...", "message": "...", "lang": "fr"}` → display `reply` in the transcript.

### 4.2 ReviewCard

**File:** `frontend/src/components/hud/ReviewCard.tsx`

**Shown when:** SSE `review_ready` event arrives (STATE_NEW axis output ready for approval).

**Renders:**
- Axis name + output summary (markdown-rendered text)
- Three buttons: **Approuver**, **Modifier...** (opens edit textarea), **Réessayer**

**API call on Approuver:** `POST /api/v1/project/{id}/review {"axis": "market", "decision": "approve"}`

### 4.3 AlertFeed

**File:** `frontend/src/components/hud/AlertFeed.tsx`

**Data source:** SSE `alert` events.

**Renders:** Scrollable list of alerts with severity icon, title, timestamp, and dismiss button. On critical alerts, also trigger TTS (see Step 6).

---

## Step 5 — Mon Parcours View

### 5.1 ScoreChart

**File:** `frontend/src/components/mon-parcours/ScoreChart.tsx`

**Data source:** `GET /api/v1/project/{id}/history` (needs an orchestrator endpoint reading `score_snapshots`).

Add orchestrator endpoint:
```python
@app.get("/api/v1/project/{project_id}/history")
async def get_history(project_id: str):
    pool = await get_pool()
    rows = await pool.fetch("""
        SELECT score_name, score, created_at
        FROM score_snapshots WHERE project_id = $1::uuid
        ORDER BY created_at ASC
    """, project_id)
    return {"snapshots": [dict(r) for r in rows]}
```

**Renders:** Recharts `LineChart` — one `Line` per composite score (5 lines), X-axis = timestamp, Y-axis = [0, 5].

```tsx
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend } from "recharts";
const SCORE_COLORS = {
  market: "#3B82F6", commercial_offer: "#10B981",
  innovation: "#8B5CF6", scalability: "#F59E0B", green: "#22C55E"
};
```

### 5.2 HistoryList

**File:** `frontend/src/components/mon-parcours/HistoryList.tsx`

**Data source:** `GET /api/v1/project/{id}/diagnostic-history` (add orchestrator endpoint reading `diagnostic_history`).

**Renders:**
- Timeline of past diagnostic runs (newest first)
- Each entry shows: date, maturity stage assigned, confidence, evidence bullet list
- Roadmap versions with completion status per action

---

## Step 6 — Voice Pipeline

### 6.1 Wake Word Detection

**File:** `frontend/src/voice/wakeword.ts`

**Library:** Porcupine Web SDK (`@picovoice/porcupine-web`)

```typescript
import { PorcupineWorker } from "@picovoice/porcupine-web";

export async function startWakeWordDetection(onWake: () => void) {
  const porcupine = await PorcupineWorker.create(
    process.env.PORCUPINE_ACCESS_KEY,
    { label: "Hey Moufida", publicPath: "/hey-moufida.ppn" },
    () => onWake()
  );
  await porcupine.start();
  return () => porcupine.release();
}
```

**Setup:** The `.ppn` wake word file is obtained from the Picovoice Console (free account). The access key is stored in `.env` as `PORCUPINE_ACCESS_KEY`.

**State transition:** On wake → set `isListening = true` → show the HUD overlay → start STT.

### 6.2 Speech-to-Text

**File:** `frontend/src/voice/stt.ts`

**Approach:** Call the Tauri backend (`invoke`) which pipes audio to `whisper-cli` (the `whisper.cpp` binary) and returns the transcript.

Voice state machine:
```
IDLE → (wake word) → LISTENING
LISTENING → (silence detected) → TRANSCRIBING
TRANSCRIBING → (whisper returns) → PROCESSING
PROCESSING → (API call returns) → SPEAKING
SPEAKING → (TTS finishes) → IDLE
```

**In `src-tauri/src/main.rs`:**
```rust
#[tauri::command]
async fn transcribe(audio_b64: String) -> Result<String, String> {
    // Write audio to temp file
    // Run: whisper-cli --model ./models/whisper.bin --language auto temp.wav
    // Return transcript
}
```

**Language detection:** Pass Whisper's detected language to the orchestrator `chat` endpoint as `lang` parameter.

### 6.3 Text-to-Speech

**File:** `frontend/src/voice/tts.ts`

**French TTS:** Pipe text to `piper` binary with `piper-fr.onnx`:
```rust
// In main.rs
#[tauri::command]
async fn speak(text: String, lang: String) -> Result<(), String> {
    if lang == "fr" {
        // Run: echo "text" | piper --model ./models/piper-fr.onnx | aplay
    } else {
        // Run: kokoro --model ./models/kokoro/model_quantized.onnx 
        //           --voice ./models/kokoro/voices/af_heart.bin
        //           --text "text" | aplay
    }
}
```

**Call from TypeScript:**
```typescript
import { invoke } from "@tauri-apps/api/core";
await invoke("speak", { text: reply, lang: "fr" });
```

---

## Step 7 — Tauri Backend (main.rs)

**File:** `frontend/src-tauri/src/main.rs`

Current state: tray icon with 4 menu items; only Quit works.

### Window Management

Add a main window that opens when "Diagnostiquer" or "Nouveau projet" is clicked:

```rust
"diagnose" => {
    let window = app.get_webview_window("main")
        .unwrap_or_else(|| {
            tauri::WebviewWindowBuilder::new(app, "main", 
                WebviewUrl::App("index.html".into()))
                .title("Moufida")
                .build()
                .unwrap()
        });
    window.show().unwrap();
    // Emit event to React to navigate to the HUD + start intake
    window.emit("start_diagnose", ()).unwrap();
}
```

### Tray Icon Pulse Animation

On non-urgent daemon signals (trend, competitor, milestone warning), animate the tray icon:

```rust
// Listen for "daemon_pulse" events from the frontend SSE consumer
app.listen("daemon_pulse", |_| {
    // Swap tray icon to pulse variant for 3 seconds
});
```

### Tauri Commands to Register

```rust
.invoke_handler(tauri::generate_handler![
    transcribe,
    speak,
    open_url,   // opens a resource URL in the system browser
])
```

---

## Step 8 — i18n Completion

**Files:** `frontend/src/locales/fr.json`, `frontend/src/locales/en.json`

Add all missing keys for the new components:

```json
{
  "maturity_stage": "Stade de maturité",
  "confidence": "Confiance",
  "perception_gap": "Écart de perception détecté",
  "score_market": "Score Marché",
  "score_innovation": "Score Innovation",
  "score_scalability": "Score Scalabilité",
  "score_commercial_offer": "Offre Commerciale",
  "score_green": "Score Green",
  "blockers_critical": "Bloquants critiques",
  "roadmap_immediate": "Immédiat",
  "roadmap_short": "Court terme",
  "roadmap_medium": "Moyen terme",
  "source": "Source",
  "approve": "Approuver",
  "retry": "Réessayer",
  "edit": "Modifier",
  "history": "Mon Parcours",
  "listening": "J'écoute...",
  "speaking": "Moufida répond...",
  "wake_prompt": "Dites « Hey Moufida » pour commencer"
}
```

---

## New Orchestrator Endpoints Needed

These need to be added to `orchestrator/app/main.py` or a new router:

```python
GET  /api/v1/project/{id}/history          # score_snapshots time series
GET  /api/v1/project/{id}/diagnostic-history  # past maturity stages + evidence
POST /api/v1/project/{id}/review           # human Approve/Edit/Retry
```

---

## Completion Criteria

- [ ] `npm run tauri dev` opens the desktop app with tray icon
- [ ] Clicking "Diagnostiquer" opens the HUD and starts voice capture
- [ ] Dashboard shows MaturityCard, 5 ScoreGauges, BlockerList, RoadmapTimeline after `run-diagnostic`
- [ ] SSE alert appears in AlertFeed within 5 seconds of a Go daemon metric being published
- [ ] Mon Parcours shows line chart with at least 2 time points after running diagnostic twice
- [ ] Saying "Hey Moufida" triggers wake-word animation (when Porcupine key is configured)
- [ ] TTS speaks the chat reply in French (`speak` Tauri command works)
- [ ] Language toggle FR ↔ EN updates all UI strings without reload
- [ ] Source links in RoadmapTimeline open in the system browser (not in the app)
