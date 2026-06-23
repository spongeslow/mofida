-- 011_roadmap_provenance.sql — extend roadmap_versions with KB provenance and stale flag.
-- trigger column already exists from 003; only add kb_version and stale.

ALTER TABLE roadmap_versions ADD COLUMN IF NOT EXISTS kb_version INT;
ALTER TABLE roadmap_versions ADD COLUMN IF NOT EXISTS stale BOOLEAN NOT NULL DEFAULT false;
