import logging
from typing import Tuple, Optional
from datetime import date
from urllib.parse import urlparse
from sqlalchemy.orm import Session
from app.models.ingestion import SourceRegistry, SourceAuthorization

logger = logging.getLogger(__name__)

class AuthorizationActivity:
    FETCH = "FETCH"
    STORE_TEXT = "STORE_TEXT"
    GENERATE_EMBEDDINGS = "GENERATE_EMBEDDINGS"
    STORE_REVIEWS = "STORE_REVIEWS"
    REPUBLISH_EXCERPTS = "REPUBLISH_EXCERPTS"

class AuthorizationDecision:
    AUTHORIZED = "AUTHORIZED"
    BLOCKED_NO_PERMISSION = "BLOCKED_NO_PERMISSION"
    BLOCKED_REVOKED = "BLOCKED_REVOKED"
    BLOCKED_EXPIRED = "BLOCKED_EXPIRED"
    BLOCKED_UNREGISTERED = "BLOCKED_UNREGISTERED"
    BLOCKED_LINK_ONLY = "BLOCKED_LINK_ONLY"
    BLOCKED_SCOPE_EXCEEDED = "BLOCKED_SCOPE_EXCEEDED"

def check_authorization(
    db: Session,
    url: str,
    activity: str = AuthorizationActivity.FETCH
) -> Tuple[bool, str, str]:
    """
    Checks if an operation on a given target URL is explicitly permitted by backend policy.
    Returns: (is_permitted: bool, reason: str, decision_code: str)
    
    Guarantees:
    - Never performs outbound network requests.
    - Strictly blocks unauthorized or link-only sources before any connection is attempted.
    - Evaluates authorization scope by domain, path, and activity.
    """
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return False, "Malformed URL: missing scheme or network location.", AuthorizationDecision.BLOCKED_UNREGISTERED

    # Reject embedded credentials in URL
    if parsed.username or parsed.password:
        return False, "Security violation: Embedded user credentials in URL are prohibited.", AuthorizationDecision.BLOCKED_SCOPE_EXCEEDED

    hostname = parsed.hostname.lower() if parsed.hostname else ""
    path = parsed.path or "/"

    # Query source registry by exact URL or domain
    clean_url = url.split("?")[0].rstrip("/")
    source = db.query(SourceRegistry).filter(
        (SourceRegistry.source_url == url) | 
        (SourceRegistry.source_url == clean_url) |
        (SourceRegistry.source_url.like(f"%{hostname}%"))
    ).first()

    if not source:
        # Check if the host belongs to a known provider restricted to link-only
        if "icicilombard.com" in hostname:
            return (
                False,
                "ICICI Lombard source is not authorized for automated crawling or content ingestion. Operating in link-only mode.",
                AuthorizationDecision.BLOCKED_LINK_ONLY
            )
        if "policybazaar.com" in hostname:
            return (
                False,
                "Policybazaar is a discovery reference and UX benchmark only; automated scraping, storage, or republication is disabled (link-only mode).",
                AuthorizationDecision.BLOCKED_LINK_ONLY
            )
        return (
            False,
            f"Domain '{hostname}' is not a registered insurance data source. External scraping is restricted to authorized registries.",
            AuthorizationDecision.BLOCKED_UNREGISTERED
        )

    # If source is explicitly marked prohibited or permission_required with link_only mode
    if source.permission_status == "prohibited":
        return (
            False,
            f"Source '{source.source_name}' is explicitly prohibited from content collection by provider policy.",
            AuthorizationDecision.BLOCKED_NO_PERMISSION
        )

    if source.ingestion_mode == "link_only" or source.permission_status == "permission_required":
        # Check if an explicit active authorization has been granted in source_authorizations
        today = date.today()
        auth = db.query(SourceAuthorization).filter(
            SourceAuthorization.provider_slug == source.provider_slug,
            SourceAuthorization.is_revoked == False,
            SourceAuthorization.effective_date <= today
        ).first()

        if not auth:
            return (
                False,
                f"Source '{source.source_name}' requires written authorization (ingestion_mode: link_only). No active authorization grant on file.",
                AuthorizationDecision.BLOCKED_NO_PERMISSION
            )

        if auth.expiration_date and auth.expiration_date < today:
            return (
                False,
                f"Authorization reference '{auth.authorization_reference}' expired on {auth.expiration_date}.",
                AuthorizationDecision.BLOCKED_EXPIRED
            )

        # Check URL scope
        url_permitted = False
        for pattern in (auth.permitted_urls or []):
            if pattern == "*" or pattern == url or url.startswith(pattern):
                url_permitted = True
                break

        if not url_permitted:
            return (
                False,
                f"URL '{url}' is outside the authorized path scope of reference '{auth.authorization_reference}'.",
                AuthorizationDecision.BLOCKED_SCOPE_EXCEEDED
            )

        # Check activity permissions
        if activity in (AuthorizationActivity.FETCH, AuthorizationActivity.STORE_TEXT):
            if not auth.collection_rights or not auth.storage_rights:
                return (
                    False,
                    f"Authorization reference '{auth.authorization_reference}' does not grant collection/storage rights.",
                    AuthorizationDecision.BLOCKED_NO_PERMISSION
                )
        elif activity == AuthorizationActivity.STORE_REVIEWS:
            if not auth.review_usage_rights:
                return (
                    False,
                    f"Authorization reference '{auth.authorization_reference}' does not grant customer review collection rights.",
                    AuthorizationDecision.BLOCKED_NO_PERMISSION
                )

        return (
            True,
            f"Operation authorized under compliance reference: {auth.authorization_reference}",
            AuthorizationDecision.AUTHORIZED
        )

    # If source permission_status == 'authorized' and crawl_allowed
    if source.permission_status == "authorized" and source.ingestion_mode == "crawl_allowed":
        return (
            True,
            f"Source '{source.source_name}' is pre-authorized for respectful informational crawling.",
            AuthorizationDecision.AUTHORIZED
        )

    return (
        False,
        f"Authorization check failed for source '{source.source_name}' (status: {source.permission_status}, mode: {source.ingestion_mode}).",
        AuthorizationDecision.BLOCKED_NO_PERMISSION
    )
