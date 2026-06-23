-- 009_tool_signals.sql — raw structured data from pull tool integrations.
-- Signal->axis routing lives in code (orchestrator/app/dependency.py TOOL_AXES).

CREATE TABLE IF NOT EXISTS tool_signals (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    tool_slug   TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    payload     JSONB NOT NULL,
    processed   BOOLEAN NOT NULL DEFAULT false,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tool_signals_unproc
    ON tool_signals(project_id) WHERE processed = false;
