from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.models.base import TimeStampedModel

class SourceRegistry(TimeStampedModel):
    __tablename__ = "source_registries"
    
    provider_name = Column(String(150), nullable=False)
    provider_slug = Column(String(100), index=True, nullable=False)
    category = Column(String(50), default="Health")
    source_name = Column(String(200), nullable=False)
    source_url = Column(String(500), unique=True, nullable=False)
    url_type = Column(String(50), nullable=False) # CATALOGUE, DOWNLOAD_CENTRE, PRODUCT_PAGE, LEGAL_TERMS, GRIEVANCE
    permission_status = Column(String(50), default="permission_required") # permission_required, authorized, prohibited
    ingestion_mode = Column(String(50), default="link_only") # link_only, crawl_allowed, manual_upload_only
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    last_checked_at = Column(DateTime(timezone=True), nullable=True)

    authorizations = relationship("SourceAuthorization", back_populates="source", cascade="all, delete-orphan")
    jobs = relationship("IngestionJob", back_populates="source")

class SourceAuthorization(TimeStampedModel):
    __tablename__ = "source_authorizations"
    
    provider_slug = Column(String(100), index=True, nullable=False)
    source_id = Column(Integer, ForeignKey("source_registries.id", ondelete="SET NULL"), nullable=True)
    authorization_reference = Column(String(150), unique=True, nullable=False)
    permitted_urls = Column(JSON, default=list) # List of exact URLs or glob patterns
    permitted_document_types = Column(JSON, default=lambda: ["PDF"]) # PDF, HTML
    collection_rights = Column(Boolean, default=False)
    storage_rights = Column(Boolean, default=False)
    review_usage_rights = Column(Boolean, default=False)
    permitted_uses = Column(Text, nullable=True)
    effective_date = Column(DateTime, nullable=False)
    expiration_date = Column(DateTime, nullable=True)
    is_revoked = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)

    source = relationship("SourceRegistry", back_populates="authorizations")

class IngestionJob(TimeStampedModel):
    __tablename__ = "ingestion_jobs"
    
    id = Column(String(64), primary_key=True) # UUID
    source_id = Column(Integer, ForeignKey("source_registries.id", ondelete="SET NULL"), nullable=True)
    provider_slug = Column(String(100), index=True, nullable=False)
    requested_url = Column(String(500), nullable=True)
    job_type = Column(String(50), nullable=False) # DISCOVERY, FETCH_DOC, MANUAL_IMPORT, FULL_INGEST
    status = Column(String(50), default="PENDING", index=True) # PENDING, RUNNING, DOWNLOADED, EXTRACTED, NEEDS_REVIEW, COMPLETED, BLOCKED, RATE_LIMITED, FAILED
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Traceability & counts
    discovered_product_count = Column(Integer, default=0)
    downloaded_document_count = Column(Integer, default=0)
    extracted_document_count = Column(Integer, default=0)
    created_record_count = Column(Integer, default=0)
    updated_record_count = Column(Integer, default=0)
    duplicate_count = Column(Integer, default=0)
    needs_review_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    
    failure_details = Column(Text, nullable=True)
    authorization_decision = Column(String(50), default="PENDING") # AUTHORIZED, BLOCKED_NO_PERMISSION, BLOCKED_EXPIRED, etc.
    log_messages = Column(JSON, default=list)

    source = relationship("SourceRegistry", back_populates="jobs")
