#!/usr/bin/env bash
# Ingest every curated knowledge-base resource into Qdrant via the RAG service.
set -euo pipefail
RAG_URL="${RAG_URL:-http://localhost:8300}"
echo ">> Triggering ingestion at $RAG_URL/ingest"
curl -fsS -X POST "$RAG_URL/ingest" -H 'content-type: application/json' -d '{}'
echo
echo "Done."
