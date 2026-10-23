import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.models.ingestion import IngestionJob

def fix_jobs():
    db = SessionLocal()
    try:
        j1 = db.query(IngestionJob).filter(IngestionJob.id == "8a35ff89-a804-4179-ac2d-64ece7d28b63").first()
        if j1:
            j1.provider_slug = "niva-bupa-health-insurance-company-limited"
            j1.requested_url = "https://irdai.gov.in/health-insurance-products?uin=NIBHLIP24044V012324"

        j2 = db.query(IngestionJob).filter(IngestionJob.id == "1308ef63-161d-4c19-a944-7b0c9cc5f613").first()
        if j2:
            j2.provider_slug = "hdfc-ergo-general-insurance-company-ltd"
            j2.requested_url = "https://irdai.gov.in/health-insurance-products?uin=HDFHLIP21171V022021"

        j3 = db.query(IngestionJob).filter(IngestionJob.id == "9996b860-7a5f-4b97-a360-66d0620dab96").first()
        if j3:
            j3.provider_slug = "star-health-and-allied-insurance-company-limited"
            j3.created_record_count = 2
            j3.requested_url = "https://irdai.gov.in/health-insurance-products?uin=SHAHLIP21213V022021"

        db.commit()
        print("Updated jobs successfully!")
    except Exception as e:
        db.rollback()
        print("Error:", e)
    finally:
        db.close()

if __name__ == "__main__":
    fix_jobs()
