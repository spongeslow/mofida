-- 002_score_snapshots.sql -- per-composite-score history with full breakdown.

CREATE TABLE IF NOT EXISTS score_snapshots (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id    UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    score_name    TEXT NOT NULL,           -- market | commercial_offer | innovation | scalability | green
    score         REAL NOT NULL,           -- 0-5 normalised
    -- Per-component contributions incl. evidence tiers and rubric outputs.
    breakdown     JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_scores_project_name
    ON score_snapshots(project_id, score_name, created_at DESC);
