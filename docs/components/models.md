# Local AI Models

**Location:** `models/` | All inference stays on the founder's machine.

---

## Language Models (via Ollama)

| Model | Size | Role |
|---|---|---|
| `llama3.1:8b` | ~4.7 GB | Generation (plan sections, justifications, chat, pitch, personas, scenarios, score debate) |
| `bge-m3` | ~1.2 GB | Multilingual embeddings (AR/FR/EN, 1024-dim) for KB ingest, retrieval, and axis-direction probe |

`bge-m3` is specifically chosen for its multilingual coverage and strong Arabic performance — a requirement for Moufida's bilingual Tunisian target audience. A Darija voice query and a French KB resource coexist in the same 1024-dim vector space.

## Voice Models (host-side native binaries)

| Model | File | Size | Role |
|---|---|---|---|
| Whisper large-v2 Q5 | `models/whisper.bin` | ~1.1 GB | STT: French, English, Tunisian Darija |
| Piper FR | `models/piper-fr.onnx` | ~61 MB | TTS: French female voice (`ff_siwis`) |
| Kokoro-82M | `models/kokoro/model_quantized.onnx` | ~89 MB | TTS: multi-language (EN `af_heart`, FR `ff_siwis`) |
| fastText LID | `models/lid.176.ftz` | ~1 MB | Language identification (176 languages, < 1ms in WASM) |

## GPU vs CPU

Ollama auto-detects CUDA/ROCm/Metal. With 8GB+ VRAM: 40–80 tokens/second for llama3.1:8b. CPU only (16GB RAM): 5–15 tokens/second. Full 3-wave diagnosis: ~15–25 s with GPU, ~60–120 s CPU-only.

## Model Setup

```bash
./scripts/setup.sh             # all models (~7 GB total)
./scripts/setup.sh --skip-whisper  # skip 1.1 GB Whisper
```

## Privacy Architecture

```
Founder data
  → Stored in local PostgreSQL (Docker)
  → Embedded by local bge-m3 (Ollama)
  → Reasoned by local llama3.1:8b (Ollama)
  → Transcribed by local Whisper (host)
  → Spoken back by local Piper/Kokoro (host)
  → Never reaches any external server
```
