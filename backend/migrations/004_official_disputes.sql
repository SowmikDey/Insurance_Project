-- 004_official_disputes.sql
-- Create official_disputes table to store verified Ombudsman & consumer commission findings
-- separating allegations, insurer responses, and final adjudicated decisions.

CREATE TABLE IF NOT EXISTS official_disputes (
    id SERIAL PRIMARY KEY,
    dispute_reference VARCHAR(150) NOT NULL UNIQUE,
    authority_name VARCHAR(150) NOT NULL,
    provider_slug VARCHAR(100) NOT NULL,
    insurer_id INTEGER REFERENCES insurers(id) ON DELETE SET NULL,
    policy_id INTEGER REFERENCES insurance_policies(id) ON DELETE SET NULL,
    product_name_stated VARCHAR(200),
    allegation TEXT NOT NULL,
    insurer_response TEXT,
    official_findings TEXT NOT NULL,
    decision_outcome VARCHAR(100) NOT NULL,
    award_amount FLOAT,
    publication_date DATE,
    source_url VARCHAR(500) NOT NULL,
    source_document_id INTEGER REFERENCES document_sources(id) ON DELETE SET NULL,
    is_verified BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

CREATE INDEX IF NOT EXISTS idx_disputes_provider_slug ON official_disputes(provider_slug);
CREATE INDEX IF NOT EXISTS idx_disputes_reference ON official_disputes(dispute_reference);
CREATE INDEX IF NOT EXISTS idx_disputes_policy_id ON official_disputes(policy_id);
