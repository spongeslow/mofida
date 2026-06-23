-- 014_competitors.sql — persisted competitor analysis board + change snapshots.
CREATE TABLE IF NOT EXISTS competitors (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    url         TEXT,
    pricing     JSONB NOT NULL DEFAULT '{}'::jsonb,   -- {tiers:[{name,price,features}]}
    positioning TEXT,                                  -- LLM one-line positioning
    funding     JSONB NOT NULL DEFAULT '{}'::jsonb,    -- {stage,amount,investors}
    news        JSONB NOT NULL DEFAULT '[]'::jsonb,    -- [{headline,url,date}]
    swot        JSONB NOT NULL DEFAULT '{}'::jsonb,    -- {strengths,weaknesses,opportunities,threats}
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (project_id, name)
);
CREATE TABLE IF NOT EXISTS competitor_snapshots (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competitor_id UUID NOT NULL REFERENCES competitors(id) ON DELETE CASCADE,
    captured_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    raw_excerpt   TEXT,                                -- trimmed page text
    diff          JSONB NOT NULL DEFAULT '{}'::jsonb   -- {field: {before, after}}
);
CREATE INDEX IF NOT EXISTS idx_competitors_project ON competitors(project_id);
CREATE INDEX IF NOT EXISTS idx_competitor_snapshots_comp
    ON competitor_snapshots(competitor_id, captured_at DESC);
