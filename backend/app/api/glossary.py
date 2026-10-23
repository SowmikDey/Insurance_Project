from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.schemas.glossary import (
    GlossaryTermSchema,
    TextHighlightResponse,
    HighlightedTermMatch
)
from app.services.glossary_service import GlossaryService

router = APIRouter(prefix="/glossary", tags=["glossary"])

@router.get("", response_model=List[GlossaryTermSchema])
def list_glossary_terms(
    category: Optional[str] = Query(None, description="Category filter (e.g. Health, Claims, General)"),
    db: Session = Depends(get_db)
):
    service = GlossaryService(db)
    return service.get_all_terms(category)

@router.get("/{slug}", response_model=GlossaryTermSchema)
def get_glossary_term(slug: str, db: Session = Depends(get_db)):
    service = GlossaryService(db)
    term = service.get_term_by_slug(slug)
    if not term:
        raise HTTPException(status_code=404, detail="Glossary term not found")
    return term

@router.post("/detect", response_model=TextHighlightResponse)
def detect_terms_in_text(
    payload: dict = Body(..., openapi_examples={"default": {"value": {"text": "This health insurance policy features a 10% co-payment and room rent capping."}}}),
    db: Session = Depends(get_db)
):
    text = payload.get("text", "")
    service = GlossaryService(db)
    matches = service.find_terms_in_text(text)
    return TextHighlightResponse(original_text=text, found_terms=matches)
