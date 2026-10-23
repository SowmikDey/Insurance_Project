from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey, Boolean, Date, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.models.base import TimeStampedModel

class AuthorizedReview(TimeStampedModel):
    __tablename__ = "authorized_reviews"
    
    provider_slug = Column(String(100), index=True, nullable=False)
    policy_id = Column(Integer, ForeignKey("insurance_policies.id", ondelete="SET NULL"), nullable=True)
    source_name = Column(String(150), nullable=False)
    source_url = Column(String(500), nullable=False)
    external_review_id = Column(String(100), nullable=True)
    rating = Column(Float, nullable=True)
    review_text = Column(Text, nullable=True) # Only stored if permitted; null for link_only
    publication_date = Column(Date, nullable=True)
    retrieval_timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    review_type = Column(String(50), default="INDEPENDENT_REVIEW") # TESTIMONIAL, INDEPENDENT_REVIEW, CUSTOMER_EXPERIENCE, COMPLAINT_ALLEGATION, DISPUTE_FINDING
    verification_status = Column(String(50), default="UNVERIFIED")
    is_outbound_link_only = Column(Boolean, default=True)
    sentiment = Column(String(20), nullable=True)

    policy = relationship("InsurancePolicy")

class OfficialDisputeRecord(TimeStampedModel):
    """
    Stores official insurance ombudsman, consumer commission, and regulatory dispute decisions.
    Strictly preserves the legal distinction between the consumer's allegation,
    the insurer's response, the authority's findings, and the final binding award/outcome.
    Never fabricates disputes, claim-settlement ratios, or outcomes.
    """
    __tablename__ = "official_disputes"

    dispute_reference = Column(String(150), unique=True, index=True, nullable=False)
    authority_name = Column(String(150), nullable=False) # Insurance Ombudsman, NCDRC, State Commission, District Forum
    provider_slug = Column(String(100), index=True, nullable=False)
    insurer_id = Column(Integer, ForeignKey("insurers.id", ondelete="SET NULL"), nullable=True)
    policy_id = Column(Integer, ForeignKey("insurance_policies.id", ondelete="SET NULL"), nullable=True)
    product_name_stated = Column(String(200), nullable=True)

    allegation = Column(Text, nullable=False) # Consumer's stated complaint
    insurer_response = Column(Text, nullable=True) # Insurer's official response
    official_findings = Column(Text, nullable=False) # Regulatory / Ombudsman observations
    decision_outcome = Column(String(100), nullable=False) # AWARD_FAVOUR_CONSUMER, REJECTED, PARTIAL_RELIEF, DISMISSED, WITHDRAWN
    award_amount = Column(Float, nullable=True)

    publication_date = Column(Date, nullable=True)
    source_url = Column(String(500), nullable=False)
    source_document_id = Column(Integer, ForeignKey("document_sources.id", ondelete="SET NULL"), nullable=True)
    is_verified = Column(Boolean, default=True)

    insurer = relationship("Insurer")
    policy = relationship("InsurancePolicy")
