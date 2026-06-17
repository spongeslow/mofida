# Moufida frontend (Tauri + React + TypeScript)

The desktop shell runs on the **host** (it needs a display and audio devices),
not inside Docker. The backend stack runs via `docker compose up` at the repo root.

## Dev
```bash
npm install
npm run tauri dev    # launches the Tauri window + Vite dev server
```

## Notes
- Voice models (Whisper TuniSpeech, Piper, Kokoro-82M) and the Porcupine wake
  word are loaded from `../models` — run `scripts/download-models.sh` first.
- A real `icons/icon.png` must be supplied before `tauri build`; a placeholder
  `.gitkeep` is checked in.
- Phases: the tray + shell exist now (Phase 0); dashboard, "Mon Parcours",
  voice pipeline, and SSE consumer arrive in Phase 4.
