-- 016_project_watch_targets.sql — per-project, LLM-derived watch targets so
-- adaptation survives restarts and doesn't re-hit the LLM every tick.
-- Refreshed when the profile changes (keyed by profile_hash).
CREATE TABLE IF NOT EXISTS project_watch_targets (
    project_id    UUID PRIMARY KEY REFERENCES profiles(id) ON DELETE CASCADE,
    feeds         JSONB NOT NULL DEFAULT '[]'::jsonb,  -- [{url, why}]
    legal_sources JSONB NOT NULL DEFAULT '[]'::jsonb,  -- [{name, url}]
    keywords      JSONB NOT NULL DEFAULT '[]'::jsonb,  -- [str]
    competitors   JSONB NOT NULL DEFAULT '[]'::jsonb,  -- [{name, url}]
    derived_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    profile_hash  TEXT                                 -- skip re-derive when unchanged
);
