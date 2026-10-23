from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey, JSON, Date
from sqlalchemy.orm import relationship
from app.models.base import TimeStampedModel

class PolicyVersion(TimeStampedModel):
    __tablename__ = "policy_versions"
    
    policy_id = Column(Integer, ForeignKey("insurance_policies.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(String(50), default="1.0")
    uin_number = Column(String(100), nullable=True)
    status = Column(String(50), default="CURRENT") # CURRENT, WITHDRAWN, SUPERSEDED, DRAFT
    effective_from_date = Column(Date, nullable=True)
    effective_to_date = Column(Date, nullable=True)
    superseded_by_version_id = Column(Integer, ForeignKey("policy_versions.id", ondelete="SET NULL"), nullable=True)
    document_source_id = Column(Integer, ForeignKey("document_sources.id", ondelete="SET NULL"), nullable=True)
    source_url = Column(String(500), nullable=True)
    raw_extracted_data = Column(JSON, default=dict)

    policy = relationship("InsurancePolicy", back_populates="versions", foreign_keys=[policy_id])
    facts = relationship("PolicyFact", back_populates="version", cascade="all, delete-orphan")
    document_source = relationship("DocumentSource")

class PolicyFact(TimeStampedModel):
    __tablename__ = "policy_facts"
    
    policy_id = Column(Integer, ForeignKey("insurance_policies.id", ondelete="CASCADE"), nullable=False)
    policy_version_id = Column(Integer, ForeignKey("policy_versions.id", ondelete="CASCADE"), nullable=True)
    
    field_name = Column(String(100), nullable=False)
    field_value = Column(Text, nullable=True)
    normalized_value = Column(Text, nullable=True)
    evidence_snippet = Column(Text, nullable=False)
    section_heading = Column(String(255), nullable=True)
    page_number = Column(Integer, nullable=True)
    source_url = Column(String(500), nullable=True)
    document_source_id = Column(Integer, ForeignKey("document_sources.id", ondelete="SET NULL"), nullable=True)
    
    extraction_method = Column(String(50), default="DETERMINISTIC_REGEX") # DETERMINISTIC_REGEX, TABLE_PARSER, MANUAL_ENTRY
    verification_status = Column(String(50), default="EXTRACTED") # EXTRACTED, NEEDS_REVIEW, VERIFIED, CONFLICTING, UNAVAILABLE
    confidence_score = Column(Float, default=1.0)
    notes = Column(Text, nullable=True)

    policy = relationship("InsurancePolicy", back_populates="facts")
    version = relationship("PolicyVersion", back_populates="facts")
    document_source = relationship("DocumentSource")
