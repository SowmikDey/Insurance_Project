import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

# Support Neon or standard PostgreSQL connection strings
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

def _sanitize_db_url(raw_url: str) -> str:
    try:
        from urllib.parse import urlparse
        parsed = urlparse(raw_url)
        host = parsed.hostname or "localhost"
        port = f":{parsed.port}" if parsed.port else ""
        db_name = parsed.path.lstrip("/") or "unknown"
        return f"{parsed.scheme}://***:***@{host}{port}/{db_name}"
    except Exception:
        return "postgresql://***:***@configured-host/database"

sanitized_url = _sanitize_db_url(db_url)

try:
    connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        echo=False,
        connect_args=connect_args
    )
    # Test connection immediately so misconfigurations fail loudly
    with engine.connect() as conn:
        logger.info("Connected successfully to PostgreSQL database: %s", sanitized_url)
except Exception as e:
    logger.critical("Database connection error for target '%s': %s", sanitized_url, e)
    raise RuntimeError(
        f"Failed to connect to configured PostgreSQL database at {sanitized_url}: {e}. "
        "Silent fallback to SQLite is disabled to prevent running against an unintended database."
    ) from e

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
