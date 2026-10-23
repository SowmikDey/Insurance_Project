from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import TimeStampedModel

class PolicyBenefit(TimeStampedModel):
    __tablename__ = "policy_benefits"
    
    policy_id = Column(Integer, ForeignKey("insurance_policies.id"), nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    is_inbuilt = Column(Boolean, default=True) # inbuilt vs optional rider
    sub_limit = Column(String(100), nullable=True)
    importance_level = Column(String(20), default="High") # High, Medium, Value-add
    
    policy = relationship("InsurancePolicy", back_populates="benefits")

class PolicyExclusion(TimeStampedModel):
    __tablename__ = "policy_exclusions"
    
    policy_id = Column(Integer, ForeignKey("insurance_policies.id"), nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    exclusion_type = Column(String(50), default="Permanent") # Permanent, Time-bound, Conditional
    irda_clause_ref = Column(String(50), nullable=True) # e.g. IRDAI Standard Exclusion List
    
    policy = relationship("InsurancePolicy", back_populates="exclusions")

class PolicyWaitingPeriod(TimeStampedModel):
    __tablename__ = "policy_waiting_periods"
    
    policy_id = Column(Integer, ForeignKey("insurance_policies.id"), nullable=False)
    category = Column(String(100), nullable=False) # "Initial Waiting Period", "Pre-existing Diseases (PED)", "Specific Named Illnesses", "Maternity"
    duration_months = Column(Integer, nullable=False) # e.g. 1 month (30 days), 24 months, 36 months
    description = Column(Text, nullable=False)
    practical_impact = Column(Text, nullable=True) # Simple explanation of what happens if claim made during this period
    
    policy = relationship("InsurancePolicy", back_populates="waiting_periods")
