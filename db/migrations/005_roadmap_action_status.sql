-- 005_roadmap_action_status.sql — per-action completion tracking for the
-- "Mon Parcours" journey view. One row per (project, action) the user marks done.
-- action_key is a stable client-computed slug of horizon + action text so the
-- same action keeps its status across roadmap re-renders within a version.

CREATE TABLE IF NOT EXISTS roadmap_action_status (
    id            SERIAL PRIMARY KEY,
    project_id    UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    action_key    TEXT NOT NULL,
    action_text   TEXT,
    horizon       TEXT,                    -- 'immediate' | 'short_term' | 'medium_term'
    completed     BOOLEAN NOT NULL DEFAULT TRUE,
    completed_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (project_id, action_key)
);

CREATE INDEX IF NOT EXISTS idx_roadmap_action_project
    ON roadmap_action_status(project_id, completed_at DESC);
