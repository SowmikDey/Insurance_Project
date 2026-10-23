"""
Master Policy Schema — 48-item Master Extraction Checklist.

Categories:
1. Policy identity and eligibility (6 items)
2. Coverage and benefits (10 items)
3. Restrictions and exclusions (10 items)
4. Premium and purchase conditions (7 items)
5. Claims and hospital access (8 items)
6. Historical and legal provenance (7 items)
Total: 48 items
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Section 1: Policy Identity and Eligibility (6 items)
# ---------------------------------------------------------------------------
class PolicyIdentityEligibility(BaseModel):
    insurer_name: str = Field(..., description="1. Insurer name and short name")
    uin_number: Optional[str] = Field(None, description="IRDAI Unique Identification Number")
    product_name: str = Field(..., description="2. Official product marketing name")
    policy_type: str = Field("Health", description="Policy category / subcategory (e.g. Indemnity, Critical Illness)")
    plan_variant: Optional[str] = Field(None, description="3. Individual, family floater, group or senior-citizen plan")
    entry_age_min: Optional[int] = Field(None, description="4. Minimum entry age in years")
    entry_age_max: Optional[int] = Field(None, description="Maximum entry age in years (or lifelong)")
    dependent_child_age_limit: Optional[str] = Field(None, description="Dependent child age coverage limit")
    eligibility_criteria: Optional[str] = Field(None, description="General eligibility requirements and residency")
    policy_tenure: Optional[str] = Field("1, 2, or 3 Years", description="5. Available policy tenures")
    renewal_terms: Optional[str] = Field("Lifelong Guaranteed Renewability", description="Lifelong renewal conditions")
    portability_conditions: Optional[str] = Field(None, description="Portability notice period and continuity benefits")
    geographic_availability: Optional[str] = Field("Pan-India", description="6. Geographic territory and zone classification")
    effective_version_date: Optional[str] = Field(None, description="Applicable version / release date")


# ---------------------------------------------------------------------------
# Section 2: Coverage and Benefits (10 items)
# ---------------------------------------------------------------------------
class CoverageBenefits(BaseModel):
    sum_insured_options: List[str] = Field(default_factory=list, description="7. Sum insured tiers and available variants")
    inpatient_hospitalization: Optional[str] = Field(None, description="8. Inpatient hospitalisation and ICU expenses")
    pre_hospitalization_days: Optional[int] = Field(None, description="9. Number of pre-hospitalisation days covered")
    post_hospitalization_days: Optional[int] = Field(None, description="Number of post-hospitalisation days covered")
    daycare_procedures: Optional[str] = Field(None, description="10. Daycare procedures and domiciliary treatment")
    domiciliary_hospitalization: Optional[str] = Field(None, description="Home / domiciliary hospitalisation conditions")
    home_healthcare: Optional[str] = Field(None, description="11. Home healthcare coverage")
    ayush_treatment: Optional[str] = Field(None, description="AYUSH (Ayurveda, Yoga, Unani, Siddha, Homeopathy) limits")
    ambulance_cover: Optional[str] = Field(None, description="12. Road and air ambulance cover limits")
    organ_donor_expenses: Optional[str] = Field(None, description="Organ donor harvesting and hospitalisation expenses")
    modern_treatments: Optional[str] = Field(None, description="Modern treatment methods / robotic surgery coverage")
    maternity_cover: Optional[str] = Field(None, description="13. Maternity, newborn, and vaccination benefits")
    opd_dental_vision: Optional[str] = Field(None, description="14. OPD, dental, vision, and mental healthcare covers")
    restoration_benefit: Optional[str] = Field(None, description="15. Restoration, refill, or reset benefit terms")
    cumulative_bonus: Optional[str] = Field(None, description="Cumulative / No Claim Bonus (NCB) terms and upper cap")
    wellness_benefits: Optional[str] = Field(None, description="Health check-up and wellness rewards")
    critical_illness_rider: Optional[str] = Field(None, description="16. Critical illness and accidental death benefits")


# ---------------------------------------------------------------------------
# Section 3: Restrictions and Exclusions (10 items)
# ---------------------------------------------------------------------------
class RestrictionsExclusions(BaseModel):
    initial_waiting_period_days: Optional[int] = Field(30, description="17. Initial waiting period (typically 30 days)")
    ped_waiting_period_months: Optional[int] = Field(None, description="18. Pre-existing disease waiting period in months")
    specific_disease_waiting_months: Optional[int] = Field(None, description="19. Specific disease/procedure waiting period")
    permanent_exclusions: List[str] = Field(default_factory=list, description="20. Standard permanent exclusions")
    room_rent_capping: Optional[str] = Field(None, description="21. Room rent limit (e.g. 1% of SI or Single Private AC Room)")
    icu_sub_limit: Optional[str] = Field(None, description="ICU daily charge limit or actuals")
    disease_sub_limits: Optional[Dict[str, str]] = Field(default_factory=dict, description="22. Disease-wise sub-limits (cataract, hernia, etc.)")
    copay_percentage: Optional[int] = Field(0, description="23. Co-payment percentage required from insured")
    deductible_amount: Optional[float] = Field(None, description="Compulsory or voluntary deductible in INR")
    zone_based_restrictions: Optional[str] = Field(None, description="24. Zone-based co-pay or proportionate deductions")
    pre_authorization_rules: Optional[str] = Field(None, description="25. Pre-authorization notice requirements")
    medical_necessity_clause: Optional[str] = Field(None, description="Medical necessity conditions for claim approval")
    non_payable_items: Optional[str] = Field(None, description="26. Consumables and non-payable hospital expenses cover")


# ---------------------------------------------------------------------------
# Section 4: Premium and Purchase Conditions (7 items)
# ---------------------------------------------------------------------------
class PremiumPurchaseConditions(BaseModel):
    indicative_annual_premium: Optional[float] = Field(None, description="27. Premium benchmark for 30yr adult, ₹5L cover")
    pricing_factors: Optional[str] = Field(None, description="28. Factors influencing premium (age, pincode, family size)")
    tenure_discounts: Optional[str] = Field(None, description="29. Multi-year discounts (e.g. 7.5% for 2yr, 10% for 3yr)")
    installment_options: Optional[str] = Field(None, description="Monthly/Quarterly/Annual premium payment frequency")
    tax_benefits: Optional[str] = Field("Section 80D up to ₹25,000 / ₹50,000", description="30. Income tax deductions applicable")
    medical_underwriting: Optional[str] = Field(None, description="31. Pre-policy medical checkup requirements & tele-underwriting")
    free_look_period_days: Optional[int] = Field(15, description="32. Free-look cancellation window (15 or 30 days)")
    cancellation_refund_terms: Optional[str] = Field(None, description="Cancellation grid and short-period refund scale")
    optional_riders: List[str] = Field(default_factory=list, description="33. Optional riders and add-on covers available")


# ---------------------------------------------------------------------------
# Section 5: Claims and Hospital Access (8 items)
# ---------------------------------------------------------------------------
class ClaimsHospitalAccess(BaseModel):
    cashless_claim_procedure: Optional[str] = Field(None, description="34. Step-by-step cashless claim workflow")
    reimbursement_claim_procedure: Optional[str] = Field(None, description="Reimbursement claim submission process")
    emergency_intimation_hours: Optional[int] = Field(24, description="35. Emergency hospitalisation intimation deadline")
    planned_intimation_hours: Optional[int] = Field(48, description="Planned hospitalisation pre-authorization deadline")
    required_claim_documents: List[str] = Field(default_factory=list, description="36. Required claim documents list")
    claim_submission_deadline_days: Optional[int] = Field(30, description="Deadline to submit bills post-discharge")
    grievance_redressal_details: Optional[str] = Field(None, description="37. Insurer grievance cell and Insurance Ombudsman contact")
    cashless_hospital_network_size: Optional[int] = Field(None, description="38. Total empaneled cashless hospital count")
    tpa_support: Optional[str] = Field("In-house / Multiple TPAs", description="39. In-house claim settlement or third-party administrator")
    turnaround_time_cashless_hours: Optional[float] = Field(None, description="40. Published cashless pre-auth decision turnaround time")
    claim_settlement_ratio: Optional[float] = Field(None, description="41. Insurer Claim Settlement Ratio (IRDAI published)")
    incurred_claim_ratio: Optional[float] = Field(None, description="Incurred Claim Ratio (ICR)")


# ---------------------------------------------------------------------------
# Section 6: Historical and Legal Provenance (7 items)
# ---------------------------------------------------------------------------
class HistoricalLegalProvenance(BaseModel):
    policy_wording_url: Optional[str] = Field(None, description="42. Official policy clauses / wording document URL")
    cis_document_url: Optional[str] = Field(None, description="Customer Information Sheet (CIS) URL")
    brochure_url: Optional[str] = Field(None, description="43. Marketing brochure URL")
    prospectus_url: Optional[str] = Field(None, description="Official prospectus URL")
    proposal_form_url: Optional[str] = Field(None, description="Blank proposal form URL")
    uin_history: Optional[str] = Field(None, description="44. UIN history and previous revisions")
    approval_date: Optional[str] = Field(None, description="45. IRDAI product approval date")
    publication_date: Optional[str] = Field(None, description="Publication / circular effective date")
    withdrawn_predecessor_plans: Optional[str] = Field(None, description="46. Previous versions or withdrawn products replaced")
    governing_regulations: List[str] = Field(
        default_factory=lambda: ["IRDAI Master Circular on Health Insurance", "IRDAI (Health Insurance) Regulations, 2016"],
        description="47. Applicable IRDAI master circulars and gazettes"
    )
    source_url: str = Field(..., description="48. Primary source URL")
    retrieval_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    document_sha256: Optional[str] = Field(None, description="Cryptographic SHA-256 hash of original document")


# ---------------------------------------------------------------------------
# Master Policy Record (aggregating all 48 items)
# ---------------------------------------------------------------------------
class MasterPolicyRecord(BaseModel):
    slug: str
    identity: PolicyIdentityEligibility
    coverage: CoverageBenefits
    restrictions: RestrictionsExclusions
    premium: PremiumPurchaseConditions
    claims: ClaimsHospitalAccess
    provenance: HistoricalLegalProvenance

    def to_summary_dict(self) -> Dict[str, Any]:
        """Provides a flat summary dictionary for quick tabular listing."""
        return {
            "slug": self.slug,
            "product_name": self.identity.product_name,
            "insurer_name": self.identity.insurer_name,
            "uin": self.identity.uin_number,
            "plan_variant": self.identity.plan_variant,
            "room_rent_capping": self.restrictions.room_rent_capping,
            "copay_percentage": self.restrictions.copay_percentage,
            "ped_waiting_months": self.restrictions.ped_waiting_period_months,
            "csr": self.claims.claim_settlement_ratio,
            "cashless_hospitals": self.claims.cashless_hospital_network_size,
            "source_url": self.provenance.source_url,
            "approval_date": self.provenance.approval_date,
        }
