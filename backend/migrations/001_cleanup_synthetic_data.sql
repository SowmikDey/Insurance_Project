-- Migration: 001_cleanup_synthetic_data.sql
-- Description: Drop obsolete tables (reviews, pricing slabs, user persistence) 
--              and purge synthetic AI-generated records from development database.

BEGIN;

-- 1. Drop obsolete tables if they exist
DROP TABLE IF EXISTS customer_reviews CASCADE;
DROP TABLE IF EXISTS policy_pricing_slabs CASCADE;
DROP TABLE IF EXISTS saved_policies CASCADE;
DROP TABLE IF EXISTS recommendation_logs CASCADE;
DROP TABLE IF EXISTS user_progress CASCADE;

-- 2. Clear synthetic RAG document chunks and sources
DELETE FROM document_chunks;
DELETE FROM document_sources;

-- 3. Clear synthetic policy details
DELETE FROM policy_waiting_periods;
DELETE FROM policy_exclusions;
DELETE FROM policy_benefits;

-- 4. Clear synthetic policies and insurers
DELETE FROM insurance_policies;
DELETE FROM insurers;

COMMIT;
