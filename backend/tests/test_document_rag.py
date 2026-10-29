import io
from fastapi.testclient import TestClient
from app.main import app
from app.services.document_rag_service import DocumentRAGService

client = TestClient(app)

SAMPLE_POLICY_DOC = """
STAR HEALTH ASSURE INSURANCE POLICY WORDINGS
Section 1: Inpatient Hospitalization
Hospital room rent is covered up to Single Private A/C Room. No proportionate deductions shall apply.
Section 2: Waiting Periods
1. Initial Waiting Period: 30 days from inception. Accidental injuries covered immediately from Day 1.
2. Specific Illness Waiting Period: 24 months for Cataract, Hernia, and Joint Replacement.
3. Pre-Existing Disease (PED) Waiting Period: 36 months from commencement date.
Section 3: Modern Treatments
Robotic surgery and stem cell therapy are covered up to 100% of the Sum Insured without sub-limits.
"""


def test_document_rag_service_extraction_and_chunking():
    service = DocumentRAGService()
    pages = service.extract_pages_from_file("sample.txt", SAMPLE_POLICY_DOC.encode("utf-8"))
    assert len(pages) >= 1
    assert "STAR HEALTH ASSURE" in pages[0]["text"]

    chunks = service.chunk_document(pages)
    assert len(chunks) >= 1
    assert any("Waiting Periods" in c["text"] for c in chunks)


def test_document_rag_service_retrieval():
    service = DocumentRAGService()
    pages = service.extract_pages_from_file("sample.txt", SAMPLE_POLICY_DOC.encode("utf-8"))
    chunks = service.chunk_document(pages)

    passages = service.retrieve_relevant_passages("cataract surgery waiting period", chunks)
    assert len(passages) >= 1
    assert "Cataract" in passages[0]["text"]
    assert passages[0]["page_number"] == 1


def test_document_rag_service_process_and_answer():
    service = DocumentRAGService()
    resp = service.process_and_answer(
        filename="star_policy.txt",
        content_bytes=SAMPLE_POLICY_DOC.encode("utf-8"),
        query="What is the waiting period for cataract surgery?"
    )
    assert resp.document_name == "star_policy.txt"
    assert resp.total_pages >= 1
    assert len(resp.citations) >= 1
    assert resp.citations[0].page_number == 1
    assert len(resp.answer) > 20


def test_chat_document_api_endpoint():
    file_bytes = io.BytesIO(SAMPLE_POLICY_DOC.encode("utf-8"))
    response = client.post(
        "/api/v1/assistant/chat-document",
        files={"file": ("test_policy.txt", file_bytes, "text/plain")},
        data={"query": "Is robotic surgery covered?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["document_name"] == "test_policy.txt"
    assert "answer" in data
    assert len(data["answer"]) > 10
    assert len(data["citations"]) >= 1
    assert data["citations"][0]["page_number"] == 1


def test_chat_document_api_validation():
    # Empty query validation
    file_bytes = io.BytesIO(b"Sample content")
    response = client.post(
        "/api/v1/assistant/chat-document",
        files={"file": ("test.txt", file_bytes, "text/plain")},
        data={"query": "   "}
    )
    assert response.status_code == 400

    # Unsupported file extension
    file_bytes2 = io.BytesIO(b"Binary content")
    response2 = client.post(
        "/api/v1/assistant/chat-document",
        files={"file": ("test.exe", file_bytes2, "application/octet-stream")},
        data={"query": "What is this?"}
    )
    assert response2.status_code == 400
