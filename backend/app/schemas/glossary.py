from pydantic import BaseModel, ConfigDict
from typing import Optional, List

class GlossaryTermSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    term: str
    aliases: List[str] = []
    category: str
    what_does_it_mean: str
    why_does_it_matter: str
    financial_impact_example: str
    trade_off_analysis: str
    watch_out_tips: str
    related_module_slug: Optional[str] = None
    official_reference_source: str

class HighlightedTermMatch(BaseModel):
    term: str
    slug: str
    matched_text: str
    summary_preview: str

class TextHighlightResponse(BaseModel):
    original_text: str
    found_terms: List[HighlightedTermMatch]
