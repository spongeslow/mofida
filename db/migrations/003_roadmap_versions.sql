-- 003_roadmap_versions.sql -- versioned roadmap output from Axis 10.

CREATE TABLE IF NOT EXISTS roadmap_versions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id    UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    version       INT NOT NULL DEFAULT 1,
    -- Full roadmap JSON: immediate / short-term / medium-term actions with
    -- rationales, resource links, and suggested deadlines.
    roadmap       JSONB NOT NULL DEFAULT '{}'::jsonb,
    trigger       TEXT,                    -- e.g. 'first_diagnosis', 'milestone', 'new_resource'
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_roadmap_project
    ON roadmap_versions(project_id, version DESC);
