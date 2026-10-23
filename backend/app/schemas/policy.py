from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date
from app.schemas.ingestion import PolicyFactSchema

class InsurerBasicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    short_name: Optional[str] = None
    slug: str
    claim_settlement_ratio: Optional[float] = None
    solvency_ratio: Optional[float] = None
    network_hospitals_count: Optional[int] = 0
    official_website: Optional[str] = None

class CategorySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = "Shield"

class PolicyBenefitSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    is_inbuilt: bool
    sub_limit: Optional[str] = None
    importance_level: Optional[str] = "High"

class PolicyExclusionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    exclusion_type: Optional[str] = "Permanent"
    irda_clause_ref: Optional[str] = None

class PolicyWaitingPeriodSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    duration_months: int
    description: str
    practical_impact: Optional[str] = None

class PolicyListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    uin_number: Optional[str] = None
    status: Optional[str] = "CURRENT"
    policy_type: Optional[str] = "Health Individual/Floater"
    category: CategorySchema
    insurer: InsurerBasicSchema
    min_sum_insured: Optional[float] = None
    max_sum_insured: Optional[float] = None
    indicative_annual_premium: Optional[float] = None
    premium_disclaimer: Optional[str] = None
    room_rent_capping: Optional[str] = None
    icu_sub_limit: Optional[str] = None
    copay_percentage: Optional[int] = None
    copay_description: Optional[str] = None
    restoration_benefit: Optional[str] = None
    no_claim_bonus: Optional[str] = None
    cashless_network_size: Optional[int] = None
    summary: Optional[str] = None
    pros: List[str] = []
    cons: List[str] = []
    last_verified_date: Optional[date] = None

class PolicyDetailSchema(PolicyListItemSchema):
    active_version_id: Optional[int] = None
    pre_hospitalization_days: Optional[int] = None
    post_hospitalization_days: Optional[int] = None
    day_care_procedures: Optional[str] = None
    ayush_treatment: Optional[str] = None
    health_checkup: Optional[str] = None
    ambulance_cover: Optional[str] = None
    entry_age_min: Optional[int] = None
    entry_age_max: Optional[int] = None
    renewal_lifetime: Optional[bool] = None
    target_audience: Optional[str] = None
    official_brochure_url: Optional[str] = None
    policy_wording_url: Optional[str] = None
    claim_procedure_url: Optional[str] = None
    source_attribution: Optional[str] = None
    benefits: List[PolicyBenefitSchema] = []
    exclusions: List[PolicyExclusionSchema] = []
    waiting_periods: List[PolicyWaitingPeriodSchema] = []
    facts: List[PolicyFactSchema] = []

class PolicyFilterParams(BaseModel):
    category_slug: Optional[str] = None
    insurer_slug: Optional[str] = None
    min_sum_insured: Optional[float] = None
    max_budget: Optional[float] = None
    zero_copay_only: Optional[bool] = False
    no_room_rent_capping_only: Optional[bool] = False
    search: Optional[str] = None
    sort_by: Optional[str] = "popular" # popular, premium_asc, premium_desc, csr_desc, sum_insured_desc
    page: int = 1
    page_size: int = 12

class PaginatedPoliciesResponse(BaseModel):
    items: List[PolicyListItemSchema]
    total: int
    page: int
    page_size: int
    total_pages: int
