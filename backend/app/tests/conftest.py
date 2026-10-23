import os
import sys

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Override env before any app import
os.environ["DATABASE_URL"] = "sqlite:///./test_bimagyan.db"
os.environ["ADMIN_API_KEY"] = "test-key"

import pytest
from app.core.database import Base, engine, SessionLocal, get_db
from app.main import app
from fastapi.testclient import TestClient

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    # Seed static curriculum and sources
    from app.data.educational_content import seed_educational_content
    from app.services.ingestion.source_registry_service import seed_source_registry
    db = SessionLocal()
    try:
        seed_educational_content(db)
        seed_source_registry(db)
    finally:
        db.close()
        
    yield
    
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("./test_bimagyan.db"):
        try:
            os.remove("./test_bimagyan.db")
        except OSError:
            pass

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

@pytest.fixture(scope="session")
def client():
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

@pytest.fixture(scope="session")
def admin_headers():
    return {"X-Admin-API-Key": "test-key"}
