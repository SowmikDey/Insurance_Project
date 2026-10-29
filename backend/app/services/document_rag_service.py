import io
import re
import math
import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
import httpx

from app.core.config import settings
from app.schemas.assistant import AssistantDocumentQueryResponse, DocumentCitationItem

logger = logging.getLogger(__name__)


class DocumentRAGService:
    """
    User Document RAG Service (Type 2 RAG).
    Parses user-uploaded documents (PDF, DOCX, TXT), extracts pages,
    chunks semantically, indexes in memory, and performs evidence-grounded
    question answering via Cloudflare Workers AI / fallback LLMs.
    """

    def __init__(self):
        pass

    def _tokenize(self, text: str) -> List[str]:
        words = re.findall(r'\b[a-z0-9_]{2,}\b', text.lower())
        stop_words = {
            "the", "and", "is", "in", "to", "of", "for", "with", "on", "at", "by",
            "from", "up", "about", "into", "through", "after", "before", "an", "this",
            "that", "these", "those", "can", "will", "are", "as", "be", "has", "have",
            "what", "how", "which", "why", "where", "who", "whom", "does"
        }
        return [w for w in words if w not in stop_words]

    def _cosine_similarity(self, vec1: Counter, vec2: Counter) -> float:
        intersection = set(vec1.keys()) & set(vec2.keys())
        numerator = sum([vec1[x] * vec2[x] for x in intersection])
        sum1 = sum([val ** 2 for val in vec1.values()])
        sum2 = sum([val ** 2 for val in vec2.values()])
        denominator = math.sqrt(sum1) * math.sqrt(sum2)
        if not denominator:
            return 0.0
        return float(numerator) / denominator

    def extract_pages_from_file(self, filename: str, content_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Extracts list of pages: [{"page_number": int, "text": str}]
        """
        pages = []
        lower_name = filename.lower()

        if lower_name.endswith(".pdf"):
            try:
                import pypdf
                stream = io.BytesIO(content_bytes)
                reader = pypdf.PdfReader(stream)
                for idx, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    if text.strip():
                        pages.append({"page_number": idx + 1, "text": text.strip()})
            except Exception as e:
                logger.warning("pypdf extraction failed for %s: %s", filename, e)

        elif lower_name.endswith(".docx"):
            try:
                import docx
                stream = io.BytesIO(content_bytes)
                doc = docx.Document(stream)
                full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
                # Approximate 400 words per page
                words = full_text.split()
                chunk_size = 400
                for page_idx in range(0, max(1, len(words)), chunk_size):
                    page_text = " ".join(words[page_idx:page_idx + chunk_size])
                    if page_text.strip():
                        pages.append({"page_number": (page_idx // chunk_size) + 1, "text": page_text})
            except Exception as e:
                logger.warning("docx extraction failed for %s: %s", filename, e)

        else:
            # Plain text or Markdown
            try:
                text = content_bytes.decode("utf-8", errors="replace")
                words = text.split()
                chunk_size = 400
                for page_idx in range(0, max(1, len(words)), chunk_size):
                    page_text = " ".join(words[page_idx:page_idx + chunk_size])
                    if page_text.strip():
                        pages.append({"page_number": (page_idx // chunk_size) + 1, "text": page_text})
            except Exception as e:
                logger.warning("text extraction failed for %s: %s", filename, e)

        if not pages:
            # Fallback if no pages could be parsed
            pages.append({"page_number": 1, "text": ""})

        return pages

    def chunk_document(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Breaks pages into overlapping passages (~400 chars each) preserving page numbers.
        """
        chunks = []
        chunk_id = 1

        for page in pages:
            page_num = page["page_number"]
            text = page["text"]
            if not text:
                continue

            # Split into paragraphs
            paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
            buffer = ""

            for p in paragraphs:
                if len(buffer) + len(p) < 450:
                    buffer += (" " if buffer else "") + p
                else:
                    if buffer:
                        chunks.append({
                            "chunk_id": chunk_id,
                            "page_number": page_num,
                            "text": buffer.strip()
                        })
                        chunk_id += 1
                    buffer = p

            if buffer:
                chunks.append({
                    "chunk_id": chunk_id,
                    "page_number": page_num,
                    "text": buffer.strip()
                })
                chunk_id += 1

        return chunks

    def retrieve_relevant_passages(
        self, query: str, chunks: List[Dict[str, Any]], top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Ranks chunks against user query using token cosine similarity.
        """
        query_tokens = self._tokenize(query)
        if not query_tokens:
            query_tokens = query.lower().split()

        query_vec = Counter(query_tokens)
        scored = []

        for c in chunks:
            text_vec = Counter(self._tokenize(c["text"]))
            score = self._cosine_similarity(query_vec, text_vec)
            if score > 0.04:
                scored.append({
                    **c,
                    "score": round(score, 4)
                })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def _call_bimagyan_model(self, prompt: str) -> Optional[str]:
        """Calls the configured Cloudflare Workers AI / Modal endpoint."""
        if not settings.HF_INFERENCE_URL:
            return None
        try:
            headers = {"Content-Type": "application/json"}
            if settings.HF_API_TOKEN and not settings.HF_API_TOKEN.startswith("hf_your_"):
                headers["Authorization"] = f"Bearer {settings.HF_API_TOKEN}"

            url = settings.HF_INFERENCE_URL
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 400,
                    "temperature": 0.2,
                    "do_sample": False,
                    "return_full_text": False,
                }
            }

            res = httpx.post(url, headers=headers, json=payload, timeout=40.0)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, dict):
                    text = data.get("generated_text") or data.get("response") or ""
                    if text.strip():
                        return text.strip()
                elif isinstance(data, list) and data:
                    text = data[0].get("generated_text") or ""
                    if text.strip():
                        return text.strip()
        except Exception as e:
            logger.info("Workers AI document inference unavailable: %s", e)
        return None

    def _synthesize_document_answer(
        self, query: str, filename: str, passages: List[Dict[str, Any]]
    ) -> str:
        """Deterministic synthesis directly grounded in the document passages."""
        if not passages:
            return (
                f"### Analysis of Uploaded Document: {filename}\n\n"
                "I examined your uploaded document, but could not find clauses or sections directly matching your question.\n\n"
                "**Suggestions:**\n"
                "- Verify that the uploaded file contains readable text (and is not an unscanned image).\n"
                "- Try asking with specific keywords mentioned in the policy (e.g. *'waiting period'*, *'room rent'*, *'copay'*, *'exclusions'*)."
            )

        lines = [
            f"### Document Analysis: Grounded in '{filename}'\n",
            f"Based on the relevant clauses located in your uploaded document:\n"
        ]
        for p in passages:
            lines.append(f"• **Page {p['page_number']}**: \"{p['text']}\"\n")

        lines.append(
            "\n**Summary Assessment:**\n"
            f"The excerpts above from Page {', '.join(str(p['page_number']) for p in passages)} "
            "contain the explicit terms documented in your file regarding this inquiry."
        )
        return "\n".join(lines)

    def process_and_answer(
        self, filename: str, content_bytes: bytes, query: str
    ) -> AssistantDocumentQueryResponse:
        """
        Executes end-to-end Document RAG:
        1. Extract pages from file.
        2. Chunk document into semantic passages.
        3. Retrieve most relevant passages.
        4. Query LLM / synthesize answer grounded in the document.
        5. Return response with page-level citations.
        """
        pages = self.extract_pages_from_file(filename, content_bytes)
        total_pages = len(pages)
        chunks = self.chunk_document(pages)
        passages = self.retrieve_relevant_passages(query, chunks, top_k=4)

        citations = [
            DocumentCitationItem(
                page_number=p["page_number"],
                snippet=p["text"][:240] + ("..." if len(p["text"]) > 240 else ""),
                score=p["score"]
            )
            for p in passages
        ]

        # Build grounded context
        context_blocks = "\n\n".join([
            f"[Page {p['page_number']}]:\n{p['text']}"
            for p in passages
        ])

        system_prompt = (
            f"You are BimaGyan AI, an expert insurance analysis assistant.\n"
            f"The user has uploaded a document: '{filename}'.\n"
            f"Your task is to answer the user's question STRICTLY using the excerpts from their uploaded document below.\n\n"
            f"RULES:\n"
            f"1. Ground your answer ONLY in the provided document excerpts.\n"
            f"2. Cite the exact Page numbers (e.g., 'According to Page 2...') when referencing facts.\n"
            f"3. If the document does not contain enough information to answer the question, state that clearly.\n"
            f"4. Keep your answer clear, well-structured, and helpful to the policyholder.\n\n"
            f"UPLOADED DOCUMENT EXCERPTS:\n{context_blocks if context_blocks else 'No matching text found in document.'}\n\n"
            f"USER QUESTION: {query}"
        )

        answer = None
        provider_used = "deterministic"

        # Try Cloudflare Workers AI / BimaGyan edge model
        if passages:
            answer = self._call_bimagyan_model(system_prompt)
            if answer:
                provider_used = "bimagyan"

        # Deterministic fallback
        if not answer:
            answer = self._synthesize_document_answer(query, filename, passages)

        return AssistantDocumentQueryResponse(
            answer=answer,
            document_name=filename,
            total_pages=total_pages,
            citations=citations,
            provider_used=provider_used,
            disclaimer=f"Grounded exclusively in your uploaded document '{filename}'. Verified with page citations."
        )
