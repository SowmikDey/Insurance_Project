import logging
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.services.ingestion.base_ingestor import BaseIngestor
from app.services.ingestion.protected_fetcher import ProtectedFetcherService
from app.services.ingestion.authorization_service import AuthorizationActivity

logger = logging.getLogger(__name__)

class HTMLIngestor(BaseIngestor):
    """
    Ingestor for authorized public insurance informational pages.
    All network fetching is strictly routed through ProtectedFetcherService,
    guaranteeing SSRF prevention, permission verification, and rate-limiting.
    """
    def __init__(self, db: Optional[Session] = None, request_interval_sec: float = 1.5):
        super().__init__(request_interval_sec)
        self.db = db
        self.fetcher = ProtectedFetcherService(db=db)

    def ingest(self, source_url: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Fetches the target URL via the centralized protected fetcher and parses structured HTML content.
        """
        fetch_result = self.fetcher.fetch(source_url, activity=AuthorizationActivity.FETCH)
        if not fetch_result.get("success"):
            return {
                "success": False,
                "error": fetch_result.get("error", "Failed to fetch document"),
                "status_code": fetch_result.get("status_code", 400),
                "decision_code": fetch_result.get("decision_code", "BLOCKED"),
                "source_url": source_url,
                "blocked": fetch_result.get("blocked", False)
            }

        raw_bytes = fetch_result["content_bytes"]
        sha256 = self.compute_sha256(raw_bytes)

        try:
            html_text = raw_bytes.decode("utf-8", errors="ignore")
            soup = BeautifulSoup(html_text, "html.parser")
            
            # Clean unwanted non-content tags
            for elem in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
                elem.decompose()

            # Extract title
            title = soup.title.string.strip() if (soup.title and soup.title.string) else "Untitled Insurance Source"
            if metadata and metadata.get("title"):
                title = metadata["title"]

            # Extract structured sections
            sections = []
            current_heading = "Overview"
            current_paras = []

            for tag in soup.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
                if tag.name in ["h1", "h2", "h3", "h4"]:
                    if current_paras:
                        sections.append({
                            "heading": current_heading,
                            "content": "\n".join(current_paras)
                        })
                        current_paras = []
                    current_heading = tag.get_text(strip=True)[:100]
                else:
                    text = tag.get_text(strip=True)
                    if text and len(text) > 15:
                        current_paras.append(text)

            if current_paras:
                sections.append({
                    "heading": current_heading,
                    "content": "\n".join(current_paras)
                })

            full_text = "\n\n".join([f"## {s['heading']}\n{s['content']}" for s in sections])

            return {
                "success": True,
                "title": title,
                "source_url": source_url,
                "sha256": sha256,
                "file_size": len(raw_bytes),
                "sections": sections,
                "full_text": full_text,
                "metadata": metadata or {}
            }
        except Exception as e:
            logger.error("Error parsing HTML from %s: %s", source_url, e)
            return {
                "success": False,
                "error": f"HTML parsing error: {str(e)}",
                "source_url": source_url
            }
