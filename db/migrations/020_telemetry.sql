-- 020_telemetry.sql — observability platform (Phase H, H4).
-- Three append-only telemetry tables fed by the orchestrator request middleware,
-- the shared LLM helper, and the daemon-signal consumer.

CREATE TABLE IF NOT EXISTS api_requests (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id  UUID NOT NULL,
    method      TEXT NOT NULL,
    path        TEXT NOT NULL,
    status_code INT  NOT NULL,
    duration_ms INT  NOT NULL,
    project_id  UUID REFERENCES profiles(id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_api_requests_created ON api_requests (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_api_requests_reqid   ON api_requests (request_id);

CREATE TABLE IF NOT EXISTS llm_calls (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id       UUID,                       -- correlates with api_requests.request_id
    axis             TEXT,                        -- logical caller (e.g. 'pitch', 'cbm', 'market')
    model            TEXT NOT NULL,
    prompt_hash      TEXT NOT NULL,               -- SHA-256 of the full prompt (privacy)
    prompt_preview   TEXT NOT NULL,               -- first 280 chars
    response_preview TEXT,                         -- first 280 chars
    duration_ms      INT,
    tokens_in        INT,
    tokens_out       INT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_llm_calls_created ON llm_calls (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_llm_calls_reqid   ON llm_calls (request_id);

CREATE TABLE IF NOT EXISTS daemon_activities (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  UUID REFERENCES profiles(id) ON DELETE SET NULL,
    watcher     TEXT NOT NULL,                    -- e.g. 'competitor', 'grant', 'legal'
    activity    TEXT NOT NULL,                    -- e.g. 'page_changed', 'grant_found'
    detail      JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_daemon_activities_created ON daemon_activities (created_at DESC);
