import pytest
from fastapi import HTTPException
from app.api.dependencies import admin_api_key
from app.api.ingestion import (
    get_ingestion_status,
    get_sources,
    get_ingestion_jobs,
    run_ingestion_job,
)
from app.schemas.ingestion import JobRunRequest
from app.services.ingestion.job_manager import JobType
from app.api.policies import list_categories, list_policies
from app.api.assistant import ask_assistant
from app.schemas.assistant import AssistantQueryRequest
from app.services.ingestion.source_registry_service import seed_source_registry

def test_ingestion_status(db_session):
    data = get_ingestion_status(db=db_session)
    assert hasattr(data, "total_sources")
    assert hasattr(data, "total_chunks")

def test_ingestion_sources_list(db_session):
    seed_source_registry(db_session)
    sources = get_sources(provider=None, db=db_session)
    assert isinstance(sources, list)
    urls = [s.source_url for s in sources]
    assert any("irdai.gov.in" in u for u in urls)
    assert any("icicilombard.com" in u for u in urls)

def test_admin_auth_dependency_rejection():
    with pytest.raises(HTTPException) as exc_info:
        admin_api_key(x_admin_api_key="wrong-key")
    assert exc_info.value.status_code == 401

def test_admin_auth_dependency_success():
    assert admin_api_key(x_admin_api_key="test-key") is True

def test_jobs_run_unauthorized_source_blocked(db_session):
    seed_source_registry(db_session)
    payload = JobRunRequest(url="https://www.icicilombard.com/health-insurance", job_type=JobType.FETCH_DOC)
    job = run_ingestion_job(payload=payload, db=db_session)
    assert "BLOCKED" in job.status
    assert "LINK_ONLY" in (job.authorization_decision or "") or "BLOCKED" in (job.authorization_decision or "")

def test_policies_categories_returns_four_categories(db_session):
    seed_source_registry(db_session)
    cats = list_categories(db=db_session)
    slugs = [c.slug for c in cats]
    assert "health" in slugs
    assert "term-life" in slugs
    assert "motor" in slugs
    assert "travel" in slugs

def test_policies_listing_pagination(db_session):
    res = list_policies(page=1, page_size=10, db=db_session)
    assert hasattr(res, "items")
    assert hasattr(res, "total")
    assert res.page == 1

def test_assistant_chat_grounding(db_session):
    req = AssistantQueryRequest(query="Explain what pre-existing disease waiting period means for a beginner.")
    res = ask_assistant(req=req, db=db_session)
    assert hasattr(res, "answer")
    assert hasattr(res, "citations")
    assert len(res.answer) > 10
