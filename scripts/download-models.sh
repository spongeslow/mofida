#!/usr/bin/env bash
# Pull every model Moufida needs into the local Ollama instance and the models/
# directory. Run after `docker compose up -d ollama`.
set -euo pipefail

OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"
MODELS_DIR="${MODELS_DIR:-./models}"
mkdir -p "$MODELS_DIR"

echo ">> Pulling Ollama models from $OLLAMA_URL"
pull() {
  echo "   - $1"
  curl -fsS "$OLLAMA_URL/api/pull" -d "{\"name\":\"$1\"}" >/dev/null
}
pull "${MOUFIDA_RUBRIC_MODEL:-mistral:7b}"     # rubric + maturity classifier
pull "${MOUFIDA_ROADMAP_MODEL:-llama3.1:8b}"   # roadmap narration + Derja->FR
pull "${MOUFIDA_EMBED_MODEL:-nomic-embed-text}" # RAG embeddings

echo ">> Voice + language assets are downloaded by the frontend build."
echo "   Expected under $MODELS_DIR:"
cat <<'EOF'
     whisper-large-v2-tunispeech.bin   (STT, Apache-2.0 fine-tune)
     whisper-large-v2-fr.bin           (STT French fallback)
     piper-fr.onnx                     (TTS French)
     kokoro-82m-ar.onnx                (TTS MSA)
     lid.176.ftz                       (fastText language ID, ~2 MB)
EOF
echo ">> Place the above checkpoints manually or via the frontend setup wizard."
echo "Done."
