#!/usr/bin/env bash
# Moufida one-shot setup: pull Ollama models and download all voice models.
#
# Run once after copying .env.example → .env to get the project fully ready.
# Everything except the Porcupine wake word is automated here.
#
# Usage:
#   ./scripts/setup.sh                  # full setup (~1.3 GB download)
#   ./scripts/setup.sh --skip-whisper   # skip the 1.1 GB Whisper model
#
# Prerequisites: Ollama must be installed and running on the host.
# See https://ollama.com/download

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS="$ROOT/models"

SKIP_WHISPER=false
for arg in "$@"; do
  [[ "$arg" == "--skip-whisper" ]] && SKIP_WHISPER=true
done

# ── Colours ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BOLD='\033[1m'; NC='\033[0m'
ok()   { echo -e "  ${GREEN}✓${NC} $*"; }
warn() { echo -e "  ${YELLOW}!${NC} $*"; }
err()  { echo -e "  ${RED}✗${NC} $*"; }
step() { echo -e "\n${BOLD}━━ $* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; }

# ── Fetch helper ──────────────────────────────────────────────────────────────
# fetch <url> <dest> [min_bytes]  — idempotent, resume-capable
fetch() {
  local url="$1" dest="$2" min="${3:-0}"
  local name; name="$(basename "$dest")"
  if [[ -f "$dest" ]]; then
    local size; size=$(stat -c%s "$dest" 2>/dev/null || stat -f%z "$dest" 2>/dev/null || echo 0)
    if (( min == 0 )) || (( size >= min )); then
      ok "$name  ($(numfmt --to=iec "$size" 2>/dev/null || echo "${size}B") — already present)"
      return 0
    fi
    warn "$name exists but is incomplete (${size}B < ${min}B) — re-downloading"
  fi
  echo "  Downloading $name..."
  if curl -L --retry 3 --retry-delay 2 --progress-bar -o "$dest" "$url"; then
    local size; size=$(stat -c%s "$dest" 2>/dev/null || stat -f%z "$dest" 2>/dev/null || echo 0)
    ok "$name  ($(numfmt --to=iec "$size" 2>/dev/null || echo "${size}B"))"
  else
    err "Failed to download $name"
    rm -f "$dest"
    return 1
  fi
}

# ════════════════════════════════════════════════════════════════════════════
# PART 1 — Ollama LLM models
# ════════════════════════════════════════════════════════════════════════════

step "1/3  Ollama models"

# Load OLLAMA_URL from .env if present, otherwise use default
OLLAMA_URL="${OLLAMA_URL:-}"
if [[ -z "$OLLAMA_URL" && -f "$ROOT/.env" ]]; then
  OLLAMA_URL=$(grep -E '^OLLAMA_URL=' "$ROOT/.env" | cut -d= -f2-)
fi
OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"

MODEL="${MOUFIDA_MODEL:-}"
if [[ -z "$MODEL" && -f "$ROOT/.env" ]]; then
  MODEL=$(grep -E '^MOUFIDA_MODEL=' "$ROOT/.env" | cut -d= -f2-)
fi
MODEL="${MODEL:-llama3.1:8b}"

EMBED_MODEL="${MOUFIDA_EMBED_MODEL:-}"
if [[ -z "$EMBED_MODEL" && -f "$ROOT/.env" ]]; then
  EMBED_MODEL=$(grep -E '^MOUFIDA_EMBED_MODEL=' "$ROOT/.env" | cut -d= -f2-)
fi
EMBED_MODEL="${EMBED_MODEL:-bge-m3}"

echo ""
echo "  Ollama endpoint : $OLLAMA_URL"
echo "  LLM model       : $MODEL"
echo "  Embedding model : $EMBED_MODEL"
echo ""

if ! curl -fsS "$OLLAMA_URL/api/tags" >/dev/null 2>&1; then
  err "Cannot reach Ollama at $OLLAMA_URL"
  echo "  Make sure Ollama is installed and running:"
  echo "    Linux:  curl -fsSL https://ollama.com/install.sh | sh && ollama serve"
  echo "    macOS:  https://ollama.com/download"
  exit 1
fi
ok "Ollama reachable"

pull_model() {
  local name="$1"
  # Check if already present
  if curl -fsS "$OLLAMA_URL/api/tags" | grep -q "\"name\":\"$name"; then
    ok "$name  (already pulled)"
    return 0
  fi
  echo "  Pulling $name  (this may take a while)..."
  curl -fsS "$OLLAMA_URL/api/pull" -d "{\"name\":\"$name\"}" \
    | grep -oP '"status":"\K[^"]+' | grep -v "^$" | tail -1
  ok "$name"
}

pull_model "$MODEL"
pull_model "$EMBED_MODEL"

# ════════════════════════════════════════════════════════════════════════════
# PART 2 — Voice models  (French + English)
# ════════════════════════════════════════════════════════════════════════════

step "2/3  Voice models"
mkdir -p "$MODELS/kokoro/voices"

# ── fastText language identification (~1 MB) ─────────────────────────────────
echo ""
echo "  [1/4] fastText language ID"
fetch \
  "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz" \
  "$MODELS/lid.176.ftz" \
  800000

# ── Piper French TTS (~61 MB) ────────────────────────────────────────────────
echo ""
echo "  [2/4] Piper French TTS  (fr_FR-siwis-medium)"
fetch \
  "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx" \
  "$MODELS/piper-fr.onnx" \
  50000000
fetch \
  "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx.json" \
  "$MODELS/piper-fr.onnx.json"

# ── Kokoro-82M ONNX — EN + FR voices (~90 MB model + 2 × ~510 KB voices) ────
echo ""
echo "  [3/4] Kokoro-82M TTS  (quantized ONNX + EN + FR voices)"
fetch \
  "https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/resolve/main/onnx/model_quantized.onnx" \
  "$MODELS/kokoro/model_quantized.onnx" \
  50000000
fetch \
  "https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/resolve/main/config.json" \
  "$MODELS/kokoro/config.json"
fetch \
  "https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/resolve/main/tokenizer.json" \
  "$MODELS/kokoro/tokenizer.json" \
  1000
# French voice: ff_siwis
fetch \
  "https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/resolve/main/voices/ff_siwis.bin" \
  "$MODELS/kokoro/voices/ff_siwis.bin" \
  100000
# English voice: af_heart  (American Female)
fetch \
  "https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/resolve/main/voices/af_heart.bin" \
  "$MODELS/kokoro/voices/af_heart.bin" \
  100000

# ── Whisper large-v2 q5_0 — EN + FR STT (~1.1 GB) ───────────────────────────
echo ""
echo "  [4/4] Whisper large-v2 q5_0  (English + French STT)"
if [[ "$SKIP_WHISPER" == true ]]; then
  warn "Skipped (--skip-whisper). To download later, run:"
  warn "  curl -L -o $MODELS/whisper.bin \\"
  warn "    https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v2-q5_0.bin"
else
  fetch \
    "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v2-q5_0.bin" \
    "$MODELS/whisper.bin" \
    500000000
fi

# ════════════════════════════════════════════════════════════════════════════
# PART 3 — Porcupine wake word  (manual)
# ════════════════════════════════════════════════════════════════════════════

step "3/3  Porcupine wake word"
echo ""
if [[ -f "$MODELS/hey-moufida.ppn" ]]; then
  ok "hey-moufida.ppn  (already present)"
else
  warn "Requires a free Picovoice account — cannot be downloaded automatically."
  echo ""
  echo "    1. Sign up at  https://console.picovoice.ai/"
  echo "    2. Keyword → Create Keyword → type  \"Hey Moufida\""
  echo "    3. Download the .ppn file for your OS platform"
  echo "    4. Place it at:   $MODELS/hey-moufida.ppn"
  echo "    5. Add to .env:   PORCUPINE_ACCESS_KEY=<your-key>"
  echo ""
fi

# ════════════════════════════════════════════════════════════════════════════
# Summary
# ════════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${BOLD}━━ Status ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

check() {
  if [[ -f "$2" || -L "$2" ]]; then ok "$1"
  else err "$1  →  missing: ${2#"$ROOT/"}"; fi
}

echo ""
echo "  Ollama models"
if curl -fsS "$OLLAMA_URL/api/tags" 2>/dev/null | grep -q "\"name\":\"$MODEL"; then
  ok "$MODEL"
else
  err "$MODEL  →  not found in Ollama"
fi
if curl -fsS "$OLLAMA_URL/api/tags" 2>/dev/null | grep -q "\"name\":\"$EMBED_MODEL"; then
  ok "$EMBED_MODEL"
else
  err "$EMBED_MODEL  →  not found in Ollama"
fi

echo ""
echo "  Voice models"
check "fastText LID"           "$MODELS/lid.176.ftz"
check "Piper FR (ONNX)"        "$MODELS/piper-fr.onnx"
check "Piper FR (config)"      "$MODELS/piper-fr.onnx.json"
check "Kokoro ONNX"            "$MODELS/kokoro/model_quantized.onnx"
check "Kokoro voice  FR"       "$MODELS/kokoro/voices/ff_siwis.bin"
check "Kokoro voice  EN"       "$MODELS/kokoro/voices/af_heart.bin"
check "Whisper large-v2 q5_0"  "$MODELS/whisper.bin"
if [[ -f "$MODELS/hey-moufida.ppn" ]]; then
  ok "Porcupine wake word"
else
  warn "Porcupine wake word  →  pending (see step 3 above)"
fi

echo ""
echo -e "${BOLD}━━ Model files ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
find "$MODELS" -not -name '.gitkeep' \( -type f -o -type l \) | sort | while read -r f; do
  size=$(stat -c%s "$f" 2>/dev/null || stat -f%z "$f" 2>/dev/null || echo "?")
  printf "  %-50s %s\n" "${f#"$ROOT/"}" "$(numfmt --to=iec "$size" 2>/dev/null || echo "${size}B")"
done
echo ""
