import logging
from sqlalchemy.orm import Session
from app.models.glossary import GlossaryTerm
from app.models.learning import LearningModule, QuizQuestion
from app.models.insurer import InsuranceCategory

logger = logging.getLogger(__name__)

# 12 Comprehensive Glossary Terms with the 5 Zerodha Varsity Pillars
GLOSSARY_TERMS_DATA = [
    {
        "slug": "deductible",
        "term": "Deductible",
        "aliases": ["deductibles", "compulsory deductible", "voluntary deductible"],
        "category": "Health & Motor",
        "what_does_it_mean": "A deductible is the upfront amount of money you agree to pay from your own pocket towards a hospital or damage bill before your insurance company starts paying a single rupee.",
        "why_does_it_matter": "It protects insurers from minor frivolous claims and drastically lowers your annual premium. However, if your medical bill is smaller than the deductible, you must bear 100% of the cost yourself.",
        "financial_impact_example": "Suppose you buy a ₹10 Lakh super top-up policy with a ₹3 Lakh deductible. If you are hospitalized and the bill is ₹5 Lakhs, you must pay the first ₹3 Lakhs (either from your base insurance or personal savings). The top-up insurance pays the remaining ₹2 Lakhs.",
        "trade_off_analysis": "A higher deductible substantially lowers your premium, but increases your personal out-of-pocket financial liability during an emergency. A lower deductible means higher annual premium, but greater protection for smaller hospitalizations.",
        "watch_out_tips": "Do not choose a high deductible unless you already have a dependable corporate policy or separate base health cover to absorb costs below that deductible threshold.",
        "related_module_slug": "deductibles-copayments-sublimits"
    },
    {
        "slug": "copayment",
        "term": "Co-payment (Co-pay)",
        "aliases": ["copay", "co-pay", "co payment", "copayment"],
        "category": "Health",
        "what_does_it_mean": "A co-payment is a mandatory percentage of every approved medical bill that you, as the policyholder, must pay yourself, while the insurer pays the remaining balance.",
        "why_does_it_matter": "Unlike a deductible which is a fixed rupee amount, a co-payment is a percentage. This means the larger your hospital bill grows, the more money you have to pay out of pocket.",
        "financial_impact_example": "If your health policy has a 20% co-payment clause and your total approved hospitalization bill is ₹5,00,000, the insurance company pays ₹4,00,000 (80%), and you MUST pay ₹1,00,000 (20%) directly to the hospital.",
        "trade_off_analysis": "Policies with high co-pay (10-20%) have cheaper premiums, which is why insurers frequently mandate them for senior citizens (above 60 years). For young buyers, paying slightly more for a 0% co-pay plan is almost always the smarter decision.",
        "watch_out_tips": "Watch out for 'Zone-based Co-payments' where an insurer charges a 20% co-pay if you buy a tier-2 city policy but get treated in a tier-1 metro hospital (like Delhi or Mumbai).",
        "related_module_slug": "deductibles-copayments-sublimits"
    },
    {
        "slug": "sum-insured",
        "term": "Sum Insured",
        "aliases": ["sum assured", "coverage amount", "coverage limit"],
        "category": "General",
        "what_does_it_mean": "The Sum Insured is the maximum total monetary amount that an insurance company will reimburse or pay out for covered medical expenses during a policy year.",
        "why_does_it_matter": "Medical inflation in India runs at 14% annually. If your sum insured is only ₹3 Lakhs, a single modern cardiac bypass or cancer surgery can exceed your entire coverage, exhausting your policy in days.",
        "financial_impact_example": "If you have a ₹10 Lakh sum insured and incur ₹6 Lakhs for an emergency surgery, you have ₹4 Lakhs remaining for the rest of the policy year. Any hospital bill exceeding ₹10 Lakhs in that year must be paid entirely by you.",
        "trade_off_analysis": "Higher sum insured gives peace of mind against catastrophic illness at moderately higher cost. Because insurance pricing is non-linear, upgrading from ₹5L to ₹10L usually costs only 20-30% more, making higher coverage far more cost-effective per rupee of protection.",
        "watch_out_tips": "Differentiate Sum Insured (used in indemnity policies like health/motor to reimburse actual expenses) from Sum Assured (a fixed guaranteed payout used in life/term policies upon demise).",
        "related_module_slug": "understanding-health-insurance"
    },
    {
        "slug": "room-rent-capping",
        "term": "Room Rent Capping",
        "aliases": ["room rent limit", "proportionate deduction", "icu sub-limit"],
        "category": "Health",
        "what_does_it_mean": "A policy clause that limits how much your insurer will pay per day for a hospital room, typically defined as 1% of the Sum Insured (or Single Private Room).",
        "why_does_it_matter": "This is the most notorious fine-print trap in Indian health insurance. If you pick a room costing even ₹1,000 more than your capped limit, the hospital applies 'Proportionate Deduction', cutting payouts for surgeon fees, ICU, investigations, and medications proportionally!",
        "financial_impact_example": "On a ₹5L cover with a 1% room rent cap (₹5,000/day), if you choose a room costing ₹10,000/day (2x limit), your insurer cuts your entire hospital bill (except medicines) by 50%! A ₹4 Lakh bill might result in a ₹2 Lakh personal deduction.",
        "trade_off_analysis": "Plans with room rent caps are 10-15% cheaper. However, in any tier-1 or tier-2 Indian city, private hospital room rents start at ₹7,000 to ₹12,000/day. Buying a policy with 'No Capping' or 'Single Private Room' is essential.",
        "watch_out_tips": "Always insist on 'No Room Rent Capping' or 'Single Private AC Room' eligibility. Never accept a policy with a 1% room rent limit in 2026.",
        "related_module_slug": "deductibles-copayments-sublimits"
    },
    {
        "slug": "waiting-period",
        "term": "Waiting Period",
        "aliases": ["waiting periods", "moratorium", "initial waiting period"],
        "category": "Health",
        "what_does_it_mean": "A specified timeframe after buying your policy during which claims for certain medical conditions or treatments are NOT payable by the insurance company.",
        "why_does_it_matter": "Insurers enforce waiting periods to prevent adverse selection (people buying insurance only after falling sick or scheduling a planned surgery).",
        "financial_impact_example": "If you buy a policy on Jan 1 with a 30-day initial waiting period and suffer malaria on Jan 15, the claim is rejected. However, if you suffer an accidental fracture on Jan 15, it is covered immediately because accidents have zero waiting period.",
        "trade_off_analysis": "Policies with shorter waiting periods (e.g. 1-2 years for Pre-Existing Diseases vs 4 years) may carry a slightly higher premium or require detailed medical underwriting. Shorter is always safer for policyholders.",
        "watch_out_tips": "IRDAI updated guidelines reducing the maximum allowable Pre-Existing Disease (PED) waiting period from 48 months to 36 months. Any insurer still quoting 48 months must be questioned.",
        "related_module_slug": "waiting-periods-ped-exclusions"
    },
    {
        "slug": "pre-existing-diseases",
        "term": "Pre-Existing Diseases (PED)",
        "aliases": ["ped", "existing illness", "pre existing condition"],
        "category": "Health",
        "what_does_it_mean": "Any medical condition, illness, or injury diagnosed by a physician, or for which medical advice or treatment was received, prior to purchasing the insurance policy (e.g. Diabetes, Hypertension, Asthma).",
        "why_does_it_matter": "Failure to declare a pre-existing condition is the number one reason insurers reject claims and cancel policies for fraud or non-disclosure in India.",
        "financial_impact_example": "If Ramesh has diabetes when buying health insurance, declares it truthfully, and completes his 24-month PED waiting period, any future diabetes-related kidney complication is fully covered. If he hid it, a ₹7 Lakh claim can be denied outright.",
        "trade_off_analysis": "Declaring PED may result in a medical test, slight premium loading (10-20%), or a waiting period. Hiding it risks 100% claim rejection when you need money the most.",
        "watch_out_tips": "Always disclose thyroid, blood pressure, diabetes, past surgeries, and tobacco consumption. Never let an agent convince you to check 'No' on the proposal form to speed up issuance.",
        "related_module_slug": "waiting-periods-ped-exclusions"
    },
    {
        "slug": "restoration-benefit",
        "term": "Restoration / Refill Benefit",
        "aliases": ["automatic restoration", "recharge benefit", "refill cover"],
        "category": "Health",
        "what_does_it_mean": "A feature that automatically reloads or restores your full Sum Insured if you exhaust it on hospitalizations within the same policy year.",
        "why_does_it_matter": "Essential for family floater policies. If one family member exhausts the ₹10L cover for a major illness, the restoration benefit instantly refills ₹10L so other family members remain protected.",
        "financial_impact_example": "Anita exhausts her ₹5 Lakh cover fighting Dengue in March. In August, she requires knee surgery costing ₹4 Lakhs. With 'Unlimited Automatic Restoration (same illness covered)', her policy restores ₹5 Lakhs, paying the ₹4 Lakh bill completely.",
        "trade_off_analysis": "Old policies only restored cover for 'unrelated illnesses' upon '100% exhaustion'. Modern policies restore upon partial exhaustion and cover both related and unrelated illnesses.",
        "watch_out_tips": "Look for 'Restoration on Partial Exhaustion' that works for the same illness as well as different illnesses.",
        "related_module_slug": "understanding-health-insurance"
    },
    {
        "slug": "no-claim-bonus",
        "term": "No Claim Bonus (NCB)",
        "aliases": ["ncb", "cumulative bonus", "super ncb"],
        "category": "Health & Motor",
        "what_does_it_mean": "A reward given by the insurer for every year you do not file a claim. In health insurance, it increases your Sum Insured for free without increasing premium. In motor insurance, it discounts your renewal premium.",
        "why_does_it_matter": "Your ₹10 Lakh health cover can double to ₹20 Lakhs in 2 to 5 years purely through cumulative bonus without paying an extra rupee.",
        "financial_impact_example": "Kunal has a ₹10 Lakh policy with 50% NCB per claim-free year. Year 1: ₹10L. Year 2 (no claims): ₹15L. Year 3 (no claims): ₹20L cover, all while paying the original ₹10L base premium.",
        "trade_off_analysis": "Look for policies with 'No NCB Reduction on Claims' or guaranteed cumulative bonus protectors, so that filing a small ₹20,000 claim doesn't wipe out years of accumulated bonus.",
        "watch_out_tips": "Some insurers reduce your accumulated NCB by the same percentage if you make a claim. Prefer plans with 'Super NCB' riders that preserve your bonus.",
        "related_module_slug": "understanding-health-insurance"
    },
    {
        "slug": "claim-settlement-ratio",
        "term": "Claim Settlement Ratio (CSR)",
        "aliases": ["csr", "claim ratio", "settlement ratio"],
        "category": "General",
        "what_does_it_mean": "The percentage of total insurance claims settled and paid by an insurer out of the total claims reported during a financial year, audited and published by IRDAI.",
        "why_does_it_matter": "A high CSR (above 95% for health, above 98% for life) indicates an insurer that honors legitimate claims smoothly rather than looking for technical loopholes to reject them.",
        "financial_impact_example": "An insurer receiving 100,000 claims that successfully pays 98,400 claims has a Claim Settlement Ratio of 98.4%.",
        "trade_off_analysis": "Do not judge an insurer solely on CSR. An insurer that sells cheap micro-insurance might have high volume but strict hospital scrutiny. Also inspect Incurred Claim Ratio (ICR) and customer grievance turnaround.",
        "watch_out_tips": "Always check 3-year consistency. An insurer with 98% CSR over 5 consecutive years is far more trustworthy than a new company reporting 99% on small claim volumes.",
        "related_module_slug": "claim-filing-and-rejection"
    },
    {
        "slug": "network-hospital",
        "term": "Network Hospital (Cashless)",
        "aliases": ["cashless hospital", "preferred provider network", "ppn"],
        "category": "Health",
        "what_does_it_mean": "A hospital that has a formal tie-up with your insurance company or Third Party Administrator (TPA) to provide direct cashless billing, meaning the hospital settles bills directly with the insurer.",
        "why_does_it_matter": "In emergency hospitalizations, you do not need to arrange Lakhs of rupees in cash or arrange personal loans. The insurance desk at the hospital handles billing directly with the insurer.",
        "financial_impact_example": "If Priya undergoes gallbladder surgery at an Apollo or Fortis network hospital costing ₹1.8 Lakhs, she only pays non-medical consumables (e.g. ₹3,500), and walks out without paying the ₹1.8 Lakhs.",
        "trade_off_analysis": "Under IRDAI's 'Cashless Everywhere' initiative, you can now obtain cashless treatment even at non-network hospitals, provided you notify the insurer 48 hours prior (planned) or within 48 hours (emergency).",
        "watch_out_tips": "Verify whether top multi-specialty tertiary hospitals near your residence and workplace are on the insurer's active cashless list.",
        "related_module_slug": "understanding-health-insurance"
    },
    {
        "slug": "free-look-period",
        "term": "Free-Look Period",
        "aliases": ["free look", "cooling-off period", "trial period"],
        "category": "General",
        "what_does_it_mean": "A statutory 15 to 30 day cooling-off window starting from the day you receive the policy document, during which you can cancel the policy for a full refund if you disagree with any terms.",
        "why_does_it_matter": "It protects consumers from aggressive or misleading sales agents. If you discover unexpected exclusions or sub-limits in the policy wording, you can cancel with zero penalty.",
        "financial_impact_example": "You buy a term insurance policy online on Oct 1. The document arrives Oct 5. You have until Nov 4 (30 days for online policies) to review and cancel for a full refund minus proportionate stamp duty.",
        "trade_off_analysis": "You cannot make a claim during the free-look period and then ask for a refund. Insurers deduct stamp duty, medical test costs, and proportionate risk premium.",
        "watch_out_tips": "The free-look clock starts on the date you *receive* the policy document, not the payment date. Keep delivery proof.",
        "related_module_slug": "spotting-misleading-sales-tactics"
    },
    {
        "slug": "zero-depreciation",
        "term": "Zero Depreciation (Bumper to Bumper)",
        "aliases": ["nil dep", "zero dep", "bumper to bumper"],
        "category": "Motor",
        "what_does_it_mean": "A motor insurance add-on cover that waives off depreciation deductions on plastic, rubber, fiber, metal, and glass parts when repairing your vehicle after an accident.",
        "why_does_it_matter": "Standard motor policies deduct 50% on plastic/nylon parts and up to 40% on metal parts due to vehicle age. With Zero Dep, the insurer pays 100% of the replacement cost.",
        "financial_impact_example": "Your car bumper and headlight are damaged. Standard policy pays only ₹12,000 on a ₹25,000 repair bill (50% plastic depreciation). Zero Dep cover pays ₹24,000, leaving you to pay only the ₹1,000 compulsory deductible.",
        "trade_off_analysis": "Zero Dep increases your motor premium by 15-20%, but for cars younger than 5 years, it saves thousands of rupees on even minor bumper scrapes.",
        "watch_out_tips": "Most insurers cap the number of Zero Dep claims per year (e.g. 2 claims per year). Check this limit before selecting an add-on.",
        "related_module_slug": "motor-insurance-explained"
    }
,

    {'slug': 'super-top-up', 'term': 'Super Top-Up Policy', 'aliases': ['super topup', 'aggregate deductible policy', 'super top up health insurance'], 'category': 'Health', 'what_does_it_mean': 'A Super Top-Up policy covers all hospitalisation expenses that collectively exceed a threshold (called the deductible) during an entire policy year. Unlike a plain Top-Up (which applies the deductible per claim), a Super Top-Up applies it once per year to the total of all claims combined.', 'why_does_it_matter': 'A Super Top-Up dramatically amplifies your health coverage at a fraction of the cost. A ₹20 Lakh Super Top-Up with a ₹5 Lakh deductible costs about ₹3,000–₹5,000 a year for a 30-year-old. Combined with a ₹5 Lakh base policy, you effectively have ₹25 Lakh total coverage.', 'financial_impact_example': 'Kavita has a ₹5 Lakh base policy and a ₹20 Lakh Super Top-Up with ₹5 Lakh deductible. She is hospitalised twice: ₹3 Lakh in April and ₹4 Lakh in September. Her base policy covers the April bill. The September bill brings her yearly total to ₹7 Lakh, crossing the ₹5 Lakh deductible — so the Super Top-Up pays ₹2 Lakh of the September bill.', 'trade_off_analysis': 'Super Top-Up is cost-efficient only when you already have a base policy to absorb the deductible. The deductible must be equal to or lower than your base cover to avoid out-of-pocket gaps. It does NOT work like a standalone policy for small claims.', 'watch_out_tips': "Never confuse a Super Top-Up with a plain Top-Up. Plain Top-Up applies deductible per-claim; Super Top-Up applies once per year. Always match the deductible amount to your base policy's sum insured.", 'related_module_slug': 'super-top-up-explained'},
    {'slug': 'family-floater', 'term': 'Family Floater Policy', 'aliases': ['floater plan', 'family health plan', 'family floater insurance'], 'category': 'Health', 'what_does_it_mean': 'A single health insurance policy where one shared Sum Insured covers an entire family — spouse, children, and sometimes parents. Any family member can use all or part of the cover, but the total paid across all claims cannot exceed the Sum Insured in a year.', 'why_does_it_matter': 'A Family Floater is cheaper than buying separate individual policies. For a family of four, a ₹10 Lakh floater might cost ₹15,000/year whereas four individual ₹5 Lakh policies could cost ₹25,000+ combined.', 'financial_impact_example': 'Ravi buys a ₹10 Lakh Family Floater for himself, wife, and two children. His wife is hospitalised for ₹4 Lakhs in June. Ravi undergoes surgery costing ₹7 Lakhs in October. Combined claims = ₹11 Lakhs, but cover is ₹10 Lakhs — Ravi pays ₹1 Lakh out of pocket.', 'trade_off_analysis': "Floaters are economical for young families. However, including senior parents raises the premium significantly because it is based on the oldest member's age. For parents above 60, separate senior citizen policies are usually more cost-effective.", 'watch_out_tips': 'If one family member has a chronic illness and makes frequent claims, the shared cover can be rapidly depleted. Consider individual policies plus a floater, or a plan with unlimited restoration benefit.', 'related_module_slug': 'family-floater-vs-individual'},
    {'slug': 'insured-declared-value', 'term': 'Insured Declared Value (IDV)', 'aliases': ['idv', 'market value car', 'vehicle declared value'], 'category': 'Motor', 'what_does_it_mean': 'The Insured Declared Value (IDV) is the approximate current market value of your vehicle assigned by the insurer at policy issuance. It is the maximum amount you will receive if your vehicle is stolen or totally destroyed (total loss).', 'why_does_it_matter': 'IDV directly determines your payout in theft or total-loss situations. Undervaluing IDV to save premium means a smaller payout if your vehicle is stolen. Overvaluing means an unnecessarily high premium.', 'financial_impact_example': "Suresh's car has a market value of ₹8 Lakhs but the IDV was set at ₹6.5 Lakhs due to standard depreciation tables. When his car was stolen, he received ₹6.5 Lakhs — not ₹8 Lakhs.", 'trade_off_analysis': 'IDV decreases every year as the vehicle depreciates. For new cars (under 3 years), set IDV as close to actual market value as possible. IDV is negotiable within a ±10% range of the standard value.', 'watch_out_tips': 'Never blindly accept the lowest IDV offered to get a cheaper premium. For new or expensive cars, always insist on the maximum IDV within the allowable range.', 'related_module_slug': 'motor-insurance-explained'},
    {'slug': 'third-party-administrator', 'term': 'Third Party Administrator (TPA)', 'aliases': ['tpa', 'insurance tpa', 'health tpa', 'claims administrator'], 'category': 'Health', 'what_does_it_mean': 'A TPA is a licensed intermediary company authorised by IRDAI that manages health insurance claims on behalf of the insurance company. TPAs verify pre-authorisation requests, manage network hospital cashless settlements, and process reimbursement claims.', 'why_does_it_matter': "When you call the insurance helpline during hospitalisation, you are often speaking to the TPA, not the insurance company directly. The TPA's efficiency determines how fast your cashless authorisation is approved and how quickly reimbursement claims are processed.", 'financial_impact_example': "Amit is hospitalised at a network hospital. The hospital's insurance desk sends a cashless pre-authorisation request to Medi Assist TPA. Medi Assist reviews and approves the amount within 2–6 hours, allowing Amit to be admitted without paying upfront.", 'trade_off_analysis': 'Some insurers (like Star Health, Care Health) manage claims in-house without a TPA — this can mean faster processing. Others outsource to TPAs, adding one administrative layer but enabling larger network hospital coverage.', 'watch_out_tips': "Know your TPA's name and helpline number BEFORE an emergency. Your insurance card will have the TPA name printed on it. Save the TPA's number in your phone the day you buy the policy.", 'related_module_slug': 'understanding-health-insurance'},
    {'slug': 'incurred-claim-ratio', 'term': 'Incurred Claim Ratio (ICR)', 'aliases': ['icr', 'loss ratio', 'claim loss ratio'], 'category': 'General', 'what_does_it_mean': 'ICR is the percentage of total premium collected by an insurer that was paid out as claims in a given financial year. ICR = (Total Claims Paid ÷ Total Premium Collected) × 100.', 'why_does_it_matter': 'ICR shows how fair an insurer is to policyholders. An ICR above 100% means the insurer is losing money and may tighten claim approvals. An ICR below 50% suggests the insurer may be aggressively rejecting valid claims.', 'financial_impact_example': 'If an insurer collected ₹1,000 Crore in health premiums and paid ₹800 Crore in claims, its ICR is 80%. An ICR of 75–90% is considered healthy — financially stable and relatively fair to claimants.', 'trade_off_analysis': 'ICR and CSR together tell the full story. A high CSR (98%) with a very low ICR (45%) might mean the insurer settles claims but only small ones while rejecting large expensive ones. Look at both numbers.', 'watch_out_tips': 'IRDAI publishes ICR data annually in its insurance industry annual report. Always check ICR data from the official IRDAI report, not just insurer marketing materials.', 'official_reference_source': 'https://www.irdai.gov.in', 'related_module_slug': 'how-to-choose-insurance-policy'},
    {'slug': 'premium', 'term': 'Insurance Premium', 'aliases': ['policy premium', 'annual premium', 'monthly premium', 'insurance cost'], 'category': 'General', 'what_does_it_mean': "The premium is the amount you pay (monthly, quarterly, or annually) to the insurance company in exchange for coverage. It is calculated based on your age, health history, sum insured, policy features, and the insurer's risk assessment.", 'why_does_it_matter': 'The premium determines affordability, but choosing insurance solely on the cheapest premium is dangerous — cheaper premiums often hide larger exclusions, higher deductibles, or inferior claim settlement practices.', 'financial_impact_example': 'Priya (28, non-smoker) pays ₹8,000/year for a ₹10 Lakh health policy. If she waits until 40, the premium rises to ₹18,000–₹22,000/year, plus possible medical loading for any conditions developed in the interim.', 'trade_off_analysis': 'Buying early locks in lower premiums. Many insurers offer a 5–10% discount for 2 or 3-year policies. GST of 18% applies on all insurance premiums in India and is non-refundable even during free-look cancellation.', 'watch_out_tips': 'Compare premiums on a like-for-like basis: same sum insured, same sub-limits, same co-pay, and same room rent category. A ₹7,000 policy with 20% co-pay is costlier in practice than a ₹9,500 policy with no co-pay and no room rent cap.', 'related_module_slug': 'what-is-insurance'},
    {'slug': 'portability', 'term': 'Health Insurance Portability', 'aliases': ['policy portability', 'porting health insurance', 'insurer switch'], 'category': 'Health', 'what_does_it_mean': 'The right guaranteed by IRDAI that allows you to switch your health insurance policy from one insurer to another at renewal, without losing accumulated waiting period credits and No Claim Bonus earned under the old policy.', 'why_does_it_matter': "Before IRDAI introduced portability, switching insurers meant restarting all waiting periods from scratch. With portability, your 3-year PED waiting period completed with Insurer A is credited to Insurer B — you don't wait another 3 years.", 'financial_impact_example': 'Kavita has been with ABC Health Insurance for 3 years and completed her 2-year PED waiting period for thyroid. She ports to XYZ Insurance. Under portability rules, XYZ must credit those 3 years — her thyroid is covered immediately, not after another 2-year wait.', 'trade_off_analysis': 'Portability preserves waiting periods but not necessarily the premium. The new insurer may charge higher premiums based on current age, health status, or claims history. NCB transfer depends on specific policy terms — confirm in writing before porting.', 'watch_out_tips': 'Apply for portability at least 45 days before your renewal date. Do NOT let your current policy lapse before the new policy is confirmed. The new insurer is legally obligated to accept port applications but may apply medical underwriting and premium loading.', 'related_module_slug': 'insurance-portability-and-renewal'},
    {'slug': 'sub-limit', 'term': 'Sub-Limit (Disease-Specific Cap)', 'aliases': ['sub limits', 'disease sublimit', 'procedure cap', 'treatment limit'], 'category': 'Health', 'what_does_it_mean': 'A cap placed by the insurer on the maximum amount payable for a specific procedure, treatment, or disease category — even if your overall Sum Insured is much larger. It is one of the most dangerous hidden clauses in health insurance policies.', 'why_does_it_matter': 'You may have a ₹10 Lakh policy but find the insurer only pays ₹1.5 Lakh for knee replacement surgery because of a sub-limit, while the actual procedure costs ₹4 Lakhs. You must pay ₹2.5 Lakhs from your own pocket despite having a large policy.', 'financial_impact_example': 'Mohan has a ₹10 Lakh policy with a ₹2 Lakh sub-limit for cataract surgery. The surgery costs ₹3.5 Lakhs. Despite ₹10 Lakhs insured, the insurer pays only ₹2 Lakhs. Mohan pays ₹1.5 Lakhs from savings.', 'trade_off_analysis': 'Policies without sub-limits are always preferred even if slightly more expensive. Modern IRDAI-compliant comprehensive policies (post-2023) are moving toward eliminating disease-specific sub-limits. Always read the benefits table in the policy wording document.', 'watch_out_tips': 'Common sub-limits to check: cataract surgery, dialysis, joint replacement, hernia repair, maternity expenses, and psychiatric treatment. If a policy has ANY disease sub-limit, treat it as a red flag.', 'related_module_slug': 'deductibles-copayments-sublimits'},
    {'slug': 'day-care-procedure', 'term': 'Day Care Procedure', 'aliases': ['daycare treatment', 'day care treatment', 'outpatient procedure'], 'category': 'Health', 'what_does_it_mean': 'A medical treatment or surgery that, thanks to modern technology, can be completed within a few hours and does NOT require a minimum 24-hour hospital admission — yet is still covered under health insurance.', 'why_does_it_matter': 'Traditional health insurance required a minimum 24-hour admission to make a claim. Modern policies cover hundreds of day-care procedures (chemotherapy, dialysis, cataract surgery, lithotripsy) done in hours, preventing denial of valid medical claims.', 'financial_impact_example': 'Sunita underwent cataract surgery in 2.5 hours at a network hospital. Bill: ₹35,000. Under her policy covering 540 day-care procedures, the cashless claim was approved and she paid nothing. 10 years ago this would have been rejected for lack of 24-hour admission.', 'trade_off_analysis': 'The list of covered day-care procedures varies per insurer. Premium policies list 500–1,000+ procedures. Budget policies may list only 150–200. Fewer listed procedures means more potential rejections for modern medical treatments.', 'watch_out_tips': 'Ask the insurer for the complete Day Care Procedure list before buying. LASIK eye surgery, dental work (outside accidents), and cosmetic procedures are typically excluded even from comprehensive policies.', 'related_module_slug': 'understanding-health-insurance'},
    {'slug': 'domiciliary-hospitalization', 'term': 'Domiciliary Hospitalisation', 'aliases': ['home hospitalization', 'home treatment cover', 'domiciliary treatment'], 'category': 'Health', 'what_does_it_mean': "Coverage for medical treatment taken at home when the patient's condition is so serious that movement to a hospital is not safe, OR when hospital beds are unavailable. The treatment must be certified by a qualified doctor and must ordinarily require hospitalisation.", 'why_does_it_matter': 'During COVID-19, lakhs of patients were treated at home due to hospital bed unavailability. Domiciliary cover was critical — it allowed claims for home nursing, oxygen concentrators, medicines, and doctor visits that would otherwise be entirely out-of-pocket.', 'financial_impact_example': "Rajesh was diagnosed with COVID-19 requiring oxygen support but couldn't find a hospital bed. His insurer approved a domiciliary claim covering ₹45,000 in home nursing, oxygen concentrator rental, medicines, and telemedicine consultations over 12 days.", 'trade_off_analysis': 'Not all policies include domiciliary cover. Some cover it only for conditions lasting 3+ days at home. The benefit is more valuable in tier-2 cities where hospital infrastructure is limited. Verify the minimum duration requirement (typically 3 days).', 'watch_out_tips': "Domiciliary claims require a doctor's written certificate stating hospital admission was not feasible. Maintain detailed records of all at-home treatments, doctor visits, invoices, and prescriptions for reimbursement.", 'related_module_slug': 'understanding-health-insurance'},
    {'slug': 'critical-illness-cover', 'term': 'Critical Illness Cover', 'aliases': ['ci cover', 'critical illness policy', 'ci insurance', 'dread disease policy'], 'category': 'Health', 'what_does_it_mean': 'A Critical Illness (CI) policy pays out a fixed lump sum when you are diagnosed with a specified life-threatening illness — such as cancer, first heart attack, stroke, organ failure, or kidney failure — regardless of actual medical expenses incurred.', 'why_does_it_matter': 'Unlike regular health insurance that reimburses hospital bills, CI insurance pays a fixed pre-agreed amount (e.g. ₹25 Lakhs) that you can use for ANY purpose: hospital bills, income replacement, home loan EMIs, or international treatment.', 'financial_impact_example': 'Arun is diagnosed with third-stage cancer. His ₹25 Lakh CI policy pays ₹25 Lakhs in one lump sum upon confirmed diagnosis. He uses ₹12 Lakhs for chemotherapy, ₹8 Lakhs to prepay his home loan, and keeps ₹5 Lakhs for living expenses while on medical leave.', 'trade_off_analysis': 'CI policies cover fewer conditions (typically 20–36 listed illnesses) but pay unconditionally upon diagnosis. Regular health insurance covers far more conditions but only reimburses actual expenses. Ideally, have both — regular health insurance plus a CI cover for catastrophic diagnoses.', 'watch_out_tips': "Strictly read the definition of each covered illness. Many CI policies require you to 'survive 30 days post-diagnosis' to receive the payout. Check the survival clause and the list of covered conditions very carefully before purchasing.", 'related_module_slug': 'critical-illness-and-riders'},
    {'slug': 'term-insurance', 'term': 'Term Life Insurance', 'aliases': ['term plan', 'pure life cover', 'term policy', 'life cover'], 'category': 'Life', 'what_does_it_mean': 'Term insurance is the simplest, most affordable form of life insurance that pays a fixed death benefit (Sum Assured) to your nominee if you pass away during the policy term. It has NO investment or savings component — it is pure, 100% risk protection.', 'why_does_it_matter': "A ₹1 Crore term insurance policy costs just ₹700–₹1,200/month for a 30-year-old non-smoker. If the insured dies during the term, the family gets ₹1 Crore — enough to replace 10–15 years of the breadwinner's income.", 'financial_impact_example': 'Vijay (30, earning ₹60,000/month) buys a ₹1 Crore term plan for ₹850/month. He passes away in a road accident at 42. His family receives ₹1 Crore tax-free. Invested at 6% returns, this generates ₹6 Lakh/year — replacing his monthly income for decades.', 'trade_off_analysis': 'Term insurance pays nothing if you survive the policy term (unlike endowment/ULIP plans). This is the correct design — term insurance is for protection, not savings. Mixing insurance with investment results in both poor protection and poor returns.', 'watch_out_tips': "Never buy a term plan where total cover is less than 10× your annual income. Avoid 'Return of Premium' (TROP) variants — they charge 2–3× the normal premium for marginal benefit. Always buy a pure term plan online directly from the insurer's website for the lowest premium.", 'related_module_slug': 'term-life-vs-investment-schemes'},
    {'slug': 'personal-accident-cover', 'term': 'Personal Accident (PA) Cover', 'aliases': ['pa cover', 'accident insurance', 'personal accident policy'], 'category': 'General', 'what_does_it_mean': 'A PA policy provides financial compensation if you suffer an accidental injury, permanent disability (partial or total), or accidental death. Benefits are paid as a lump sum or structured compensation, regardless of your other insurance policies.', 'why_does_it_matter': 'Road accidents are among the leading causes of death and disability in India. A PA policy supplements your health insurance (which covers hospitalization costs) by also paying for income loss, permanent disability compensation, and accidental death — which health insurance does NOT cover.', 'financial_impact_example': 'Ravi, a delivery executive, meets with a road accident and loses his right hand. His PA policy covers: ₹5 Lakhs for permanent partial disability (loss of limb = 50% payout of ₹10 Lakh sum), ₹50,000 for hospitalisation, and ₹3,000/week for 26 weeks of temporary disability income.', 'trade_off_analysis': 'PA policies are very affordable (₹2,000–₹5,000/year for ₹25 Lakh cover) because accidents are statistically less frequent than illness. However, they cover ONLY accidents — not diseases or natural death. They complement, not replace, health and term insurance.', 'watch_out_tips': 'Check whether the PA policy covers both road and non-road accidents (workplace accidents, slips, sports injuries). Also verify if it covers partial disability, not just total permanent disability or death, since partial disabilities are far more common.', 'related_module_slug': 'what-is-insurance'},
    {'slug': 'insurance-ombudsman', 'term': 'Insurance Ombudsman (Bima Lokpal)', 'aliases': ['ombudsman', 'insurance grievance officer', 'insurance complaint authority', 'bima lokpal'], 'category': 'General', 'what_does_it_mean': 'The Insurance Ombudsman (Bima Lokpal) is an independent, free grievance redressal authority established by the Government of India under IRDAI. It resolves disputes between policyholders and insurance companies — including claim rejections, premium disputes, and policy cancellations — at absolutely no cost to the consumer.', 'why_does_it_matter': "If your insurer unfairly rejects your claim or delays settlement beyond 30 days, you can approach the Insurance Ombudsman. Cases are resolved within 3 months. The insurer must comply with the Ombudsman's award. It is faster and cheaper than consumer court.", 'financial_impact_example': "Lakshmi's health insurer rejected her ₹3.2 Lakh hospitalisation claim citing 'non-disclosure'. She filed a complaint with the Insurance Ombudsman of Chennai. After review, the Ombudsman ordered the insurer to pay ₹2.8 Lakhs within 30 days.", 'trade_off_analysis': 'The Ombudsman can adjudicate disputes up to ₹50 Lakhs in value (as of 2024). For larger disputes, the Consumer Disputes Redressal Commission (Consumer Court) is the appropriate forum. There are 17 Ombudsman offices across major Indian cities.', 'watch_out_tips': "File a complaint with the Ombudsman only after exhausting the insurer's internal grievance mechanism (write to the Grievance Officer and wait 15–30 days). Maintain a grievance reference number from the insurer before escalating to the Ombudsman.", 'official_reference_source': 'https://cioins.co.in', 'related_module_slug': 'claim-filing-and-rejection'},
    {'slug': 'moratorium-period', 'term': 'Moratorium Period (8-Year Rule)', 'aliases': ['moratorium', 'irdai 8 year rule', 'non-contestability period'], 'category': 'Health', 'what_does_it_mean': 'Under IRDAI rules, after a health insurance policy has been continuously in force for 8 years, the insurer CANNOT reject any claim on the grounds of non-disclosure or misrepresentation of Pre-Existing Diseases — unless the insurer can prove outright fraud.', 'why_does_it_matter': 'This is one of the strongest consumer protections in Indian insurance. Even if you forgot to disclose a minor health condition, after 8 continuous years the insurer loses the legal right to reject claims based on that non-disclosure (except for deliberate fraud).', 'financial_impact_example': 'Ramesh bought a policy in 2014 without disclosing a minor thyroid condition he was unaware of. In 2023 (after 9 years), he filed a ₹5.5 Lakh claim for thyroid cancer. The insurer attempted rejection based on non-disclosure but could not — the 8-year moratorium had passed.', 'trade_off_analysis': 'The moratorium does NOT protect fraud or deliberate concealment. If you knowingly hid a heart condition or diabetes to avoid premium loading, the insurer can still reject claims and cancel the policy. Always disclose in good faith.', 'watch_out_tips': 'Maintain continuous renewals without any lapse to benefit from the moratorium. A policy lapse may reset the clock. Always renew on time — set up auto-payment reminders for your renewal date.', 'official_reference_source': 'https://www.irdai.gov.in', 'related_module_slug': 'waiting-periods-ped-exclusions'},
    {'slug': 'ayushman-bharat-pmjay', 'term': 'Ayushman Bharat – PM-JAY', 'aliases': ['pmjay', 'ayushman bharat', 'pradhan mantri jan arogya yojana', 'golden card scheme'], 'category': 'Health', 'what_does_it_mean': "Ayushman Bharat – PM-JAY is India's flagship government health insurance scheme that provides free hospitalisation coverage of up to ₹5 Lakh per year per family to economically vulnerable households identified through the SECC database.", 'why_does_it_matter': "PM-JAY is the world's largest government-funded health insurance scheme, covering over 55 Crore beneficiaries. Covered families can access cashless treatment at 28,000+ empanelled hospitals across India without any premium payment.", 'financial_impact_example': 'Savitribai from a rural Maharashtra BPL family undergoes heart bypass surgery costing ₹3.5 Lakhs at a district empanelled hospital. Under PM-JAY, the entire surgery is cashless and free — she pays nothing. Without PM-JAY, this would have required selling family land or livestock.', 'trade_off_analysis': 'PM-JAY covers only hospitalisations — no OPD, no medicines, no diagnostics outside hospital admission. Coverage is limited to ₹5 Lakh per family per year. For middle-class families not eligible for PM-JAY, private health insurance with higher Sum Insured remains necessary.', 'watch_out_tips': "Check eligibility using the official PM-JAY portal (pmjay.gov.in). Ayushman cards are free and obtained from Common Service Centres (CSCs). Beware of agents charging money to 'register' for PM-JAY — it is completely FREE.", 'official_reference_source': 'https://pmjay.gov.in', 'related_module_slug': 'what-is-insurance'},
    {'slug': 'uin-number', 'term': 'UIN – Unique Identification Number', 'aliases': ['uin', 'policy uin', 'irdai uin', 'product uin'], 'category': 'General', 'what_does_it_mean': 'A UIN (Unique Identification Number) is a unique alphanumeric code assigned by IRDAI to every officially approved insurance product sold in India. Every legitimate health, life, motor, or travel policy must carry a valid UIN in its policy document.', 'why_does_it_matter': "The UIN confirms the insurance product is genuine, IRDAI-approved, and legally permitted to be sold in India. Checking the UIN on IRDAI's registry protects you from fraudulent insurance products sold by unlicensed agents or fake insurers.", 'financial_impact_example': "Meera was sold a 'health insurance plan' by an individual agent. When she tried to file a claim, the hospital couldn't verify the insurer. Her policy document had no valid UIN. The 'policy' was fake and her ₹12,000 annual premium was gone.", 'trade_off_analysis': 'All IRDAI-registered products must quote their UIN on the policy certificate. If a policy document, brochure, or sales pitch does not mention a UIN, it is a major red flag regardless of how attractive the coverage appears.', 'watch_out_tips': "Cross-check the UIN on IRDAI's product registry portal at irdai.gov.in. A valid UIN format looks like 'IRDAI/HLT/NICHI/P-H/V.I/102/2022-23'. A valid UIN means the product has regulatory oversight.", 'official_reference_source': 'https://www.irdai.gov.in', 'related_module_slug': 'spotting-misleading-sales-tactics'},
    {'slug': 'policy-lapse', 'term': 'Policy Lapse', 'aliases': ['lapsed policy', 'policy expiry', 'lapse in coverage', 'policy cancellation'], 'category': 'General', 'what_does_it_mean': 'A policy lapse occurs when you fail to pay the renewal premium by the due date (including any grace period given by the insurer), causing the insurance contract to terminate. A lapsed policy offers no coverage — any claim filed after a lapse is automatically rejected.', 'why_does_it_matter': 'A lapsed health policy is catastrophic in two ways: (1) You have zero coverage during the lapse period, and (2) When you reinstate or buy a new policy, all waiting periods reset from Day 1 — your previously completed PED waiting period is lost.', 'financial_impact_example': 'Deepak forgot to renew his 4-year-old health policy (he had completed his 2-year PED waiting period). The policy lapsed on March 31. On April 14, he was hospitalised for a cardiac event costing ₹4.2 Lakhs. The claim was rejected — no active policy. He paid entirely from savings.', 'trade_off_analysis': 'Most insurers allow a 15–30 day grace period after the premium due date. Beyond that, the policy lapses. Some insurers allow revival within 90–180 days with a fresh medical examination and possible premium loading.', 'watch_out_tips': 'Set an auto-debit mandate for all insurance renewals. Treat insurance renewal as non-negotiable as your EMI. Even a 31-day lapse can cost you years of accumulated waiting period credits and leave you uncovered during that gap.', 'related_module_slug': 'insurance-portability-and-renewal'}
]

# 10 Structured Educational Learning Modules with Quizzes
MODULES_DATA = [
    {
        "slug": "what-is-insurance",
        "order_index": 1,
        "title": "What is Insurance, and Why Do You Need It?",
        "subtitle": "The foundational principle of risk pooling explained with everyday Indian analogies.",
        "category": "Basics",
        "estimated_minutes": 6,
        "level": "Beginner",
        "concept_explanation": """
Insurance is not an investment or a wealth-generating scheme; **it is a financial safety net designed to protect you from catastrophic financial ruin.**

In simple words, insurance works on the principle of **Risk Pooling**. Imagine 1,000 families living in an apartment society in Pune. Each family deposits ₹5,000 every year into a central emergency fund (total fund = ₹50 Lakhs). In any given year, statistically, only 2 or 3 families will face a severe medical emergency costing ₹15 Lakhs each. The central fund pays for those 2 families entirely. None of the 1,000 families go bankrupt, and all 1,000 sleep peacefully knowing they are protected.

An insurance company is simply the professional manager of this community pool. Your annual fee to participate in the pool is called your **Premium**.
        """,
        "why_it_matters": "In India, one medical emergency or prolonged hospitalization can wipe out 5 to 10 years of personal savings, forcing families to take high-interest private debt or sell gold and property.",
        "practical_indian_example": "Ramesh (age 28, earning ₹45,000/month) pays ₹850/month for a ₹10 Lakh health insurance policy. When he contracted acute viral encephalitis requiring 14 days in ICU costing ₹6.8 Lakhs, his insurance settled the entire bill. Without insurance, his entire ₹4 Lakh life savings would have been wiped out, leaving him in ₹2.8 Lakh debt.",
        "common_mistakes": [
            "Treating insurance as an investment ('If I don't file a claim, my premium is wasted').",
            "Relying solely on employer corporate insurance, which disappears the moment you change jobs or retire.",
            "Waiting until age 40 or until sickness strikes before buying insurance."
        ],
        "key_takeaways": [
            "Insurance is financial protection against sudden, high-cost catastrophic events.",
            "It works by pooling risk across thousands of policyholders.",
            "Premiums are cheapest and medical tests are fewest when you buy in your twenties."
        ],
        "official_source_links": [
            {"title": "IRDAI Consumer Education Portal", "url": "https://policyholder.gov.in"},
            {"title": "Bima Bharosa Grievance System", "url": "https://bimabharosa.irdai.gov.in"}
        ],
        "quizzes": [
            {
                "order_index": 1,
                "question": "What is the primary purpose of buying insurance?",
                "options": [
                    "To double your money over a 10-year period like a mutual fund",
                    "To protect yourself and your dependents from catastrophic financial loss",
                    "To evade paying GST on healthcare products",
                    "To guarantee that you will never fall sick"
                ],
                "correct_option_index": 1,
                "explanation": "Insurance is pure risk transfer and financial protection, not a wealth compounding investment tool."
            },
            {
                "order_index": 2,
                "question": "If you don't file a claim in a particular year, is your premium 'wasted'?",
                "options": [
                    "Yes, the insurer stole your money",
                    "No, you purchased 365 days of guaranteed financial protection and risk coverage",
                    "Yes, you should have admitted yourself to hospital to get your money back",
                    "No, but only if the insurer refunds 100% of the money with interest"
                ],
                "correct_option_index": 1,
                "explanation": "Insurance purchases peaceful protection. Just like you don't regret that your car airbag didn't deploy, you don't regret remaining healthy."
            }
        ]
    },
    {
        "slug": "understanding-health-insurance",
        "order_index": 2,
        "title": "Understanding Health Insurance: Cashless vs Reimbursement",
        "subtitle": "How hospital bills are settled in India and how to avoid running around with papers.",
        "category": "Health",
        "estimated_minutes": 8,
        "level": "Beginner",
        "concept_explanation": """
Health insurance covers medical hospitalization costs. In India, there are two ways a claim is settled:

1. **Cashless Claim:** You get treated at a **Network Hospital**. You present your digital insurance card and Government ID at the hospital's TPA / Insurance desk. The hospital sends an electronic pre-authorization request to your insurer. Once approved, the insurer settles the bill directly with the hospital. You only pay for non-covered items (such as gloves or registration charges).

2. **Reimbursement Claim:** If you get admitted to a hospital that is NOT part of the insurer's network, you must pay the entire hospital bill upfront from your own pocket upon discharge. Afterwards, you collect all original discharge summaries, itemized bills, pharmacy receipts, and doctor prescriptions, submit them to the insurer, and wait 15 to 30 days to receive reimbursement into your bank account.
        """,
        "why_it_matters": "Cashless settlement eliminates the need to arrange ₹5 Lakhs to ₹10 Lakhs in liquid cash during an emotional medical crisis.",
        "practical_indian_example": "When Sunita was admitted for a planned gall bladder surgery at an Apollo hospital (which is on her insurer's network), the hospital desk handled the ₹1,20,000 bill directly. She walked out paying only ₹1,800 for disposable patient kits.",
        "common_mistakes": [
            "Forgetting to notify the insurer within 24 hours of an emergency hospitalization.",
            "Failing to collect original itemized pharmacy bills and discharge summaries during reimbursement.",
            "Assuming all hospitals provide cashless automatically without checking the insurer's network list."
        ],
        "key_takeaways": [
            "Cashless claims are settled directly between insurer and network hospital.",
            "Reimbursement requires paying upfront and submitting original bills later.",
            "Always intimate your insurer immediately upon admission (within 24-48 hours)."
        ],
        "official_source_links": [
            {"title": "IRDAI Master Circular on Health Insurance", "url": "https://www.irdai.gov.in"},
            {"title": "General Insurance Council 'Cashless Everywhere'", "url": "https://www.gicouncil.in"}
        ],
        "quizzes": [
            {
                "order_index": 1,
                "question": "What is the main benefit of a Cashless hospitalization claim?",
                "options": [
                    "You get free food in the hospital cafeteria",
                    "The insurer settles medical bills directly with the hospital so you don't pay upfront",
                    "The doctor waives all surgery charges",
                    "You are exempt from paying future insurance premiums"
                ],
                "correct_option_index": 1,
                "explanation": "Cashless claims allow direct electronic settlement between insurer and hospital, saving you from liquidating funds."
            }
        ]
    },
    {
        "slug": "deductibles-copayments-sublimits",
        "order_index": 3,
        "title": "Deductibles, Co-payments, and Sub-limits (The Hidden Traps)",
        "subtitle": "Learn how small clauses in the fine print can lead to massive out-of-pocket deductions.",
        "category": "Health",
        "estimated_minutes": 10,
        "level": "Intermediate",
        "concept_explanation": """
Many first-time buyers choose the cheapest policy without realizing it contains **out-of-pocket cost traps**:

1. **Room Rent Capping:** If a policy limits room rent to '1% of Sum Insured' on a ₹5L cover, you are only entitled to a room costing ₹5,000/day. If you stay in an ₹8,000 room, the hospital applies **Proportionate Deduction**, cutting your surgeon fees, nursing charges, and doctor visits by 37.5%!
2. **Co-payment:** A clause stating you must pay a fixed percentage (e.g. 10% or 20%) of the total approved bill yourself.
3. **Sub-limits:** Specific maximum caps on common procedures (e.g. Cataract surgery capped at ₹30,000, or Joint Replacement capped at ₹1.5 Lakhs), even if your overall policy is ₹10 Lakhs!
4. **Deductible:** A fixed threshold amount that you must pay out-of-pocket before the policy pays anything.
        """,
        "why_it_matters": "A policy with a 1% room rent cap and a 20% co-pay can turn a ₹5 Lakh hospital bill into a ₹2.2 Lakh personal expense, completely defeating the purpose of buying insurance.",
        "practical_indian_example": "Amit had a ₹5L policy with a 1% room rent cap (₹5,000). He chose a room costing ₹10,000/day for 4 days. Because he exceeded the room limit by 100%, the insurer halved his ₹3,00,000 total bill. Amit received only ₹1,50,000 and had to pay ₹1,50,000 from his savings.",
        "common_mistakes": [
            "Buying policies with 1% room rent caps to save ₹1,500 on annual premium.",
            "Accepting mandatory co-payments for young individuals.",
            "Ignoring disease-specific sub-limits on heart stents, cataracts, and knee surgeries."
        ],
        "key_takeaways": [
            "Always choose 'No Room Rent Capping' or 'Single Private Room' eligibility.",
            "Avoid policies with mandatory co-payments unless required for senior citizens.",
            "Look for policies with zero sub-limits on common medical conditions."
        ],
        "official_source_links": [
            {"title": "IRDAI Standardization of Health Insurance Contracts", "url": "https://policyholder.gov.in"}
        ],
        "quizzes": [
            {
                "order_index": 1,
                "question": "What happens if you stay in a hospital room that costs more than your policy's Room Rent Cap?",
                "options": [
                    "You only pay the difference in room rent per day",
                    "The insurer proportionally reduces payouts across doctor fees, surgery, and nursing",
                    "The hospital automatically upgrades you for free",
                    "The insurer pays the entire bill without penalty"
                ],
                "correct_option_index": 1,
                "explanation": "Under the Proportionate Deduction clause, exceeding the room rent limit reduces associated medical expenses proportionally!"
            }
        ]
    },
    {
        "slug": "waiting-periods-ped-exclusions",
        "order_index": 4,
        "title": "Waiting Periods, Pre-Existing Diseases (PED), and Exclusions",
        "subtitle": "Why declaring medical history honestly is the only way to ensure your claim is paid.",
        "category": "Health",
        "estimated_minutes": 9,
        "level": "Intermediate",
        "concept_explanation": """
Every health insurance policy in India contains three standard waiting periods:

1. **Initial Waiting Period (30 Days):** No illness is covered for the first 30 days from policy inception. The only exception is accidental injuries requiring hospitalization, which are covered from Day 1.
2. **Specific Illness Waiting Period (24 Months):** Common non-emergency, slow-developing conditions like cataracts, kidney stones, piles, hernia, joint replacements, and uterine fibroids require 2 years of continuous coverage before claims are honored.
3. **Pre-Existing Disease (PED) Waiting Period (24-36 Months):** Any medical condition you already have prior to buying the policy (such as Diabetes, Hypertension, Thyroid, Asthma) must undergo a waiting period of up to 3 years.

**Exclusions:** Permanent situations that are never covered under standard health policies, such as cosmetic surgery, self-inflicted injuries, and adventure sports injuries.
        """,
        "why_it_matters": "Attempting to hide diabetes or hypertension to get a policy issued without medical checkup will backfire: insurers easily detect medical history from hospital discharge summaries, leading to outright claim rejection.",
        "practical_indian_example": "Kavita declared her mild hypertension when buying her policy. After completing her 36-month waiting period, she was admitted for a cardiovascular blockage. Because she disclosed her condition truthfully from day 1, her ₹4.5 Lakh claim was settled without question.",
        "common_mistakes": [
            "Letting an aggressive insurance agent fill the form with 'No' to all medical questions.",
            "Assuming a pre-existing condition will never be found out by the insurer's investigation team.",
            "Believing that waiting periods restart every year upon policy renewal (waiting periods are cumulative)."
        ],
        "key_takeaways": [
            "Accidents are covered from Day 1; general sickness after 30 days.",
            "Pre-existing illnesses require 24 to 36 months of waiting period.",
            "Honest disclosure at inception is the single biggest guarantee of claim approval."
        ],
        "official_source_links": [
            {"title": "IRDAI Guidelines on Pre-Existing Conditions", "url": "https://www.irdai.gov.in"}
        ],
        "quizzes": [
            {
                "order_index": 1,
                "question": "If you suffer an accidental bone fracture on day 10 of a new health policy, is it covered?",
                "options": [
                    "No, because the 30-day initial waiting period applies to all treatments",
                    "Yes, because emergency accidental hospitalizations are covered from Day 1",
                    "Only if you pay a double premium penalty",
                    "No, fractures take 24 months to become eligible"
                ],
                "correct_option_index": 1,
                "explanation": "Accidental injuries are exempt from the 30-day initial waiting period and are covered from Day 1."
            }
        ]
    },
    {
        "slug": "term-life-vs-investment-schemes",
        "order_index": 5,
        "title": "Term Life Insurance vs Investment Schemes (Endowment & ULIPs)",
        "subtitle": "Why mixing insurance with investment is a financial blunder.",
        "category": "Life",
        "estimated_minutes": 8,
        "level": "Beginner",
        "concept_explanation": """
In India, millions of people buy traditional **Endowment, Money-Back, or ULIP plans** believing they are doing smart financial planning. In reality:

- **Traditional Endowment / Money-Back Policy:** You pay ₹50,000 every year for 20 years. If you die, your family gets ₹10 Lakhs. If you survive, you get back ₹15 Lakhs. That represents a terrible annualized return of just 4-5% (lower than inflation), while leaving your family with a measly ₹10 Lakh cover that won't even last 2 years!
- **Pure Term Life Insurance:** You pay just ₹8,000/year for pure protection. If you pass away, your family receives a massive **₹1 Crore**. If you survive, you receive ₹0 back.

**The Golden Rule:** Keep Insurance and Investment completely separate. Buy pure Term Insurance for protection, and invest the remaining money in Equity Mutual Funds / PPF for wealth creation!
        """,
        "why_it_matters": "A breadwinner with ₹50,000/month salary needs at least ₹1 Crore coverage (15-20x annual income) to protect their spouse and children, which only pure term insurance can provide affordably.",
        "practical_indian_example": "Rahul pays ₹60,000/yr for an endowment plan offering ₹12 Lakh cover. Vikram pays ₹9,000/yr for a ₹1 Crore pure term plan, and invests the remaining ₹51,000/yr in a Nifty 50 index fund. After 25 years, Vikram's family had 8X higher life coverage throughout, and his mutual fund corpus grew to over ₹70 Lakhs!",
        "common_mistakes": [
            "Buying insurance because an uncle/agent told you 'You get all your money back with bonus!'",
            "Buying a life insurance policy for a child (children don't have dependents or income to replace).",
            "Having inadequate life cover (₹5L or ₹10L) when family living expenses require ₹1 Crore."
        ],
        "key_takeaways": [
            "Pure term insurance gives the highest coverage for the lowest premium.",
            "Endowment plans give poor returns (~4-5%) and dangerously low life coverage.",
            "Target a term life cover equal to 15-20 times your annual take-home income."
        ],
        "official_source_links": [
            {"title": "IRDAI Consumer Protection in Life Insurance", "url": "https://policyholder.gov.in"}
        ],
        "quizzes": [
            {
                "order_index": 1,
                "question": "Why is pure Term Insurance superior to traditional Endowment policies for protection?",
                "options": [
                    "It gives a huge sum assured (e.g. ₹1 Crore) at a very low cost, allowing you to invest savings separately",
                    "It promises guaranteed 15% stock market returns",
                    "It is run only by foreign government agencies",
                    "You can take out personal gold loans against it"
                ],
                "correct_option_index": 0,
                "explanation": "Pure term insurance focuses exclusively on providing high death benefit affordably without diluting money into low-yield endowments."
            }
        ]
    },
    {
        "slug": "motor-insurance-explained",
        "order_index": 6,
        "title": "Motor Insurance: Third-Party vs Comprehensive Explained",
        "subtitle": "Navigating Indian motor vehicle laws, Zero Dep add-on, and IDV.",
        "category": "Motor",
        "estimated_minutes": 7,
        "level": "Beginner",
        "concept_explanation": """
Under the Indian Motor Vehicles Act, motor insurance is legally mandatory for any vehicle driven on public roads:

1. **Third-Party (TP) Liability Cover (Mandatory by Law):** Covers bodily injury, death, or property damage caused by your vehicle to another person (the third party). It does **NOT** pay a single rupee for repairs to your own vehicle!
2. **Comprehensive Motor Insurance (Own Damage + Third Party):** Covers both third-party legal liability AND accidental damage, fire, flood, cyclone, or theft of your own car or bike.
3. **Zero Depreciation (Bumper-to-Bumper) Add-on:** Standard policies deduct 50% on plastic/fiber parts due to aging. Zero Dep waives this deduction, paying 100% of replacement costs during accident repairs.
        """,
        "why_it_matters": "Driving without at least a valid Third-Party insurance policy attracts a ₹2,000 fine and up to 3 months imprisonment under the amended Motor Vehicles Act.",
        "practical_indian_example": "Deepak's car collided with a pole, damaging the front bumper, headlight, and radiator (repair bill ₹32,000). With his Zero Dep add-on, the insurer paid ₹31,000 and Deepak paid only the standard ₹1,000 compulsory file charge.",
        "common_mistakes": [
            "Assuming third-party insurance will pay for your own car's dent repairs.",
            "Letting your Insured Declared Value (IDV) drop unrealistically low just to save ₹200 on premium.",
            "Forgetting to transfer accumulated No Claim Bonus (NCB) when selling an old car and buying a new one."
        ],
        "key_takeaways": [
            "Third-party insurance is legally mandatory; comprehensive is practically essential.",
            "Zero Depreciation add-on eliminates 50% deductions on plastic and fiber parts.",
            "NCB belongs to the car owner, not the car, and can be transferred to a new vehicle."
        ],
        "official_source_links": [
            {"title": "Ministry of Road Transport & Highways Motor Rules", "url": "https://morth.nic.in"}
        ],
        "quizzes": [
            {
                "order_index": 1,
                "question": "Does mandatory Third-Party Motor Insurance cover repairs to your own car if you cause an accident?",
                "options": [
                    "Yes, up to 100% of car value",
                    "No, it only covers liabilities and damages caused to other people and their property",
                    "Only if the accident occurred on a national highway",
                    "Yes, provided you pay an extra fee at the police station"
                ],
                "correct_option_index": 1,
                "explanation": "Third-Party insurance protects others from harm caused by your vehicle; it covers zero damage to your own car."
            }
        ]
    },
    {
        "slug": "how-to-read-policy-wordings",
        "order_index": 7,
        "title": "How to Read Policy Wordings & Prospectus Like a Pro",
        "subtitle": "Deciphering the legal document behind glossy advertising brochures.",
        "category": "Basics",
        "estimated_minutes": 8,
        "level": "Intermediate",
        "concept_explanation": """
An insurance sales brochure is marketing material; the **Policy Wording** is the legally binding contract between you and the insurance company.

To inspect any Indian insurance policy document like an expert, focus on these five specific sections:
1. **Definitions Section:** Check how 'Hospital', 'Room Rent', and 'Pre-existing Disease' are legally defined.
2. **Scope of Coverage:** Look for pre- and post-hospitalization day limits (ideal is 60/180 days).
3. **Specific Condition Sub-limits:** Search for caps on Robotic Surgeries, Cataracts, Stents, and Modern Treatments.
4. **Permanent Exclusions:** Review the standard exclusions list (Section 4) mandated by IRDAI.
5. **Portability and Renewal Clauses:** Verify that the policy offers guaranteed lifetime renewability without age-based cancellation.
        """,
        "why_it_matters": "Sales agents may say 'everything is covered', but the policy wording is the only document that a court of law or insurance ombudsman will enforce.",
        "practical_indian_example": "Rajesh was told by an agent that his health policy covers robotic cancer surgery. Upon reading Section 3.8 of the policy wording, he discovered robotic surgeries were capped at ₹1 Lakh, despite a ₹15 Lakh sum insured! He immediately opted for a policy without sub-limits.",
        "common_mistakes": [
            "Relying solely on one-page marketing flyers.",
            "Not looking up the policy's UIN (Unique Identification Number) on the IRDAI portal.",
            "Discarding the policy wording document without reviewing during the 30-day Free-Look period."
        ],
        "key_takeaways": [
            "The Policy Wording is the true legal contract, not the sales brochure.",
            "Verify room rent, sub-limits, and exclusions in the actual document.",
            "Use the 30-day Free-Look window to cancel if the wording contradicts what was sold."
        ],
        "official_source_links": [
            {"title": "IRDAI Product Filing Verification", "url": "https://www.irdai.gov.in"}
        ],
        "quizzes": [
            {
                "order_index": 1,
                "question": "If an insurance agent's verbal promise conflicts with the written Policy Wording, which one prevails?",
                "options": [
                    "The agent's verbal promise",
                    "The written Policy Wording document registered with IRDAI",
                    "Whichever benefits the customer more",
                    "The hospital's billing desk rules"
                ],
                "correct_option_index": 1,
                "explanation": "The registered Policy Wording is the sole legally binding contract recognized by consumer courts and the ombudsman."
            }
        ]
    },
    {
        "slug": "claim-filing-and-rejection",
        "order_index": 8,
        "title": "Claim Filing Process & Top Reasons Claims Get Rejected",
        "subtitle": "Step-by-step claim settlement guide and what to do if an insurer rejects your claim.",
        "category": "Claims",
        "estimated_minutes": 9,
        "level": "Intermediate",
        "concept_explanation": """
Understanding the claim process ensures you never face sudden rejections:

**Step-by-Step Cashless Hospitalization:**
1. **Intimation:** For planned hospitalizations, notify the insurer/TPA 48 hours prior. For emergencies, notify within 24 hours of admission.
2. **Pre-Authorization:** Submit insurance e-card and doctor's admission advice at the hospital insurance desk.
3. **Approval:** Insurer reviews policy limits and issues initial approval letter.
4. **Final Discharge:** Hospital submits final bill, pharmacy receipts, and discharge summary; insurer settles the approved amount.

**Top Reasons Claims Get Rejected in India:**
1. Non-disclosure or concealment of pre-existing medical conditions (PED).
2. Claim filed during the active waiting period (e.g. planned surgery in year 1).
3. Treatment in an excluded/blacklisted hospital (fraudulent clinic).
4. Admission primarily for diagnostic tests without active in-patient medical management.
5. Inordinate delay in intimating the insurer without valid justification.
        """,
        "why_it_matters": "Knowing how to appeal an unfair rejection through the **Internal Grievance Officer, Bima Bharosa portal, or the Insurance Ombudsman** can recover lakhs of rupees without hiring lawyers.",
        "practical_indian_example": "When Priya's mother was hospitalized, the insurer initially deducted ₹40,000 citing missing investigation reports. Priya collected the signed doctor's lab notes, submitted a formal reconsideration request through the insurer's portal, and had the full ₹40,000 reimbursed within 7 working days.",
        "common_mistakes": [
            "Failing to notify the insurer within 24-48 hours of admission.",
            "Throwing away original cash receipts for pharmacy and blood tests.",
            "Accepting an unfair rejection without filing an appeal with the Insurance Ombudsman (which is 100% free)."
        ],
        "key_takeaways": [
            "Always notify the insurer within 24 hours of emergency hospitalization.",
            "Save every doctor prescription and itemized hospital bill.",
            "The Insurance Ombudsman offers free, binding dispute resolution if an insurer rejects your valid claim."
        ],
        "official_source_links": [
            {"title": "Insurance Ombudsman India Portal", "url": "https://www.cioins.co.in"},
            {"title": "Bima Bharosa Online Grievance System", "url": "https://bimabharosa.irdai.gov.in"}
        ],
        "quizzes": [
            {
                "order_index": 1,
                "question": "What is the single most common reason health insurance claims are repudiated in India?",
                "options": [
                    "Paying premium online using UPI",
                    "Non-disclosure of pre-existing medical history at proposal stage",
                    "Getting treated on a weekend",
                    "Visiting a doctor younger than 40 years"
                ],
                "correct_option_index": 1,
                "explanation": "Concealing medical history like diabetes or hypertension is the leading cause of claim rejection across Indian insurers."
            }
        ]
    },
    {
        "slug": "spotting-misleading-sales-tactics",
        "order_index": 9,
        "title": "How to Identify Misleading Insurance Selling Practices",
        "subtitle": "Protect yourself from deceptive bank cross-selling, phantom bonuses, and dark patterns.",
        "category": "Consumer Protection",
        "estimated_minutes": 8,
        "level": "Advanced",
        "concept_explanation": """
Insurance mis-selling is rampant in India. Here are the most common tactics used by deceptive sellers and how to counter them:

1. **Bank Locker / Loan Tie-in Extortion:** Bank managers telling you, 'To get a home loan or bank locker, you must purchase this ₹1 Lakh/yr insurance policy.' This is **illegal and strictly prohibited by RBI and IRDAI**.
2. **Phantom 'Guaranteed Return' Pitch:** Agents presenting a life insurance policy as a 'high-yield fixed deposit' or 'special government tax-free bond'.
3. **Ghost Form Filling:** Agents asking you to just sign blank forms while they tick 'No' on all health questions to ensure quick policy issuance.
4. **Fake IRDAI Bonus Calls:** Fraudsters calling pretending to be from IRDAI offering 'unclaimed bonuses' if you buy a new policy. **IRDAI never calls customers or sells insurance!**
        """,
        "why_it_matters": "Falling for misleading selling locks your hard-earned money into multi-year commitments that offer terrible value and high surrender penalties.",
        "practical_indian_example": "When applying for an education loan, Meera was told she must buy a ₹40,000 endowment insurance policy. Knowing RBI regulations, she requested the manager's requirement in writing citing RBI circular RBI/2014-15/419. The bank immediately waived the condition and disbursed her loan.",
        "common_mistakes": [
            "Signing blank proposal forms.",
            "Believing callers claiming IRDAI is distributing bonuses.",
            "Accepting mandatory insurance bundling for bank services without questioning."
        ],
        "key_takeaways": [
            "Banks cannot force you to buy insurance to open accounts or get loans.",
            "IRDAI does not sell policies or distribute financial bonuses.",
            "Use the 30-day Free-Look period immediately if you were tricked into buying a bad policy."
        ],
        "official_source_links": [
            {"title": "IRDAI Warning on Spurious Calls and Fictitious Offers", "url": "https://policyholder.gov.in"},
            {"title": "RBI Guidelines on Bank Assurance Mis-selling", "url": "https://www.rbi.org.in"}
        ],
        "quizzes": [
            {
                "order_index": 1,
                "question": "Can a bank legally force you to buy an insurance policy as a mandatory condition for sanctioning a home loan?",
                "options": [
                    "Yes, banks make their own legal rules in India",
                    "No, coercive bundling of insurance with loans is strictly prohibited by RBI and IRDAI regulations",
                    "Only if the loan amount is over ₹5 Lakhs",
                    "Yes, if the branch manager insists"
                ],
                "correct_option_index": 1,
                "explanation": "RBI and IRDAI strictly prohibit banks from tying loan approval to the purchase of insurance products."
            }
        ]
    },
    {
        "slug": "how-to-choose-insurance-policy",
        "order_index": 10,
        "title": "How to Choose an Insurance Policy Based on Life Stage & Budget",
        "subtitle": "A pragmatic, step-by-step decision framework tailored to your age and finances.",
        "category": "Consumer Protection",
        "estimated_minutes": 9,
        "level": "Advanced",
        "concept_explanation": """
Here is your life-stage insurance checklist:

**Stage 1: In Your 20s (First Job, Unmarried)**
- **Health:** Get an individual ₹10 Lakh to ₹15 Lakh health policy with No Room Rent Capping and Zero Co-pay. Premiums are at their lowest (~₹600 - ₹900/month).
- **Term Life:** If you have financially dependent parents or educational loans, buy a ₹1 Crore pure term policy.

**Stage 2: In Your 30s (Married, Young Kids)**
- **Health:** Upgrade to a Family Floater (₹15L to ₹25L) or maintain separate base covers plus a high-deductible Super Top-up policy (₹50 Lakhs).
- **Term Life:** Essential. Maintain 15-20X annual income pure term cover with critical illness rider.

**Stage 3: In Your 40s & 50s (Approaching Peak Income & Aging Parents)**
- **Health:** Separate aging parents onto their own senior citizen plan so their health claims don't raise floater premiums for you and your children.
- **Top-up Cover:** Add a ₹50L or ₹1 Crore Super Top-up cover to buffer against serious illnesses like oncology or cardiac surgeries.
        """,
        "why_it_matters": "Structuring your policies correctly by life stage prevents overpaying on unneeded riders while avoiding catastrophic under-insurance when your family depends on you.",
        "practical_indian_example": "At age 31, Karthik bought a ₹10L base health policy (₹10,500/yr) and added a ₹40L Super Top-up with a ₹10L deductible (₹4,200/yr). For just ₹14,700/year, he secured a massive ₹50 Lakh total safety net for his family!",
        "common_mistakes": [
            "Clubbing 65-year-old parents with young children on the same family floater policy.",
            "Buying expensive low-deductible policies when a Base + Super Top-up combination gives 5X coverage at the same price.",
            "Postponing term insurance until 40 when premium rates double or health conditions disqualify you."
        ],
        "key_takeaways": [
            "Separate elderly parents onto dedicated policies to protect your family floater.",
            "Combine a ₹10L Base Policy with a ₹40L Super Top-up for maximum cost efficiency.",
            "Lock in term life insurance in your twenties to pay low fixed rates for 30 years."
        ],
        "official_source_links": [
            {"title": "IRDAI Consumer Guide to Insurance Planning", "url": "https://policyholder.gov.in"}
        ],
        "quizzes": [
            {
                "order_index": 1,
                "question": "Why is it wise to keep elderly parents on a separate health policy rather than your family floater?",
                "options": [
                    "Parents are legally forbidden from sharing family insurance in India",
                    "The highest age in a floater determines the premium for everyone, and parents' claims will exhaust the family's shared sum insured",
                    "Senior citizens cannot use cashless network hospitals",
                    "Because floater policies only cover vehicles"
                ],
                "correct_option_index": 1,
                "explanation": "In a floater, the oldest member sets the premium rate, and their higher claim frequency risks exhausting cover for your spouse and kids."
            }
        ]
    }
,

    {'slug': 'super-top-up-explained', 'order_index': 11, 'title': 'Super Top-Up: Get ₹25 Lakh Cover for ₹5,000 a Year', 'subtitle': 'How combining a base policy with a Super Top-Up is the smartest hack in Indian health insurance.', 'category': 'Health', 'estimated_minutes': 8, 'level': 'Intermediate', 'concept_explanation': "\nIf you have ever wondered how people get ₹20 Lakh or ₹25 Lakh health coverage without paying a huge premium, the answer is almost always a **Super Top-Up policy**.\n\n**How it works — the core idea:**\nA Super Top-Up policy has a 'deductible' — a minimum threshold of claims you must cross in a year before the top-up kicks in. Unlike a plain Top-Up (which applies the deductible *per claim*), a Super Top-Up applies the deductible once to the **total of all claims in the entire year**.\n\n**The cost-efficient combination:**\n| Layer | Cover | Annual Premium (age 30) |\n|---|---|---|\n| Base Health Policy | ₹5 Lakh | ₹8,000/year |\n| Super Top-Up (₹5L deductible) | ₹20 Lakh | ₹3,000–₹4,500/year |\n| **Total effective cover** | **₹25 Lakh** | **₹11,000–₹12,500/year** |\n\nBuying a standalone ₹25 Lakh health policy would cost ₹22,000–₹28,000/year. The combo costs less than half!\n\n**Key rule:** The Super Top-Up deductible must equal or be lower than your base policy's sum insured. A mismatch creates an uncovered gap you must pay from your own pocket.\n", 'why_it_matters': 'Medical inflation in India runs at 12–14% annually. A cardiac bypass surgery that cost ₹3.5 Lakhs in 2015 costs ₹6–8 Lakhs in 2025. A ₹5 Lakh standalone policy is dangerously inadequate for serious illnesses. The Super Top-Up combo gets you meaningful coverage without breaking the bank.', 'practical_indian_example': 'Anand (32, Bengaluru, IT professional) has a ₹5 Lakh employer group policy. He adds a personal ₹20 Lakh Super Top-Up (₹5 Lakh deductible) for ₹3,800/year. When he undergoes cardiac angioplasty costing ₹8.5 Lakhs, his employer policy covers ₹5 Lakhs and the Super Top-Up pays ₹3.5 Lakhs. Total out-of-pocket cost: ₹0. Total personal premium paid: ₹3,800/year.', 'common_mistakes': ['Buying a Super Top-Up without a base policy — you end up paying the full deductible from pocket.', "Choosing a higher deductible than your base policy's sum insured, creating an uncovered gap.", "Confusing Super Top-Up with plain Top-Up — the 'per-claim vs. yearly aggregate' difference is critical.", "Not checking if the Super Top-Up insurer's network hospital list overlaps with your base policy's network."], 'key_takeaways': ['Super Top-Up applies its deductible once to ALL claims in the year, not per individual claim.', 'Base policy sum insured must equal the Super Top-Up deductible to avoid coverage gaps.', 'The combo (base + Super Top-Up) costs 40–60% less than buying equivalent standalone cover.', 'Ideal strategy: ₹5 Lakh base + ₹20–25 Lakh Super Top-Up for comprehensive affordable coverage.'], 'official_source_links': [{'title': 'IRDAI Health Insurance Guidelines', 'url': 'https://www.irdai.gov.in'}, {'title': 'IRDAI Consumer Education Portal', 'url': 'https://policyholder.gov.in'}], 'quizzes': [{'order_index': 1, 'question': 'Rohan has a ₹5 Lakh base policy and a Super Top-Up with ₹5 Lakh deductible. He makes three claims in a year: ₹2L, ₹2L, and ₹3L. How much does the Super Top-Up pay?', 'options': ["₹0 — the Super Top-Up doesn't cover anything", '₹2 Lakh — because the total (₹7L) exceeds the ₹5L deductible by ₹2L', '₹7 Lakh — the Super Top-Up pays everything', '₹3 Lakh — it only pays on the largest single claim'], 'correct_option_index': 1, 'explanation': "The Super Top-Up's deductible is applied to the TOTAL yearly claims. Total = ₹7L. Deductible = ₹5L. The Super Top-Up pays ₹7L − ₹5L = ₹2L."}, {'order_index': 2, 'question': 'Which of these is the main advantage of a Super Top-Up over a plain Top-Up?', 'options': ['Super Top-Up has lower premiums because it covers fewer conditions', 'Super Top-Up applies the deductible once to all yearly claims combined, not per claim', "Super Top-Up doesn't require a base policy", 'Super Top-Up automatically renews without any waiting period'], 'correct_option_index': 1, 'explanation': 'The aggregate deductible (per year, not per claim) is the defining feature of a Super Top-Up, making it far more useful than a plain Top-Up when multiple hospitalizations occur in a year.'}]},
    {'slug': 'family-floater-vs-individual', 'order_index': 12, 'title': 'Family Floater vs. Individual Policies: Which Protects Better?', 'subtitle': 'Understanding when shared cover is smart and when it becomes a dangerous gamble.', 'category': 'Health', 'estimated_minutes': 7, 'level': 'Intermediate', 'concept_explanation': "\n**Family Floater:** One policy, one shared Sum Insured, entire family covered. Any family member can use any portion of the cover in a year.\n\n**Individual Policy:** Each person has their own dedicated Sum Insured. Claims by one person don't reduce cover available to another.\n\n**When Family Floater makes sense:**\n- Young nuclear family (ages 25–45) with no major health conditions\n- Budget-conscious buyers wanting lower combined premium\n- Families where simultaneous hospitalisations are statistically unlikely\n\n**When Individual Policies make more sense:**\n- Including parents above 55 in a floater raises everyone's premium significantly\n- A family member with a chronic illness (diabetes, hypertension) will exhaust shared cover\n- Multiple simultaneous hospitalisations (e.g. accident) could exhaust floater cover instantly\n\n**The Premium Impact of Age:**\nIn a floater, the premium is calculated based on the **oldest member's age**. Adding a 62-year-old parent to a young family's floater can **double the premium** overnight.\n\n**The Smart Approach:**\nBuy a floater for the young nuclear family. Buy separate individual senior citizen policies for parents. Add a Super Top-Up layer for everyone.\n", 'why_it_matters': 'Making the wrong choice between floater and individual can either leave you paying far too much in premiums or leave family members exposed during a crisis when shared cover is already exhausted.', 'practical_indian_example': "Meera and her husband (both 34) have two children (6 and 9) and her parents (both 64). Option A: One family floater for all 6 = ₹42,000/year (premium driven by 64-year-old parents). Option B: ₹10L floater for the 4 young members (₹14,500/year) + two separate senior policies for parents (₹28,000/year combined) = ₹42,500 total but FAR better protection with no risk of parents' frequent claims exhausting children's cover.", 'common_mistakes': ["Adding senior parents to a young family's floater without considering the premium and claim impact.", 'Buying only ₹5 Lakh floater for 4–5 family members — exhaustion risk is very high.', 'Assuming family floater is always cheaper — for families with elderly members, it often is not.', 'Not adding a restoration benefit to a floater — essential to refill cover if it gets exhausted mid-year.'], 'key_takeaways': ['Family floater = shared pool; individual = dedicated cover. Shared pools deplete on heavy use.', 'Premium in a floater is based on the oldest member — adding elderly parents can be very expensive.', 'For young nuclear families without chronic illness, floaters are cost-effective.', 'Always add a Super Top-Up over a floater base for genuinely large coverage at low cost.'], 'official_source_links': [{'title': 'IRDAI Master Circular on Health Insurance 2024', 'url': 'https://www.irdai.gov.in'}], 'quizzes': [{'order_index': 1, 'question': 'Deepa (32) wants to add her father (67) to her ₹10 Lakh family floater. What is the PRIMARY risk of doing this?', 'options': ['IRDAI prohibits adding parents above 60 to family floaters', "The premium will be based on her father's age (67), significantly increasing costs, and his frequent claims could exhaust cover for Deepa's children", 'Her father cannot use cashless facilities in a family floater', 'Family floaters only allow 3 members maximum by law'], 'correct_option_index': 1, 'explanation': "The oldest member's age sets the premium rate, and a senior citizen's frequent claims risk depleting the shared Sum Insured, leaving other family members under-covered."}]},
    {'slug': 'travel-insurance-complete-guide', 'order_index': 13, 'title': 'Travel Insurance: Why Skipping It on Your Next Trip Is Risky', 'subtitle': 'Medical emergencies abroad, trip cancellations, and baggage loss — what travel insurance actually covers.', 'category': 'Travel', 'estimated_minutes': 9, 'level': 'Beginner', 'concept_explanation': '\nTravel insurance is a short-term, trip-specific policy that covers a range of financial losses that can occur while travelling — domestically or internationally. It is one of the most underutilised insurance products in India despite being one of the cheapest.\n\n**What Travel Insurance Covers (Key Sections):**\n\n**1. Emergency Medical Expenses (Abroad)**\nHealthcare costs in countries like the USA, UK, or Singapore are 20–50× higher than India. A simple appendicitis surgery in the USA costs ₹30–₹50 Lakhs. Your domestic health insurance does NOT cover international treatment. Travel insurance pays for emergency hospitalisation, surgery, ambulance, and evacuation.\n\n**2. Trip Cancellation & Interruption**\nIf you must cancel a non-refundable ₹2 Lakh flight + hotel booking due to sudden illness or a family emergency, travel insurance reimburses the non-refundable losses.\n\n**3. Baggage Loss & Delay**\nIf your checked baggage is lost, delayed, or stolen, travel insurance pays up to a fixed limit (typically USD 500–1,000) for replacement of essentials and lost items.\n\n**4. Passport Loss**\nEmergency assistance and expenses for replacing a lost passport abroad.\n\n**5. Flight Delay Compensation**\nIf your flight is delayed more than 6–12 hours, daily allowances are paid.\n\n**6. Personal Liability**\nIf you accidentally injure someone or damage property in a foreign country, travel insurance covers legal costs.\n\n**Cost:** For a 10-day international trip, a comprehensive travel policy costs ₹800–₹2,500 — a tiny fraction of any potential loss.\n', 'why_it_matters': 'A single medical emergency in the USA, Europe, or UAE can cost ₹20 Lakhs to ₹1 Crore — amounts that can wipe out a lifetime of savings. Many Schengen visa applications for Europe legally REQUIRE proof of travel insurance with minimum EUR 30,000 (₹27 Lakh) medical cover.', 'practical_indian_example': 'Vikram (38, Hyderabad) travelled to Dubai for a week without travel insurance to save ₹900. On Day 3, he had a severe asthma attack requiring emergency hospitalisation for 2 days. The UAE hospital bill: AED 28,000 (≈₹6.5 Lakhs). Vikram had to make an emergency call home for fund transfer. A ₹900 travel policy would have covered every rupee of this bill.', 'common_mistakes': ['Assuming domestic health insurance covers international medical emergencies — it does NOT.', 'Buying travel insurance with inadequate medical cover (less than USD 100,000 for international trips).', "Not reading the 'pre-existing disease' exclusion — most travel policies don't cover PED-related emergencies abroad.", 'Skipping travel insurance for short trips or domestic travel (domestic travel insurance is surprisingly cheap and useful).'], 'key_takeaways': ['Your Indian health insurance does NOT cover medical emergencies abroad — travel insurance does.', 'For Schengen (Europe) visas, EUR 30,000 medical cover travel insurance is legally mandatory.', 'A 10-day international travel policy costs ₹800–₹2,500 — always worth buying.', 'Read the PED exclusion clause — most travel policies exclude emergency hospitalisation caused by declared pre-existing conditions.'], 'official_source_links': [{'title': 'IRDAI on Travel Insurance', 'url': 'https://www.irdai.gov.in'}, {'title': 'IRDAI Consumer Education Portal', 'url': 'https://policyholder.gov.in'}], 'quizzes': [{'order_index': 1, 'question': 'Does your Indian health insurance policy cover a medical emergency that occurs in London (UK)?', 'options': ['Yes, Indian health insurance covers emergencies worldwide', 'No, Indian health insurance is valid only within India — you need separate travel insurance for international cover', 'Yes, if you have a policy with more than ₹10 Lakh sum insured', 'Yes, all IRDAI-regulated policies cover emergencies in Commonwealth countries'], 'correct_option_index': 1, 'explanation': 'Standard Indian health insurance policies are valid ONLY within India. Medical emergencies abroad are NOT covered. Travel insurance (or a specific international health plan) is required for overseas coverage.'}, {'order_index': 2, 'question': 'Which of these is NOT typically covered under a standard international travel insurance policy?', 'options': ['Emergency hospitalisation after an accident abroad', 'Loss of checked baggage by the airline', 'Cosmetic dental surgery you planned before the trip', 'Trip cancellation due to sudden serious illness'], 'correct_option_index': 2, 'explanation': 'Planned elective procedures (like cosmetic dentistry) are excluded. Travel insurance covers UNEXPECTED emergencies and accidents, not pre-planned medical treatments.'}]},
    {'slug': 'critical-illness-and-riders', 'order_index': 14, 'title': 'Critical Illness Insurance & Riders: The Lump-Sum Safety Net', 'subtitle': 'Why a cancer or heart attack diagnosis needs more than regular health insurance.', 'category': 'Health', 'estimated_minutes': 8, 'level': 'Intermediate', 'concept_explanation': "\nWhen a life-altering illness strikes — cancer, heart attack, stroke, kidney failure — the financial impact goes far beyond hospital bills. Consider what happens:\n\n- **Income stops:** You or your spouse may be unable to work for 6–18 months.\n- **Ongoing treatment costs:** Chemotherapy cycles, radiation, physiotherapy — these continue for months.\n- **EMIs don't pause:** Home loan, car loan, children's school fees continue regardless.\n- **Lifestyle adjustments:** Dietary changes, medical equipment, nursing care at home.\n\nRegular health insurance reimburses only the hospitalisation bills. It does NOT replace lost income or cover the cascading financial impact of a serious illness.\n\n**Critical Illness (CI) Policy — How It Works:**\nOn diagnosis of any of the listed illnesses (typically 20–36 conditions), the insurer pays the **entire sum assured as a tax-free lump sum** — regardless of actual expenses incurred. You can use the money for anything.\n\n**Common Covered Conditions:**\nCancer (all stages), First Heart Attack, Stroke with permanent symptoms, Kidney Failure, Major Organ Transplant, Coronary Artery Bypass Graft, Paralysis, Multiple Sclerosis, Motor Neuron Disease\n\n**CI as a Rider vs. Standalone Policy:**\n- **Rider:** Added to a term life or health policy at lower cost. Coverage terminates if the base policy ends.\n- **Standalone:** Independent CI policy. More flexible, higher cover, portable.\n\n**The 30-Day Survival Clause:**\nMost CI policies require you to survive 30 days after the diagnosis event to receive the payout. This protects insurers from immediate large payouts on terminal diagnoses.\n", 'why_it_matters': 'In India, 1 in 10 adults will develop cancer in their lifetime. Heart disease is the leading cause of death. Treatment costs for cancer can range from ₹5 Lakhs to ₹50 Lakhs over 2–3 years. During treatment, income often drops to zero. CI insurance bridges this financial catastrophe.', 'practical_indian_example': 'Arun (42, Mumbai) is diagnosed with Stage 2 colon cancer. He has a ₹10 Lakh regular health policy and a ₹25 Lakh CI policy. The health policy covers surgery and hospitalisation (₹8 Lakhs). The CI policy pays ₹25 Lakhs as a lump sum. Arun uses ₹12 Lakhs for chemotherapy cycles (not all covered by health insurance), ₹6 Lakhs to prepay his home loan, and ₹7 Lakhs as income replacement while on medical leave for 14 months.', 'common_mistakes': ['Assuming regular health insurance covers all financial impact of a critical illness — it only covers hospitalisation bills.', 'Not reading which stage of cancer is covered — some CI policies exclude early-stage (Stage 1) cancers.', 'Missing the 30-day survival clause — the insured must survive 30 days post-event to receive payout.', 'Buying insufficient CI cover — ₹10 Lakh is often inadequate; ₹25–₹50 Lakh is recommended.'], 'key_takeaways': ['CI insurance pays a LUMP SUM on diagnosis — not just hospital bills. You use the money as you choose.', "CI complements (doesn't replace) regular health insurance.", 'Most CI policies have a 30-day survival clause post-diagnosis for the lump sum to be payable.', 'A standalone CI policy of ₹25–₹50 Lakh is recommended alongside your base health cover.'], 'official_source_links': [{'title': 'IRDAI Health Insurance Guidelines', 'url': 'https://www.irdai.gov.in'}, {'title': 'National Cancer Grid India', 'url': 'https://www.tmc.gov.in'}], 'quizzes': [{'order_index': 1, 'question': 'If you have a ₹10 Lakh health insurance policy and a ₹25 Lakh critical illness policy, and you are diagnosed with cancer with total treatment costs of ₹15 Lakhs, how much does the CI policy pay?', 'options': ['₹5 Lakh — only the amount not covered by health insurance', '₹25 Lakh — the full sum assured, regardless of actual treatment costs', '₹15 Lakh — the exact treatment cost', '₹0 — because health insurance already covers the treatment'], 'correct_option_index': 1, 'explanation': 'Critical Illness policies pay the FULL sum assured as a lump sum upon diagnosis — completely independently of what other policies pay or what the actual bills are.'}, {'order_index': 2, 'question': "What does the '30-day survival clause' in a Critical Illness policy mean?", 'options': ['You must survive 30 days after buying the policy before CI cover begins', 'The insurer takes 30 days to process the payment after your claim is filed', 'You must survive for 30 days after the diagnosis date to be eligible for the CI payout', "The CI policy lapses if you don't file a claim within 30 days of diagnosis"], 'correct_option_index': 2, 'explanation': 'Most CI policies require the policyholder to survive 30 days post-diagnosis as a pre-condition for receiving the lump sum payout. This is one of the most important clauses to check before purchasing a CI policy.'}]},
    {'slug': 'insurance-portability-and-renewal', 'order_index': 15, 'title': 'Health Insurance Portability & Renewal: Never Lose Your Benefits', 'subtitle': 'How to switch insurers without starting over — and why continuous renewal is non-negotiable.', 'category': 'Consumer Protection', 'estimated_minutes': 7, 'level': 'Intermediate', 'concept_explanation': "\n**What is Portability?**\nIRDAI's portability rules (2011, updated 2024) give you the legal right to move your health insurance policy from one insurer to another at renewal — **without losing the waiting period credits you have already completed.**\n\nThis means: If you've been with Insurer A for 3 years and completed a 2-year PED waiting period for your thyroid condition, moving to Insurer B on porting means Insurer B MUST credit you those 3 years. Your thyroid is covered from Day 1 at the new insurer.\n\n**What Gets Ported:**\n✅ Completed waiting period credit (all types — initial, PED, specific illness)\n✅ Continuity of No Claim Bonus (NCB) — to the extent applicable\n❌ Premium rate is NOT locked — new insurer prices based on current age and health\n❌ Policy-specific benefits (like specific hospital cashback) may not transfer\n\n**The Portability Process:**\n1. Apply to new insurer at least **45 days** before renewal\n2. New insurer submits portability request to old insurer on IRDAI's portal\n3. Old insurer provides claim history within 7 working days\n4. New insurer underwrites and offers a quote\n5. You accept, pay new premium, and get new policy — seamlessly\n\n**Why Continuous Renewal Matters:**\nA lapsed policy = waiting periods reset to zero. Even a 31-day gap eliminates years of accumulated benefits. Set auto-debit for every policy renewal. Treat it like your SIP.\n\n**The 8-Year Moratorium:**\nAfter 8 continuous years with any combination of insurers (porting is counted as continuous), no insurer can reject claims for non-disclosure of PED — except proven fraud.\n", 'why_it_matters': 'Many people stay with an insurer that provides poor service simply because they fear losing their waiting period credits. IRDAI portability gives you the power to switch without penalty. Conversely, a policy lapse — even brief — can wipe out years of protection built through continuous renewals.', 'practical_indian_example': "Sanjana (36, Pune) has been with New India Assurance for 4 years. She completed her 2-year thyroid PED waiting period and built ₹5 Lakh NCB. She is unhappy with claim rejections and poor network hospitals. She ports to Niva Bupa (Bupa India) 45 days before renewal. IRDAI rules mandate Niva Bupa credits her 4 years of continuity. She gets: thyroid covered from Day 1, NCB credited, better hospital network. She starts fresh only on the new policy's specific terms — not the waiting period clock.", 'common_mistakes': ['Waiting until the last moment (less than 45 days before renewal) to apply for portability — this can cause the porting to fail.', 'Letting the old policy lapse before the new policy is confirmed — creates a dangerous coverage gap.', 'Assuming the new insurer must match the old premium — they will price based on current age and health.', 'Not getting the porting confirmation and waiting period credits in writing before cancelling old policy.'], 'key_takeaways': ['IRDAI portability lets you switch insurers at renewal without losing completed waiting period credits.', 'Apply for portability at least 45 days before your renewal date.', 'Never let your current policy lapse before the new policy is active.', 'After 8 continuous years (including ported years), the moratorium protects you from PED-based rejections.'], 'official_source_links': [{'title': 'IRDAI Portability Guidelines', 'url': 'https://www.irdai.gov.in'}, {'title': 'IRDAI Consumer Portal on Portability', 'url': 'https://policyholder.gov.in'}], 'quizzes': [{'order_index': 1, 'question': 'Rahul has completed 3 years with Insurer A and ports to Insurer B. What happens to his 2-year PED waiting period for diabetes that he completed with Insurer A?', 'options': ['He must wait another 2 years for diabetes to be covered with Insurer B', 'Insurer B must credit his 3 years of continuity — his diabetes PED waiting period is already complete and diabetes is covered from Day 1 at Insurer B', 'He loses all waiting period credits because he switched insurers', 'Insurer B covers diabetes only for the first 6 months after porting'], 'correct_option_index': 1, 'explanation': 'IRDAI portability rules mandate that the new insurer credits ALL accumulated continuity from the previous insurer. Completed waiting periods do not reset on a valid port.'}, {'order_index': 2, 'question': 'How many days before your renewal date should you apply for portability to ensure a smooth switch?', 'options': ['7 days before renewal', '15 days before renewal', 'At least 45 days before renewal', 'Any time — portability can be done even after renewal'], 'correct_option_index': 2, 'explanation': 'IRDAI guidelines specify that portability applications must be submitted at least 45 days before the renewal date to give both insurers adequate time for data transfer and underwriting.'}]}
]

# Static application reference categories
CATEGORIES_DATA = [
    {
        "slug": "health",
        "name": "Health Insurance",
        "description": "Individual and family floater coverage for hospitalization, medical treatments, day-care procedures, and critical illnesses.",
        "icon": "Shield"
    },
    {
        "slug": "term-life",
        "name": "Term Life Insurance",
        "description": "Pure risk protection providing financial security and guaranteed sum assured to dependents upon untimely demise.",
        "icon": "Award"
    },
    {
        "slug": "motor",
        "name": "Motor Insurance",
        "description": "Mandatory third-party liability and comprehensive own-damage protection for two-wheelers and four-wheelers.",
        "icon": "TrendingUp"
    },
    {
        "slug": "travel",
        "name": "Travel Insurance",
        "description": "Emergency medical treatment, baggage loss, passport loss, and trip cancellation coverage for domestic and overseas journeys.",
        "icon": "Compass"
    }
]

def seed_educational_content(db: Session) -> dict:
    """
    Seeds ONLY legitimate, static educational content:
    - 4 legitimate insurance categories
    - 12 comprehensive 5-pillar glossary terms
    - 10 structured educational modules with quizzes
    
    NEVER seeds fabricated insurance companies, policies, reviews, pricing slabs, or synthetic RAG documents.
    """
    categories_count = 0
    terms_count = 0
    modules_count = 0

    # 1. Legitimate Static Insurance Categories
    for cdata in CATEGORIES_DATA:
        cat = db.query(InsuranceCategory).filter(InsuranceCategory.slug == cdata["slug"]).first()
        if not cat:
            cat = InsuranceCategory(**cdata)
            db.add(cat)
            categories_count += 1
        else:
            for k, v in cdata.items():
                setattr(cat, k, v)
    db.flush()

    # 2. Comprehensive 5-Pillar Glossary Terms
    for gdata in GLOSSARY_TERMS_DATA:
        gt = db.query(GlossaryTerm).filter(GlossaryTerm.slug == gdata["slug"]).first()
        if not gt:
            gt = GlossaryTerm(**gdata)
            db.add(gt)
            terms_count += 1
        else:
            for k, v in gdata.items():
                setattr(gt, k, v)
    db.flush()

    # 3. Educational Modules & Quizzes
    for mdata in MODULES_DATA:
        m_copy = dict(mdata)
        quizzes = m_copy.pop("quizzes", [])
        m = db.query(LearningModule).filter(LearningModule.slug == m_copy["slug"]).first()
        if not m:
            m = LearningModule(**m_copy)
            db.add(m)
            db.flush()
            modules_count += 1
        else:
            for k, v in m_copy.items():
                setattr(m, k, v)
            db.flush()

        if not m.quizzes and quizzes:
            for q in quizzes:
                db.add(QuizQuestion(module_id=m.id, **q))
    db.flush()

    db.commit()
    logger.info("Educational content seeded successfully: %d categories, %d glossary terms, %d modules.", categories_count, terms_count, modules_count)
    return {
        "categories": len(CATEGORIES_DATA),
        "glossary_terms": len(GLOSSARY_TERMS_DATA),
        "learning_modules": len(MODULES_DATA)
    }

