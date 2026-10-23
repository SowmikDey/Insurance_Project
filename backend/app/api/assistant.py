from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.assistant import AssistantQueryRequest, AssistantQueryResponse
from app.services.rag_service import RAGService

router = APIRouter(prefix="/assistant", tags=["assistant"])

@router.post("/chat", response_model=AssistantQueryResponse)
def ask_assistant(req: AssistantQueryRequest, db: Session = Depends(get_db)):
    service = RAGService(db)
    return service.generate_response(req)
