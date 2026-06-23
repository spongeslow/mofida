-- 007_plan_sections.sql — versioned per-axis plan content for creation mode.
-- Write rule: new version flips the prior live row superseded=true, inserts
-- the new row with version = prev+1. Live plan = all superseded=false rows.

CREATE TABLE IF NOT EXISTS plan_sections (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    axis_slug   TEXT NOT NULL,
    version     INT  NOT NULL DEFAULT 1,
    content     JSONB NOT NULL,
    summary     TEXT,
    approved    BOOLEAN NOT NULL DEFAULT false,
    superseded  BOOLEAN NOT NULL DEFAULT false,
    source      TEXT NOT NULL DEFAULT 'generate'
        CHECK (source IN ('generate','manual','chat','tool','daemon')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Enforce exactly one live (non-superseded) row per (project, axis).
CREATE UNIQUE INDEX IF NOT EXISTS uq_plan_live
    ON plan_sections(project_id, axis_slug) WHERE superseded = false;

CREATE INDEX IF NOT EXISTS idx_plan_project
    ON plan_sections(project_id, axis_slug, version DESC);
