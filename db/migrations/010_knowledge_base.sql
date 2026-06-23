-- 010_knowledge_base.sql — versioned RAG knowledge base catalogue.
-- project_id NULL = global KB. Embedding vectors live in Qdrant keyed by id.
-- kb_version is bumped on every mutation; roadmap generations record which
-- version they used (see 011_roadmap_provenance.sql).

CREATE TABLE IF NOT EXISTS knowledge_base (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  UUID REFERENCES profiles(id) ON DELETE CASCADE,
    source      TEXT NOT NULL CHECK (source IN ('seed','tool','upload','manual','feed')),
    title       TEXT,
    content     TEXT NOT NULL,
    metadata    JSONB NOT NULL DEFAULT '{}'::jsonb,
    kb_version  INT  NOT NULL DEFAULT 1,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_kb_scope ON knowledge_base(project_id, kb_version DESC);
