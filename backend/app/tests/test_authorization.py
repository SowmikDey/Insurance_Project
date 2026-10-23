import pytest
from app.services.ingestion.authorization_service import (
    check_authorization,
    AuthorizationActivity,
    AuthorizationDecision,
)
from app.services.ingestion.source_registry_service import seed_source_registry
from app.services.ingestion.protected_fetcher import ProtectedFetcherService, SSRFSecurityException

def test_unregistered_domain_blocked(db_session):
    is_perm, reason, decision = check_authorization(
        db_session,
        "https://some-random-unknown-site.in/plans",
        activity=AuthorizationActivity.FETCH
    )
    assert not is_perm
    assert decision == AuthorizationDecision.BLOCKED_UNREGISTERED

def test_icici_lombard_link_only(db_session):
    seed_source_registry(db_session)
    is_perm, reason, decision = check_authorization(
        db_session,
        "https://www.icicilombard.com/health-insurance",
        activity=AuthorizationActivity.FETCH
    )
    assert not is_perm
    assert decision in (AuthorizationDecision.BLOCKED_LINK_ONLY, AuthorizationDecision.BLOCKED_NO_PERMISSION)

def test_policybazaar_link_only(db_session):
    seed_source_registry(db_session)
    is_perm, reason, decision = check_authorization(
        db_session,
        "https://www.policybazaar.com/health-insurance/",
        activity=AuthorizationActivity.FETCH
    )
    assert not is_perm
    assert decision in (AuthorizationDecision.BLOCKED_LINK_ONLY, AuthorizationDecision.BLOCKED_NO_PERMISSION)

def test_irdai_authorized_for_crawling(db_session):
    seed_source_registry(db_session)
    is_perm, reason, decision = check_authorization(
        db_session,
        "https://irdai.gov.in/health-insurance-products",
        activity=AuthorizationActivity.FETCH
    )
    assert is_perm
    assert decision == AuthorizationDecision.AUTHORIZED

def test_ssrf_rejection_for_private_and_metadata_ips():
    fetcher = ProtectedFetcherService()
    
    with pytest.raises(SSRFSecurityException):
        fetcher.validate_url_syntax("http://169.254.169.254/latest/meta-data")

    with pytest.raises(SSRFSecurityException):
        fetcher.validate_url_syntax("http://metadata.google.internal/computeMetadata/v1")

    with pytest.raises(SSRFSecurityException):
        fetcher.validate_url_syntax("http://user:password@malicious-site.com")
