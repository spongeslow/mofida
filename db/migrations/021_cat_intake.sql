-- 021_cat_intake.sql -- Computerized Adaptive Testing (CAT) intake results.
--
-- The full CAT state (latent θ, SE, stage, stage posterior, items answered) is
-- stored inside the profile JSONB under the `cat` key. These denormalised
-- columns mirror the headline values so the stage distribution can be queried
-- and aggregated across projects (cohort benchmarking, perception-gap analytics)
-- without unpacking JSONB. Populated by PATCH /project/{id}/profile on intake
-- completion.

ALTER TABLE profiles
    ADD COLUMN IF NOT EXISTS cat_theta REAL,
    ADD COLUMN IF NOT EXISTS cat_se    REAL,
    ADD COLUMN IF NOT EXISTS cat_stage SMALLINT;

CREATE INDEX IF NOT EXISTS idx_profiles_cat_stage
    ON profiles(cat_stage) WHERE cat_stage IS NOT NULL;
