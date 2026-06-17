-- 001_init.sql -- core profile, diagnostic history, and alert log.

CREATE TABLE IF NOT EXISTS profiles (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name          TEXT,
    state         TEXT NOT NULL DEFAULT 'NEW' CHECK (state IN ('NEW', 'EXISTING')),
    sector        TEXT NOT NULL DEFAULT 'cross-sector',
    language      TEXT NOT NULL DEFAULT 'fr',
    -- Full StartupProfile (Table 1 field catalogue) as flexible JSONB.
    profile       JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS diagnostic_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    maturity_stage  TEXT,
    self_assessed   TEXT,
    perception_gap  TEXT,
    confidence      REAL,
    evidence        JSONB NOT NULL DEFAULT '[]'::jsonb,
    blockers        JSONB NOT NULL DEFAULT '[]'::jsonb,
    anomalies       JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS alerts (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id    UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    type          TEXT NOT NULL,
    severity      TEXT NOT NULL DEFAULT 'info' CHECK (severity IN ('critical', 'warning', 'info')),
    payload       JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_diag_project ON diagnostic_history(project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_project ON alerts(project_id, created_at DESC);
