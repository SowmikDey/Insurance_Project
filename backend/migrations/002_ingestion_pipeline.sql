-- Migration: 002_ingestion_pipeline.sql
-- Description: Non-destructive migration creating tables for source registry,
--              source authorizations, ingestion jobs, policy versions, policy facts,
--              and authorized review metadata.

BEGIN;

-- 1. Source Registry
CREATE TABLE IF NOT EXISTS source_registries (
    id SERIAL PRIMARY KEY,
    provider_name VARCHAR(150) NOT NULL,
    provider_slug VARCHAR(100) NOT NULL,
    category VARCHAR(50) DEFAULT 'Health',
    source_name VARCHAR(200) NOT NULL,
    source_url VARCHAR(500) NOT NULL UNIQUE,
    url_type VARCHAR(50) NOT NULL,
    permission_status VARCHAR(50) DEFAULT 'permission_required',
    ingestion_mode VARCHAR(50) DEFAULT 'link_only',
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    last_checked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_source_reg_provider ON source_registries(provider_slug);
CREATE INDEX IF NOT EXISTS idx_source_reg_status ON source_registries(permission_status);

-- 2. Source Authorizations
CREATE TABLE IF NOT EXISTS source_authorizations (
    id SERIAL PRIMARY KEY,
    provider_slug VARCHAR(100) NOT NULL,
    source_id INTEGER REFERENCES source_registries(id) ON DELETE SET NULL,
    authorization_reference VARCHAR(150) NOT NULL UNIQUE,
    permitted_urls JSONB DEFAULT '[]'::jsonb,
    permitted_document_types JSONB DEFAULT '["PDF"]'::jsonb,
    collection_rights BOOLEAN DEFAULT FALSE,
    storage_rights BOOLEAN DEFAULT FALSE,
    review_usage_rights BOOLEAN DEFAULT FALSE,
    permitted_uses TEXT,
    effective_date DATE NOT NULL,
    expiration_date DATE,
    is_revoked BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_source_auth_provider ON source_authorizations(provider_slug);

-- 3. Ingestion Jobs
CREATE TABLE IF NOT EXISTS ingestion_jobs (
    id VARCHAR(64) PRIMARY KEY,
    source_id INTEGER REFERENCES source_registries(id) ON DELETE SET NULL,
    provider_slug VARCHAR(100) NOT NULL,
    requested_url VARCHAR(500),
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'PENDING',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    discovered_product_count INTEGER DEFAULT 0,
    downloaded_document_count INTEGER DEFAULT 0,
    extracted_document_count INTEGER DEFAULT 0,
    created_record_count INTEGER DEFAULT 0,
    updated_record_count INTEGER DEFAULT 0,
    duplicate_count INTEGER DEFAULT 0,
    needs_review_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    failure_details TEXT,
    authorization_decision VARCHAR(50) DEFAULT 'PENDING',
    log_messages JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_status ON ingestion_jobs(status);
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_provider ON ingestion_jobs(provider_slug);

-- 4. Policy Versions
CREATE TABLE IF NOT EXISTS policy_versions (
    id SERIAL PRIMARY KEY,
    policy_id INTEGER REFERENCES insurance_policies(id) ON DELETE CASCADE,
    version_number VARCHAR(50) DEFAULT '1.0',
    uin_number VARCHAR(100),
    status VARCHAR(50) DEFAULT 'CURRENT',
    effective_from_date DATE,
    effective_to_date DATE,
    superseded_by_version_id INTEGER REFERENCES policy_versions(id) ON DELETE SET NULL,
    document_source_id INTEGER REFERENCES document_sources(id) ON DELETE SET NULL,
    source_url VARCHAR(500),
    raw_extracted_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_policy_versions_policy ON policy_versions(policy_id);
CREATE INDEX IF NOT EXISTS idx_policy_versions_uin ON policy_versions(uin_number);

-- 5. Policy Facts with Traceable Evidence
CREATE TABLE IF NOT EXISTS policy_facts (
    id SERIAL PRIMARY KEY,
    policy_id INTEGER REFERENCES insurance_policies(id) ON DELETE CASCADE,
    policy_version_id INTEGER REFERENCES policy_versions(id) ON DELETE CASCADE,
    field_name VARCHAR(100) NOT NULL,
    field_value TEXT,
    normalized_value TEXT,
    evidence_snippet TEXT NOT NULL,
    section_heading VARCHAR(255),
    page_number INTEGER,
    source_url VARCHAR(500),
    document_source_id INTEGER REFERENCES document_sources(id) ON DELETE SET NULL,
    extraction_method VARCHAR(50) DEFAULT 'DETERMINISTIC_REGEX',
    verification_status VARCHAR(50) DEFAULT 'EXTRACTED',
    confidence_score FLOAT DEFAULT 1.0,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_policy_facts_policy ON policy_facts(policy_id);
CREATE INDEX IF NOT EXISTS idx_policy_facts_field ON policy_facts(field_name);
CREATE INDEX IF NOT EXISTS idx_policy_facts_status ON policy_facts(verification_status);

-- 6. Authorized Reviews (Outbound link metadata & compliant storage)
CREATE TABLE IF NOT EXISTS authorized_reviews (
    id SERIAL PRIMARY KEY,
    provider_slug VARCHAR(100) NOT NULL,
    policy_id INTEGER REFERENCES insurance_policies(id) ON DELETE SET NULL,
    source_name VARCHAR(150) NOT NULL,
    source_url VARCHAR(500) NOT NULL,
    external_review_id VARCHAR(100),
    rating FLOAT,
    review_text TEXT,
    publication_date DATE,
    retrieval_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    review_type VARCHAR(50) DEFAULT 'INDEPENDENT_REVIEW',
    verification_status VARCHAR(50) DEFAULT 'UNVERIFIED',
    is_outbound_link_only BOOLEAN DEFAULT TRUE,
    sentiment VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_auth_reviews_provider ON authorized_reviews(provider_slug);

-- 7. Add columns to existing tables non-destructively
ALTER TABLE insurance_policies ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'CURRENT';
ALTER TABLE insurance_policies ADD COLUMN IF NOT EXISTS active_version_id INTEGER REFERENCES policy_versions(id) ON DELETE SET NULL;
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS page_number INTEGER;
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS policy_version_id INTEGER REFERENCES policy_versions(id) ON DELETE SET NULL;

COMMIT;
