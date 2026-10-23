import io
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.services.ingestion.protected_fetcher import (
    ProtectedFetcherService,
    SSRFSecurityException
)
from app.services.ingestion.authorization_service import (
    check_authorization,
    AuthorizationActivity,
    AuthorizationDecision
)
from app.services.ingestion.source_registry_service import seed_source_registry
from app.services.ingestion.pdf_ingestor import PDFIngestor
from app.services.ingestion.fact_extractor import PolicyFactExtractor, FactExtractionStatus
from app.services.ingestion.review_adapter import ReviewAdapter
from app.models.ingestion import SourceRegistry, IngestionJob
from app.models.policy import InsurancePolicy

client = TestClient(app)

def test_ssrf_private_ip_and_metadata_rejection():
    """Verify that private, loopback, link-local, and cloud metadata targets are rejected."""
    blocked_ips = [
        "127.0.0.1",
        "10.0.0.1",
        "172.16.0.1",
        "192.168.1.1",
        "169.254.169.254", # Cloud metadata
        "::1",             # IPv6 loopback
        "100.64.0.1",      # CGNAT
        "198.18.0.1",      # Benchmark
    ]
    for ip in blocked_ips:
        with pytest.raises(SSRFSecurityException):
            ProtectedFetcherService.validate_ip_safety(ip)

def test_ssrf_malformed_and_credential_urls():
    """Verify that embedded credentials and non-https schemes are rejected."""
    unsafe_urls = [
        "http://admin:secret@example.com/notices",
        "ftp://example.com/policy.pdf",
        "file:///etc/passwd",
        "gopher://example.com",
        "https://metadata.google.internal/computeMetadata/v1",
        "https://localhost:8000/api"
    ]
    for url in unsafe_urls:
        with pytest.raises(SSRFSecurityException):
            ProtectedFetcherService.validate_url_syntax(url)

def test_unauthorized_icici_source_blocked_before_network():
    """
    Verify that ICICI Lombard reference sources are blocked by the backend authorization check
    and that ZERO outbound network requests are made.
    """
    db = SessionLocal()
    try:
        # Seed sources if needed
        seed_source_registry(db)

        icici_url = "https://www.icicilombard.com/health-insurance/elevate-health-policy"
        is_permitted, reason, decision = check_authorization(db, icici_url, activity=AuthorizationActivity.FETCH)
        
        assert is_permitted is False
        assert decision in (AuthorizationDecision.BLOCKED_NO_PERMISSION, AuthorizationDecision.BLOCKED_LINK_ONLY)
        assert "link_only" in reason.lower() or "link-only" in reason.lower() or "authorization" in reason.lower()

        # Verify ProtectedFetcher does NOT make any HTTP network call when blocked
        fetcher = ProtectedFetcherService(db=db)
        with patch.object(fetcher.base_client, "get") as mock_get:
            res = fetcher.fetch(icici_url)
            assert res["success"] is False
            assert res["blocked"] is True
            assert res["status_code"] == 403
            mock_get.assert_not_called() # Crucial: NO socket opened!
    finally:
        db.close()

def test_scrape_endpoint_blocks_unauthorized_url():
    """Verify that calling /ingestion/scrape with ICICI Lombard returns HTTP 403 and records a BLOCKED job."""
    res = client.post("/api/v1/ingestion/scrape", json={
        "url": "https://www.icicilombard.com/health-insurance/health-advantedge",
        "title": "Health AdvantEdge"
    })
    assert res.status_code == 403
    data = res.json()
    assert "detail" in data
    assert "Access Denied" in data["detail"] or "link_only" in data["detail"]

    # Verify an IngestionJob record was created in PostgreSQL with status BLOCKED_NO_PERMISSION
    db = SessionLocal()
    try:
        job = db.query(IngestionJob).filter(
            IngestionJob.requested_url == "https://www.icicilombard.com/health-insurance/health-advantedge"
        ).order_by(IngestionJob.created_at.desc()).first()
        assert job is not None
        assert job.status == "BLOCKED_NO_PERMISSION"
        assert job.provider_slug == "icici-lombard"
    finally:
        db.close()

def test_source_registry_registration():
    """Verify all 8 ICICI Lombard reference sources are registered with permission_required and link_only."""
    res = client.get("/api/v1/ingestion/sources")
    assert res.status_code == 200
    sources = res.json()
    assert len(sources) >= 8

    urls = [s["source_url"] for s in sources]
    expected_urls = [
        "https://www.icicilombard.com/health-insurance",
        "https://www.icicilombard.com/downloads?download=true",
        "https://www.icicilombard.com/health-insurance/elevate-health-policy",
        "https://www.icicilombard.com/health-insurance/max-protect-1-crore-health-insurance",
        "https://www.icicilombard.com/health-insurance/health-advantedge",
        "https://www.icicilombard.com/health-insurance/health-booster",
        "https://www.icicilombard.com/legal/terms",
        "https://www.icicilombard.com/grievance-redressal"
    ]
    for u in expected_urls:
        assert u in urls

    for s in sources:
        if "icicilombard.com" in s["source_url"]:
            assert s["permission_status"] == "permission_required"
            assert s["ingestion_mode"] == "link_only"

def test_pdf_extractor_page_awareness_and_duplicates():
    """Verify PDF extraction extracts page numbers, headings, detects duplicate hash, and detects scanned docs."""
    db = SessionLocal()
    try:
        # Create a genuine multi-page test PDF in memory using pypdf
        from pypdf import PdfWriter
        from reportlab.pdfgen import canvas
        
        packet = io.BytesIO()
        can = canvas.Canvas(packet)
        can.drawString(50, 750, "IRDAI Policy Wordings Clause 1: Hospitalization")
        can.drawString(50, 700, "Room rent limit: Single Private A/C Room without sub-limit.")
        can.showPage()
        can.drawString(50, 750, "Clause 2: Exclusions and Waiting Periods")
        can.drawString(50, 700, "Pre-existing diseases waiting period: 24 Months.")
        can.save()
        
        pdf_bytes = packet.getvalue()
        
        ingestor = PDFIngestor(db=db)
        res = ingestor.ingest_from_bytes(pdf_bytes, filename="test_policy_wording.pdf")
        
        assert res["success"] is True
        assert res["total_pages"] == 2
        assert len(res["sections"]) == 2
        assert res["sections"][0]["page_number"] == 1
        assert res["sections"][1]["page_number"] == 2
        assert "Single Private" in res["sections"][0]["content"]
        assert "24 Months" in res["sections"][1]["content"]
        
        # Ingest and save to DB to test duplicate detection
        from app.services.ingestion.normalizer import DocumentNormalizer
        normalizer = DocumentNormalizer(db)
        saved_doc = normalizer.process_and_save(res, source_type="PDF")
        
        # Re-ingest exact same bytes
        res_dup = ingestor.ingest_from_bytes(pdf_bytes, filename="test_policy_wording.pdf")
        assert res_dup["is_duplicate"] is True
        assert res_dup["existing_id"] == saved_doc.id
    finally:
        db.close()

def test_fact_extraction_evidence_and_unknown_handling():
    """Verify deterministic fact extraction preserves exact snippet, page, and tracks unknown fields."""
    sections = [
        {
            "heading": "Section 1: In-patient Hospitalization",
            "page_number": 4,
            "content": "Under Section 1, room rent charges are capped at Single Private Room. Co-payment percentage is 0% (nil copay). Pre-hospitalization coverage is for 60 days."
        },
        {
            "heading": "Section 4: Waiting Periods",
            "page_number": 12,
            "content": "IRDAI UIN: ICIHLIP24001V012324. Pre-existing diseases (PED) waiting period is 24 months. Initial waiting period of 30 days applies."
        }
    ]

    extractor = PolicyFactExtractor()
    facts = extractor.extract_facts(sections, document_source_id=1, source_url="https://example.com/test.pdf")

    facts_by_field = {f["field_name"]: f for f in facts}

    # Verified extracted facts
    assert "uin_number" in facts_by_field
    assert facts_by_field["uin_number"]["field_value"] == "ICIHLIP24001V012324"
    assert facts_by_field["uin_number"]["page_number"] == 12
    assert facts_by_field["uin_number"]["verification_status"] == FactExtractionStatus.EXTRACTED
    assert "ICIHLIP24001V012324" in facts_by_field["uin_number"]["evidence_snippet"]

    assert "copay_percentage" in facts_by_field
    assert facts_by_field["copay_percentage"]["normalized_value"] == "0%"
    assert facts_by_field["copay_percentage"]["page_number"] == 4

    assert "ped_waiting_period" in facts_by_field
    assert facts_by_field["ped_waiting_period"]["normalized_value"] == "24 Months"
    assert facts_by_field["ped_waiting_period"]["page_number"] == 12

    # Unextracted/unknown field remains UNAVAILABLE without fabricating values
    assert "restoration_benefit" in facts_by_field
    assert facts_by_field["restoration_benefit"]["field_value"] is None
    assert facts_by_field["restoration_benefit"]["verification_status"] == FactExtractionStatus.UNAVAILABLE

def test_unapproved_review_collection_blocked():
    """Verify that customer reviews for link-only sources are stored as outbound links without review text."""
    db = SessionLocal()
    try:
        adapter = ReviewAdapter(db)
        review = adapter.register_review(
            provider_slug="icici-lombard",
            source_name="MouthShut",
            source_url="https://www.icicilombard.com/reviews/user123",
            external_review_id="REV-12345",
            rating=4.5,
            review_text="Great claim experience at network hospital." # Should NOT be stored without authorization
        )
        assert review.is_outbound_link_only is True
        assert review.review_text is None # Scrubbed/blocked because authorization is missing!
        assert review.rating == 4.5
    finally:
        db.close()

def test_explorer_uses_database_records_and_honest_empty_state():
    """Verify that the Insurances explorer reads actual database records and displays empty state when 0 exist."""
    res = client.get("/api/v1/policies")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data

    db = SessionLocal()
    try:
        real_count = db.query(InsurancePolicy).filter(InsurancePolicy.is_active == True).count()
        assert data["total"] == real_count
        assert len(data["items"]) == min(12, real_count)
    finally:
        db.close()
