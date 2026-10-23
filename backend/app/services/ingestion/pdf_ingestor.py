import os
import io
import re
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.services.ingestion.base_ingestor import BaseIngestor
from app.services.ingestion.protected_fetcher import ProtectedFetcherService
from app.services.ingestion.authorization_service import AuthorizationActivity
from app.models.document import DocumentSource

logger = logging.getLogger(__name__)

# Try importing PyMuPDF (fitz), with graceful fallback to pypdf
try:
    import fitz
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

from pypdf import PdfReader

class PDFIngestor(BaseIngestor):
    """
    Page-aware PDF ingestor for official policy wordings, prospectuses, and regulatory circulars.
    Extracts text page-by-page, preserves page numbers (1-indexed) and headings,
    computes SHA-256 fingerprint, detects scanned PDFs requiring OCR, and checks for duplicates.
    """
    def __init__(self, db: Optional[Session] = None, request_interval_sec: float = 1.0):
        super().__init__(request_interval_sec)
        self.db = db
        self.fetcher = ProtectedFetcherService(db=db)

    def is_duplicate(self, sha256_hash: str) -> Optional[DocumentSource]:
        """Checks if a document with the identical SHA-256 hash has already been ingested."""
        if not self.db:
            return None
        return self.db.query(DocumentSource).filter(DocumentSource.sha256_hash == sha256_hash).first()

    def ingest_from_bytes(
        self,
        pdf_bytes: bytes,
        filename: str = "document.pdf",
        metadata: Optional[Dict[str, Any]] = None,
        source_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Parses PDF bytes page-by-page using PyMuPDF (with pypdf fallback).
        Calculates SHA-256 and detects scanned documents.
        """
        sha256 = self.compute_sha256(pdf_bytes)

        # Check for duplicate document
        existing = self.is_duplicate(sha256)
        if existing:
            logger.info("Document '%s' already indexed with hash %s (ID: %d)", filename, sha256, existing.id)
            return {
                "success": True,
                "is_duplicate": True,
                "existing_id": existing.id,
                "title": existing.title,
                "filename": filename,
                "sha256": sha256,
                "total_pages": existing.chunk_count,
                "sections": [],
                "full_text": existing.extracted_text_summary or "",
                "message": "Document is identical to previously ingested source."
            }

        sections = []
        pages_data = []
        full_text_list = []
        total_chars = 0
        total_pages = 0

        # Method 1: PyMuPDF (fitz)
        if HAS_PYMUPDF:
            try:
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                total_pages = len(doc)

                for page_idx in range(total_pages):
                    page_num = page_idx + 1
                    page = doc[page_idx]
                    page_text = page.get_text("text") or ""
                    clean_text = page_text.strip()
                    char_count = len(clean_text)
                    total_chars += char_count

                    # Extract section heading candidates from top lines of the page
                    heading = f"Page {page_num}"
                    lines = [ln.strip() for ln in clean_text.splitlines() if ln.strip()]
                    if lines and len(lines[0]) < 80 and not lines[0].isdigit():
                        heading = f"Page {page_num}: {lines[0]}"

                    if clean_text:
                        full_text_list.append(f"--- [Page {page_num}] ---\n{clean_text}")
                        sections.append({
                            "heading": heading,
                            "page_number": page_num,
                            "content": clean_text
                        })
                        pages_data.append({
                            "page_number": page_num,
                            "text": clean_text,
                            "heading": heading
                        })

                doc.close()
            except Exception as e:
                logger.warning("PyMuPDF parsing failed for %s, falling back to pypdf: %s", filename, e)
                full_text_list = []
                sections = []
                pages_data = []
                total_chars = 0

        # Method 2: Fallback to pypdf if PyMuPDF not available or failed
        if not pages_data:
            try:
                reader = PdfReader(io.BytesIO(pdf_bytes))
                total_pages = len(reader.pages)

                for page_idx, page in enumerate(reader.pages):
                    page_num = page_idx + 1
                    page_text = page.extract_text() or ""
                    clean_text = page_text.strip()
                    total_chars += len(clean_text)

                    heading = f"Page {page_num}"
                    lines = [ln.strip() for ln in clean_text.splitlines() if ln.strip()]
                    if lines and len(lines[0]) < 80 and not lines[0].isdigit():
                        heading = f"Page {page_num}: {lines[0]}"

                    if clean_text:
                        full_text_list.append(f"--- [Page {page_num}] ---\n{clean_text}")
                        sections.append({
                            "heading": heading,
                            "page_number": page_num,
                            "content": clean_text
                        })
                        pages_data.append({
                            "page_number": page_num,
                            "text": clean_text,
                            "heading": heading
                        })
            except Exception as e:
                logger.error("Failed to parse PDF %s with pypdf: %s", filename, e)
                return {
                    "success": False,
                    "error": f"PDF extraction failed: {str(e)}",
                    "filename": filename,
                    "sha256": sha256
                }

        # Scanned PDF Detection (OCR requirement)
        avg_chars_per_page = (total_chars / total_pages) if total_pages > 0 else 0
        is_scanned = (total_chars < 50 and total_pages > 0) or (avg_chars_per_page < 30 and total_pages > 1)

        doc_title = metadata.get("title") if metadata else None
        if not doc_title:
            doc_title = filename.replace(".pdf", "").replace("_", " ").title()

        return {
            "success": True,
            "is_duplicate": False,
            "title": doc_title,
            "filename": filename,
            "source_url": source_url,
            "sha256": sha256,
            "file_size": len(pdf_bytes),
            "total_pages": total_pages,
            "total_characters": total_chars,
            "is_scanned": is_scanned,
            "ocr_required": is_scanned,
            "sections": sections,
            "pages": pages_data,
            "full_text": "\n\n".join(full_text_list),
            "metadata": metadata or {}
        }

    def ingest_url(self, pdf_url: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Downloads and ingests a remote PDF via ProtectedFetcherService.
        Enforces SSRF validation, authorization checks, and size limits.
        """
        fetch_res = self.fetcher.fetch(pdf_url, activity=AuthorizationActivity.FETCH)
        if not fetch_res.get("success"):
            return {
                "success": False,
                "error": fetch_res.get("error", "Failed to download PDF"),
                "status_code": fetch_res.get("status_code", 400),
                "decision_code": fetch_res.get("decision_code", "BLOCKED"),
                "blocked": fetch_res.get("blocked", False),
                "source_url": pdf_url
            }

        filename = os.path.basename(pdf_url.split("?")[0]) or "policy_wording.pdf"
        return self.ingest_from_bytes(fetch_res["content_bytes"], filename, metadata, source_url=pdf_url)

    def ingest(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Reads local PDF file and delegates to ingest_from_bytes."""
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}

        with open(file_path, "rb") as f:
            pdf_bytes = f.read()

        filename = os.path.basename(file_path)
        return self.ingest_from_bytes(pdf_bytes, filename, metadata)
