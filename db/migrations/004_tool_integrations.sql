-- 004_tool_integrations.sql — per-tool user configuration (global, not per-project).
-- Each registered tool integration has exactly one row here once configured.
-- config stores credentials/settings as JSONB (encrypted at rest by the OS on
-- single-user desktop deployments; rotate service account keys regularly).

CREATE TABLE IF NOT EXISTS tool_integrations (
    id           SERIAL PRIMARY KEY,
    slug         TEXT NOT NULL UNIQUE,          -- 'slack' | 'notion' | 'google_sheets' | 'google_analytics' | 'github'
    enabled      BOOLEAN NOT NULL DEFAULT FALSE,
    config       JSONB NOT NULL DEFAULT '{}'::jsonb,   -- tool-specific credentials and settings
    last_sync_at TIMESTAMPTZ,                   -- last successful push or pull
    last_error   TEXT,                          -- last error message if sync failed
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tool_integrations_slug ON tool_integrations(slug);
