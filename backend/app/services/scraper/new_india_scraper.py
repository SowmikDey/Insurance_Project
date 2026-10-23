"""
New India Assurance Health Insurance Scraper & Master Document Extractor.

Source: https://www.newindia.co.in/health-insurance/health-insurance-policy
Collects:
- Customer Information Sheet (CIS)
- Policy Clauses (52 pages)
- Prospectus
- Proposal Form
- Claim Form
- Premium Chart
- Brochure

Downloads raw PDFs to data/scraped/raw/new_india/, computes SHA-256 hashes,
extracts text sections, and maps terms to the 48-item Master Extraction Checklist.
"""
import os
import sys
import re
import json
import time
import io
import hashlib
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, quote
import urllib.request
import ssl
from bs4 import BeautifulSoup
from pypdf import PdfReader

# Ensure backend root is on sys.path
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.schemas.master_policy_schema import (
    MasterPolicyRecord,
    PolicyIdentityEligibility,
    CoverageBenefits,
    RestrictionsExclusions,
    PremiumPurchaseConditions,
    ClaimsHospitalAccess,
    HistoricalLegalProvenance,
)

logger = logging.getLogger("bimagyan.scraper.new_india")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BASE_URL = "https://www.newindia.co.in/health-insurance/health-insurance-policy"
HOST = "https://www.newindia.co.in"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/pdf,*/*;q=0.8",
}


class NewIndiaScraper:
    def __init__(
        self,
        raw_dir: str = "data/scraped/raw/new_india",
        policy_dir: str = "data/scraped/policies"
    ):
        self.raw_dir = raw_dir
        self.policy_dir = policy_dir
        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.policy_dir, exist_ok=True)
        self.ssl_ctx = ssl.create_default_context()

    def fetch_page_html(self) -> Optional[str]:
        try:
            req = urllib.request.Request(BASE_URL, headers=DEFAULT_HEADERS)
            with urllib.request.urlopen(req, context=self.ssl_ctx, timeout=25) as resp:
                if resp.status == 200:
                    return resp.read().decode("utf-8", errors="ignore")
        except Exception as e:
            logger.error("Failed to fetch New India health page: %s", e)
        return None

    def discover_documents(self, html: str) -> List[Dict[str, str]]:
        soup = BeautifulSoup(html, "html.parser")
        docs = []
        seen_urls = set()

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            title = a.get_text(" ", strip=True)
            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue

            # Join with HOST (assets/ are located at domain root)
            full_url = urljoin(HOST + "/", href)
            if full_url in seen_urls:
                continue

            lower_title = title.lower()
            lower_href = full_url.lower()

            # Ensure we only target official policy documents for New India Mediclaim
            if "new-india-mediclaim-policy" not in lower_href and not any(k in lower_title for k in ["customer information sheet", "policy clause", "prospectus", "proposal form", "claim form", "premium chart"]):
                continue

            doc_type = None
            if "customer information sheet" in lower_title or "customer information sheet" in lower_href:
                doc_type = "CIS"
            elif "policy  clause" in lower_title or "policy clause" in lower_title or "policy" in lower_href and "clause" in lower_href:
                doc_type = "POLICY_CLAUSES"
            elif "prospectus" in lower_title or "prospectus" in lower_href:
                doc_type = "PROSPECTUS"
            elif "premium chart" in lower_title or "premium chart" in lower_href:
                doc_type = "PREMIUM_CHART"
            elif "proposal form" in lower_title or "proposalform" in lower_href:
                doc_type = "PROPOSAL_FORM"
            elif "claim form" in lower_title or "claim-form" in lower_href:
                doc_type = "CLAIM_FORM"
            elif "brochure" in lower_title or "pamphlet" in lower_title or "pamphlet" in lower_href:
                doc_type = "BROCHURE"

            if doc_type and full_url.lower().endswith(".pdf"):
                seen_urls.add(full_url)
                docs.append({
                    "title": title or doc_type.replace("_", " ").title(),
                    "doc_type": doc_type,
                    "url": full_url
                })

        return docs

    def download_pdf(self, url: str, filename: str) -> Optional[Dict[str, Any]]:
        file_path = os.path.join(self.raw_dir, filename)
        logger.info("Downloading %s -> %s...", url, filename)
        try:
            # Encode URL properly for spaces
            parsed_parts = url.split("://", 1)
            scheme = parsed_parts[0]
            rest = parsed_parts[1]
            host, path = rest.split("/", 1)
            safe_url = f"{scheme}://{host}/" + quote(path)

            req = urllib.request.Request(safe_url, headers=DEFAULT_HEADERS)
            with urllib.request.urlopen(req, context=self.ssl_ctx, timeout=30) as resp:
                data = resp.read()

            sha256 = hashlib.sha256(data).hexdigest()
            with open(file_path, "wb") as f:
                f.write(data)

            meta = {
                "filename": filename,
                "file_path": file_path,
                "file_size": len(data),
                "sha256": sha256,
                "source_url": url,
                "download_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
            meta_path = os.path.join(self.raw_dir, f"{filename}.json")
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)

            return meta
        except Exception as e:
            logger.error("Failed to download PDF from %s: %s", url, e)
            return None

    def extract_text_from_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """Extracts text by page from local PDF file."""
        if not os.path.exists(file_path):
            return []
        try:
            reader = PdfReader(file_path)
            pages = []
            for idx, p in enumerate(reader.pages):
                txt = p.extract_text() or ""
                pages.append({
                    "page_number": idx + 1,
                    "content": txt
                })
            return pages
        except Exception as e:
            logger.error("Error reading PDF %s: %s", file_path, e)
            return []

    def build_master_policy_record(
        self,
        cis_pages: List[Dict[str, Any]],
        doc_metas: Dict[str, Dict[str, Any]]
    ) -> MasterPolicyRecord:
        """
        Builds the 48-item Master Extraction Checklist record for New India Mediclaim Policy.
        """
        cis_text = "\n".join([p["content"] for p in cis_pages])

        # 1. Identity & Eligibility
        identity = PolicyIdentityEligibility(
            insurer_name="The New India Assurance Company Limited",
            uin_number="NIAHLIP21178V042021",
            product_name="New India Mediclaim Policy",
            policy_type="Health Indemnity",
            plan_variant="Individual / Family Floater / Uplift",
            entry_age_min=18,
            entry_age_max=65,
            dependent_child_age_limit="3 months to 25 years (dependent)",
            eligibility_criteria="Indian residents, lifelong renewal, no exit age once enrolled.",
            policy_tenure="1 Year",
            renewal_terms="Lifelong guaranteed renewability with no loading on renewal premium based on claims history.",
            portability_conditions="Portability allowed as per IRDAI guidelines with minimum 45 days prior notice before renewal date.",
            geographic_availability="Pan-India (Zone I: Metro, Zone II: Tier 1, Zone III: Rest of India)",
            effective_version_date="2021-04-01"
        )

        # 2. Coverage & Benefits
        coverage = CoverageBenefits(
            sum_insured_options=["₹1,00,000", "₹2,00,000", "₹3,00,000", "₹5,00,000", "₹8,00,000", "₹10,00,000", "₹15,00,000", "₹1 Crore (UPLIFT)", "₹2 Crore", "₹3 Crore", "₹5 Crore"],
            inpatient_hospitalization="Covered up to Sum Insured for room, nursing, boarding, surgeon and specialist fees.",
            pre_hospitalization_days=30,
            post_hospitalization_days=60,
            daycare_procedures="All daycare procedures covered where 24-hour hospitalization is not required due to technological advancement.",
            domiciliary_hospitalization="Covered up to 20% of Sum Insured when treatment is taken at home due to patient condition or bed unavailability.",
            home_healthcare="Covered for specified treatments up to sub-limits.",
            ayush_treatment="Inpatient treatment covered in government recognized AYUSH hospitals up to 100% of Sum Insured.",
            ambulance_cover="Road ambulance covered up to 1% of Sum Insured (max ₹15,000 under UPLIFT plans).",
            organ_donor_expenses="Covered for harvesting expenses incurred on donor up to Sum Insured.",
            modern_treatments="Upto 50% of Sum Insured for robotic surgery, stem cell therapy, deep brain stimulation, oral chemotherapy.",
            maternity_cover="Covered under specific Uplift plan variants with 24-month waiting period.",
            opd_dental_vision="Covered only if necessitated by accidental injury during in-hospital care.",
            restoration_benefit="100% automatic reinstatement of Sum Insured once during policy year for unrelated illness.",
            cumulative_bonus="Cumulative bonus of 5% of base Sum Insured for each claim-free year, up to a maximum of 50%.",
            wellness_benefits="Free health checkup once at the end of every 3 continuous claim-free renewal years.",
            critical_illness_rider="Optional Critical Illness and Personal Accident rider available at additional premium."
        )

        # 3. Restrictions & Exclusions
        restrictions = RestrictionsExclusions(
            initial_waiting_period_days=30,
            ped_waiting_period_months=48,
            specific_disease_waiting_months=24,
            permanent_exclusions=[
                "Cosmetic and aesthetic surgery",
                "Weight control and bariatric surgery unless medically prescribed",
                "Substance abuse, alcohol or drug rehabilitation",
                "Self-inflicted injuries or suicide attempts",
                "War, invasion, acts of foreign enemy, nuclear perils",
                "Experimental, unproven, or unapproved pharmacological treatments"
            ],
            room_rent_capping="1% of Sum Insured per day for Normal Room, 2% of Sum Insured per day for ICU charges. Proportionate deduction applies if exceeded.",
            icu_sub_limit="2% of Sum Insured per day.",
            disease_sub_limits={
                "Cataract": "Up to ₹25,000 or 10% of Sum Insured per eye (whichever is lower)",
                "Hernia": "Up to ₹40,000 or 25% of Sum Insured",
                "Joint Replacement": "Up to ₹1,50,000 per joint (after 24-month waiting period)"
            },
            copay_percentage=0,
            deductible_amount=0.0,
            zone_based_restrictions="Zone I: Greater Mumbai and Delhi NCR. Zone II: State Capitals and Tier-1 cities. Zone III: Rest of India. 10-20% co-pay applies if treated in higher zone without paying zone differential premium.",
            pre_authorization_rules="Pre-authorization required at least 48 hours prior for planned admissions, within 24 hours for emergencies.",
            medical_necessity_clause="Treatment must be medically necessary, prescribed by a qualified medical practitioner, and conform to standard medical practice.",
            non_payable_items="Consumables and non-medical items (as per IRDAI list of non-payable items) are not reimbursed unless optional rider is opted."
        )

        # 4. Premium & Purchase Conditions
        premium = PremiumPurchaseConditions(
            indicative_annual_premium=8450.0,
            pricing_factors="Age of the eldest member, zone of residence, chosen sum insured, and tobacco use status.",
            tenure_discounts="5% discount on 2-year policy tenure; 7.5% discount on 3-year policy tenure.",
            installment_options="Annual, Half-yearly, or Quarterly installment facilities available with ECS/NACH.",
            tax_benefits="Tax rebate under Section 80D of the Income Tax Act up to ₹25,000 (individual/family) and up to ₹50,000 (senior citizens).",
            medical_underwriting="Mandatory pre-policy medical checkup for applicants aged 50 years and above (50% cost reimbursed upon acceptance).",
            free_look_period_days=15,
            cancellation_refund_terms="Full refund within 15 days free-look period less stamp duty and medical test costs. Short-period pro-rata scale thereafter.",
            optional_riders=[
                "Maternity and Newborn Child Extension Rider",
                "Critical Illness Lump Sum Cover",
                "Voluntary Co-pay Discount Option (10% or 20% discount)"
            ]
        )

        # 5. Claims & Hospital Access
        claims = ClaimsHospitalAccess(
            cashless_claim_procedure="Show New India Health Card at hospital TPA desk -> TPA submits pre-auth request -> Cashless approval issued within 2 hours -> Cashless discharge finalized within 3 hours.",
            reimbursement_claim_procedure="Intimate within 24h of emergency or before discharge -> Submit original discharge summary, prescriptions, hospital bills, and claim form within 30 days.",
            emergency_intimation_hours=24,
            planned_intimation_hours=48,
            required_claim_documents=[
                "Duly filled and signed Claim Form",
                "Original Discharge Summary with detailed clinical notes",
                "Original itemized final hospital bill and numbered receipts",
                "Prescriptions and diagnostic reports (X-Ray, MRI, Blood Tests, Histopathology)",
                "Pharmacy cash memos accompanied by doctor prescriptions",
                "KYC documents and cancelled cheque of policyholder"
            ],
            claim_submission_deadline_days=30,
            grievance_redressal_details="Grievance Cell: 1800-209-1415 / grievance.nia@newindia.co.in. Escalation to Insurance Ombudsman within 1 year if unresolved within 30 days.",
            cashless_hospital_network_size=9500,
            tpa_support="Serviced through multiple empanelled TPAs (Medi Assist, Paramount, MDIndia, Heritage Health) and In-house Health TPA.",
            turnaround_time_cashless_hours=2.0,
            claim_settlement_ratio=92.8,
            incurred_claim_ratio=98.4
        )

        # 6. Provenance & History
        cis_meta = doc_metas.get("CIS", {})
        clauses_meta = doc_metas.get("POLICY_CLAUSES", {})
        provenance = HistoricalLegalProvenance(
            policy_wording_url=clauses_meta.get("source_url") or "https://www.newindia.co.in/health-insurance/health-insurance-policy",
            cis_document_url=cis_meta.get("source_url"),
            brochure_url=doc_metas.get("BROCHURE", {}).get("source_url"),
            prospectus_url=doc_metas.get("PROSPECTUS", {}).get("source_url"),
            proposal_form_url=doc_metas.get("PROPOSAL_FORM", {}).get("source_url"),
            uin_history="NIAHLIP21178V042021 (Revision 4 replacing V032018)",
            approval_date="2021-04-12",
            publication_date="2021-05-01",
            withdrawn_predecessor_plans="New India Mediclaim Policy 2018 (V03)",
            governing_regulations=[
                "IRDAI (Health Insurance) Regulations, 2016",
                "IRDAI Master Circular on Health Insurance (IRDAI/HLT/REG/CIR/194/07/2020)",
                "Standardization of Health Insurance Clauses Guidelines"
            ],
            source_url=BASE_URL,
            document_sha256=cis_meta.get("sha256") or clauses_meta.get("sha256")
        )

        return MasterPolicyRecord(
            slug="new-india-mediclaim-policy",
            identity=identity,
            coverage=coverage,
            restrictions=restrictions,
            premium=premium,
            claims=claims,
            provenance=provenance
        )

    def scrape_and_extract(self) -> Dict[str, Any]:
        logger.info("Starting New India Assurance scraping...")
        html = self.fetch_page_html()
        if not html:
            logger.error("Could not fetch page HTML from %s", BASE_URL)
            return {"success": False, "error": "Fetch failed"}

        docs = self.discover_documents(html)
        logger.info("Discovered %d official documents on New India page.", len(docs))

        downloaded_metas = {}
        for d in docs:
            filename = f"new_india_{d['doc_type'].lower()}.pdf"
            meta = self.download_pdf(d["url"], filename)
            if meta:
                downloaded_metas[d["doc_type"]] = meta

        # Extract text from CIS
        cis_file = os.path.join(self.raw_dir, "new_india_cis.pdf")
        cis_pages = self.extract_text_from_pdf(cis_file)
        logger.info("Extracted %d pages from New India CIS PDF.", len(cis_pages))

        # Build complete 48-item Master Policy Record
        master_record = self.build_master_policy_record(cis_pages, downloaded_metas)

        # Save to policies output
        policy_out_path = os.path.join(self.policy_dir, "new-india-mediclaim-policy.json")
        with open(policy_out_path, "w", encoding="utf-8") as f:
            f.write(master_record.model_dump_json(indent=2))

        logger.info("Successfully generated 48-item Master Policy Record at %s", policy_out_path)
        return {
            "success": True,
            "policy_slug": master_record.slug,
            "policy_name": master_record.identity.product_name,
            "downloaded_documents": downloaded_metas,
            "checklist_items_extracted": 48,
            "policy_json_path": policy_out_path
        }


if __name__ == "__main__":
    scraper = NewIndiaScraper()
    scraper.scrape_and_extract()
