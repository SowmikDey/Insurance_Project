from sqlalchemy import Column, String, Text, Boolean, Integer, Float
from sqlalchemy.orm import relationship
from app.models.base import TimeStampedModel

class InsuranceCategory(TimeStampedModel):
    __tablename__ = "insurance_categories"
    
    slug = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), default="Shield")
    is_active = Column(Boolean, default=True)
    
    policies = relationship("InsurancePolicy", back_populates="category")

class Insurer(TimeStampedModel):
    __tablename__ = "insurers"
    
    slug = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(150), nullable=False)
    short_name = Column(String(50), nullable=True)
    irdai_registration_no = Column(String(50), nullable=True)
    claim_settlement_ratio = Column(Float, nullable=True) # e.g. 98.4%
    solvency_ratio = Column(Float, nullable=True) # IRDAI mandated min is 1.5
    network_hospitals_count = Column(Integer, default=0)
    customer_care_number = Column(String(50), nullable=True)
    official_website = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    policies = relationship("InsurancePolicy", back_populates="insurer")
