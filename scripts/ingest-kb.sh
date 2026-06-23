#!/usr/bin/env bash
# Chunk + embed ALL KB resources into Qdrant via the RAG service.
#
# This globs every backend/rag/knowledge-base/resources/*.json file, including
# the multilingual per-axis resources produced by scripts/generate_kb_axis.py.
# Each resource is routed to the Qdrant collection named in its `collection`
# field (default: the main KB collection), created on demand by the ingest.
set -euo pipefail
RAG_URL="${RAG_URL:-http://localhost:8300}"
echo ">> Triggering ingestion at $RAG_URL/ingest ..."
response=$(curl -fsS -X POST "$RAG_URL/ingest" -H 'content-type: application/json' -d '{}')
echo "$response"
resources=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('resources',0))" 2>/dev/null || echo "?")
chunks=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('chunks',0))" 2>/dev/null || echo "?")
errors=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('errors',[])))" 2>/dev/null || echo "?")
echo
echo "Ingested: $resources resources, $chunks chunks, $errors errors."
echo "Per collection:"
echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); [print(f'  {k}: {v} chunks') for k,v in sorted(d.get('collections',{}).items())]" 2>/dev/null || true
