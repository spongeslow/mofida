-- 006_project_meta.sql — extend profiles for multi-project dashboard.
-- mode is a generated column so design-doc vocabulary works in queries
-- without a second source of truth. state remains the writable column.

ALTER TABLE profiles ADD COLUMN IF NOT EXISTS archived      BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS plan_complete BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS mode TEXT
    GENERATED ALWAYS AS (
        CASE state WHEN 'NEW' THEN 'creation' ELSE 'diagnosis' END
    ) STORED;
