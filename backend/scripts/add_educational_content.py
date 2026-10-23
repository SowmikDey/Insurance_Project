"""
One-shot script: appends 18 new glossary terms and 5 new learning modules
to GLOSSARY_TERMS_DATA / MODULES_DATA in educational_content.py, then
re-runs seed_educational_content() so the database is updated.

Run from the backend/ directory:
    python scripts/add_educational_content.py
"""
import sys
import os
import ast
import textwrap

# ---------------------------------------------------------------------------
# 18 new glossary entries
# ---------------------------------------------------------------------------
NEW_GLOSSARY_TERMS = [
    {
        "slug": "super-top-up",
        "term": "Super Top-Up Policy",
        "aliases": ["super topup", "aggregate deductible policy", "super top up health insurance"],
        "category": "Health",
        "what_does_it_mean": (
            "A Super Top-Up policy covers all hospitalisation expenses that collectively exceed a threshold "
            "(called the deductible) during an entire policy year. Unlike a plain Top-Up (which applies the "
            "deductible per claim), a Super Top-Up applies it once per year to the total of all claims combined."
        ),
        "why_does_it_matter": (
            "A Super Top-Up dramatically amplifies your health coverage at a fraction of the cost. A ₹20 Lakh "
            "Super Top-Up with a ₹5 Lakh deductible costs about ₹3,000–₹5,000 a year for a 30-year-old. "
            "Combined with a ₹5 Lakh base policy, you effectively have ₹25 Lakh total coverage."
        ),
        "financial_impact_example": (
            "Kavita has a ₹5 Lakh base policy and a ₹20 Lakh Super Top-Up with ₹5 Lakh deductible. She is "
            "hospitalised twice: ₹3 Lakh in April and ₹4 Lakh in September. Her base policy covers the April "
            "bill. The September bill brings her yearly total to ₹7 Lakh, crossing the ₹5 Lakh deductible — "
            "so the Super Top-Up pays ₹2 Lakh of the September bill."
        ),
        "trade_off_analysis": (
            "Super Top-Up is cost-efficient only when you already have a base policy to absorb the deductible. "
            "The deductible must be equal to or lower than your base cover to avoid out-of-pocket gaps. "
            "It does NOT work like a standalone policy for small claims."
        ),
        "watch_out_tips": (
            "Never confuse a Super Top-Up with a plain Top-Up. Plain Top-Up applies deductible per-claim; "
            "Super Top-Up applies once per year. Always match the deductible amount to your base policy's sum insured."
        ),
        "related_module_slug": "super-top-up-explained",
    },
    {
        "slug": "family-floater",
        "term": "Family Floater Policy",
        "aliases": ["floater plan", "family health plan", "family floater insurance"],
        "category": "Health",
        "what_does_it_mean": (
            "A single health insurance policy where one shared Sum Insured covers an entire family — spouse, "
            "children, and sometimes parents. Any family member can use all or part of the cover, but the total "
            "paid across all claims cannot exceed the Sum Insured in a year."
        ),
        "why_does_it_matter": (
            "A Family Floater is cheaper than buying separate individual policies. For a family of four, a ₹10 Lakh "
            "floater might cost ₹15,000/year whereas four individual ₹5 Lakh policies could cost ₹25,000+ combined."
        ),
        "financial_impact_example": (
            "Ravi buys a ₹10 Lakh Family Floater for himself, wife, and two children. His wife is hospitalised for "
            "₹4 Lakhs in June. Ravi undergoes surgery costing ₹7 Lakhs in October. Combined claims = ₹11 Lakhs, "
            "but cover is ₹10 Lakhs — Ravi pays ₹1 Lakh out of pocket."
        ),
        "trade_off_analysis": (
            "Floaters are economical for young families. However, including senior parents raises the premium "
            "significantly because it is based on the oldest member's age. For parents above 60, separate senior "
            "citizen policies are usually more cost-effective."
        ),
        "watch_out_tips": (
            "If one family member has a chronic illness and makes frequent claims, the shared cover can be rapidly "
            "depleted. Consider individual policies plus a floater, or a plan with unlimited restoration benefit."
        ),
        "related_module_slug": "family-floater-vs-individual",
    },
    {
        "slug": "insured-declared-value",
        "term": "Insured Declared Value (IDV)",
        "aliases": ["idv", "market value car", "vehicle declared value"],
        "category": "Motor",
        "what_does_it_mean": (
            "The Insured Declared Value (IDV) is the approximate current market value of your vehicle assigned by "
            "the insurer at policy issuance. It is the maximum amount you will receive if your vehicle is stolen "
            "or totally destroyed (total loss)."
        ),
        "why_does_it_matter": (
            "IDV directly determines your payout in theft or total-loss situations. Undervaluing IDV to save "
            "premium means a smaller payout if your vehicle is stolen. Overvaluing means an unnecessarily high premium."
        ),
        "financial_impact_example": (
            "Suresh's car has a market value of ₹8 Lakhs but the IDV was set at ₹6.5 Lakhs due to standard "
            "depreciation tables. When his car was stolen, he received ₹6.5 Lakhs — not ₹8 Lakhs."
        ),
        "trade_off_analysis": (
            "IDV decreases every year as the vehicle depreciates. For new cars (under 3 years), set IDV as close "
            "to actual market value as possible. IDV is negotiable within a ±10% range of the standard value."
        ),
        "watch_out_tips": (
            "Never blindly accept the lowest IDV offered to get a cheaper premium. For new or expensive cars, "
            "always insist on the maximum IDV within the allowable range."
        ),
        "related_module_slug": "motor-insurance-explained",
    },
    {
        "slug": "third-party-administrator",
        "term": "Third Party Administrator (TPA)",
        "aliases": ["tpa", "insurance tpa", "health tpa", "claims administrator"],
        "category": "Health",
        "what_does_it_mean": (
            "A TPA is a licensed intermediary company authorised by IRDAI that manages health insurance claims "
            "on behalf of the insurance company. TPAs verify pre-authorisation requests, manage network hospital "
            "cashless settlements, and process reimbursement claims."
        ),
        "why_does_it_matter": (
            "When you call the insurance helpline during hospitalisation, you are often speaking to the TPA, "
            "not the insurance company directly. The TPA's efficiency determines how fast your cashless "
            "authorisation is approved and how quickly reimbursement claims are processed."
        ),
        "financial_impact_example": (
            "Amit is hospitalised at a network hospital. The hospital's insurance desk sends a cashless "
            "pre-authorisation request to Medi Assist TPA. Medi Assist reviews and approves the amount within "
            "2–6 hours, allowing Amit to be admitted without paying upfront."
        ),
        "trade_off_analysis": (
            "Some insurers (like Star Health, Care Health) manage claims in-house without a TPA — this can mean "
            "faster processing. Others outsource to TPAs, adding one administrative layer but enabling larger "
            "network hospital coverage."
        ),
        "watch_out_tips": (
            "Know your TPA's name and helpline number BEFORE an emergency. Your insurance card will have the TPA "
            "name printed on it. Save the TPA's number in your phone the day you buy the policy."
        ),
        "related_module_slug": "understanding-health-insurance",
    },
    {
        "slug": "incurred-claim-ratio",
        "term": "Incurred Claim Ratio (ICR)",
        "aliases": ["icr", "loss ratio", "claim loss ratio"],
        "category": "General",
        "what_does_it_mean": (
            "ICR is the percentage of total premium collected by an insurer that was paid out as claims in a "
            "given financial year. ICR = (Total Claims Paid ÷ Total Premium Collected) × 100."
        ),
        "why_does_it_matter": (
            "ICR shows how fair an insurer is to policyholders. An ICR above 100% means the insurer is losing "
            "money and may tighten claim approvals. An ICR below 50% suggests the insurer may be aggressively "
            "rejecting valid claims."
        ),
        "financial_impact_example": (
            "If an insurer collected ₹1,000 Crore in health premiums and paid ₹800 Crore in claims, its ICR is "
            "80%. An ICR of 75–90% is considered healthy — financially stable and relatively fair to claimants."
        ),
        "trade_off_analysis": (
            "ICR and CSR together tell the full story. A high CSR (98%) with a very low ICR (45%) might mean "
            "the insurer settles claims but only small ones while rejecting large expensive ones. Look at both numbers."
        ),
        "watch_out_tips": (
            "IRDAI publishes ICR data annually in its insurance industry annual report. Always check ICR data "
            "from the official IRDAI report, not just insurer marketing materials."
        ),
        "official_reference_source": "https://www.irdai.gov.in",
        "related_module_slug": "how-to-choose-insurance-policy",
    },
    {
        "slug": "premium",
        "term": "Insurance Premium",
        "aliases": ["policy premium", "annual premium", "monthly premium", "insurance cost"],
        "category": "General",
        "what_does_it_mean": (
            "The premium is the amount you pay (monthly, quarterly, or annually) to the insurance company in "
            "exchange for coverage. It is calculated based on your age, health history, sum insured, policy "
            "features, and the insurer's risk assessment."
        ),
        "why_does_it_matter": (
            "The premium determines affordability, but choosing insurance solely on the cheapest premium is "
            "dangerous — cheaper premiums often hide larger exclusions, higher deductibles, or inferior claim "
            "settlement practices."
        ),
        "financial_impact_example": (
            "Priya (28, non-smoker) pays ₹8,000/year for a ₹10 Lakh health policy. If she waits until 40, "
            "the premium rises to ₹18,000–₹22,000/year, plus possible medical loading for any conditions "
            "developed in the interim."
        ),
        "trade_off_analysis": (
            "Buying early locks in lower premiums. Many insurers offer a 5–10% discount for 2 or 3-year policies. "
            "GST of 18% applies on all insurance premiums in India and is non-refundable even during free-look "
            "cancellation."
        ),
        "watch_out_tips": (
            "Compare premiums on a like-for-like basis: same sum insured, same sub-limits, same co-pay, and same "
            "room rent category. A ₹7,000 policy with 20% co-pay is costlier in practice than a ₹9,500 policy "
            "with no co-pay and no room rent cap."
        ),
        "related_module_slug": "what-is-insurance",
    },
    {
        "slug": "portability",
        "term": "Health Insurance Portability",
        "aliases": ["policy portability", "porting health insurance", "insurer switch"],
        "category": "Health",
        "what_does_it_mean": (
            "The right guaranteed by IRDAI that allows you to switch your health insurance policy from one "
            "insurer to another at renewal, without losing accumulated waiting period credits and No Claim Bonus "
            "earned under the old policy."
        ),
        "why_does_it_matter": (
            "Before IRDAI introduced portability, switching insurers meant restarting all waiting periods from "
            "scratch. With portability, your 3-year PED waiting period completed with Insurer A is credited to "
            "Insurer B — you don't wait another 3 years."
        ),
        "financial_impact_example": (
            "Kavita has been with ABC Health Insurance for 3 years and completed her 2-year PED waiting period "
            "for thyroid. She ports to XYZ Insurance. Under portability rules, XYZ must credit those 3 years — "
            "her thyroid is covered immediately, not after another 2-year wait."
        ),
        "trade_off_analysis": (
            "Portability preserves waiting periods but not necessarily the premium. The new insurer may charge "
            "higher premiums based on current age, health status, or claims history. NCB transfer depends on "
            "specific policy terms — confirm in writing before porting."
        ),
        "watch_out_tips": (
            "Apply for portability at least 45 days before your renewal date. Do NOT let your current policy "
            "lapse before the new policy is confirmed. The new insurer is legally obligated to accept port "
            "applications but may apply medical underwriting and premium loading."
        ),
        "related_module_slug": "insurance-portability-and-renewal",
    },
    {
        "slug": "sub-limit",
        "term": "Sub-Limit (Disease-Specific Cap)",
        "aliases": ["sub limits", "disease sublimit", "procedure cap", "treatment limit"],
        "category": "Health",
        "what_does_it_mean": (
            "A cap placed by the insurer on the maximum amount payable for a specific procedure, treatment, or "
            "disease category — even if your overall Sum Insured is much larger. It is one of the most dangerous "
            "hidden clauses in health insurance policies."
        ),
        "why_does_it_matter": (
            "You may have a ₹10 Lakh policy but find the insurer only pays ₹1.5 Lakh for knee replacement "
            "surgery because of a sub-limit, while the actual procedure costs ₹4 Lakhs. You must pay ₹2.5 Lakhs "
            "from your own pocket despite having a large policy."
        ),
        "financial_impact_example": (
            "Mohan has a ₹10 Lakh policy with a ₹2 Lakh sub-limit for cataract surgery. The surgery costs "
            "₹3.5 Lakhs. Despite ₹10 Lakhs insured, the insurer pays only ₹2 Lakhs. Mohan pays ₹1.5 Lakhs "
            "from savings."
        ),
        "trade_off_analysis": (
            "Policies without sub-limits are always preferred even if slightly more expensive. Modern IRDAI-compliant "
            "comprehensive policies (post-2023) are moving toward eliminating disease-specific sub-limits. Always "
            "read the benefits table in the policy wording document."
        ),
        "watch_out_tips": (
            "Common sub-limits to check: cataract surgery, dialysis, joint replacement, hernia repair, maternity "
            "expenses, and psychiatric treatment. If a policy has ANY disease sub-limit, treat it as a red flag."
        ),
        "related_module_slug": "deductibles-copayments-sublimits",
    },
    {
        "slug": "day-care-procedure",
        "term": "Day Care Procedure",
        "aliases": ["daycare treatment", "day care treatment", "outpatient procedure"],
        "category": "Health",
        "what_does_it_mean": (
            "A medical treatment or surgery that, thanks to modern technology, can be completed within a few "
            "hours and does NOT require a minimum 24-hour hospital admission — yet is still covered under "
            "health insurance."
        ),
        "why_does_it_matter": (
            "Traditional health insurance required a minimum 24-hour admission to make a claim. Modern policies "
            "cover hundreds of day-care procedures (chemotherapy, dialysis, cataract surgery, lithotripsy) done "
            "in hours, preventing denial of valid medical claims."
        ),
        "financial_impact_example": (
            "Sunita underwent cataract surgery in 2.5 hours at a network hospital. Bill: ₹35,000. Under her "
            "policy covering 540 day-care procedures, the cashless claim was approved and she paid nothing. "
            "10 years ago this would have been rejected for lack of 24-hour admission."
        ),
        "trade_off_analysis": (
            "The list of covered day-care procedures varies per insurer. Premium policies list 500–1,000+ "
            "procedures. Budget policies may list only 150–200. Fewer listed procedures means more potential "
            "rejections for modern medical treatments."
        ),
        "watch_out_tips": (
            "Ask the insurer for the complete Day Care Procedure list before buying. LASIK eye surgery, dental "
            "work (outside accidents), and cosmetic procedures are typically excluded even from comprehensive policies."
        ),
        "related_module_slug": "understanding-health-insurance",
    },
    {
        "slug": "domiciliary-hospitalization",
        "term": "Domiciliary Hospitalisation",
        "aliases": ["home hospitalization", "home treatment cover", "domiciliary treatment"],
        "category": "Health",
        "what_does_it_mean": (
            "Coverage for medical treatment taken at home when the patient's condition is so serious that "
            "movement to a hospital is not safe, OR when hospital beds are unavailable. The treatment must be "
            "certified by a qualified doctor and must ordinarily require hospitalisation."
        ),
        "why_does_it_matter": (
            "During COVID-19, lakhs of patients were treated at home due to hospital bed unavailability. "
            "Domiciliary cover was critical — it allowed claims for home nursing, oxygen concentrators, "
            "medicines, and doctor visits that would otherwise be entirely out-of-pocket."
        ),
        "financial_impact_example": (
            "Rajesh was diagnosed with COVID-19 requiring oxygen support but couldn't find a hospital bed. "
            "His insurer approved a domiciliary claim covering ₹45,000 in home nursing, oxygen concentrator "
            "rental, medicines, and telemedicine consultations over 12 days."
        ),
        "trade_off_analysis": (
            "Not all policies include domiciliary cover. Some cover it only for conditions lasting 3+ days at "
            "home. The benefit is more valuable in tier-2 cities where hospital infrastructure is limited. "
            "Verify the minimum duration requirement (typically 3 days)."
        ),
        "watch_out_tips": (
            "Domiciliary claims require a doctor's written certificate stating hospital admission was not "
            "feasible. Maintain detailed records of all at-home treatments, doctor visits, invoices, and "
            "prescriptions for reimbursement."
        ),
        "related_module_slug": "understanding-health-insurance",
    },
    {
        "slug": "critical-illness-cover",
        "term": "Critical Illness Cover",
        "aliases": ["ci cover", "critical illness policy", "ci insurance", "dread disease policy"],
        "category": "Health",
        "what_does_it_mean": (
            "A Critical Illness (CI) policy pays out a fixed lump sum when you are diagnosed with a specified "
            "life-threatening illness — such as cancer, first heart attack, stroke, organ failure, or kidney "
            "failure — regardless of actual medical expenses incurred."
        ),
        "why_does_it_matter": (
            "Unlike regular health insurance that reimburses hospital bills, CI insurance pays a fixed pre-agreed "
            "amount (e.g. ₹25 Lakhs) that you can use for ANY purpose: hospital bills, income replacement, "
            "home loan EMIs, or international treatment."
        ),
        "financial_impact_example": (
            "Arun is diagnosed with third-stage cancer. His ₹25 Lakh CI policy pays ₹25 Lakhs in one lump sum "
            "upon confirmed diagnosis. He uses ₹12 Lakhs for chemotherapy, ₹8 Lakhs to prepay his home loan, "
            "and keeps ₹5 Lakhs for living expenses while on medical leave."
        ),
        "trade_off_analysis": (
            "CI policies cover fewer conditions (typically 20–36 listed illnesses) but pay unconditionally upon "
            "diagnosis. Regular health insurance covers far more conditions but only reimburses actual expenses. "
            "Ideally, have both — regular health insurance plus a CI cover for catastrophic diagnoses."
        ),
        "watch_out_tips": (
            "Strictly read the definition of each covered illness. Many CI policies require you to 'survive "
            "30 days post-diagnosis' to receive the payout. Check the survival clause and the list of covered "
            "conditions very carefully before purchasing."
        ),
        "related_module_slug": "critical-illness-and-riders",
    },
    {
        "slug": "term-insurance",
        "term": "Term Life Insurance",
        "aliases": ["term plan", "pure life cover", "term policy", "life cover"],
        "category": "Life",
        "what_does_it_mean": (
            "Term insurance is the simplest, most affordable form of life insurance that pays a fixed death "
            "benefit (Sum Assured) to your nominee if you pass away during the policy term. It has NO investment "
            "or savings component — it is pure, 100% risk protection."
        ),
        "why_does_it_matter": (
            "A ₹1 Crore term insurance policy costs just ₹700–₹1,200/month for a 30-year-old non-smoker. If "
            "the insured dies during the term, the family gets ₹1 Crore — enough to replace 10–15 years of the "
            "breadwinner's income."
        ),
        "financial_impact_example": (
            "Vijay (30, earning ₹60,000/month) buys a ₹1 Crore term plan for ₹850/month. He passes away in a "
            "road accident at 42. His family receives ₹1 Crore tax-free. Invested at 6% returns, this generates "
            "₹6 Lakh/year — replacing his monthly income for decades."
        ),
        "trade_off_analysis": (
            "Term insurance pays nothing if you survive the policy term (unlike endowment/ULIP plans). This is "
            "the correct design — term insurance is for protection, not savings. Mixing insurance with investment "
            "results in both poor protection and poor returns."
        ),
        "watch_out_tips": (
            "Never buy a term plan where total cover is less than 10× your annual income. Avoid 'Return of "
            "Premium' (TROP) variants — they charge 2–3× the normal premium for marginal benefit. Always buy "
            "a pure term plan online directly from the insurer's website for the lowest premium."
        ),
        "related_module_slug": "term-life-vs-investment-schemes",
    },
    {
        "slug": "personal-accident-cover",
        "term": "Personal Accident (PA) Cover",
        "aliases": ["pa cover", "accident insurance", "personal accident policy"],
        "category": "General",
        "what_does_it_mean": (
            "A PA policy provides financial compensation if you suffer an accidental injury, permanent disability "
            "(partial or total), or accidental death. Benefits are paid as a lump sum or structured compensation, "
            "regardless of your other insurance policies."
        ),
        "why_does_it_matter": (
            "Road accidents are among the leading causes of death and disability in India. A PA policy supplements "
            "your health insurance (which covers hospitalization costs) by also paying for income loss, permanent "
            "disability compensation, and accidental death — which health insurance does NOT cover."
        ),
        "financial_impact_example": (
            "Ravi, a delivery executive, meets with a road accident and loses his right hand. His PA policy covers: "
            "₹5 Lakhs for permanent partial disability (loss of limb = 50% payout of ₹10 Lakh sum), ₹50,000 for "
            "hospitalisation, and ₹3,000/week for 26 weeks of temporary disability income."
        ),
        "trade_off_analysis": (
            "PA policies are very affordable (₹2,000–₹5,000/year for ₹25 Lakh cover) because accidents are "
            "statistically less frequent than illness. However, they cover ONLY accidents — not diseases or "
            "natural death. They complement, not replace, health and term insurance."
        ),
        "watch_out_tips": (
            "Check whether the PA policy covers both road and non-road accidents (workplace accidents, slips, "
            "sports injuries). Also verify if it covers partial disability, not just total permanent disability "
            "or death, since partial disabilities are far more common."
        ),
        "related_module_slug": "what-is-insurance",
    },
    {
        "slug": "insurance-ombudsman",
        "term": "Insurance Ombudsman (Bima Lokpal)",
        "aliases": ["ombudsman", "insurance grievance officer", "insurance complaint authority", "bima lokpal"],
        "category": "General",
        "what_does_it_mean": (
            "The Insurance Ombudsman (Bima Lokpal) is an independent, free grievance redressal authority "
            "established by the Government of India under IRDAI. It resolves disputes between policyholders "
            "and insurance companies — including claim rejections, premium disputes, and policy cancellations — "
            "at absolutely no cost to the consumer."
        ),
        "why_does_it_matter": (
            "If your insurer unfairly rejects your claim or delays settlement beyond 30 days, you can approach "
            "the Insurance Ombudsman. Cases are resolved within 3 months. The insurer must comply with the "
            "Ombudsman's award. It is faster and cheaper than consumer court."
        ),
        "financial_impact_example": (
            "Lakshmi's health insurer rejected her ₹3.2 Lakh hospitalisation claim citing 'non-disclosure'. "
            "She filed a complaint with the Insurance Ombudsman of Chennai. After review, the Ombudsman ordered "
            "the insurer to pay ₹2.8 Lakhs within 30 days."
        ),
        "trade_off_analysis": (
            "The Ombudsman can adjudicate disputes up to ₹50 Lakhs in value (as of 2024). For larger disputes, "
            "the Consumer Disputes Redressal Commission (Consumer Court) is the appropriate forum. There are "
            "17 Ombudsman offices across major Indian cities."
        ),
        "watch_out_tips": (
            "File a complaint with the Ombudsman only after exhausting the insurer's internal grievance mechanism "
            "(write to the Grievance Officer and wait 15–30 days). Maintain a grievance reference number from "
            "the insurer before escalating to the Ombudsman."
        ),
        "official_reference_source": "https://cioins.co.in",
        "related_module_slug": "claim-filing-and-rejection",
    },
    {
        "slug": "moratorium-period",
        "term": "Moratorium Period (8-Year Rule)",
        "aliases": ["moratorium", "irdai 8 year rule", "non-contestability period"],
        "category": "Health",
        "what_does_it_mean": (
            "Under IRDAI rules, after a health insurance policy has been continuously in force for 8 years, "
            "the insurer CANNOT reject any claim on the grounds of non-disclosure or misrepresentation of "
            "Pre-Existing Diseases — unless the insurer can prove outright fraud."
        ),
        "why_does_it_matter": (
            "This is one of the strongest consumer protections in Indian insurance. Even if you forgot to "
            "disclose a minor health condition, after 8 continuous years the insurer loses the legal right "
            "to reject claims based on that non-disclosure (except for deliberate fraud)."
        ),
        "financial_impact_example": (
            "Ramesh bought a policy in 2014 without disclosing a minor thyroid condition he was unaware of. "
            "In 2023 (after 9 years), he filed a ₹5.5 Lakh claim for thyroid cancer. The insurer attempted "
            "rejection based on non-disclosure but could not — the 8-year moratorium had passed."
        ),
        "trade_off_analysis": (
            "The moratorium does NOT protect fraud or deliberate concealment. If you knowingly hid a heart "
            "condition or diabetes to avoid premium loading, the insurer can still reject claims and cancel "
            "the policy. Always disclose in good faith."
        ),
        "watch_out_tips": (
            "Maintain continuous renewals without any lapse to benefit from the moratorium. A policy lapse "
            "may reset the clock. Always renew on time — set up auto-payment reminders for your renewal date."
        ),
        "official_reference_source": "https://www.irdai.gov.in",
        "related_module_slug": "waiting-periods-ped-exclusions",
    },
    {
        "slug": "ayushman-bharat-pmjay",
        "term": "Ayushman Bharat – PM-JAY",
        "aliases": ["pmjay", "ayushman bharat", "pradhan mantri jan arogya yojana", "golden card scheme"],
        "category": "Health",
        "what_does_it_mean": (
            "Ayushman Bharat – PM-JAY is India's flagship government health insurance scheme that provides "
            "free hospitalisation coverage of up to ₹5 Lakh per year per family to economically vulnerable "
            "households identified through the SECC database."
        ),
        "why_does_it_matter": (
            "PM-JAY is the world's largest government-funded health insurance scheme, covering over 55 Crore "
            "beneficiaries. Covered families can access cashless treatment at 28,000+ empanelled hospitals "
            "across India without any premium payment."
        ),
        "financial_impact_example": (
            "Savitribai from a rural Maharashtra BPL family undergoes heart bypass surgery costing ₹3.5 Lakhs "
            "at a district empanelled hospital. Under PM-JAY, the entire surgery is cashless and free — she "
            "pays nothing. Without PM-JAY, this would have required selling family land or livestock."
        ),
        "trade_off_analysis": (
            "PM-JAY covers only hospitalisations — no OPD, no medicines, no diagnostics outside hospital "
            "admission. Coverage is limited to ₹5 Lakh per family per year. For middle-class families not "
            "eligible for PM-JAY, private health insurance with higher Sum Insured remains necessary."
        ),
        "watch_out_tips": (
            "Check eligibility using the official PM-JAY portal (pmjay.gov.in). Ayushman cards are free and "
            "obtained from Common Service Centres (CSCs). Beware of agents charging money to 'register' for "
            "PM-JAY — it is completely FREE."
        ),
        "official_reference_source": "https://pmjay.gov.in",
        "related_module_slug": "what-is-insurance",
    },
    {
        "slug": "uin-number",
        "term": "UIN – Unique Identification Number",
        "aliases": ["uin", "policy uin", "irdai uin", "product uin"],
        "category": "General",
        "what_does_it_mean": (
            "A UIN (Unique Identification Number) is a unique alphanumeric code assigned by IRDAI to every "
            "officially approved insurance product sold in India. Every legitimate health, life, motor, or "
            "travel policy must carry a valid UIN in its policy document."
        ),
        "why_does_it_matter": (
            "The UIN confirms the insurance product is genuine, IRDAI-approved, and legally permitted to be "
            "sold in India. Checking the UIN on IRDAI's registry protects you from fraudulent insurance "
            "products sold by unlicensed agents or fake insurers."
        ),
        "financial_impact_example": (
            "Meera was sold a 'health insurance plan' by an individual agent. When she tried to file a claim, "
            "the hospital couldn't verify the insurer. Her policy document had no valid UIN. The 'policy' was "
            "fake and her ₹12,000 annual premium was gone."
        ),
        "trade_off_analysis": (
            "All IRDAI-registered products must quote their UIN on the policy certificate. If a policy document, "
            "brochure, or sales pitch does not mention a UIN, it is a major red flag regardless of how "
            "attractive the coverage appears."
        ),
        "watch_out_tips": (
            "Cross-check the UIN on IRDAI's product registry portal at irdai.gov.in. A valid UIN format looks "
            "like 'IRDAI/HLT/NICHI/P-H/V.I/102/2022-23'. A valid UIN means the product has regulatory oversight."
        ),
        "official_reference_source": "https://www.irdai.gov.in",
        "related_module_slug": "spotting-misleading-sales-tactics",
    },
    {
        "slug": "policy-lapse",
        "term": "Policy Lapse",
        "aliases": ["lapsed policy", "policy expiry", "lapse in coverage", "policy cancellation"],
        "category": "General",
        "what_does_it_mean": (
            "A policy lapse occurs when you fail to pay the renewal premium by the due date (including any "
            "grace period given by the insurer), causing the insurance contract to terminate. A lapsed policy "
            "offers no coverage — any claim filed after a lapse is automatically rejected."
        ),
        "why_does_it_matter": (
            "A lapsed health policy is catastrophic in two ways: (1) You have zero coverage during the lapse "
            "period, and (2) When you reinstate or buy a new policy, all waiting periods reset from Day 1 — "
            "your previously completed PED waiting period is lost."
        ),
        "financial_impact_example": (
            "Deepak forgot to renew his 4-year-old health policy (he had completed his 2-year PED waiting "
            "period). The policy lapsed on March 31. On April 14, he was hospitalised for a cardiac event "
            "costing ₹4.2 Lakhs. The claim was rejected — no active policy. He paid entirely from savings."
        ),
        "trade_off_analysis": (
            "Most insurers allow a 15–30 day grace period after the premium due date. Beyond that, the policy "
            "lapses. Some insurers allow revival within 90–180 days with a fresh medical examination and "
            "possible premium loading."
        ),
        "watch_out_tips": (
            "Set an auto-debit mandate for all insurance renewals. Treat insurance renewal as non-negotiable "
            "as your EMI. Even a 31-day lapse can cost you years of accumulated waiting period credits and "
            "leave you uncovered during that gap."
        ),
        "related_module_slug": "insurance-portability-and-renewal",
    },
]

# ---------------------------------------------------------------------------
# 5 new learning modules
# ---------------------------------------------------------------------------
NEW_MODULES = [
    {
        "slug": "super-top-up-explained",
        "order_index": 11,
        "title": "Super Top-Up: Get ₹25 Lakh Cover for ₹5,000 a Year",
        "subtitle": "How combining a base policy with a Super Top-Up is the smartest hack in Indian health insurance.",
        "category": "Health",
        "estimated_minutes": 8,
        "level": "Intermediate",
        "concept_explanation": textwrap.dedent("""
            If you have ever wondered how people get ₹20 Lakh or ₹25 Lakh health coverage without paying a huge premium, the answer is almost always a **Super Top-Up policy**.

            **How it works — the core idea:**
            A Super Top-Up policy has a 'deductible' — a minimum threshold of claims you must cross in a year before the top-up kicks in. Unlike a plain Top-Up (which applies the deductible *per claim*), a Super Top-Up applies the deductible once to the **total of all claims in the entire year**.

            **The cost-efficient combination:**
            | Layer | Cover | Annual Premium (age 30) |
            |---|---|---|
            | Base Health Policy | ₹5 Lakh | ₹8,000/year |
            | Super Top-Up (₹5L deductible) | ₹20 Lakh | ₹3,000–₹4,500/year |
            | **Total effective cover** | **₹25 Lakh** | **₹11,000–₹12,500/year** |

            Buying a standalone ₹25 Lakh health policy would cost ₹22,000–₹28,000/year. The combo costs less than half!

            **Key rule:** The Super Top-Up deductible must equal or be lower than your base policy's sum insured. A mismatch creates an uncovered gap you must pay from your own pocket.
        """),
        "why_it_matters": (
            "Medical inflation in India runs at 12–14% annually. A cardiac bypass surgery that cost ₹3.5 Lakhs "
            "in 2015 costs ₹6–8 Lakhs in 2025. A ₹5 Lakh standalone policy is dangerously inadequate for "
            "serious illnesses. The Super Top-Up combo gets you meaningful coverage without breaking the bank."
        ),
        "practical_indian_example": (
            "Anand (32, Bengaluru, IT professional) has a ₹5 Lakh employer group policy. He adds a personal "
            "₹20 Lakh Super Top-Up (₹5 Lakh deductible) for ₹3,800/year. When he undergoes cardiac angioplasty "
            "costing ₹8.5 Lakhs, his employer policy covers ₹5 Lakhs and the Super Top-Up pays ₹3.5 Lakhs. "
            "Total out-of-pocket cost: ₹0. Total personal premium paid: ₹3,800/year."
        ),
        "common_mistakes": [
            "Buying a Super Top-Up without a base policy — you end up paying the full deductible from pocket.",
            "Choosing a higher deductible than your base policy's sum insured, creating an uncovered gap.",
            "Confusing Super Top-Up with plain Top-Up — the 'per-claim vs. yearly aggregate' difference is critical.",
            "Not checking if the Super Top-Up insurer's network hospital list overlaps with your base policy's network.",
        ],
        "key_takeaways": [
            "Super Top-Up applies its deductible once to ALL claims in the year, not per individual claim.",
            "Base policy sum insured must equal the Super Top-Up deductible to avoid coverage gaps.",
            "The combo (base + Super Top-Up) costs 40–60% less than buying equivalent standalone cover.",
            "Ideal strategy: ₹5 Lakh base + ₹20–25 Lakh Super Top-Up for comprehensive affordable coverage.",
        ],
        "official_source_links": [
            {"title": "IRDAI Health Insurance Guidelines", "url": "https://www.irdai.gov.in"},
            {"title": "IRDAI Consumer Education Portal", "url": "https://policyholder.gov.in"},
        ],
        "quizzes": [
            {
                "order_index": 1,
                "question": "Rohan has a ₹5 Lakh base policy and a Super Top-Up with ₹5 Lakh deductible. He makes three claims in a year: ₹2L, ₹2L, and ₹3L. How much does the Super Top-Up pay?",
                "options": [
                    "₹0 — the Super Top-Up doesn't cover anything",
                    "₹2 Lakh — because the total (₹7L) exceeds the ₹5L deductible by ₹2L",
                    "₹7 Lakh — the Super Top-Up pays everything",
                    "₹3 Lakh — it only pays on the largest single claim",
                ],
                "correct_option_index": 1,
                "explanation": (
                    "The Super Top-Up's deductible is applied to the TOTAL yearly claims. Total = ₹7L. "
                    "Deductible = ₹5L. The Super Top-Up pays ₹7L − ₹5L = ₹2L."
                ),
            },
            {
                "order_index": 2,
                "question": "Which of these is the main advantage of a Super Top-Up over a plain Top-Up?",
                "options": [
                    "Super Top-Up has lower premiums because it covers fewer conditions",
                    "Super Top-Up applies the deductible once to all yearly claims combined, not per claim",
                    "Super Top-Up doesn't require a base policy",
                    "Super Top-Up automatically renews without any waiting period",
                ],
                "correct_option_index": 1,
                "explanation": (
                    "The aggregate deductible (per year, not per claim) is the defining feature of a Super Top-Up, "
                    "making it far more useful than a plain Top-Up when multiple hospitalizations occur in a year."
                ),
            },
        ],
    },
    {
        "slug": "family-floater-vs-individual",
        "order_index": 12,
        "title": "Family Floater vs. Individual Policies: Which Protects Better?",
        "subtitle": "Understanding when shared cover is smart and when it becomes a dangerous gamble.",
        "category": "Health",
        "estimated_minutes": 7,
        "level": "Intermediate",
        "concept_explanation": textwrap.dedent("""
            **Family Floater:** One policy, one shared Sum Insured, entire family covered. Any family member can use any portion of the cover in a year.

            **Individual Policy:** Each person has their own dedicated Sum Insured. Claims by one person don't reduce cover available to another.

            **When Family Floater makes sense:**
            - Young nuclear family (ages 25–45) with no major health conditions
            - Budget-conscious buyers wanting lower combined premium
            - Families where simultaneous hospitalisations are statistically unlikely

            **When Individual Policies make more sense:**
            - Including parents above 55 in a floater raises everyone's premium significantly
            - A family member with a chronic illness (diabetes, hypertension) will exhaust shared cover
            - Multiple simultaneous hospitalisations (e.g. accident) could exhaust floater cover instantly

            **The Premium Impact of Age:**
            In a floater, the premium is calculated based on the **oldest member's age**. Adding a 62-year-old parent to a young family's floater can **double the premium** overnight.

            **The Smart Approach:**
            Buy a floater for the young nuclear family. Buy separate individual senior citizen policies for parents. Add a Super Top-Up layer for everyone.
        """),
        "why_it_matters": (
            "Making the wrong choice between floater and individual can either leave you paying far too much "
            "in premiums or leave family members exposed during a crisis when shared cover is already exhausted."
        ),
        "practical_indian_example": (
            "Meera and her husband (both 34) have two children (6 and 9) and her parents (both 64). Option A: "
            "One family floater for all 6 = ₹42,000/year (premium driven by 64-year-old parents). Option B: "
            "₹10L floater for the 4 young members (₹14,500/year) + two separate senior policies for parents "
            "(₹28,000/year combined) = ₹42,500 total but FAR better protection with no risk of parents' "
            "frequent claims exhausting children's cover."
        ),
        "common_mistakes": [
            "Adding senior parents to a young family's floater without considering the premium and claim impact.",
            "Buying only ₹5 Lakh floater for 4–5 family members — exhaustion risk is very high.",
            "Assuming family floater is always cheaper — for families with elderly members, it often is not.",
            "Not adding a restoration benefit to a floater — essential to refill cover if it gets exhausted mid-year.",
        ],
        "key_takeaways": [
            "Family floater = shared pool; individual = dedicated cover. Shared pools deplete on heavy use.",
            "Premium in a floater is based on the oldest member — adding elderly parents can be very expensive.",
            "For young nuclear families without chronic illness, floaters are cost-effective.",
            "Always add a Super Top-Up over a floater base for genuinely large coverage at low cost.",
        ],
        "official_source_links": [
            {"title": "IRDAI Master Circular on Health Insurance 2024", "url": "https://www.irdai.gov.in"},
        ],
        "quizzes": [
            {
                "order_index": 1,
                "question": "Deepa (32) wants to add her father (67) to her ₹10 Lakh family floater. What is the PRIMARY risk of doing this?",
                "options": [
                    "IRDAI prohibits adding parents above 60 to family floaters",
                    "The premium will be based on her father's age (67), significantly increasing costs, and his frequent claims could exhaust cover for Deepa's children",
                    "Her father cannot use cashless facilities in a family floater",
                    "Family floaters only allow 3 members maximum by law",
                ],
                "correct_option_index": 1,
                "explanation": (
                    "The oldest member's age sets the premium rate, and a senior citizen's frequent claims "
                    "risk depleting the shared Sum Insured, leaving other family members under-covered."
                ),
            },
        ],
    },
    {
        "slug": "travel-insurance-complete-guide",
        "order_index": 13,
        "title": "Travel Insurance: Why Skipping It on Your Next Trip Is Risky",
        "subtitle": "Medical emergencies abroad, trip cancellations, and baggage loss — what travel insurance actually covers.",
        "category": "Travel",
        "estimated_minutes": 9,
        "level": "Beginner",
        "concept_explanation": textwrap.dedent("""
            Travel insurance is a short-term, trip-specific policy that covers a range of financial losses that can occur while travelling — domestically or internationally. It is one of the most underutilised insurance products in India despite being one of the cheapest.

            **What Travel Insurance Covers (Key Sections):**

            **1. Emergency Medical Expenses (Abroad)**
            Healthcare costs in countries like the USA, UK, or Singapore are 20–50× higher than India. A simple appendicitis surgery in the USA costs ₹30–₹50 Lakhs. Your domestic health insurance does NOT cover international treatment. Travel insurance pays for emergency hospitalisation, surgery, ambulance, and evacuation.

            **2. Trip Cancellation & Interruption**
            If you must cancel a non-refundable ₹2 Lakh flight + hotel booking due to sudden illness or a family emergency, travel insurance reimburses the non-refundable losses.

            **3. Baggage Loss & Delay**
            If your checked baggage is lost, delayed, or stolen, travel insurance pays up to a fixed limit (typically USD 500–1,000) for replacement of essentials and lost items.

            **4. Passport Loss**
            Emergency assistance and expenses for replacing a lost passport abroad.

            **5. Flight Delay Compensation**
            If your flight is delayed more than 6–12 hours, daily allowances are paid.

            **6. Personal Liability**
            If you accidentally injure someone or damage property in a foreign country, travel insurance covers legal costs.

            **Cost:** For a 10-day international trip, a comprehensive travel policy costs ₹800–₹2,500 — a tiny fraction of any potential loss.
        """),
        "why_it_matters": (
            "A single medical emergency in the USA, Europe, or UAE can cost ₹20 Lakhs to ₹1 Crore — amounts "
            "that can wipe out a lifetime of savings. Many Schengen visa applications for Europe legally REQUIRE "
            "proof of travel insurance with minimum EUR 30,000 (₹27 Lakh) medical cover."
        ),
        "practical_indian_example": (
            "Vikram (38, Hyderabad) travelled to Dubai for a week without travel insurance to save ₹900. On "
            "Day 3, he had a severe asthma attack requiring emergency hospitalisation for 2 days. The UAE hospital "
            "bill: AED 28,000 (≈₹6.5 Lakhs). Vikram had to make an emergency call home for fund transfer. "
            "A ₹900 travel policy would have covered every rupee of this bill."
        ),
        "common_mistakes": [
            "Assuming domestic health insurance covers international medical emergencies — it does NOT.",
            "Buying travel insurance with inadequate medical cover (less than USD 100,000 for international trips).",
            "Not reading the 'pre-existing disease' exclusion — most travel policies don't cover PED-related emergencies abroad.",
            "Skipping travel insurance for short trips or domestic travel (domestic travel insurance is surprisingly cheap and useful).",
        ],
        "key_takeaways": [
            "Your Indian health insurance does NOT cover medical emergencies abroad — travel insurance does.",
            "For Schengen (Europe) visas, EUR 30,000 medical cover travel insurance is legally mandatory.",
            "A 10-day international travel policy costs ₹800–₹2,500 — always worth buying.",
            "Read the PED exclusion clause — most travel policies exclude emergency hospitalisation caused by declared pre-existing conditions.",
        ],
        "official_source_links": [
            {"title": "IRDAI on Travel Insurance", "url": "https://www.irdai.gov.in"},
            {"title": "IRDAI Consumer Education Portal", "url": "https://policyholder.gov.in"},
        ],
        "quizzes": [
            {
                "order_index": 1,
                "question": "Does your Indian health insurance policy cover a medical emergency that occurs in London (UK)?",
                "options": [
                    "Yes, Indian health insurance covers emergencies worldwide",
                    "No, Indian health insurance is valid only within India — you need separate travel insurance for international cover",
                    "Yes, if you have a policy with more than ₹10 Lakh sum insured",
                    "Yes, all IRDAI-regulated policies cover emergencies in Commonwealth countries",
                ],
                "correct_option_index": 1,
                "explanation": (
                    "Standard Indian health insurance policies are valid ONLY within India. Medical emergencies "
                    "abroad are NOT covered. Travel insurance (or a specific international health plan) is "
                    "required for overseas coverage."
                ),
            },
            {
                "order_index": 2,
                "question": "Which of these is NOT typically covered under a standard international travel insurance policy?",
                "options": [
                    "Emergency hospitalisation after an accident abroad",
                    "Loss of checked baggage by the airline",
                    "Cosmetic dental surgery you planned before the trip",
                    "Trip cancellation due to sudden serious illness",
                ],
                "correct_option_index": 2,
                "explanation": (
                    "Planned elective procedures (like cosmetic dentistry) are excluded. Travel insurance covers "
                    "UNEXPECTED emergencies and accidents, not pre-planned medical treatments."
                ),
            },
        ],
    },
    {
        "slug": "critical-illness-and-riders",
        "order_index": 14,
        "title": "Critical Illness Insurance & Riders: The Lump-Sum Safety Net",
        "subtitle": "Why a cancer or heart attack diagnosis needs more than regular health insurance.",
        "category": "Health",
        "estimated_minutes": 8,
        "level": "Intermediate",
        "concept_explanation": textwrap.dedent("""
            When a life-altering illness strikes — cancer, heart attack, stroke, kidney failure — the financial impact goes far beyond hospital bills. Consider what happens:

            - **Income stops:** You or your spouse may be unable to work for 6–18 months.
            - **Ongoing treatment costs:** Chemotherapy cycles, radiation, physiotherapy — these continue for months.
            - **EMIs don't pause:** Home loan, car loan, children's school fees continue regardless.
            - **Lifestyle adjustments:** Dietary changes, medical equipment, nursing care at home.

            Regular health insurance reimburses only the hospitalisation bills. It does NOT replace lost income or cover the cascading financial impact of a serious illness.

            **Critical Illness (CI) Policy — How It Works:**
            On diagnosis of any of the listed illnesses (typically 20–36 conditions), the insurer pays the **entire sum assured as a tax-free lump sum** — regardless of actual expenses incurred. You can use the money for anything.

            **Common Covered Conditions:**
            Cancer (all stages), First Heart Attack, Stroke with permanent symptoms, Kidney Failure, Major Organ Transplant, Coronary Artery Bypass Graft, Paralysis, Multiple Sclerosis, Motor Neuron Disease

            **CI as a Rider vs. Standalone Policy:**
            - **Rider:** Added to a term life or health policy at lower cost. Coverage terminates if the base policy ends.
            - **Standalone:** Independent CI policy. More flexible, higher cover, portable.

            **The 30-Day Survival Clause:**
            Most CI policies require you to survive 30 days after the diagnosis event to receive the payout. This protects insurers from immediate large payouts on terminal diagnoses.
        """),
        "why_it_matters": (
            "In India, 1 in 10 adults will develop cancer in their lifetime. Heart disease is the leading cause "
            "of death. Treatment costs for cancer can range from ₹5 Lakhs to ₹50 Lakhs over 2–3 years. "
            "During treatment, income often drops to zero. CI insurance bridges this financial catastrophe."
        ),
        "practical_indian_example": (
            "Arun (42, Mumbai) is diagnosed with Stage 2 colon cancer. He has a ₹10 Lakh regular health policy "
            "and a ₹25 Lakh CI policy. The health policy covers surgery and hospitalisation (₹8 Lakhs). "
            "The CI policy pays ₹25 Lakhs as a lump sum. Arun uses ₹12 Lakhs for chemotherapy cycles (not all "
            "covered by health insurance), ₹6 Lakhs to prepay his home loan, and ₹7 Lakhs as income replacement "
            "while on medical leave for 14 months."
        ),
        "common_mistakes": [
            "Assuming regular health insurance covers all financial impact of a critical illness — it only covers hospitalisation bills.",
            "Not reading which stage of cancer is covered — some CI policies exclude early-stage (Stage 1) cancers.",
            "Missing the 30-day survival clause — the insured must survive 30 days post-event to receive payout.",
            "Buying insufficient CI cover — ₹10 Lakh is often inadequate; ₹25–₹50 Lakh is recommended.",
        ],
        "key_takeaways": [
            "CI insurance pays a LUMP SUM on diagnosis — not just hospital bills. You use the money as you choose.",
            "CI complements (doesn't replace) regular health insurance.",
            "Most CI policies have a 30-day survival clause post-diagnosis for the lump sum to be payable.",
            "A standalone CI policy of ₹25–₹50 Lakh is recommended alongside your base health cover.",
        ],
        "official_source_links": [
            {"title": "IRDAI Health Insurance Guidelines", "url": "https://www.irdai.gov.in"},
            {"title": "National Cancer Grid India", "url": "https://www.tmc.gov.in"},
        ],
        "quizzes": [
            {
                "order_index": 1,
                "question": "If you have a ₹10 Lakh health insurance policy and a ₹25 Lakh critical illness policy, and you are diagnosed with cancer with total treatment costs of ₹15 Lakhs, how much does the CI policy pay?",
                "options": [
                    "₹5 Lakh — only the amount not covered by health insurance",
                    "₹25 Lakh — the full sum assured, regardless of actual treatment costs",
                    "₹15 Lakh — the exact treatment cost",
                    "₹0 — because health insurance already covers the treatment",
                ],
                "correct_option_index": 1,
                "explanation": (
                    "Critical Illness policies pay the FULL sum assured as a lump sum upon diagnosis — "
                    "completely independently of what other policies pay or what the actual bills are."
                ),
            },
            {
                "order_index": 2,
                "question": "What does the '30-day survival clause' in a Critical Illness policy mean?",
                "options": [
                    "You must survive 30 days after buying the policy before CI cover begins",
                    "The insurer takes 30 days to process the payment after your claim is filed",
                    "You must survive for 30 days after the diagnosis date to be eligible for the CI payout",
                    "The CI policy lapses if you don't file a claim within 30 days of diagnosis",
                ],
                "correct_option_index": 2,
                "explanation": (
                    "Most CI policies require the policyholder to survive 30 days post-diagnosis as a "
                    "pre-condition for receiving the lump sum payout. This is one of the most important "
                    "clauses to check before purchasing a CI policy."
                ),
            },
        ],
    },
    {
        "slug": "insurance-portability-and-renewal",
        "order_index": 15,
        "title": "Health Insurance Portability & Renewal: Never Lose Your Benefits",
        "subtitle": "How to switch insurers without starting over — and why continuous renewal is non-negotiable.",
        "category": "Consumer Protection",
        "estimated_minutes": 7,
        "level": "Intermediate",
        "concept_explanation": textwrap.dedent("""
            **What is Portability?**
            IRDAI's portability rules (2011, updated 2024) give you the legal right to move your health insurance policy from one insurer to another at renewal — **without losing the waiting period credits you have already completed.**

            This means: If you've been with Insurer A for 3 years and completed a 2-year PED waiting period for your thyroid condition, moving to Insurer B on porting means Insurer B MUST credit you those 3 years. Your thyroid is covered from Day 1 at the new insurer.

            **What Gets Ported:**
            ✅ Completed waiting period credit (all types — initial, PED, specific illness)
            ✅ Continuity of No Claim Bonus (NCB) — to the extent applicable
            ❌ Premium rate is NOT locked — new insurer prices based on current age and health
            ❌ Policy-specific benefits (like specific hospital cashback) may not transfer

            **The Portability Process:**
            1. Apply to new insurer at least **45 days** before renewal
            2. New insurer submits portability request to old insurer on IRDAI's portal
            3. Old insurer provides claim history within 7 working days
            4. New insurer underwrites and offers a quote
            5. You accept, pay new premium, and get new policy — seamlessly

            **Why Continuous Renewal Matters:**
            A lapsed policy = waiting periods reset to zero. Even a 31-day gap eliminates years of accumulated benefits. Set auto-debit for every policy renewal. Treat it like your SIP.

            **The 8-Year Moratorium:**
            After 8 continuous years with any combination of insurers (porting is counted as continuous), no insurer can reject claims for non-disclosure of PED — except proven fraud.
        """),
        "why_it_matters": (
            "Many people stay with an insurer that provides poor service simply because they fear losing their "
            "waiting period credits. IRDAI portability gives you the power to switch without penalty. "
            "Conversely, a policy lapse — even brief — can wipe out years of protection built through "
            "continuous renewals."
        ),
        "practical_indian_example": (
            "Sanjana (36, Pune) has been with New India Assurance for 4 years. She completed her 2-year "
            "thyroid PED waiting period and built ₹5 Lakh NCB. She is unhappy with claim rejections and "
            "poor network hospitals. She ports to Niva Bupa (Bupa India) 45 days before renewal. IRDAI rules "
            "mandate Niva Bupa credits her 4 years of continuity. She gets: thyroid covered from Day 1, "
            "NCB credited, better hospital network. She starts fresh only on the new policy's specific terms "
            "— not the waiting period clock."
        ),
        "common_mistakes": [
            "Waiting until the last moment (less than 45 days before renewal) to apply for portability — this can cause the porting to fail.",
            "Letting the old policy lapse before the new policy is confirmed — creates a dangerous coverage gap.",
            "Assuming the new insurer must match the old premium — they will price based on current age and health.",
            "Not getting the porting confirmation and waiting period credits in writing before cancelling old policy.",
        ],
        "key_takeaways": [
            "IRDAI portability lets you switch insurers at renewal without losing completed waiting period credits.",
            "Apply for portability at least 45 days before your renewal date.",
            "Never let your current policy lapse before the new policy is active.",
            "After 8 continuous years (including ported years), the moratorium protects you from PED-based rejections.",
        ],
        "official_source_links": [
            {"title": "IRDAI Portability Guidelines", "url": "https://www.irdai.gov.in"},
            {"title": "IRDAI Consumer Portal on Portability", "url": "https://policyholder.gov.in"},
        ],
        "quizzes": [
            {
                "order_index": 1,
                "question": "Rahul has completed 3 years with Insurer A and ports to Insurer B. What happens to his 2-year PED waiting period for diabetes that he completed with Insurer A?",
                "options": [
                    "He must wait another 2 years for diabetes to be covered with Insurer B",
                    "Insurer B must credit his 3 years of continuity — his diabetes PED waiting period is already complete and diabetes is covered from Day 1 at Insurer B",
                    "He loses all waiting period credits because he switched insurers",
                    "Insurer B covers diabetes only for the first 6 months after porting",
                ],
                "correct_option_index": 1,
                "explanation": (
                    "IRDAI portability rules mandate that the new insurer credits ALL accumulated continuity "
                    "from the previous insurer. Completed waiting periods do not reset on a valid port."
                ),
            },
            {
                "order_index": 2,
                "question": "How many days before your renewal date should you apply for portability to ensure a smooth switch?",
                "options": [
                    "7 days before renewal",
                    "15 days before renewal",
                    "At least 45 days before renewal",
                    "Any time — portability can be done even after renewal",
                ],
                "correct_option_index": 2,
                "explanation": (
                    "IRDAI guidelines specify that portability applications must be submitted at least 45 days "
                    "before the renewal date to give both insurers adequate time for data transfer and underwriting."
                ),
            },
        ],
    },
]

# ---------------------------------------------------------------------------
# Patch the educational_content.py file
# ---------------------------------------------------------------------------
def patch_educational_content():
    content_file = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "app", "data", "educational_content.py")
    )
    print(f"Patching: {content_file}")

    with open(content_file, "r", encoding="utf-8") as f:
        content = f.read()

    # --- patch glossary ---
    GLOSSARY_CLOSE = "]\n\n# 10 Structured Educational Learning Modules with Quizzes\nMODULES_DATA = ["
    if GLOSSARY_CLOSE not in content:
        # Try CRLF variant
        GLOSSARY_CLOSE_CRLF = "]\r\n\r\n# 10 Structured Educational Learning Modules with Quizzes\r\nMODULES_DATA = ["
        if GLOSSARY_CLOSE_CRLF in content:
            GLOSSARY_CLOSE = GLOSSARY_CLOSE_CRLF
            sep = "\r\n"
        else:
            print("ERROR: Could not find GLOSSARY_TERMS_DATA closing marker!")
            return False
    else:
        sep = "\n"

    new_glossary_entries = ",".join(
        "\n    " + repr(entry) for entry in NEW_GLOSSARY_TERMS
    )

    # Build the replacement: append new terms before the closing ]
    glossary_append = f",\n{new_glossary_entries}\n"
    modules_close_marker = f"{sep}{sep}# 10 Structured Educational Learning Modules with Quizzes{sep}MODULES_DATA = ["
    modules_open_marker = f"\n\n# 10 Structured Educational Learning Modules with Quizzes\nMODULES_DATA = ["

    # Replace the closing of GLOSSARY_TERMS_DATA
    old_close = "]" + modules_close_marker
    new_close = glossary_append + "]" + modules_open_marker
    if old_close not in content:
        print("ERROR: Could not locate the exact glossary closing + modules opening!")
        return False
    content = content.replace(old_close, new_close, 1)

    # --- patch modules ---
    MODULES_CLOSE = "]\n\n# Static application reference categories\nCATEGORIES_DATA = ["
    MODULES_CLOSE_CRLF = "]\r\n\r\n# Static application reference categories\r\nCATEGORIES_DATA = ["
    if MODULES_CLOSE not in content and MODULES_CLOSE_CRLF not in content:
        print("ERROR: Could not find MODULES_DATA closing marker!")
        return False

    new_module_entries = ",".join(
        "\n    " + repr(mod) for mod in NEW_MODULES
    )
    modules_append = f",\n{new_module_entries}\n"

    for close_str in [MODULES_CLOSE, MODULES_CLOSE_CRLF]:
        if close_str in content:
            cats_open = "\n\n# Static application reference categories\nCATEGORIES_DATA = ["
            new_close2 = modules_append + "]" + cats_open
            content = content.replace(close_str, new_close2, 1)
            break

    with open(content_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Successfully patched {content_file}")
    return True


# ---------------------------------------------------------------------------
# Run the seeder
# ---------------------------------------------------------------------------
def run_seeder():
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from app.core.database import SessionLocal
    from app.data.educational_content import seed_educational_content
    db = SessionLocal()
    try:
        result = seed_educational_content(db)
        print("Seeder result:", result)
    finally:
        db.close()


if __name__ == "__main__":
    if patch_educational_content():
        print("\nRunning seeder to sync DB...")
        run_seeder()
    else:
        print("Patching failed — DB not updated.")
