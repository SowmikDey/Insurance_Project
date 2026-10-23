from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date

class SourceRegistrySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider_name: str
    provider_slug: str
    category: Optional[str] = "Health"
    source_name: str
    source_url: str
    url_type: str
    permission_status: str
    ingestion_mode: str
    description: Optional[str] = None
    is_active: bool = True
    last_checked_at: Optional[datetime] = None

class SourceAuthorizationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider_slug: str
    source_id: Optional[int] = None
    authorization_reference: str
    permitted_urls: List[str] = []
    permitted_document_types: List[str] = ["PDF"]
    collection_rights: bool = False
    storage_rights: bool = False
    review_usage_rights: bool = False
    permitted_uses: Optional[str] = None
    effective_date: date
    expiration_date: Optional[date] = None
    is_revoked: bool = False
    notes: Optional[str] = None

class PolicyFactSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    policy_id: int
    policy_version_id: Optional[int] = None
    field_name: str
    field_value: Optional[str] = None
    normalized_value: Optional[str] = None
    evidence_snippet: str
    section_heading: Optional[str] = None
    page_number: Optional[int] = None
    source_url: Optional[str] = None
    document_source_id: Optional[int] = None
    extraction_method: str = "DETERMINISTIC_REGEX"
    verification_status: str = "EXTRACTED"
    confidence_score: float = 1.0
    notes: Optional[str] = None

class PolicyVersionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    policy_id: int
    version_number: str = "1.0"
    uin_number: Optional[str] = None
    status: str = "CURRENT"
    effective_from_date: Optional[date] = None
    effective_to_date: Optional[date] = None
    superseded_by_version_id: Optional[int] = None
    document_source_id: Optional[int] = None
    source_url: Optional[str] = None
    raw_extracted_data: Dict[str, Any] = {}

class IngestionJobSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_id: Optional[int] = None
    provider_slug: str
    requested_url: Optional[str] = None
    job_type: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    discovered_product_count: int = 0
    downloaded_document_count: int = 0
    extracted_document_count: int = 0
    created_record_count: int = 0
    updated_record_count: int = 0
    duplicate_count: int = 0
    needs_review_count: int = 0
    error_count: int = 0
    failure_details: Optional[str] = None
    authorization_decision: Optional[str] = "PENDING"
    log_messages: List[Dict[str, Any]] = []

class ScrapeRequest(BaseModel):
    url: str
    title: Optional[str] = "Official Insurance Page"
    insurer_name: Optional[str] = None
    policy_id: Optional[int] = None

class JobRunRequest(BaseModel):
    source_id: Optional[int] = None
    url: Optional[str] = None
    job_type: str = "FETCH_DOC"

class MarketUpdatesApplyRequest(BaseModel):
    items: List[Dict[str, Any]]
    applied_by: Optional[str] = "Admin"

class PolicyStatusUpdateRequest(BaseModel):
    status: str
    reason: Optional[str] = None
