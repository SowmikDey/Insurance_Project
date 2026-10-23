import re
import logging
from urllib.parse import urlparse, urljoin
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.services.ingestion.protected_fetcher import ProtectedFetcherService
from app.services.ingestion.authorization_service import (
    check_authorization,
    AuthorizationActivity,
    AuthorizationDecision
)

logger = logging.getLogger(__name__)

class PolicyCategoryDetector:
    TOP_UP_KEYWORDS = ["top-up", "top up", "booster", "super top-up", "super top up", "deductible"]
    RIDER_KEYWORDS = ["rider", "add-on", "addon", "optional cover", "critical illness rider"]
    COMBO_KEYWORDS = ["combo", "package", "bundle"]

    @classmethod
    def classify_product(cls, name: str, url: str) -> str:
        text = f"{name} {url}".lower()
        if any(k in text for k in cls.RIDER_KEYWORDS):
            return "RIDER"
        if any(k in text for k in cls.TOP_UP_KEYWORDS):
            return "SUPER_TOP_UP"
        if any(k in text for k in cls.COMBO_KEYWORDS):
            return "COMBO"
        return "STANDALONE"

class ProductDiscoveryService:
    """
    Generic, bounded product discovery engine for authorized public insurance catalogues.
    Enforces authorization check first, extracts permitted product and wording links,
    normalizes URLs, detects duplicates, and classifies product types without indiscriminate crawling.
    """

    def __init__(self, db: Session):
        self.db = db
        self.fetcher = ProtectedFetcherService(db=db)

    def discover_from_catalogue(
        self,
        catalogue_url: str,
        provider_slug: str,
        max_products: int = 15
    ) -> Dict[str, Any]:
        """
        Scans an authorized catalogue page to discover candidate product pages and PDF wordings.
        Strictly blocks if the catalogue source is link-only or unauthorized.
        """
        # Step 1: Authorization & SSRF Check via ProtectedFetcher
        fetch_res = self.fetcher.fetch(catalogue_url, activity=AuthorizationActivity.FETCH)
        if not fetch_res.get("success"):
            return {
                "success": False,
                "status": fetch_res.get("decision_code", "BLOCKED"),
                "error": fetch_res.get("error", "Access restricted"),
                "blocked": fetch_res.get("blocked", False),
                "discovered_products": [],
                "discovered_documents": []
            }

        html_bytes = fetch_res["content_bytes"]
        html_text = html_bytes.decode("utf-8", errors="ignore")
        soup = BeautifulSoup(html_text, "html.parser")

        parsed_cat = urlparse(catalogue_url)
        base_host = (parsed_cat.hostname or "").lower()

        discovered_products = []
        discovered_documents = []
        seen_urls = set()

        for a_tag in soup.find_all("a", href=True):
            raw_href = a_tag["href"].strip()
            if not raw_href or raw_href.startswith("#") or raw_href.startswith("javascript:"):
                continue

            full_url = urljoin(catalogue_url, raw_href)
            norm_url = full_url.split("?")[0].rstrip("/")

            if norm_url in seen_urls:
                continue

            parsed_href = urlparse(full_url)
            # Enforce same domain scope
            if (parsed_href.hostname or "").lower() != base_host:
                continue

            anchor_text = a_tag.get_text(strip=True)
            if not anchor_text or len(anchor_text) < 4:
                anchor_text = a_tag.get("title", "").strip() or "Insurance Product"

            seen_urls.add(norm_url)

            # Check if this is a PDF document link
            if full_url.lower().endswith(".pdf") or "download" in full_url.lower():
                discovered_documents.append({
                    "title": anchor_text,
                    "url": full_url,
                    "type": "PDF",
                    "source_catalogue": catalogue_url
                })
            elif any(k in full_url.lower() for k in ["/health-insurance/", "/insurance-plans/", "/plans/", "/policy/"]):
                product_type = PolicyCategoryDetector.classify_product(anchor_text, full_url)
                discovered_products.append({
                    "name": anchor_text,
                    "url": full_url,
                    "provider_slug": provider_slug,
                    "product_type": product_type
                })

            if len(discovered_products) >= max_products:
                break

        return {
            "success": True,
            "status": "DISCOVERY_COMPLETED",
            "catalogue_url": catalogue_url,
            "provider_slug": provider_slug,
            "discovered_products": discovered_products,
            "discovered_documents": discovered_documents,
            "count": len(discovered_products)
        }
