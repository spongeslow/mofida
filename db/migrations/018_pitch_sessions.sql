-- 018_pitch_sessions.sql — Investor Pitch Simulator (Phase H, H1).
-- One row per rehearsal session; the exchange transcript and final readiness
-- report are stored as JSONB.
CREATE TABLE IF NOT EXISTS pitch_sessions (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id       UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    investor_profile TEXT NOT NULL,                 -- seed_vc | angel | impact_fund | strategic
    exchanges        JSONB NOT NULL DEFAULT '[]',   -- [{role, text, trace, reasoning}]
    evidence         JSONB,                          -- snapshot of the grounding evidence
    readiness        JSONB,                          -- final PitchReadinessReport
    started_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at         TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_pitch_sessions_project
    ON pitch_sessions(project_id, started_at DESC);
