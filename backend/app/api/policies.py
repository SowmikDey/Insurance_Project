from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc
from typing import Optional, List
from app.core.database import get_db
from app.models.policy import InsurancePolicy
from app.models.insurer import Insurer, InsuranceCategory
from app.schemas.policy import (
    PolicyListItemSchema,
    PolicyDetailSchema,
    PaginatedPoliciesResponse,
    CategorySchema,
    InsurerBasicSchema
)

router = APIRouter(prefix="/policies", tags=["policies"])

@router.get("/categories", response_model=List[CategorySchema])
def list_categories(db: Session = Depends(get_db)):
    return db.query(InsuranceCategory).filter(InsuranceCategory.is_active == True).all()

@router.get("/insurers", response_model=List[InsurerBasicSchema])
def list_insurers(db: Session = Depends(get_db)):
    return db.query(Insurer).order_by(Insurer.name.asc()).all()

@router.get("", response_model=PaginatedPoliciesResponse)
def list_policies(
    category: Optional[str] = Query(None, description="Category slug, e.g. health, term-life, motor"),
    insurer: Optional[str] = Query(None, description="Insurer slug"),
    min_sum_insured: Optional[float] = Query(None, description="Minimum sum insured in INR"),
    max_budget: Optional[float] = Query(None, description="Maximum indicative annual premium in INR"),
    zero_copay: Optional[bool] = Query(False, description="Filter only policies with 0% co-payment"),
    no_room_rent_capping: Optional[bool] = Query(False, description="Filter only policies with no room rent capping"),
    search: Optional[str] = Query(None, description="Search term in policy name or description"),
    sort_by: Optional[str] = Query("popular", description="popular, premium_asc, premium_desc, csr_desc, sum_insured_desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db)
):
    # Normalize params if invoked directly without FastAPI dependency injection
    if not isinstance(category, str):
        category = None
    if not isinstance(insurer, str):
        insurer = None
    if not isinstance(min_sum_insured, (int, float)):
        min_sum_insured = None
    if not isinstance(max_budget, (int, float)):
        max_budget = None
    if not isinstance(zero_copay, bool):
        zero_copay = False
    if not isinstance(no_room_rent_capping, bool):
        no_room_rent_capping = False
    if not isinstance(search, str):
        search = None
    if not isinstance(sort_by, str):
        sort_by = "popular"
    if not isinstance(page, int):
        page = 1
    if not isinstance(page_size, int):
        page_size = 12

    query = db.query(InsurancePolicy).join(InsuranceCategory).join(Insurer).filter(InsurancePolicy.is_active == True)

    if category and category.lower() != "all":
        query = query.filter(InsuranceCategory.slug == category.lower())

    if insurer and insurer.lower() != "all":
        query = query.filter(Insurer.slug == insurer.lower())

    if min_sum_insured:
        query = query.filter(InsurancePolicy.max_sum_insured >= min_sum_insured)

    if max_budget:
        query = query.filter(
            or_(
                InsurancePolicy.indicative_annual_premium == None,
                InsurancePolicy.indicative_annual_premium <= max_budget
            )
        )

    if zero_copay:
        query = query.filter(InsurancePolicy.copay_percentage == 0)

    if no_room_rent_capping:
        query = query.filter(
            or_(
                InsurancePolicy.room_rent_capping.ilike("%no capping%"),
                InsurancePolicy.room_rent_capping.ilike("%single private%")
            )
        )

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                InsurancePolicy.name.ilike(search_filter),
                InsurancePolicy.summary.ilike(search_filter),
                Insurer.name.ilike(search_filter)
            )
        )

    # Sorting
    if sort_by == "premium_asc":
        query = query.order_by(asc(InsurancePolicy.indicative_annual_premium))
    elif sort_by == "premium_desc":
        query = query.order_by(desc(InsurancePolicy.indicative_annual_premium))
    elif sort_by == "csr_desc":
        query = query.order_by(desc(Insurer.claim_settlement_ratio))
    elif sort_by == "sum_insured_desc":
        query = query.order_by(desc(InsurancePolicy.max_sum_insured))
    else:
        # Popular / Default
        query = query.order_by(desc(InsurancePolicy.cashless_network_size))

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return PaginatedPoliciesResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/{slug_or_id}", response_model=PolicyDetailSchema)
def get_policy_detail(slug_or_id: str, db: Session = Depends(get_db)):
    if slug_or_id.isdigit():
        policy = db.query(InsurancePolicy).filter(InsurancePolicy.id == int(slug_or_id)).first()
    else:
        policy = db.query(InsurancePolicy).filter(InsurancePolicy.slug == slug_or_id).first()

    if not policy:
        raise HTTPException(status_code=404, detail="Insurance policy not found")

    return policy
