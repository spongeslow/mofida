-- 019_customer_personas.sql — Customer Persona Simulator (Phase H, H3).
-- Evidence-grounded customer personas generated from the diagnostic + KB.
CREATE TABLE IF NOT EXISTS customer_personas (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id   UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    name         TEXT NOT NULL,
    archetype    TEXT NOT NULL,
    data         JSONB NOT NULL,        -- full Persona object incl. source_refs
    generated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_customer_personas_project
    ON customer_personas(project_id, generated_at DESC);
