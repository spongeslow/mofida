-- 015_opportunities.sql — grant / deadline radar: profile-matched funding calls.
CREATE TABLE IF NOT EXISTS opportunities (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id   UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    title        TEXT NOT NULL,
    source       TEXT NOT NULL,               -- 'startup_act' | 'apii' | 'eu_calls' | ...
    url          TEXT,
    deadline     DATE,                         -- apply-by date (LLM-extracted)
    match_reason TEXT,                         -- why it fits this project
    match_score  REAL NOT NULL DEFAULT 0,      -- 0..1 profile fit
    dismissed    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (project_id, url)
);
CREATE INDEX IF NOT EXISTS idx_opportunities_active
    ON opportunities(project_id) WHERE dismissed = FALSE;
