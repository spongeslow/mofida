-- 008_events.sql — interpreted, actionable update events from any source.
-- alerts stays as the raw daemon log; an event is the interpreted record.

CREATE TABLE IF NOT EXISTS events (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id    UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    source        TEXT NOT NULL CHECK (source IN ('manual','chat','tool','daemon')),
    type          TEXT NOT NULL,
    severity      TEXT NOT NULL DEFAULT 'info'
        CHECK (severity IN ('critical','warning','info')),
    summary       TEXT NOT NULL,
    detail        TEXT,
    axes_affected TEXT[] NOT NULL DEFAULT '{}',
    diff          JSONB,
    suggestion    JSONB,
    status        TEXT NOT NULL DEFAULT 'new'
        CHECK (status IN ('new','acted','manual','ignored')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_events_project ON events(project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_status  ON events(project_id, status);
