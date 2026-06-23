-- 017_concept_scores.sql — Concept Bottleneck layer (Koh et al. ICML 2020,
-- Label-Free variant Oikarinen et al. ICLR 2023).
-- One row per (project, axis) per diagnostic: the LLM-scored concept activations,
-- the linear bottleneck head's composite score, and the identified bottleneck.
CREATE TABLE IF NOT EXISTS concept_scores (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    axis        TEXT NOT NULL,                 -- network axis slug (e.g. 'market')
    concepts    JSONB NOT NULL,                -- { concept_id: float in [0,1] }
    cbm_score   REAL,                          -- 0..5 composite from the linear head
    actual_score REAL,                         -- mapped composite axis score (ridge calibration target)
    bottleneck  JSONB,                         -- { concept_id, current, weight, score_if_fixed }
    calibrated  BOOLEAN NOT NULL DEFAULT FALSE,-- axis-specific weights vs. equal-weight fallback
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_concept_scores_latest
    ON concept_scores(project_id, axis, created_at DESC);
