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
    disclaimer: str = "This educational explanation is grounded in official policy wordings and IRDAI standards. It does not constitute licensed financial or legal advice."
