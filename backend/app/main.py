import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
import app.models # registers models
from app.data.educational_content import seed_educational_content
from app.api.policies import router as policies_router
from app.api.glossary import router as glossary_router
from app.api.education import router as education_router
from app.api.assistant import router as assistant_router
from app.api.ingestion import router as ingestion_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("bimagyan")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure active tables exist and seed static educational curriculum if empty
    logger.info("Initializing active database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        from app.models.glossary import GlossaryTerm
        glossary_count = db.query(GlossaryTerm).count()
        if glossary_count == 0:
            logger.info("Database empty, seeding educational curriculum and glossary...")
            seed_educational_content(db)
        else:
            logger.info("Database contains %d glossary terms. Educational content ready.", glossary_count)

        # Idempotently register official reference sources (ICICI Lombard link-only references)
        from app.services.ingestion.source_registry_service import seed_source_registry
        seed_source_registry(db)
    except Exception as e:
        logger.error("Error during startup seed: %s", e)
    finally:
        db.close()
        
    yield
    logger.info("Shutting down application...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Comprehensive AI-powered Insurance Education, Exploration, and Ingestion Platform for India.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all local origins during development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Retained Core API Routers
api_v1_prefix = settings.API_V1_STR
app.include_router(policies_router, prefix=api_v1_prefix)
app.include_router(glossary_router, prefix=api_v1_prefix)
app.include_router(education_router, prefix=api_v1_prefix)
app.include_router(assistant_router, prefix=api_v1_prefix)
app.include_router(ingestion_router, prefix=api_v1_prefix)

@app.get("/")
def root():
    return {
        "platform": settings.PROJECT_NAME,
        "status": "online",
        "docs_url": "/docs",
        "version": "1.0.0",
        "api_prefix": settings.API_V1_STR
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
