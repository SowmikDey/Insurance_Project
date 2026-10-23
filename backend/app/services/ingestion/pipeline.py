"""
IngestionPipeline — wires all ingestion services into a complete, idempotent pipeline.

Flow per job:
  1. Validate source authorization
  2. Discover product pages from a catalogue URL
  3. For each product page: fetch HTML → normalize → extract facts
  4. For each PDF link: fetch PDF bytes → extract → normalize → extract facts
  5. Create/update InsurancePolicy stub, PolicyVersion, DocumentSource, DocumentChunk,
     and PolicyFact records
  6. Update job counters throughout
  7. Mark job COMPLETED or FAILED
"""
import logging
import re
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.fact import PolicyVersion
from app.models.ingestion import IngestionJob, SourceRegistry
from app.models.insurer import InsuranceCategory, Insurer
from app.models.policy import InsurancePolicy
from app.services.ingestion.authorization_service import (
    AuthorizationActivity,
    check_authorization,
)
from app.services.ingestion.fact_extractor import PolicyFactExtractor
from app.services.ingestion.html_ingestor import HTMLIngestor
from app.services.ingestion.job_manager import JobManager, JobStatus
from app.services.ingestion.normalizer import DocumentNormalizer
from app.services.ingestion.pdf_ingestor import PDFIngestor
from app.services.ingestion.product_discovery import ProductDiscoveryService
from app.services.ingestion.protected_fetcher import ProtectedFetcherService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slugify(text: str) -> str:
    """Convert arbitrary text into a URL-safe slug (lowercase, hyphens only)."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-{2,}", "-", text)
    return text[:120].strip("-")


def _get_or_create_policy(
    db: Session,
    product_name: str,
    provider_slug: str,
    source_url: Optional[str] = None,
) -> InsurancePolicy:
    """
    Idempotently fetch-or-create an InsurancePolicy stub.
    Category defaults to 'health' if none exists; insurer defaults to the
    provider_slug insurer, creating a minimal stub if needed.
    """
    policy_slug = f"{_slugify(product_name)}-{_slugify(provider_slug)}"

    existing = db.query(InsurancePolicy).filter(InsurancePolicy.slug == policy_slug).first()
    if existing:
        return existing

    # Resolve insurer record
    insurer = db.query(Insurer).filter(Insurer.slug == provider_slug).first()
    if not insurer:
        insurer = Insurer(
            name=provider_slug.replace("-", " ").title(),
            short_name=provider_slug.replace("-", " ").title(),
            slug=provider_slug,
        )
        db.add(insurer)
        db.flush()

    # Resolve category — default to health
    category = db.query(InsuranceCategory).filter(InsuranceCategory.slug == "health").first()
    if not category:
        category = InsuranceCategory(
            slug="health",
            name="Health Insurance",
            description="Health insurance products",
            icon="Shield",
        )
        db.add(category)
        db.flush()

    policy = InsurancePolicy(
        slug=policy_slug,
        name=product_name,
        category_id=category.id,
        insurer_id=insurer.id,
        policy_wording_url=source_url,
        status="CURRENT",
        is_active=True,
    )
    db.add(policy)
    db.flush()
    return policy


def _get_or_create_version(
    db: Session,
    policy: InsurancePolicy,
    source_url: Optional[str] = None,
    document_source_id: Optional[int] = None,
) -> PolicyVersion:
    """
    Return existing PolicyVersion linked to this policy, or create a new one.
    """
    existing = (
        db.query(PolicyVersion)
        .filter(PolicyVersion.policy_id == policy.id)
        .order_by(PolicyVersion.id.desc())
        .first()
    )
    if existing:
        return existing

    version = PolicyVersion(
        policy_id=policy.id,
        version_number="1.0",
        status="CURRENT",
        source_url=source_url,
        document_source_id=document_source_id,
    )
    db.add(version)
    db.flush()
    return version


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class IngestionPipeline:
    """
    Orchestrates the full ingestion pipeline for a single IngestionJob.

    Designed to be safe to call synchronously from an API endpoint.
    Per-product failures are caught, logged, and counted — they never abort
    the whole job so partial results are always preserved.
    """

    def __init__(self, db: Session):
        self.db = db
        self.fetcher = ProtectedFetcherService(db=db)
        self.discovery = ProductDiscoveryService(db=db)
        self.normalizer = DocumentNormalizer(db=db)
        self.fact_extractor = PolicyFactExtractor(db=db)
        self.html_ingestor = HTMLIngestor(db=db)
        self.pdf_ingestor = PDFIngestor(db=db)
        self.job_manager = JobManager  # class reference

    # ------------------------------------------------------------------
    def run(self, job: IngestionJob, payload: Dict[str, Any]) -> IngestionJob:
        """
        Execute the full ingestion pipeline for *job*.

        Parameters
        ----------
        job:
            The IngestionJob record (already persisted, status RUNNING).
        payload:
            Dict with keys from JobRunRequest.dict() — relevant keys:
            ``url``, ``source_id``, ``provider_slug``, ``job_type``.

        Returns
        -------
        The updated IngestionJob (COMPLETED or FAILED).
        """
        target_url: str = job.requested_url or payload.get("url", "")
        provider_slug: str = job.provider_slug or "unknown"

        # Counters
        discovered_count = 0
        downloaded_count = 0
        extracted_count = 0
        created_count = 0
        updated_count = 0
        duplicate_count = 0
        error_count = 0

        try:
            # ── Step 1: Validate source authorization ──────────────────
            is_permitted, reason, decision_code = check_authorization(
                self.db, target_url, activity=AuthorizationActivity.FETCH
            )
            if not is_permitted:
                self.job_manager.record_blocked(
                    self.db, job.id, reason, decision_code=decision_code
                )
                logger.warning(
                    "Pipeline blocked for job %s: %s (%s)", job.id, reason, decision_code
                )
                return self.job_manager.get_job(self.db, job.id)

            # ── Step 2: Discover product pages from catalogue URL ──────
            self.job_manager.log_event(
                self.db, job.id, f"Starting product discovery from {target_url}"
            )
            discovery_result = self.discovery.discover_from_catalogue(
                catalogue_url=target_url,
                provider_slug=provider_slug,
                max_products=15,
            )

            discovered_products = discovery_result.get("discovered_products", [])
            discovered_documents = discovery_result.get("discovered_documents", [])
            discovered_count = len(discovered_products) + len(discovered_documents)

            self.job_manager.log_event(
                self.db,
                job.id,
                f"Discovery: {len(discovered_products)} product pages, "
                f"{len(discovered_documents)} PDF documents.",
            )

            # ── Step 3: Process each product (HTML) page ───────────────
            for product in discovered_products:
                product_url = product.get("url", "")
                product_name = product.get("name", "Insurance Product")
                try:
                    html_result = self.html_ingestor.ingest(
                        product_url,
                        metadata={"title": product_name, "insurer": provider_slug},
                    )
                    if not html_result.get("success"):
                        logger.warning(
                            "HTML ingest failed for %s: %s",
                            product_url,
                            html_result.get("error"),
                        )
                        error_count += 1
                        continue

                    downloaded_count += 1

                    # Create / fetch policy stub
                    policy = _get_or_create_policy(
                        self.db, product_name, provider_slug, source_url=product_url
                    )
                    is_new_policy = policy.id is None  # flush() ensures ID exists

                    # Normalise and save document
                    doc_source = self.normalizer.process_and_save(
                        html_result,
                        source_type="HTML",
                        policy_id=policy.id,
                        insurer_name=provider_slug,
                    )

                    if html_result.get("sha256") and doc_source.chunk_count == 0:
                        # process_and_save returns existing doc on duplicate
                        duplicate_count += 1
                    else:
                        extracted_count += 1
                        created_count += doc_source.chunk_count

                    # Resolve / create version
                    version = _get_or_create_version(
                        self.db,
                        policy,
                        source_url=product_url,
                        document_source_id=doc_source.id,
                    )

                    # Extract facts
                    sections = html_result.get("sections", [])
                    if sections:
                        facts = self.fact_extractor.extract_facts(
                            sections,
                            document_source_id=doc_source.id,
                            source_url=product_url,
                            policy_id=policy.id,
                            policy_version_id=version.id,
                        )
                        self.fact_extractor.save_facts(
                            facts,
                            self.db,
                            policy_id=policy.id,
                            policy_version_id=version.id,
                        )

                    self.job_manager.log_event(
                        self.db,
                        job.id,
                        f"Processed HTML product page: {product_name} ({product_url})",
                    )

                except Exception as exc:
                    error_count += 1
                    logger.exception(
                        "Error processing HTML product %s: %s", product_url, exc
                    )
                    self.job_manager.log_event(
                        self.db,
                        job.id,
                        f"ERROR processing {product_url}: {exc}",
                        level="ERROR",
                    )

            # ── Step 4: Process each PDF document ──────────────────────
            for doc in discovered_documents:
                doc_url = doc.get("url", "")
                doc_title = doc.get("title", "Policy Wording")
                try:
                    pdf_result = self.pdf_ingestor.ingest_url(
                        doc_url,
                        metadata={"title": doc_title, "insurer": provider_slug},
                    )
                    if not pdf_result.get("success"):
                        logger.warning(
                            "PDF ingest failed for %s: %s",
                            doc_url,
                            pdf_result.get("error"),
                        )
                        error_count += 1
                        continue

                    downloaded_count += 1

                    if pdf_result.get("is_duplicate"):
                        duplicate_count += 1
                        continue

                    # Attempt to match to an existing policy by title heuristic
                    policy = _get_or_create_policy(
                        self.db, doc_title, provider_slug, source_url=doc_url
                    )

                    doc_source = self.normalizer.process_and_save(
                        pdf_result,
                        source_type="PDF",
                        policy_id=policy.id,
                        insurer_name=provider_slug,
                    )
                    extracted_count += 1
                    created_count += doc_source.chunk_count

                    version = _get_or_create_version(
                        self.db,
                        policy,
                        source_url=doc_url,
                        document_source_id=doc_source.id,
                    )

                    # Extract facts from PDF sections
                    sections = pdf_result.get("sections", [])
                    if sections:
                        facts = self.fact_extractor.extract_facts(
                            sections,
                            document_source_id=doc_source.id,
                            source_url=doc_url,
                            policy_id=policy.id,
                            policy_version_id=version.id,
                        )
                        self.fact_extractor.save_facts(
                            facts,
                            self.db,
                            policy_id=policy.id,
                            policy_version_id=version.id,
                        )

                    self.job_manager.log_event(
                        self.db,
                        job.id,
                        f"Processed PDF: {doc_title} ({doc_url})",
                    )

                except Exception as exc:
                    error_count += 1
                    logger.exception(
                        "Error processing PDF %s: %s", doc_url, exc
                    )
                    self.job_manager.log_event(
                        self.db,
                        job.id,
                        f"ERROR processing PDF {doc_url}: {exc}",
                        level="ERROR",
                    )

            # ── Step 7: Mark job completed ─────────────────────────────
            updated_job = self.job_manager.record_completed(
                self.db,
                job.id,
                discovered_count=discovered_count,
                downloaded_count=downloaded_count,
                extracted_count=extracted_count,
                created_count=created_count,
                updated_count=updated_count,
                duplicate_count=duplicate_count,
                needs_review_count=error_count,
            )
            return updated_job

        except Exception as top_level_exc:
            logger.exception("Fatal pipeline error for job %s: %s", job.id, top_level_exc)
            return self.job_manager.record_failed(
                self.db, job.id, str(top_level_exc)
            )
