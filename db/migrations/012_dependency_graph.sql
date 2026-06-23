-- 012_dependency_graph.sql — queryable mirror of the in-code dependency graph.
-- Seeded from dependency.py DEPENDS_ON on orchestrator startup (idempotent upsert).
-- The code graph is authoritative; this table exists for traceability only.

CREATE TABLE IF NOT EXISTS dependency_graph (
    axis       TEXT NOT NULL,
    depends_on TEXT[] NOT NULL,
    version    INT  NOT NULL DEFAULT 1,
    PRIMARY KEY (axis, version)
);
