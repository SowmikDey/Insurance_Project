"""
BimaGyan Insurance Web Scraper & Ingestion Pipeline Orchestrator.

CLI tool to scrape, normalize, and store official insurance data from:
1. IRDAI Health Insurance Products Catalogue
2. IRDAI Consumer Guidance, Regulations, & Insurer Directory
3. New India Assurance (Official CIS, Policy Clauses, Prospectus PDFs)
4. Ditto Feature & Benchmark Discovery (Care Supreme, Optima Secure, ReAssure 2.0)
5. Database Synchronizer (PostgreSQL / Neon)

Usage:
    python backend/run_scraper.py --all
    python backend/run_scraper.py --irdai-catalogue --pages 3
    python backend/run_scraper.py --irdai-guidance
    python backend/run_scraper.py --new-india
    python backend/run_scraper.py --ditto
    python backend/run_scraper.py --sync-db
    python backend/run_scraper.py --stats
"""
import os
import sys
import argparse
import logging

# Ensure backend root is on sys.path
backend_root = os.path.dirname(os.path.abspath(__file__))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.services.scraper.irdai_catalogue_scraper import IRDAICatalogueScraper
from app.services.scraper.irdai_guidance_scraper import IRDAIGuidanceScraper
from app.services.scraper.new_india_scraper import NewIndiaScraper
from app.services.scraper.star_health_scraper import StarHealthScraper
from app.services.scraper.tata_aig_scraper import TataAIGScraper
from app.services.scraper.acko_scraper import AckoScraper
from app.services.scraper.irdai_batch_pdf_ingestor import IRDAIBatchPDFIngestor
from app.services.scraper.ditto_feature_scraper import DittoFeatureScraper
from app.services.scraper.db_sync import ScrapedDataDBSynchronizer

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("bimagyan.orchestrator")


def print_stats():
    from app.core.database import SessionLocal
    from app.models import (
        InsurancePolicy,
        Insurer,
        DocumentSource,
        DocumentChunk,
        PolicyFact,
        PolicyBenefit,
        PolicyExclusion,
        PolicyWaitingPeriod,
    )
    db = SessionLocal()
    print("\n=======================================================")
    print("           BIMAGYAN DATABASE & STORAGE STATS          ")
    print("=======================================================")
    print(f" Registered Insurers:       {db.query(Insurer).count()}")
    print(f" Insurance Policies:        {db.query(InsurancePolicy).count()}")
    print(f" Indexed Document Sources:  {db.query(DocumentSource).count()}")
    print(f" RAG Document Chunks:       {db.query(DocumentChunk).count()}")
    print(f" Evidence Policy Facts:     {db.query(PolicyFact).count()}")
    print(f" Policy Benefits Mapped:    {db.query(PolicyBenefit).count()}")
    print(f" Policy Exclusions Mapped:  {db.query(PolicyExclusion).count()}")
    print(f" Waiting Periods Mapped:    {db.query(PolicyWaitingPeriod).count()}")
    print("-------------------------------------------------------")

    policies = db.query(InsurancePolicy).all()
    for p in policies:
        name_str = (p.name or "").encode("ascii", "replace").decode()
        ins_name = (p.insurer.short_name or p.insurer.name or "").encode("ascii", "replace").decode()
        room_rent = (p.room_rent_capping or "N/A").replace("₹", "Rs.").encode("ascii", "replace").decode()
        print(f" * [{p.slug}] {name_str} ({ins_name})")
        print(f"    - Room Rent: {room_rent}")
        print(f"    - Co-pay: {p.copay_percentage if p.copay_percentage is not None else 'N/A'}% | Pre/Post: {p.pre_hospitalization_days}d / {p.post_hospitalization_days}d")
        print(f"    - Verified Facts: {len(p.facts)} | Benefits: {len(p.benefits)} | Exclusions: {len(p.exclusions)}")
    print("=======================================================\n")
    db.close()


def main():
    parser = argparse.ArgumentParser(description="BimaGyan Web Scraper & Master Checklist Pipeline")
    parser.add_argument("--all", action="store_true", help="Run full pipeline across all sources and sync database")
    parser.add_argument("--irdai-catalogue", action="store_true", help="Scrape IRDAI Health Insurance Products catalogue")
    parser.add_argument("--pages", type=int, default=3, help="Number of pages to scrape from IRDAI catalogue (default: 3)")
    parser.add_argument("--irdai-guidance", action="store_true", help="Scrape IRDAI guidance, FAQs, and registered insurer listings")
    parser.add_argument("--new-india", action="store_true", help="Scrape New India Assurance and download official PDFs")
    parser.add_argument("--star-health", action="store_true", help="Scrape Star Health and download official PDFs (Star Comprehensive)")
    parser.add_argument("--tata-aig", action="store_true", help="Scrape Tata AIG and download official PDFs (Tata AIG MediCare)")
    parser.add_argument("--acko", action="store_true", help="Scrape ACKO and download official PDFs (ACKO Platinum Health)")
    parser.add_argument("--batch-irdai-pdfs", action="store_true", help="Batch download and ingest official PDFs from IRDAI catalogue")
    parser.add_argument("--batch-limit", type=int, default=50, help="Maximum number of IRDAI PDFs to batch ingest (default: 50)")
    parser.add_argument("--ditto", action="store_true", help="Scrape Ditto feature benchmarks (Care Supreme, Optima Secure, ReAssure 2.0)")
    parser.add_argument("--sync-db", action="store_true", help="Synchronize scraped files and facts into PostgreSQL database")
    parser.add_argument("--stats", action="store_true", help="Print current database and storage statistics")

    args = parser.parse_args()

    # If no flags passed, show help
    if not any([args.all, args.irdai_catalogue, args.irdai_guidance, args.new_india, args.star_health, args.tata_aig, args.acko, args.batch_irdai_pdfs, args.ditto, args.sync_db, args.stats]):
        parser.print_help()
        sys.exit(0)

    if args.stats:
        print_stats()
        return

    run_all = args.all

    if run_all or args.irdai_catalogue:
        logger.info(">>> STEP 1: Scraping IRDAI Health Products Catalogue (%d pages)...", args.pages)
        catalogue_scraper = IRDAICatalogueScraper()
        catalogue_scraper.scrape(max_pages=args.pages)

    if run_all or args.irdai_guidance:
        logger.info(">>> STEP 2: Scraping IRDAI Consumer Guidance & Regulations...")
        guidance_scraper = IRDAIGuidanceScraper()
        guidance_scraper.scrape_all()

    if run_all or args.new_india:
        logger.info(">>> STEP 3: Scraping New India Assurance Policy & Downloading PDFs...")
        new_india_scraper = NewIndiaScraper()
        new_india_scraper.scrape_and_extract()

    if run_all or args.star_health:
        logger.info(">>> STEP 4: Scraping Star Health & Downloading Official PDFs (Star Comprehensive)...")
        star_scraper = StarHealthScraper()
        star_scraper.scrape_and_extract()

    if run_all or args.tata_aig:
        logger.info(">>> STEP 5: Scraping Tata AIG & Downloading Official PDFs (Tata AIG MediCare)...")
        tata_scraper = TataAIGScraper()
        tata_scraper.scrape_and_extract()

    if run_all or args.acko:
        logger.info(">>> STEP 6: Scraping ACKO & Downloading Official PDFs (ACKO Platinum Health)...")
        acko_scraper = AckoScraper()
        acko_scraper.scrape_and_extract()

    if run_all or args.batch_irdai_pdfs:
        logger.info(">>> STEP 7: Batch Ingesting Top %d IRDAI Approved Health Product PDFs...", args.batch_limit)
        batch_ingestor = IRDAIBatchPDFIngestor(batch_limit=args.batch_limit)
        batch_ingestor.ingest_batch()

    if run_all or args.ditto:
        logger.info(">>> STEP 8: Scraping Ditto Feature Benchmarks...")
        ditto_scraper = DittoFeatureScraper()
        ditto_scraper.scrape_all()

    if run_all or args.sync_db:
        logger.info(">>> STEP 9: Synchronizing Scraped Data into PostgreSQL...")
        syncer = ScrapedDataDBSynchronizer()
        syncer.sync_insurers_from_catalogue()
        syncer.sync_master_policies()
        syncer.close()
        logger.info(">>> Database Synchronization Complete!")

    print_stats()


if __name__ == "__main__":
    main()
