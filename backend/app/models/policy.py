from sqlalchemy import Column, String, Text, Boolean, Integer, Float, ForeignKey, JSON, Date
from sqlalchemy.orm import relationship
from datetime import date
from app.models.base import TimeStampedModel

class InsurancePolicy(TimeStampedModel):
    __tablename__ = "insurance_policies"
    
    slug = Column(String(150), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    uin_number = Column(String(100), nullable=True, index=True) # IRDAI Unique Identification Number
    status = Column(String(50), default="CURRENT") # CURRENT, WITHDRAWN, SUPERSEDED
    
    category_id = Column(Integer, ForeignKey("insurance_categories.id"), nullable=False)
    insurer_id = Column(Integer, ForeignKey("insurers.id"), nullable=False)
    active_version_id = Column(Integer, ForeignKey("policy_versions.id", ondelete="SET NULL"), nullable=True)
    
    # Financial coverage details (nullable when unknown or not yet verified from source)
    min_sum_insured = Column(Float, nullable=True) # in INR, e.g. 500000 (5 Lakhs)
    max_sum_insured = Column(Float, nullable=True) # in INR, e.g. 10000000 (1 Crore)
    indicative_annual_premium = Column(Float, nullable=True)
    premium_disclaimer = Column(String(255), nullable=True)
    
    # Health/Category specific core parameters
    room_rent_capping = Column(String(100), nullable=True)
    icu_sub_limit = Column(String(100), nullable=True)
    copay_percentage = Column(Integer, nullable=True) # None until verified from evidence
    copay_description = Column(String(255), nullable=True)
    
    # Value features
    restoration_benefit = Column(String(255), nullable=True)
    no_claim_bonus = Column(String(255), nullable=True)
    pre_hospitalization_days = Column(Integer, nullable=True) # None until verified
    post_hospitalization_days = Column(Integer, nullable=True) # None until verified
    day_care_procedures = Column(String(100), nullable=True)
    ayush_treatment = Column(String(100), nullable=True)
    health_checkup = Column(String(100), nullable=True)
    ambulance_cover = Column(String(100), nullable=True)
    
    # Term Life / Motor specific fields
    policy_type = Column(String(50), default="Health Individual/Floater")
    entry_age_min = Column(Integer, nullable=True) # None until verified
    entry_age_max = Column(Integer, nullable=True) # None until verified
    renewal_lifetime = Column(Boolean, nullable=True)
    cashless_network_size = Column(Integer, nullable=True)
    
    # Transparency & verification (leave empty until source-grounded summaries can be generated)
    summary = Column(Text, nullable=True)
    target_audience = Column(String(255), nullable=True)
    pros = Column(JSON, default=list) # List of key positive highlights
    cons = Column(JSON, default=list) # List of key limitations & caveats
    
    official_brochure_url = Column(String(255), nullable=True)
    policy_wording_url = Column(String(255), nullable=True)
    claim_procedure_url = Column(String(255), nullable=True)
    source_attribution = Column(String(255), nullable=True)
    last_verified_date = Column(Date, nullable=True) # Populated only upon actual verification event
    is_active = Column(Boolean, default=True)

    # Relationships
    category = relationship("InsuranceCategory", back_populates="policies")
    insurer = relationship("Insurer", back_populates="policies")
    benefits = relationship("PolicyBenefit", back_populates="policy", cascade="all, delete-orphan")
    exclusions = relationship("PolicyExclusion", back_populates="policy", cascade="all, delete-orphan")
    waiting_periods = relationship("PolicyWaitingPeriod", back_populates="policy", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="policy")
    versions = relationship("PolicyVersion", back_populates="policy", foreign_keys="PolicyVersion.policy_id", cascade="all, delete-orphan")
    facts = relationship("PolicyFact", back_populates="policy", cascade="all, delete-orphan")
