import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.ingestion import SourceRegistry
from app.models.insurer import Insurer, InsuranceCategory

logger = logging.getLogger(__name__)

# ICICI Lombard 8 reference URLs as specified by compliance and source registration requirements
ICICI_LOMBARD_REFERENCE_SOURCES = [
    {
        "source_name": "ICICI Lombard Health Insurance Catalogue",
        "source_url": "https://www.icicilombard.com/health-insurance",
        "url_type": "CATALOGUE",
        "description": "Public catalogue of health insurance products offered by ICICI Lombard."
    },
    {
        "source_name": "ICICI Lombard Policy Wordings Download Centre",
        "source_url": "https://www.icicilombard.com/downloads?download=true",
        "url_type": "DOWNLOAD_CENTRE",
        "description": "Public repository of customer information sheets and policy wordings."
    },
    {
        "source_name": "ICICI Lombard Elevate Health Policy",
        "source_url": "https://www.icicilombard.com/health-insurance/elevate-health-policy",
        "url_type": "PRODUCT_PAGE",
        "description": "Product disclosure page for ICICI Lombard Elevate Health Insurance plan."
    },
    {
        "source_name": "ICICI Lombard MaxProtect 1 Crore Health Insurance",
        "source_url": "https://www.icicilombard.com/health-insurance/max-protect-1-crore-health-insurance",
        "url_type": "PRODUCT_PAGE",
        "description": "Product disclosure page for ICICI Lombard MaxProtect 1 Crore high sum-insured plan."
    },
    {
        "source_name": "ICICI Lombard Health AdvantEdge Policy",
        "source_url": "https://www.icicilombard.com/health-insurance/health-advantedge",
        "url_type": "PRODUCT_PAGE",
        "description": "Product disclosure page for ICICI Lombard Health AdvantEdge comprehensive plan."
    },
    {
        "source_name": "ICICI Lombard Health Booster Super Top-up",
        "source_url": "https://www.icicilombard.com/health-insurance/health-booster",
        "url_type": "PRODUCT_PAGE",
        "description": "Product disclosure page for ICICI Lombard Health Booster super top-up plan."
    },
    {
        "source_name": "ICICI Lombard Website Terms and Conditions",
        "source_url": "https://www.icicilombard.com/legal/terms",
        "url_type": "LEGAL_TERMS",
        "description": "Official website legal terms governing systematic access, reproduction, and copyright."
    },
    {
        "source_name": "ICICI Lombard Grievance Redressal Policy",
        "source_url": "https://www.icicilombard.com/grievance-redressal",
        "url_type": "GRIEVANCE",
        "description": "Official customer grievance redressal policy, escalation matrix, and Ombudsman details."
    }
]

# IRDAI official sources — authorized for crawling
IRDAI_REFERENCE_SOURCES = [
    {
        "source_name": "IRDAI Health Insurance Products Catalogue",
        "source_url": "https://irdai.gov.in/health-insurance-products",
        "url_type": "CATALOGUE",
        "description": "Official IRDAI catalogue of approved health insurance products in India.",
        "permission_status": "authorized",
        "ingestion_mode": "crawl_allowed",
    },
    {
        "source_name": "IRDAI Non-Life Insurance Products Catalogue",
        "source_url": "https://irdai.gov.in/non-life-insurance-products",
        "url_type": "CATALOGUE",
        "description": "Official IRDAI catalogue of approved non-life (general) insurance products in India.",
        "permission_status": "authorized",
        "ingestion_mode": "crawl_allowed",
    },
    {
        "source_name": "IRDAI Official Website Root",
        "source_url": "https://irdai.gov.in/",
        "url_type": "ROOT",
        "description": "Root of the Insurance Regulatory and Development Authority of India public website.",
        "permission_status": "authorized",
        "ingestion_mode": "crawl_allowed",
    },
]

# Policybazaar reference sources — strictly link-only benchmark
POLICYBAZAAR_REFERENCE_SOURCES = [
    {
        "source_name": "Policybazaar Health Insurance Reference",
        "source_url": "https://www.policybazaar.com/health-insurance/",
        "url_type": "CATALOGUE",
        "description": "Public product discovery reference and UX benchmark (strictly link-only, automated scraping prohibited).",
        "permission_status": "permission_required",
        "ingestion_mode": "link_only",
    }
]

# Four canonical insurance categories
INSURANCE_CATEGORIES = [
    {"slug": "health", "name": "Health Insurance", "description": "Covers medical expenses, hospitalisation, and critical illness.", "icon": "Shield"},
    {"slug": "term-life", "name": "Term Life Insurance", "description": "Pure-risk life cover providing a death benefit to nominees.", "icon": "Heart"},
    {"slug": "motor", "name": "Motor Insurance", "description": "Covers own-damage and third-party liability for vehicles.", "icon": "Car"},
    {"slug": "travel", "name": "Travel Insurance", "description": "Covers trip cancellations, medical emergencies, and baggage loss abroad.", "icon": "Plane"},
]


def seed_irdai_sources(db: Session) -> int:
    """
    Idempotently seeds the IRDAI insurer profile and 3 official reference URLs.
    IRDAI sources are marked authorized / crawl_allowed because they are a public
    regulatory body whose data is in the public interest.
    """
    # 1. Ensure IRDAI Insurer profile exists
    insurer = db.query(Insurer).filter(Insurer.slug == "irdai").first()
    if not insurer:
        insurer = Insurer(
            name="Insurance Regulatory and Development Authority of India",
            short_name="IRDAI",
            slug="irdai",
            official_website="https://irdai.gov.in",
        )
        db.add(insurer)
        db.flush()
        logger.info("Registered insurer profile: %s", insurer.name)

    # 2. Seed IRDAI reference sources
    seeded_count = 0
    for src in IRDAI_REFERENCE_SOURCES:
        existing = db.query(SourceRegistry).filter(SourceRegistry.source_url == src["source_url"]).first()
        if not existing:
            reg = SourceRegistry(
                provider_name="Insurance Regulatory and Development Authority of India",
                provider_slug="irdai",
                category="Health",
                source_name=src["source_name"],
                source_url=src["source_url"],
                url_type=src["url_type"],
                permission_status=src["permission_status"],
                ingestion_mode=src["ingestion_mode"],
                description=src["description"],
                is_active=True,
            )
            db.add(reg)
            seeded_count += 1
        else:
            existing.provider_name = "Insurance Regulatory and Development Authority of India"
            existing.url_type = src["url_type"]
            existing.description = src["description"]
            existing.permission_status = src["permission_status"]
            existing.ingestion_mode = src["ingestion_mode"]

    db.commit()
    logger.info("IRDAI source registry seeded: %d new sources.", seeded_count)
    return seeded_count


def seed_insurance_categories(db: Session) -> int:
    """
    Idempotently seeds the 4 canonical insurance categories into insurance_categories table.
    """
    seeded_count = 0
    for cat in INSURANCE_CATEGORIES:
        existing = db.query(InsuranceCategory).filter(InsuranceCategory.slug == cat["slug"]).first()
        if not existing:
            category = InsuranceCategory(
                slug=cat["slug"],
                name=cat["name"],
                description=cat["description"],
                icon=cat["icon"],
                is_active=True,
            )
            db.add(category)
            seeded_count += 1
        else:
            # Update metadata idempotently
            existing.name = cat["name"]
            existing.description = cat["description"]
            existing.icon = cat["icon"]

    db.commit()
    logger.info("Insurance categories seeded: %d new categories.", seeded_count)
    return seeded_count


def seed_source_registry(db: Session) -> int:
    """
    Idempotently seeds ICICI Lombard insurer profile and 8 official reference URLs.
    Sets permission_status = 'permission_required' and ingestion_mode = 'link_only'.
    Also seeds IRDAI sources (authorized, crawl_allowed) and 4 insurance categories.
    Strictly performs local database operations without any outbound network calls.
    """
    # 1. Ensure Insurer profile exists
    insurer = db.query(Insurer).filter(Insurer.slug == "icici-lombard").first()
    if not insurer:
        insurer = Insurer(
            name="ICICI Lombard General Insurance Company Limited",
            short_name="ICICI Lombard",
            slug="icici-lombard",
            official_website="https://www.icicilombard.com",
        )
        db.add(insurer)
        db.flush()
        logger.info("Registered insurer profile: %s", insurer.name)

    # 2. Seed Reference Sources
    seeded_count = 0
    for src in ICICI_LOMBARD_REFERENCE_SOURCES:
        existing = db.query(SourceRegistry).filter(SourceRegistry.source_url == src["source_url"]).first()
        if not existing:
            reg = SourceRegistry(
                provider_name="ICICI Lombard General Insurance",
                provider_slug="icici-lombard",
                category="Health",
                source_name=src["source_name"],
                source_url=src["source_url"],
                url_type=src["url_type"],
                permission_status="permission_required",
                ingestion_mode="link_only",
                description=src["description"],
                is_active=True
            )
            db.add(reg)
            seeded_count += 1
        else:
            # Update metadata if needed while preserving permission and activity state
            existing.provider_name = "ICICI Lombard General Insurance"
            existing.url_type = src["url_type"]
            existing.description = src["description"]

    db.commit()
    logger.info("Source registry initialized: %d new reference sources registered.", seeded_count)

    # 3. Seed Policybazaar link-only reference
    for src in POLICYBAZAAR_REFERENCE_SOURCES:
        existing = db.query(SourceRegistry).filter(SourceRegistry.source_url == src["source_url"]).first()
        if not existing:
            reg = SourceRegistry(
                provider_name="Policybazaar Insurance Brokers",
                provider_slug="policybazaar",
                category="Health",
                source_name=src["source_name"],
                source_url=src["source_url"],
                url_type=src["url_type"],
                permission_status=src["permission_status"],
                ingestion_mode=src["ingestion_mode"],
                description=src["description"],
                is_active=True,
            )
            db.add(reg)
            seeded_count += 1
    db.commit()

    # 4. Seed IRDAI sources
    seed_irdai_sources(db)

    # 5. Seed insurance categories
    seed_insurance_categories(db)

    return seeded_count

def list_registered_sources(db: Session, provider_slug: Optional[str] = None) -> List[SourceRegistry]:
    query = db.query(SourceRegistry)
    if provider_slug:
        query = query.filter(SourceRegistry.provider_slug == provider_slug)
    return query.order_by(SourceRegistry.id.asc()).all()

def get_source_by_url(db: Session, url: str) -> Optional[SourceRegistry]:
    # Exact match first, or strip trailing slashes
    clean_url = url.rstrip("/")
    return db.query(SourceRegistry).filter(
        (SourceRegistry.source_url == url) | 
        (SourceRegistry.source_url == clean_url) |
        (SourceRegistry.source_url == f"{clean_url}/")
    ).first()
