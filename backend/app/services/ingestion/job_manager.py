import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.models.ingestion import IngestionJob

logger = logging.getLogger(__name__)

class JobStatus:
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    BLOCKED_NO_PERMISSION = "BLOCKED_NO_PERMISSION"
    RATE_LIMITED = "RATE_LIMITED"
    FAILED = "FAILED"
    NEEDS_REVIEW = "NEEDS_REVIEW"

class JobType:
    FETCH_DOC = "FETCH_DOC"
    MANUAL_IMPORT = "MANUAL_IMPORT"
    DISCOVERY = "DISCOVERY"
    FULL_INGEST = "FULL_INGEST"
    MARKET_SCAN = "MARKET_SCAN"
    MARKET_UPDATE = "MARKET_UPDATE"

class JobManager:
    """
    Manages lifecycle, counts, status transitions, and audit logs for IngestionJob records.
    Provides idempotent tracking without external message brokers.
    """

    @staticmethod
    def create_job(
        db: Session,
        provider_slug: str,
        requested_url: Optional[str] = None,
        job_type: str = JobType.FETCH_DOC,
        source_id: Optional[int] = None
    ) -> IngestionJob:
        job_id = str(uuid.uuid4())
        job = IngestionJob(
            id=job_id,
            source_id=source_id,
            provider_slug=provider_slug,
            requested_url=requested_url,
            job_type=job_type,
            status=JobStatus.PENDING,
            started_at=datetime.now(timezone.utc),
            authorization_decision="PENDING",
            log_messages=[]
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        logger.info("Created ingestion job %s (type: %s, provider: %s)", job_id, job_type, provider_slug)
        return job

    @staticmethod
    def log_event(db: Session, job_id: str, message: str, level: str = "INFO") -> None:
        job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
        if not job:
            return

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message
        }
        current_logs = list(job.log_messages or [])
        current_logs.append(entry)
        job.log_messages = current_logs
        db.commit()

    @staticmethod
    def record_blocked(
        db: Session,
        job_id: str,
        reason: str,
        decision_code: str = "BLOCKED_NO_PERMISSION"
    ) -> IngestionJob:
        job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        job.status = JobStatus.BLOCKED_NO_PERMISSION
        job.authorization_decision = decision_code
        job.failure_details = reason
        job.completed_at = datetime.now(timezone.utc)
        
        JobManager.log_event(db, job_id, f"Job blocked by authorization policy: {reason}", level="WARNING")
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def record_running(db: Session, job_id: str, authorization_decision: str = "AUTHORIZED") -> IngestionJob:
        job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        job.status = JobStatus.RUNNING
        job.authorization_decision = authorization_decision
        JobManager.log_event(db, job_id, "Job execution started in background executor.", level="INFO")
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def record_completed(
        db: Session,
        job_id: str,
        discovered_count: int = 0,
        downloaded_count: int = 0,
        extracted_count: int = 0,
        created_count: int = 0,
        updated_count: int = 0,
        duplicate_count: int = 0,
        needs_review_count: int = 0
    ) -> IngestionJob:
        job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now(timezone.utc)
        job.discovered_product_count = discovered_count
        job.downloaded_document_count = downloaded_count
        job.extracted_document_count = extracted_count
        job.created_record_count = created_count
        job.updated_record_count = updated_count
        job.duplicate_count = duplicate_count
        job.needs_review_count = needs_review_count

        JobManager.log_event(
            db,
            job_id,
            f"Job completed successfully. Extracted {extracted_count} docs, created {created_count} records.",
            level="INFO"
        )
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def record_failed(db: Session, job_id: str, error_message: str) -> IngestionJob:
        job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        job.status = JobStatus.FAILED
        job.failure_details = error_message
        job.error_count += 1
        job.completed_at = datetime.now(timezone.utc)
        
        JobManager.log_event(db, job_id, f"Job failed: {error_message}", level="ERROR")
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def get_job(db: Session, job_id: str) -> Optional[IngestionJob]:
        return db.query(IngestionJob).filter(IngestionJob.id == job_id).first()

    @staticmethod
    def list_jobs(db: Session, limit: int = 20) -> List[IngestionJob]:
        return db.query(IngestionJob).order_by(IngestionJob.started_at.desc()).limit(limit).all()
