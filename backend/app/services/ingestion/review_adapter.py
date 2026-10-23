import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, date, timezone
from sqlalchemy.orm import Session
from app.models.review import AuthorizedReview
from app.services.ingestion.authorization_service import (
    check_authorization,
    AuthorizationActivity
)

logger = logging.getLogger(__name__)

class ReviewType:
    TESTIMONIAL = "TESTIMONIAL"
    INDEPENDENT_REVIEW = "INDEPENDENT_REVIEW"
    CUSTOMER_EXPERIENCE = "CUSTOMER_EXPERIENCE"
    COMPLAINT_ALLEGATION = "COMPLAINT_ALLEGATION"
    DISPUTE_FINDING = "DISPUTE_FINDING"

class ReviewVerificationStatus:
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"
    ADJUDICATED = "ADJUDICATED"

class ReviewAdapter:
    """
    Adapter for processing and storing customer reviews and outbound review references.
    Strictly complies with collection permissions:
    - If provider/source does not authorize review text storage, stores outbound link & metadata only.
    - Categorizes review types and ensures complaint allegations are never labeled as adjudicated findings.
    - Stored strictly in PostgreSQL (no external NoSQL/MongoDB).
    """

    def __init__(self, db: Session):
        self.db = db

    def register_review(
        self,
        provider_slug: str,
        source_name: str,
        source_url: str,
        review_type: str = ReviewType.INDEPENDENT_REVIEW,
        policy_id: Optional[int] = None,
        external_review_id: Optional[str] = None,
        rating: Optional[float] = None,
        review_text: Optional[str] = None,
        publication_date: Optional[date] = None,
        sentiment: Optional[str] = None
    ) -> AuthorizedReview:
        """
        Stores review entry. If source authorization does not permit text storage,
        forces review_text to None and flags is_outbound_link_only = True.
        """
        # Check authorization for storing review text
        is_permitted, reason, _ = check_authorization(
            self.db,
            source_url,
            activity=AuthorizationActivity.STORE_REVIEWS
        )

        # For link-only or unauthorized sources (like ICICI Lombard), enforce outbound link only
        if not is_permitted:
            is_outbound_link_only = True
            stored_text = None
        else:
            is_outbound_link_only = False
            stored_text = review_text

        # Deduplicate by external_review_id and source_url if provided
        existing = None
        if external_review_id:
            existing = self.db.query(AuthorizedReview).filter(
                AuthorizedReview.provider_slug == provider_slug,
                AuthorizedReview.external_review_id == external_review_id
            ).first()

        if existing:
            existing.rating = rating
            existing.is_outbound_link_only = is_outbound_link_only
            if not is_outbound_link_only:
                existing.review_text = stored_text
            self.db.commit()
            self.db.refresh(existing)
            return existing

        review = AuthorizedReview(
            provider_slug=provider_slug,
            policy_id=policy_id,
            source_name=source_name,
            source_url=source_url,
            external_review_id=external_review_id,
            rating=rating,
            review_text=stored_text,
            publication_date=publication_date,
            retrieval_timestamp=datetime.now(timezone.utc),
            review_type=review_type,
            verification_status=ReviewVerificationStatus.UNVERIFIED,
            is_outbound_link_only=is_outbound_link_only,
            sentiment=sentiment
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review

    def get_reviews_for_policy(self, policy_id: int) -> List[AuthorizedReview]:
        return self.db.query(AuthorizedReview).filter(
            AuthorizedReview.policy_id == policy_id
        ).order_by(AuthorizedReview.publication_date.desc()).all()

    def get_reviews_for_provider(self, provider_slug: str) -> List[AuthorizedReview]:
        return self.db.query(AuthorizedReview).filter(
            AuthorizedReview.provider_slug == provider_slug
        ).order_by(AuthorizedReview.publication_date.desc()).all()
