import pytest
import io
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_and_health():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "online"

    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

def test_list_categories():
    res = client.get("/api/v1/policies/categories")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 4
    slugs = [c["slug"] for c in data]
    assert "health" in slugs
    assert "term-life" in slugs
    assert "motor" in slugs
    assert "travel" in slugs

def test_list_policies_empty_or_paginated():
    res = client.get("/api/v1/policies?category=health")
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "items" in data
    assert isinstance(data["items"], list)
    assert data["page"] == 1

def test_glossary_endpoints():
    res = client.get("/api/v1/glossary")
    assert res.status_code == 200
    terms = res.json()
    assert len(terms) >= 12
    
    # Single term
    res_single = client.get("/api/v1/glossary/deductible")
    assert res_single.status_code == 200
    data = res_single.json()
    assert data["term"] == "Deductible"
    assert "financial_impact_example" in data

    # Term detection in arbitrary text
    res_detect = client.post("/api/v1/glossary/detect", json={
        "text": "This policy offers zero deductible and no co-payment, but includes a 36-month waiting period."
    })
    assert res_detect.status_code == 200
    detected = res_detect.json()
    detected_slugs = [d["slug"] for d in detected["found_terms"]]
    assert "deductible" in detected_slugs
    assert "copayment" in detected_slugs
    assert "waiting-period" in detected_slugs

def test_education_modules_and_quiz():
    res = client.get("/api/v1/education/modules")
    assert res.status_code == 200
    modules = res.json()
    assert len(modules) == 10
    assert modules[0]["slug"] == "what-is-insurance"

    # Detail
    res_mod = client.get("/api/v1/education/modules/what-is-insurance")
    assert res_mod.status_code == 200
    mod_data = res_mod.json()
    assert len(mod_data["quizzes"]) >= 1

    # Submit quiz
    first_q = mod_data["quizzes"][0]
    sub_res = client.post("/api/v1/education/quiz/submit", json={
        "user_session_id": "test_user_session",
        "answers": {first_q["id"]: first_q["correct_option_index"]}
    })
    assert sub_res.status_code == 200
    quiz_res = sub_res.json()
    assert quiz_res["score"] == 1
    assert quiz_res["passed"] == True

def test_assistant_chat():
    res = client.post("/api/v1/assistant/chat", json={
        "query": "Explain what a deductible is and how it works."
    })
    assert res.status_code == 200
    answer_data = res.json()
    assert "answer" in answer_data
    assert "disclaimer" in answer_data
    assert isinstance(answer_data["related_glossary_terms"], list)

def test_ingestion_endpoints():
    # Ingestion status
    res = client.get("/api/v1/ingestion/status")
    assert res.status_code == 200
    status_data = res.json()
    assert "total_sources" in status_data
    assert "total_chunks" in status_data

    # Upload authentic plain text policy document
    file_content = b"Sample Official Health Policy Wordings\nSection 1: Hospitalization expenses covered up to Sum Insured."
    upload_res = client.post(
        "/api/v1/ingestion/upload",
        data={"title": "Test Policy Wordings", "insurer_name": "Test Insurer"},
        files={"file": ("test_policy.txt", io.BytesIO(file_content), "text/plain")}
    )
    assert upload_res.status_code == 200
    uploaded_doc = upload_res.json()
    assert uploaded_doc["title"] == "Test Policy Wordings"
    assert uploaded_doc["chunk_count"] >= 1

def test_obsolete_endpoints_removed():
    # Verify comparison endpoint does not exist
    res_comp = client.post("/api/v1/comparison", json={"policy_ids": [1, 2]})
    assert res_comp.status_code == 404

    # Verify recommendation endpoint does not exist
    res_rec = client.post("/api/v1/recommendation", json={})
    assert res_rec.status_code == 404

    # Verify admin seed endpoint does not exist
    res_seed = client.post("/api/v1/admin/seed")
    assert res_seed.status_code == 404
