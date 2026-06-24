# Desktop Application

**Location:** `frontend/` | **Stack:** React 18, TypeScript, Vite, Tauri v2 (Rust shell), Zustand, custom `useT()` i18n hook

A Tauri v2 application — a Rust shell wrapping a Vite + React webview. Tauri provides the system tray, two native windows (main + companion), file system access, and the bridges to Whisper/Piper/Kokoro running on the host. The app communicates with the backend exclusively through HTTP and SSE to `localhost:8001`.

---

## Tauri Shell (`src-tauri/src/main.rs`)

Seven Tauri commands callable from the React webview:

| Command | Function |
|---|---|
| `show_main_window` / `toggle_main_window` | Main window visibility |
| `set_companion_visible` | Shows/hides companion window |
| `transcribe` | Invokes `whisper-cli` on base64 WebM audio → returns transcribed text |
| `speak` | TTS: French via Piper + `piper-fr.onnx` → `aplay`; other via Kokoro ONNX |
| `read_dropped_file` | Reads a file from disk (PDF/txt/md/csv, max 25 MB) → base64 |
| `open_url` | Cross-platform URL opener (xdg-open/open/cmd) |

**Companion window:** 110×200 logical px, transparent, always-on-top, skip-taskbar, no decorations. Positioned at bottom-right.

**System tray:** French menu — Nouveau projet, Diagnostiquer, Paramètres, Quitter. Tray events emit Tauri events to the main window.

**Default hidden:** the main window is `visible: false` at startup. Click the tray icon or the companion character to open.

---

## Application State (`src/store.ts`)

Zustand flat store (~40 fields) grouped by domain:

```typescript
// Project
projectId, lang, view // 8 views: dashboard | hud | parcours | settings | personas | pitch | scenarios | kb | intake | creation | projects

// Diagnostic results
scores, scoreBreakdowns, justifications, maturityStage, selfAssessedStage, perceptionGap, blockers, roadmap, evidence, confidence

// CBM layer
conceptScores, conceptNonce

// Creation mode
projectMode, planSections, currentProposal, currentAxisIndex, creationPhase

// Companion
companionPulse: { state: CompanionState; nonce: number }, companionVisible

// Daemon
daemonPaused, daemonAlive, daemonFocusProjectId

// Live feed (ring buffer max 200)
eventFeed, roadmapStale, horizonCompleteNonce, competitorNonce, opportunityNonce, kbRefreshNonce
```

---

## Voice Pipeline (`src/voice/`)

**Wake word (`wakeword.ts`)** — optional Porcupine Web SDK for "Hey Moufida." Falls back to `Ctrl+Space`.

**STT (`stt.ts`):**
```
MediaRecorder → audio chunks
AnalyserNode → silence detection (RMS < 0.015 for 1500ms) → stop recording
Encode to base64 WebM → invoke('transcribe') → Rust → whisper-cli → text
```

**TTS (`tts.ts`):** `invoke('speak', { text, lang })`. Non-blocking — UI stays interactive while Moufida speaks.

**Language detection** — per utterance via fastText `lid.176.ftz` (176 languages, < 1ms, runs in JS via WASM).

---

## SSE Consumer (`src/sse/consumer.ts`)

Connects to `GET /api/v1/project/{id}/events/stream`. Handles 13 event types dispatched to Zustand + companion pulses:

| Event | Zustand action | Companion reaction |
|---|---|---|
| `score_update` | Updates scores/breakdowns | — |
| `review_ready` | Marks diagnosis complete | `celebrating` |
| `alert` (critical) | Adds to eventFeed | `alert` + jump |
| `score_update` (drop ≥1.0) | — | `worried` |
| `maturity_update` | Updates stage/gap | — |
| `daemon_status` | Updates daemon state | `sleeping` (if paused) |
| `concept_update` | Updates conceptScores | `presenting` |
| `kb_updated` | Bumps kbRefreshNonce | `reading` → `celebrating` |
| `horizon_complete` | Bumps horizonCompleteNonce | `celebrating` |
| `opportunity_new` | Bumps opportunityNonce | `cheering` |
| `competitor_update` | Bumps competitorNonce | — |

---

## Pixel-Art Companion (`src/pixelArt/moufida.ts` + `src/companion.ts`)

Pure Canvas 2D — no sprites, no image files. The character is drawn from rectangle arrays at `SC=6` pixels/unit (92×168px canvas).

**24 expressive states:** idle, walking, sleeping, listening, thinking, speaking, celebrating, worried, alert, typing, stretching, shrug, crying, facepalm, cool, skeptic, presenting, reading, waving, startled, bowing, cheering, and more.

**5 palette themes:** default (dashboard), blue (Pitch), purple (Scénarios), green (Mon Parcours), rose (Personas). Only costume colours swap — skin, hair, eyes are constant.

**Animation loop (60fps in companion window):**
- Roams within a 220px strip at screen right edge; turns at boundaries
- Walk frame toggle every 380ms, position update every 55ms
- Blinks every ~4.5s
- Idle pool: wave / stretch / shrug every ~5s (random pick)
- Auto-typing after 55s of no interaction (10s duration)
- Auto-sleep after 3 min of no interaction

**Interactions:**
- Single click → `show_main_window` + startled bounce
- Double-click → show window + emit `run_quick_diagnostic`
- Drag → reposition; drop → startled bounce
- File drop (PDF) → `read_dropped_file` → POST to KB endpoint → celebrate on success

**Companion pulse system:** `{ state, nonce }` in Zustand. The nonce ensures reactions fire even when the state repeats (e.g., consecutive alerts all produce a jump). Pulse duration: 2–3 seconds, then returns to ambient state.

**UX rationale:** The character communicates system state passively — a worried character means something needs attention without requiring the founder to open the app. A sleeping character is a visible signal that daemon monitoring is paused.

---

## i18n

Full FR/EN/AR parity (~260 keys each). Custom `useT()` hook. RTL layout activates automatically for Arabic.

---

## Global Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+Shift+M` | Toggle main window |
| `Ctrl+Shift+D` | Run diagnostic |
| `Ctrl+Shift+V` | Start voice input |
