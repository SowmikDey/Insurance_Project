import httpx
import threading
from typing import Optional
from fastapi import APIRouter, Depends, BackgroundTasks, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.schemas.assistant import AssistantQueryRequest, AssistantQueryResponse, AssistantDocumentQueryResponse
from app.services.rag_service import RAGService
from app.services.document_rag_service import DocumentRAGService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/chat", response_model=AssistantQueryResponse)
def ask_assistant(req: AssistantQueryRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    service = RAGService(db)
    response = service.generate_response(req)
    # After answering, ensure the edge inference container remains warm
    if settings.HF_INFERENCE_URL:
        background_tasks.add_task(_ping_inference_warmup_sync)
    return response


@router.post("/chat-document", response_model=AssistantDocumentQueryResponse)
async def ask_assistant_with_document(
    file: UploadFile = File(...),
    query: str = Form(...),
    history: Optional[str] = Form("[]"),
):
    """
    Type 2 RAG Endpoint: User Document Grounded QA.
    Accepts an uploaded PDF, DOCX, or TXT document along with a question.
    Extracts pages, chunks in memory, retrieves the most relevant passages,
    and returns a response with page citations from the user's document.
    """
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # Validate file extension
    filename = file.filename or "uploaded_document.txt"
    allowed = (".pdf", ".docx", ".txt", ".md", ".csv")
    if not any(filename.lower().endswith(ext) for ext in allowed):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Please upload a PDF, DOCX, or TXT file."
        )

    content_bytes = await file.read()
    if len(content_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Max 20MB
    if len(content_bytes) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 20MB limit.")

    doc_service = DocumentRAGService()
    response = doc_service.process_and_answer(
        filename=filename,
        content_bytes=content_bytes,
        query=query.strip()
    )
    return response


@router.post("/warmup")
def warmup_model():
    """
    Sends a warmup request to the Cloudflare Workers AI edge endpoint in a background thread.
    The endpoint returns immediately; the warmup continues in the background.
    Called automatically when the user opens the chat page.
    """
    if not settings.HF_INFERENCE_URL:
        return {"status": "no_endpoint_configured"}

    # Fire the actual warmup in a daemon thread so the HTTP response returns instantly
    t = threading.Thread(target=_ping_inference_warmup_sync, daemon=True)
    t.start()
    return {"status": "warmup_started"}


def _ping_inference_warmup_sync():
    """
    Sends a lightweight warmup request to keep the Workers AI model primed.
    This runs in a background thread / BackgroundTask, not in the request path.
    """
    if not settings.HF_INFERENCE_URL:
        return
    try:
        headers = {"Content-Type": "application/json"}
        if settings.HF_API_TOKEN and not settings.HF_API_TOKEN.startswith("hf_your_"):
            headers["Authorization"] = f"Bearer {settings.HF_API_TOKEN}"

        url = settings.HF_INFERENCE_URL
        payload = {
            "inputs": "What is health insurance?",
            "parameters": {"max_new_tokens": 10, "do_sample": False}
        }

        httpx.post(url, headers=headers, json=payload, timeout=20.0)
        logger.info("Inference endpoint warmup completed successfully.")
    except Exception as e:
        logger.info("Warmup ping completed: %s", e)
