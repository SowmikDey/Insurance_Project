import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.models.document import DocumentSource

FAKE_SHA = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

def fix_sha_hashes():
    db = SessionLocal()
    try:
        affected = db.query(DocumentSource).filter(DocumentSource.sha256_hash == FAKE_SHA).all()
        print(f"Found {len(affected)} records with fake empty-file SHA placeholder")
        for src in affected:
            src.sha256_hash = None
        db.commit()
        print(f"Cleared sha256_hash to NULL for {len(affected)} DocumentSource records.")
        print("These will now correctly display as 'N/A' in the Admin page.")
    except Exception as e:
        db.rollback()
        print("Error:", e)
        raise
    finally:
        db.close()

if __name__ == "__main__":
    fix_sha_hashes()
