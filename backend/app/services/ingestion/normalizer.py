import re
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.document import DocumentSource, DocumentChunk

logger = logging.getLogger(__name__)

class DocumentNormalizer:
    def __init__(self, db: Session):
        self.db = db

    def chunk_text(self, text: str, max_chunk_chars: int = 800, overlap_chars: int = 100) -> List[Dict[str, Any]]:
        """
        Splits structured policy text into chunks while preserving paragraph integrity.
        """
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks = []
        current_chunk = []
        current_len = 0
        current_heading = "General Terms"

        for p in paragraphs:
            if p.startswith("#") or p.startswith("Section") or p.startswith("Clause"):
                current_heading = p.replace("#", "").strip()[:80]

            p_len = len(p)
            if current_len + p_len > max_chunk_chars and current_chunk:
                chunk_str = "\n\n".join(current_chunk)
                chunks.append({
                    "heading": current_heading,
                    "content": chunk_str
                })
                current_chunk = [current_chunk[-1]] if len(current_chunk) > 1 else []
                current_len = sum(len(x) for x in current_chunk)

            current_chunk.append(p)
            current_len += p_len

        if current_chunk:
            chunks.append({
                "heading": current_heading,
                "content": "\n\n".join(current_chunk)
            })

        return chunks

    def process_and_save(
        self,
        ingested_data: Dict[str, Any],
        source_type: str = "PDF",
        policy_id: Optional[int] = None,
        policy_version_id: Optional[int] = None,
        insurer_name: Optional[str] = None
    ) -> DocumentSource:
        title = ingested_data.get("title", "Official Policy Source")
        sha256 = ingested_data.get("sha256")
        
        # Check if already indexed
        if sha256:
            existing = self.db.query(DocumentSource).filter(DocumentSource.sha256_hash == sha256).first()
            if existing:
                logger.info("Document already indexed with hash %s (ID: %d)", sha256, existing.id)
                return existing

        full_text = ingested_data.get("full_text", "")
        summary = full_text[:400] + "..." if len(full_text) > 400 else full_text

        # Resolve policy_name if policy_id is provided or present in data
        pol_name = ingested_data.get("policy_name")
        if not pol_name and policy_id:
            from app.models.policy import InsurancePolicy
            p = self.db.query(InsurancePolicy).filter(InsurancePolicy.id == policy_id).first()
            if p:
                pol_name = p.name

        doc_source = DocumentSource(
            title=title,
            source_type=source_type,
            source_url=ingested_data.get("source_url"),
            file_path=ingested_data.get("filename"),
            sha256_hash=sha256,
            file_size_bytes=ingested_data.get("file_size", 0),
            insurer_name=insurer_name,
            policy_name=pol_name,
            extracted_text_summary=summary,
            is_processed=True,
            metadata_json=ingested_data.get("metadata", {})
        )
        self.db.add(doc_source)
        self.db.flush()

        created_chunks = 0
        pages = ingested_data.get("pages", [])

        if pages:
            # Page-aware chunking preserving exact page numbers
            for idx, p in enumerate(pages):
                page_text = p.get("text", "")
                page_num = p.get("page_number", idx + 1)
                heading = p.get("heading", f"Page {page_num}")

                chunk = DocumentChunk(
                    document_source_id=doc_source.id,
                    policy_id=policy_id,
                    policy_version_id=policy_version_id,
                    chunk_index=idx,
                    page_number=page_num,
                    section_title=heading[:200],
                    content=page_text,
                    metadata_json={
                        "source_title": title,
                        "page_number": page_num,
                        "sha256": sha256
                    }
                )
                self.db.add(chunk)
                created_chunks += 1
        else:
            # Paragraph chunking for HTML or plain text
            raw_chunks = self.chunk_text(full_text)
            for idx, rc in enumerate(raw_chunks):
                chunk = DocumentChunk(
                    document_source_id=doc_source.id,
                    policy_id=policy_id,
                    policy_version_id=policy_version_id,
                    chunk_index=idx,
                    section_title=rc["heading"][:200],
                    content=rc["content"],
                    metadata_json={"source_title": title, "index": idx, "sha256": sha256}
                )
                self.db.add(chunk)
                created_chunks += 1

        doc_source.chunk_count = created_chunks
        self.db.commit()
        self.db.refresh(doc_source)
        logger.info("Successfully normalized and saved document %s with %d chunks", title, created_chunks)
        return doc_source
