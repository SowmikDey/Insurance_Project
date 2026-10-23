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

