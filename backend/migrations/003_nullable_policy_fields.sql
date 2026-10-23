-- Migration: 003_nullable_policy_fields.sql
-- Description: Non-destructive migration to allow source-dependent columns to be nullable
--              and drop misleading default values.

BEGIN;

ALTER TABLE insurance_policies ALTER COLUMN min_sum_insured DROP NOT NULL;
ALTER TABLE insurance_policies ALTER COLUMN max_sum_insured DROP NOT NULL;
ALTER TABLE insurance_policies ALTER COLUMN copay_percentage DROP DEFAULT;
ALTER TABLE insurance_policies ALTER COLUMN pre_hospitalization_days DROP DEFAULT;
ALTER TABLE insurance_policies ALTER COLUMN post_hospitalization_days DROP DEFAULT;
ALTER TABLE insurance_policies ALTER COLUMN entry_age_min DROP DEFAULT;
ALTER TABLE insurance_policies ALTER COLUMN entry_age_max DROP DEFAULT;
ALTER TABLE insurance_policies ALTER COLUMN last_verified_date DROP DEFAULT;
ALTER TABLE policy_benefits ALTER COLUMN sub_limit DROP DEFAULT;

COMMIT;
