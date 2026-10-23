import os
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.document import DocumentSource, DocumentChunk
from app.models.ingestion import SourceRegistry, SourceAuthorization, IngestionJob
from app.models.fact import PolicyFact, PolicyVersion
from app.models.policy import InsurancePolicy
from app.schemas.document import DocumentSourceSchema, IngestionStatusResponse
from app.schemas.ingestion import (
    SourceRegistrySchema,
    SourceAuthorizationSchema,
    IngestionJobSchema,
    PolicyFactSchema,
    ScrapeRequest,
    JobRunRequest,
    MarketUpdatesApplyRequest,
    PolicyStatusUpdateRequest
)
from app.services.ingestion.market_watch_service import MarketWatchService
from app.services.ingestion.pdf_ingestor import PDFIngestor
from app.services.ingestion.html_ingestor import HTMLIngestor
from app.services.ingestion.normalizer import DocumentNormalizer
from app.services.ingestion.fact_extractor import PolicyFactExtractor
from app.services.ingestion.job_manager import JobManager, JobStatus, JobType
from app.services.ingestion.source_registry_service import list_registered_sources, get_source_by_url
from app.services.ingestion.authorization_service import check_authorization, AuthorizationActivity
from app.services.ingestion.protected_fetcher import SSRFSecurityException
from app.api.dependencies import admin_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingestion", tags=["ingestion"])

@router.get("/status", response_model=IngestionStatusResponse)
def get_ingestion_status(db: Session = Depends(get_db)):
    """Provides overall metrics on indexed sources and chunks in PostgreSQL."""
    from sqlalchemy import case
    total_sources = db.query(DocumentSource).count()
    total_chunks = db.query(DocumentChunk).count()
    processed_sources = db.query(DocumentSource).filter(DocumentSource.is_processed == True).count()
    # Sort: real SHA-256 hashes first (non-null), then by created_at desc
    sha_order = case((DocumentSource.sha256_hash.isnot(None), 0), else_=1)
    recent = (
        db.query(DocumentSource)
        .order_by(sha_order, DocumentSource.created_at.desc())
        .limit(50)
        .all()
    )
    
    return IngestionStatusResponse(
        total_sources=total_sources,
        total_chunks=total_chunks,
        processed_sources=processed_sources,
        recent_sources=recent
    )

@router.get("/sources", response_model=List[SourceRegistrySchema])
def get_sources(provider: Optional[str] = None, db: Session = Depends(get_db)):
    """Lists registered insurance data sources with permission status and ingestion modes."""
    return list_registered_sources(db, provider_slug=provider)

@router.get("/authorizations", response_model=List[SourceAuthorizationSchema])
def get_authorizations(db: Session = Depends(get_db)):
    """Lists documented source authorizations and compliance scopes."""
    return db.query(SourceAuthorization).order_by(SourceAuthorization.effective_date.desc()).all()

@router.get("/jobs", response_model=List[IngestionJobSchema])
def get_ingestion_jobs(limit: int = 20, db: Session = Depends(get_db)):
    """Lists recent ingestion jobs with status, counts, and authorization audit decisions."""
    return JobManager.list_jobs(db, limit=limit)

@router.get("/facts/{policy_id}", response_model=List[PolicyFactSchema])
def get_policy_facts(policy_id: int, db: Session = Depends(get_db)):
    """Retrieves all evidence-backed policy facts for a given policy ID."""
    return db.query(PolicyFact).filter(
        PolicyFact.policy_id == policy_id
    ).order_by(PolicyFact.page_number.asc().nulls_last()).all()

@router.post("/upload", response_model=DocumentSourceSchema)
async def upload_policy_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    insurer_name: Optional[str] = Form(None),
    policy_id: Optional[int] = Form(None),
    db: Session = Depends(get_db), admin_auth: bool = Depends(admin_api_key)
):
    """
    Safely processes an uploaded PDF or TXT policy document.
    Extracts pages, headings, detects scanned documents, indexes into RAG,
    and extracts evidence-backed policy facts if a policy ID is attached.
    """
    if not file.filename.lower().endswith((".pdf", ".txt")):
        raise HTTPException(status_code=400, detail="Only PDF and TXT policy documents are supported.")

    total_size = 0
    max_size = 25 * 1024 * 1024  # 25 MiB
    content_bytes = bytearray()
    while True:
        chunk = await file.read(1024 * 1024)  # 1 MiB chunks
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > max_size:
            raise HTTPException(status_code=400, detail="File size exceeds 25MB limit.")
        content_bytes.extend(chunk)

    doc_title = title or file.filename.replace(".pdf", "").replace("_", " ").title()

    if file.filename.lower().endswith(".pdf"):
        pdf_ingestor = PDFIngestor(db=db)
        parsed = pdf_ingestor.ingest_from_bytes(
            bytes(content_bytes),
            file.filename,
            metadata={"title": doc_title, "insurer": insurer_name}
        )
    else:
        # Plain text
        parsed = {
            "success": True,
            "title": doc_title,
            "filename": file.filename,
            "file_size": len(content_bytes),
            "sha256": PDFIngestor().compute_sha256(bytes(content_bytes)),
            "full_text": bytes(content_bytes).decode("utf-8", errors="ignore"),
            "sections": [{"heading": "Uploaded Document", "content": bytes(content_bytes).decode("utf-8", errors="ignore")}],
            "metadata": {"title": doc_title}
        }

    if not parsed.get("success"):
        raise HTTPException(status_code=500, detail=f"Failed to extract document: {parsed.get('error')}")

    # Check for duplicate
    if parsed.get("is_duplicate"):
        existing_doc = db.query(DocumentSource).filter(DocumentSource.id == parsed.get("existing_id")).first()
        if existing_doc:
            return existing_doc

    normalizer = DocumentNormalizer(db)
    doc_source = normalizer.process_and_save(
        parsed,
        source_type="MANUAL_UPLOAD",
        policy_id=policy_id,
        insurer_name=insurer_name
    )

    # Extract policy facts if a policy record is linked
    if policy_id and parsed.get("sections"):
        policy_obj = db.query(InsurancePolicy).filter(InsurancePolicy.id == policy_id).first()
        version_id = policy_obj.active_version_id if policy_obj else None
        if not version_id and policy_obj:
            ver = db.query(PolicyVersion).filter(PolicyVersion.policy_id == policy_id).first()
            if not ver:
                ver = PolicyVersion(
                    policy_id=policy_id,
                    version_number="1.0",
                    document_source_id=doc_source.id,
                    source_url=file.filename
                )
                db.add(ver)
                db.flush()
            version_id = ver.id
            policy_obj.active_version_id = version_id
            db.flush()

        fact_extractor = PolicyFactExtractor(db=db)
        extracted = fact_extractor.extract_facts(
            parsed["sections"],
            document_source_id=doc_source.id,
            source_url=file.filename,
            policy_id=policy_id,
            policy_version_id=version_id
        )
        fact_extractor.save_facts(extracted, db, policy_id=policy_id, policy_version_id=version_id)

    return doc_source

@router.post("/scrape", response_model=DocumentSourceSchema)
def scrape_official_url(
    payload: ScrapeRequest,
    db: Session = Depends(get_db)
):
    """
    Fetches and normalizes an authorized official insurance disclosure URL.
    Strictly enforced by ProtectedFetcherService:
    - Validates HTTPS and rejects internal/loopback/cloud metadata (SSRF protection).
    - Blocks unauthorized or link-only sources (such as ICICI Lombard) before making any network request.
    - Records an IngestionJob entry for traceability.
    """
    url = payload.url.strip()
    title = payload.title or "Official Insurance Page"
    policy_id = payload.policy_id
    insurer_name = payload.insurer_name

    # Determine provider slug
    provider_slug = "unknown"
    registered_source = get_source_by_url(db, url)
    if registered_source:
        provider_slug = registered_source.provider_slug
    elif "icicilombard.com" in url.lower():
        provider_slug = "icici-lombard"

    # Create tracked job
    job = JobManager.create_job(
        db,
        provider_slug=provider_slug,
        requested_url=url,
        job_type=JobType.FETCH_DOC,
        source_id=registered_source.id if registered_source else None
    )

    # Enforce backend authorization check BEFORE network call
    is_permitted, auth_reason, decision_code = check_authorization(
        db,
        url,
        activity=AuthorizationActivity.FETCH
    )

    if not is_permitted:
        # Record blocked job in database
        JobManager.record_blocked(db, job.id, auth_reason, decision_code=decision_code)
        logger.warning("Scrape request blocked: %s (Decision: %s)", url, decision_code)
        raise HTTPException(
            status_code=403,
            detail=f"Access Denied: {auth_reason} (Job ID: {job.id})"
        )

    # Execute protected fetch & extraction
    try:
        html_ingestor = HTMLIngestor(db=db)
        result = html_ingestor.ingest(url, metadata={"title": title, "insurer": insurer_name})
    except SSRFSecurityException as e:
        JobManager.record_blocked(db, job.id, f"SSRF Security Violation: {str(e)}", decision_code="BLOCKED_SSRF")
        raise HTTPException(status_code=400, detail=f"SSRF Protection: {str(e)}")
    except Exception as e:
        JobManager.record_failed(db, job.id, str(e))
        raise HTTPException(status_code=500, detail=f"Unexpected extraction error: {str(e)}")

    if not result.get("success"):
        if result.get("blocked"):
            JobManager.record_blocked(
                db,
                job.id,
                result.get("error", "Access blocked"),
                decision_code=result.get("decision_code", "BLOCKED")
            )
            raise HTTPException(status_code=403, detail=result.get("error"))

        JobManager.record_failed(db, job.id, result.get("error", "Extraction failed"))
        raise HTTPException(
            status_code=422,
            detail=f"Could not ingest source URL: {result.get('error')}. You can upload the policy document PDF directly."
        )

    # Normalize and save into PostgreSQL
    normalizer = DocumentNormalizer(db)
    doc_source = normalizer.process_and_save(
        result,
        source_type="HTML",
        policy_id=policy_id,
        insurer_name=insurer_name
    )

    # Extract policy facts if linked to policy
    if policy_id and result.get("sections"):
        policy_obj = db.query(InsurancePolicy).filter(InsurancePolicy.id == policy_id).first()
        version_id = policy_obj.active_version_id if policy_obj else None
        if not version_id and policy_obj:
            ver = db.query(PolicyVersion).filter(PolicyVersion.policy_id == policy_id).first()
            if not ver:
                ver = PolicyVersion(
                    policy_id=policy_id,
                    version_number="1.0",
                    document_source_id=doc_source.id,
                    source_url=url
                )
                db.add(ver)
                db.flush()
            version_id = ver.id
            policy_obj.active_version_id = version_id
            db.flush()

        fact_extractor = PolicyFactExtractor(db=db)
        extracted = fact_extractor.extract_facts(
            result["sections"],
            document_source_id=doc_source.id,
            source_url=url,
            policy_id=policy_id,
            policy_version_id=version_id
        )
        fact_extractor.save_facts(extracted, db, policy_id=policy_id, policy_version_id=version_id)

    # Mark job as completed
    JobManager.record_completed(
        db,
        job.id,
        downloaded_count=1,
        extracted_count=1,
        created_count=doc_source.chunk_count
    )

    return doc_source

@router.post("/jobs/run", response_model=IngestionJobSchema)
def run_ingestion_job(
    payload: JobRunRequest,
    db: Session = Depends(get_db)
):
    """
    Triggers an ingestion job for a registered source or URL.
    Enforces authorization check. If unauthorized, records BLOCKED_NO_PERMISSION and rejects.
    """
    source = None
    target_url = payload.url

    if payload.source_id:
        source = db.query(SourceRegistry).filter(SourceRegistry.id == payload.source_id).first()
        if source:
            target_url = source.source_url

    if not target_url:
        raise HTTPException(status_code=400, detail="Either source_id or target URL must be provided.")

    provider_slug = source.provider_slug if source else "unknown"
    if "icicilombard.com" in target_url.lower():
        provider_slug = "icici-lombard"

    job = JobManager.create_job(
        db,
        provider_slug=provider_slug,
        requested_url=target_url,
        job_type=payload.job_type,
        source_id=source.id if source else None
    )

    # Check authorization
    is_permitted, reason, decision_code = check_authorization(
        db,
        target_url,
        activity=AuthorizationActivity.FETCH
    )

    if not is_permitted:
        JobManager.record_blocked(db, job.id, reason, decision_code=decision_code)
        return job

    # If authorized, mark running and execute the ingestion pipeline
    JobManager.record_running(db, job.id, authorization_decision="AUTHORIZED")
    try:
        from app.services.ingestion.pipeline import IngestionPipeline
        pipeline = IngestionPipeline(db)
        job = pipeline.run(job, payload.model_dump() if hasattr(payload, "model_dump") else payload.dict())
    except Exception as exc:
        logger.exception("Pipeline run failed for job %s: %s", job.id, exc)
        job = JobManager.record_failed(db, job.id, str(exc))
    return job


@router.get("/market-updates")
def get_market_updates(db: Session = Depends(get_db)):
    """
    Scans registered market sources & IRDAI catalogue against existing database records.
    Returns: new discoveries, detected revisions, status alerts, and policy inventory.
    """
    return MarketWatchService.scan_market(db)


@router.post("/market-updates/scan")
def trigger_market_scan(db: Session = Depends(get_db)):
    """Triggers an on-demand market scan for newly filed policies and revisions."""
    return MarketWatchService.scan_market(db)


@router.post("/market-updates/apply")
def apply_market_updates(
    payload: MarketUpdatesApplyRequest,
    db: Session = Depends(get_db)
):
    """
    Applies admin-approved market updates.
    Ingests brand new policies into DB or updates revisions to existing policies.
    """
    try:
        result = MarketWatchService.apply_market_updates(
            db,
            items=payload.items,
            applied_by=payload.applied_by or "Admin"
        )
        return result
    except Exception as exc:
        logger.exception("Failed to apply market updates: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.patch("/policies/{policy_id}/status")
def update_policy_status(
    policy_id: int,
    payload: PolicyStatusUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Updates the lifecycle status of an insurance policy (CURRENT, WITHDRAWN, NEEDS_REVIEW, SUPERSEDED).
    Persists immediately to PostgreSQL and audits the change.
    """
    try:
        result = MarketWatchService.update_policy_status(
            db,
            policy_id=policy_id,
            new_status=payload.status,
            reason=payload.reason
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as exc:
        logger.exception("Failed to update policy status: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
