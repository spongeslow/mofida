-- 013_daemon_control.sql — single-row control plane for the background daemon.
-- id is pinned to TRUE so there is always exactly one row (upsert on conflict).
CREATE TABLE IF NOT EXISTS daemon_control (
    id          BOOLEAN PRIMARY KEY DEFAULT TRUE CHECK (id),
    paused      BOOLEAN NOT NULL DEFAULT FALSE,
    -- which project the daemon watches; chosen from the UI. Replaces the
    -- startup-only MOUFIDA_PROJECT_ID. ON DELETE SET NULL parks the daemon
    -- cleanly when the focused project is deleted from the picker.
    focus_project_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    last_beat   TIMESTAMPTZ,                 -- updated by the daemon heartbeat
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
INSERT INTO daemon_control (id, paused) VALUES (TRUE, FALSE)
    ON CONFLICT (id) DO NOTHING;
