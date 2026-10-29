from pydantic import BaseModel
from typing import List, Optional

class ChatMessage(BaseModel):
    role: str # "user" or "assistant"
    content: str

class CitationItem(BaseModel):
    title: str
    section: Optional[str] = None
    snippet: str
    source_type: str # Official Brochure, Policy Wordings, IRDAI Regulation
    source_url: Optional[str] = None
    policy_name: Optional[str] = None

class AssistantQueryRequest(BaseModel):
    query: str
    history: List[ChatMessage] = []
    policy_id: Optional[int] = None # Optional context when chatting about a specific policy

class AssistantQueryResponse(BaseModel):
    answer: str
    citations: List[CitationItem] = []
    related_glossary_terms: List[str] = []
    provider_used: Optional[str] = None  # "bimagyan" (Cloudflare Workers AI) or "deterministic"
    disclaimer: str = "This educational explanation is grounded in official policy wordings and IRDAI standards. It does not constitute licensed financial or legal advice."

class DocumentCitationItem(BaseModel):
    page_number: Optional[int] = None
    snippet: str
    score: Optional[float] = None

class AssistantDocumentQueryResponse(BaseModel):
    answer: str
    document_name: str
    total_pages: int
    citations: List[DocumentCitationItem] = []
    provider_used: Optional[str] = None
    disclaimer: str = "This answer is grounded exclusively in your uploaded document. It does not constitute licensed financial or legal advice."
