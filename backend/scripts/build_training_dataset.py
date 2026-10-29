#!/usr/bin/env python3
"""
BimaGyan LLM Training Dataset Builder
======================================
Exports ALL available data from Python source files and Neon PostgreSQL
into an Alpaca-style instruction-tuning JSONL dataset.

Usage:
    cd c:/Projects/Insurance_Project
    python backend/scripts/build_training_dataset.py

Output:
    training_data/train.jsonl      (~90% of examples)
    training_data/val.jsonl        (~10% of examples)
    training_data/dataset_stats.json  (counts per category)

Training categories generated:
    1. concept_explanation   - Full module explanations as "explain X" tasks
    2. glossary_definition   - 5-pillar term deep dives
    3. quiz_qa               - MCQ questions with reasoning explanations
    4. common_mistakes       - "What mistakes should I avoid?"
    5. practical_scenario    - Named-person ₹ scenario evaluations
    6. policy_comparison     - Cross-policy field comparisons
    7. coverage_qa           - Specific coverage/exclusion questions per policy
    8. claims_guidance       - Step-by-step claim filing instructions
    9. regulatory_facts      - IRDAI rules, waiting periods, portability
   10. buyer_advice          - Personalised "I am X years old" advice generation
"""

import os
import sys
import json
import random
import re
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime
from pathlib import Path

# ── resolve project root ─────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("dataset_builder")

OUTPUT_DIR = PROJECT_ROOT / "training_data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_FILE = OUTPUT_DIR / "train.jsonl"
VAL_FILE = OUTPUT_DIR / "val.jsonl"
STATS_FILE = OUTPUT_DIR / "dataset_stats.json"

SYSTEM_PROMPT = (
    "You are BimaGyan AI, a knowledgeable, objective, and consumer-first Indian insurance "
    "education assistant. You explain complex insurance concepts clearly using plain English, "
    "concrete Indian Rupee examples, and IRDAI regulatory context. You never recommend a "
    "specific policy as 'the best' — you explain trade-offs and help users make informed decisions."
)


# ─── helpers ─────────────────────────────────────────────────────────────────

def clean(text: str) -> str:
    """Strip markdown asterisks, extra whitespace from source text."""
    if not text:
        return ""
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def make_example(instruction: str, output: str, category: str, input_text: str = "") -> Dict[str, Any]:
    """Create a single training example in Alpaca/ShareGPT format."""
    return {
        "system": SYSTEM_PROMPT,
        "instruction": instruction.strip(),
        "input": input_text.strip(),
        "output": output.strip(),
        "category": category,
    }


def make_chat_example(user_msg: str, assistant_msg: str, category: str) -> Dict[str, Any]:
    """Create a chat-format example (also valid for Alpaca-style fine-tuning)."""
    return make_example(user_msg, assistant_msg, category)


# ─── 1. GLOSSARY EXAMPLES ────────────────────────────────────────────────────

def build_glossary_examples(glossary_terms: List[Dict]) -> List[Dict]:
    examples = []
    logger.info("Building glossary examples from %d terms...", len(glossary_terms))

    for term in glossary_terms:
        t = term["term"]
        slug = term["slug"]
        cat = term.get("category", "General")
        what = clean(term.get("what_does_it_mean", ""))
        why = clean(term.get("why_does_it_matter", ""))
        example = clean(term.get("financial_impact_example", ""))
        tradeoff = clean(term.get("trade_off_analysis", ""))
        tips = clean(term.get("watch_out_tips", ""))

        if not what:
            continue

        # 1a. Simple definition
        examples.append(make_example(
            instruction=f"What is {t} in Indian insurance? Explain in simple terms.",
            output=what,
            category="glossary_definition",
        ))

        # 1b. Why does it matter
        if why:
            examples.append(make_example(
                instruction=f"Why does {t} matter when buying insurance in India?",
                output=why,
                category="glossary_definition",
            ))

        # 1c. Financial impact example
        if example:
            examples.append(make_example(
                instruction=f"Give me a practical Indian rupee example of how {t} affects my claim.",
                output=example,
                category="practical_scenario",
            ))

        # 1d. Trade-off analysis
        if tradeoff:
            examples.append(make_example(
                instruction=f"What are the trade-offs when choosing a higher vs lower {t}?",
                output=tradeoff,
                category="buyer_advice",
            ))

        # 1e. Watch-out tips
        if tips:
            examples.append(make_example(
                instruction=f"What should I watch out for regarding {t} when comparing insurance policies?",
                output=tips,
                category="regulatory_facts",
            ))

        # 1f. Combined deep-dive (high-quality long-form example)
        if what and why and example:
            full_output = (
                f"{what}\n\n"
                f"Why it matters: {why}\n\n"
                + (f"Practical example: {example}\n\n" if example else "")
                + (f"Trade-off: {tradeoff}\n\n" if tradeoff else "")
                + (f"Watch out: {tips}" if tips else "")
            )
            examples.append(make_example(
                instruction=f"Give me a complete explanation of {t} including examples and tips for an Indian buyer.",
                output=full_output.strip(),
                category="glossary_definition",
            ))

    logger.info("  → %d glossary examples", len(examples))
    return examples


# ─── 2. MODULE EXAMPLES ──────────────────────────────────────────────────────

def build_module_examples(modules_data: List[Dict]) -> List[Dict]:
    examples = []
    logger.info("Building module examples from %d modules...", len(modules_data))

    for mod in modules_data:
        title = mod["title"]
        concept = clean(mod.get("concept_explanation", ""))
        why = clean(mod.get("why_it_matters", ""))
        practical = clean(mod.get("practical_indian_example", ""))
        mistakes = mod.get("common_mistakes", [])
        takeaways = mod.get("key_takeaways", [])

        if not concept:
            continue

        # 2a. Full concept explanation
        examples.append(make_example(
            instruction=f"Explain: {title}",
            output=concept,
            category="concept_explanation",
        ))

        # 2b. Why it matters
        if why:
            examples.append(make_example(
                instruction=f"Why does {title.lower()} matter before buying insurance in India?",
                output=why,
                category="concept_explanation",
            ))

        # 2c. Practical scenario
        if practical:
            examples.append(make_example(
                instruction=f"Give me a real-world Indian example that demonstrates {title.lower()}.",
                output=practical,
                category="practical_scenario",
            ))

        # 2d. Common mistakes
        if mistakes:
            mistakes_formatted = "\n".join(f"{i+1}. {clean(m)}" for i, m in enumerate(mistakes))
            examples.append(make_example(
                instruction=f"What are the most common mistakes people make regarding {title.lower()} in India?",
                output=mistakes_formatted,
                category="common_mistakes",
            ))

        # 2e. Key takeaways / rules
        if takeaways:
            takeaways_formatted = "\n".join(f"• {clean(k)}" for k in takeaways)
            examples.append(make_example(
                instruction=f"What are the golden rules I should follow for {title.lower()}?",
                output=takeaways_formatted,
                category="buyer_advice",
            ))

        # 2f. Combined summary (module overview as long-form output)
        summary_parts = [concept]
        if why:
            summary_parts.append(f"Why it matters:\n{why}")
        if practical:
            summary_parts.append(f"Real example:\n{practical}")
        if mistakes:
            summary_parts.append("Common mistakes to avoid:\n" + "\n".join(f"• {clean(m)}" for m in mistakes))
        if takeaways:
            summary_parts.append("Key takeaways:\n" + "\n".join(f"• {clean(k)}" for k in takeaways))

        examples.append(make_example(
            instruction=f"I want to learn everything about {title}. Give me a complete guide.",
            output="\n\n".join(summary_parts),
            category="concept_explanation",
        ))

    logger.info("  → %d module examples", len(examples))
    return examples


# ─── 3. QUIZ EXAMPLES ────────────────────────────────────────────────────────

def build_quiz_examples(modules_data: List[Dict]) -> List[Dict]:
    examples = []
    logger.info("Building quiz examples...")

    for mod in modules_data:
        title = mod["title"]
        for quiz in mod.get("quizzes", []):
            question = clean(quiz.get("question", ""))
            options = quiz.get("options", [])
            correct_idx = quiz.get("correct_option_index", 0)
            explanation = clean(quiz.get("explanation", ""))

            if not question or not options or not explanation:
                continue

            correct_answer = options[correct_idx]
            options_text = "\n".join(f"{chr(65+i)}. {o}" for i, o in enumerate(options))

            # 3a. MCQ format with answer + explanation
            output = (
                f"The correct answer is: {chr(65+correct_idx)}. {correct_answer}\n\n"
                f"Explanation: {explanation}"
            )
            examples.append(make_example(
                instruction=f"[Quiz — {title}]\n{question}\n\n{options_text}",
                output=output,
                category="quiz_qa",
            ))

            # 3b. Open-ended version (reuse explanation as answer)
            examples.append(make_example(
                instruction=question,
                output=f"{correct_answer}\n\n{explanation}",
                category="quiz_qa",
            ))

    logger.info("  → %d quiz examples", len(examples))
    return examples


# ─── 4. POLICY EXAMPLES ──────────────────────────────────────────────────────

def build_policy_examples(policy_files_dir: Path) -> List[Dict]:
    examples = []
    policy_files = list(policy_files_dir.glob("*.json"))
    logger.info("Building policy examples from %d policy JSON files...", len(policy_files))

    policies = []
    for f in policy_files:
        try:
            with open(f, encoding="utf-8") as fp:
                policies.append(json.load(fp))
        except Exception as e:
            logger.warning("  Skipping %s: %s", f.name, e)

    for pol in policies:
        identity = pol.get("identity", {})
        coverage = pol.get("coverage", {})
        restrictions = pol.get("restrictions", {})
        premium = pol.get("premium", {})
        claims = pol.get("claims", {})
        provenance = pol.get("provenance", {})

        name = identity.get("product_name") or pol.get("slug", "Policy")
        insurer = identity.get("insurer_name", "the insurer")
        uin = identity.get("uin_number", "N/A")

        # 4a. Full policy summary
        summary_lines = [
            f"{name} is offered by {insurer} (UIN: {uin}).",
            f"Entry age: {identity.get('entry_age_min', 'N/A')}–{identity.get('entry_age_max', 'N/A')} years.",
            f"Policy tenure: {identity.get('policy_tenure', 'N/A')}.",
            f"Room rent: {restrictions.get('room_rent_capping', 'N/A')}.",
            f"Co-pay: {restrictions.get('copay_percentage', 0)}%.",
            f"Initial waiting period: {restrictions.get('initial_waiting_period_days', 30)} days.",
            f"PED waiting period: {restrictions.get('ped_waiting_period_months', 'N/A')} months.",
            f"Restoration: {coverage.get('restoration_benefit', 'N/A')}.",
            f"Network hospitals: {claims.get('cashless_hospital_network_size', 'N/A')}.",
            f"Claim settlement ratio: {claims.get('claim_settlement_ratio', 'N/A')}%.",
            f"Indicative premium (standard profile): ₹{premium.get('indicative_annual_premium', 'N/A')}/year.",
        ]

        examples.append(make_example(
            instruction=f"Give me a complete factual summary of the {name} policy.",
            output="\n".join(summary_lines),
            category="coverage_qa",
        ))

        # 4b. Room rent question
        room_rent = restrictions.get("room_rent_capping")
        if room_rent:
            examples.append(make_example(
                instruction=f"What is the room rent limit for {name}? Does proportionate deduction apply?",
                output=f"{name}: {room_rent}",
                category="coverage_qa",
            ))

        # 4c. Waiting periods
        initial_wp = restrictions.get("initial_waiting_period_days")
        ped_wp = restrictions.get("ped_waiting_period_months")
        specific_wp = restrictions.get("specific_disease_waiting_months")
        if initial_wp or ped_wp:
            wp_text = (
                f"For {name} ({insurer}):\n"
                f"• Initial waiting period: {initial_wp or 30} days (accidents covered from Day 1).\n"
                + (f"• Specific illness waiting period: {specific_wp} months.\n" if specific_wp else "")
                + (f"• Pre-Existing Disease (PED) waiting period: {ped_wp} months.\n" if ped_wp else "")
            )
            examples.append(make_example(
                instruction=f"What are the waiting periods for {name}?",
                output=wp_text.strip(),
                category="regulatory_facts",
            ))

        # 4d. Claim filing process
        cashless_proc = claims.get("cashless_claim_procedure")
        reimb_proc = claims.get("reimbursement_claim_procedure")
        docs = claims.get("required_claim_documents", [])
        if cashless_proc or reimb_proc:
            claim_text = ""
            if cashless_proc:
                claim_text += f"Cashless claim: {cashless_proc}\n\n"
            if reimb_proc:
                claim_text += f"Reimbursement claim: {reimb_proc}\n\n"
            if docs:
                claim_text += "Required documents:\n" + "\n".join(f"• {d}" for d in docs)
            examples.append(make_example(
                instruction=f"How do I file a claim with {name}? What documents do I need?",
                output=claim_text.strip(),
                category="claims_guidance",
            ))

        # 4e. Permanent exclusions
        exclusions = restrictions.get("permanent_exclusions", [])
        if exclusions:
            excl_text = (
                f"The following are NOT covered under {name} under any circumstances:\n"
                + "\n".join(f"• {e}" for e in exclusions)
            )
            examples.append(make_example(
                instruction=f"What does {name} NOT cover? List permanent exclusions.",
                output=excl_text,
                category="coverage_qa",
            ))

        # 4f. Coverage highlights
        cov_highlights = []
        for field, label in [
            ("restoration_benefit", "Restoration benefit"),
            ("cumulative_bonus", "Cumulative/No Claim Bonus"),
            ("maternity_cover", "Maternity cover"),
            ("ayush_treatment", "AYUSH treatment"),
            ("modern_treatments", "Modern/robotic treatments"),
            ("ambulance_cover", "Ambulance cover"),
            ("organ_donor_expenses", "Organ donor expenses"),
        ]:
            val = coverage.get(field)
            if val:
                cov_highlights.append(f"• {label}: {val}")

        if cov_highlights:
            examples.append(make_example(
                instruction=f"What are the key coverage highlights of {name}?",
                output="\n".join(cov_highlights),
                category="coverage_qa",
            ))

        # 4g. Premium and tax
        prem = premium.get("indicative_annual_premium")
        tax = premium.get("tax_benefits")
        if prem:
            prem_text = f"The indicative annual premium for {name} is approximately ₹{prem}. {premium.get('pricing_factors', '')}"
            if tax:
                prem_text += f"\n\nTax benefit: {tax}"
            examples.append(make_example(
                instruction=f"What is the approximate premium for {name} and what tax benefits does it offer?",
                output=prem_text,
                category="coverage_qa",
            ))

    logger.info("  → %d policy examples", len(examples))
    return examples


# ─── 5. POLICY COMPARISON EXAMPLES ───────────────────────────────────────────

def build_comparison_examples(comparison_files_dir: Path, policies: List[Dict]) -> List[Dict]:
    examples = []
    comparison_files = list(comparison_files_dir.glob("*.json"))
    logger.info("Building comparison examples from %d comparison files + %d policy pairs...",
                len(comparison_files), len(policies))

    # 5a. From dedicated comparison files
    for f in comparison_files:
        try:
            with open(f, encoding="utf-8") as fp:
                comp = json.load(fp)
            # Use file content as a Q&A about the compared policies
            slug = f.stem.replace("_comparison", "")
            examples.append(make_example(
                instruction=f"Compare the key details of {slug.replace('-', ' ').title()} with other policies.",
                output=json.dumps(comp, indent=2, ensure_ascii=False),
                category="policy_comparison",
            ))
        except Exception:
            pass

    # 5b. Cross-policy comparison pairs from policy JSONs
    fields_to_compare = [
        ("room_rent_capping", "restrictions", "room rent capping"),
        ("copay_percentage", "restrictions", "co-payment percentage"),
        ("restoration_benefit", "coverage", "restoration benefit"),
        ("cashless_hospital_network_size", "claims", "network hospital count"),
        ("claim_settlement_ratio", "claims", "claim settlement ratio"),
        ("ped_waiting_period_months", "restrictions", "PED waiting period"),
    ]

    loaded = []
    policy_files = list((PROJECT_ROOT / "data" / "scraped" / "policies").glob("*.json"))
    for f in policy_files:
        try:
            with open(f, encoding="utf-8") as fp:
                loaded.append(json.load(fp))
        except Exception:
            pass

    if len(loaded) >= 2:
        for field_key, section, label in fields_to_compare:
            comparison_lines = []
            for pol in loaded:
                pol_name = pol.get("identity", {}).get("product_name") or pol.get("slug", "Policy")
                val = pol.get(section, {}).get(field_key, "N/A")
                comparison_lines.append(f"• {pol_name}: {val}")

            if any("N/A" not in line for line in comparison_lines):
                examples.append(make_example(
                    instruction=f"Compare {label} across all major Indian health insurance policies in your database.",
                    output="\n".join(comparison_lines),
                    category="policy_comparison",
                ))

        # 5c. Specific two-policy comparisons
        for i in range(len(loaded)):
            for j in range(i + 1, min(i + 3, len(loaded))):
                pol_a = loaded[i]
                pol_b = loaded[j]
                name_a = pol_a.get("identity", {}).get("product_name") or pol_a.get("slug")
                name_b = pol_b.get("identity", {}).get("product_name") or pol_b.get("slug")

                diff_lines = [f"Comparison: {name_a} vs {name_b}\n"]
                for field_key, section, label in fields_to_compare:
                    va = pol_a.get(section, {}).get(field_key, "N/A")
                    vb = pol_b.get(section, {}).get(field_key, "N/A")
                    diff_lines.append(f"• {label}: {name_a} = {va} | {name_b} = {vb}")

                examples.append(make_example(
                    instruction=f"Compare {name_a} and {name_b} health insurance policies. Which is better and why?",
                    output="\n".join(diff_lines)
                           + "\n\nNote: The best policy depends on your specific age, city, sum insured needs, "
                             "and whether you have pre-existing conditions. Always read the official policy wording.",
                    category="policy_comparison",
                ))

    logger.info("  → %d comparison examples", len(examples))
    return examples


# ─── 6. REGULATORY & BUYER ADVICE EXAMPLES ───────────────────────────────────

def build_comprehensive_beginner_guides() -> List[Dict]:
    """
    High-value, in-depth pedagogical guides for beginners, claims workflows,
    policy architecture, and Rupee scenario calculations.
    """
    examples = []

    guides = [
        (
            "Explain health insurance to me as a beginner.",
            "Health insurance is a financial safety net designed to protect your savings from being wiped out by unexpected hospitalization and medical treatments in India.\n\n"
            "### 1. The Core Concept: How It Works\n"
            "• You pay an annual fee called a **Premium** (e.g., ₹10,000–₹18,000 per year for a ₹10–15 Lakh cover for a healthy 30-year-old).\n"
            "• In exchange, the insurance company agrees to pay your hospital bills up to a chosen maximum limit called the **Sum Insured** (SI).\n"
            "• If you undergo treatment requiring 24+ hours of hospitalization (or modern daycare procedures like chemotherapy or cataract surgery), the insurer covers room rent, doctor visits, surgery, medicines, and ICU charges.\n\n"
            "### 2. Cashless vs. Reimbursement Claims\n"
            "• **Cashless Hospitalization**: You get admitted to an empanelled 'network hospital'. The hospital coordinates directly with your insurer/TPA. After pre-authorization, the insurer pays the hospital directly — you only pay for personal non-medical items (like gloves and toiletries).\n"
            "• **Reimbursement**: If you go to a non-network hospital, you pay the bills yourself upon discharge, submit original invoices, prescriptions, and discharge summaries to the insurer, and receive your money back in 15–30 days.\n\n"
            "### 3. The 3 Golden Rules for Beginners When Buying\n"
            "1. **No Room Rent Capping**: Never choose a policy with a 1% or 2% room rent cap. A 1% cap on a ₹5 Lakh policy limits you to ₹5,000/day; choosing an ₹8,000/day room triggers 'proportionate deductions', slashing doctor, OT, and surgery payouts by 37.5%!\n"
            "2. **Zero Co-payment**: Avoid mandatory co-pay clauses (like 20% co-pay), which force you to pay 20% of every hospital bill out of your own pocket.\n"
            "3. **Short Pre-Existing Disease (PED) Waiting Period**: By IRDAI rules, PED waiting periods are capped at 36 months (3 years). Look for policies offering 24 to 36 months, or 1-year reduction riders if you have existing conditions like hypertension or diabetes.\n\n"
            "### 4. What Is NOT Covered (Exclusions)\n"
            "• Routine outpatient check-ups and OPD medicines (unless an OPD rider is purchased).\n"
            "• Cosmetic or aesthetic surgeries (unless reconstructive post-trauma).\n"
            "• Non-medical consumables (gloves, masks, registration charges) — though modern 'consumables cover' riders now cover these.\n\n"
            "**Key Takeaway**: Start early in your 20s or early 30s when premiums are lowest, medical tests are rarely required, and you can serve all waiting periods while in peak health.",
            "concept_explanation"
        ),
        (
            "How does health insurance work in India? Give a step-by-step beginner guide.",
            "Here is the complete step-by-step lifecycle of how health insurance functions in India:\n\n"
            "### Step 1: Policy Selection & Proposal\n"
            "You choose a Sum Insured (typically ₹10–25 Lakhs for urban families) and disclose all past health conditions truthfully on the proposal form. Complete disclosure is vital: under the principle of utmost good faith (*Uberrima Fides*), hiding diabetes or asthma can result in permanent claim repudiation.\n\n"
            "### Step 2: Serving the Waiting Periods\n"
            "Once your policy starts:\n"
            "• **First 30 Days (Initial Waiting Period)**: Only accidental emergencies are covered. Illness hospitalizations are excluded.\n"
            "• **First 24 Months (Specific Illnesses)**: Slow-growing conditions (cataracts, hernia, kidney stones, joint replacements) are excluded.\n"
            "• **24 to 36 Months (Pre-Existing Diseases)**: Any disease diagnosed or treated before purchasing the policy is covered only after this window.\n\n"
            "### Step 3: Hospitalization & Claim Settlement\n"
            "When medical treatment is required:\n"
            "• **Planned Admission**: Inform the insurer/TPA desk at the hospital 48–72 hours in advance with your health card and doctor's admission note.\n"
            "• **Emergency Admission**: Notify within 24 hours of admission.\n"
            "• The insurer approves a pre-authorization amount. Upon discharge, the final hospital bill is audited and settled cashless.\n\n"
            "### Step 4: Pre & Post Hospitalization Expenses\n"
            "Most good policies cover medical bills incurred **60 days prior to admission** (diagnostic tests, doctor consultations) and **90 to 180 days after discharge** (follow-up visits, rehabilitation medicines). These are claimed via reimbursement by submitting original bills.\n\n"
            "### Step 5: Annual Renewal & No Claim Bonus\n"
            "If you do not file a claim during the year, your insurer rewards you with a **No Claim Bonus (NCB)**, increasing your Sum Insured by 10% to 50% without increasing your premium.",
            "concept_explanation"
        ),
        (
            "What is the difference between Deductible and Co-payment in health insurance? Explain with a ₹5,00,000 bill example.",
            "While both Deductibles and Co-payments require you to share costs with your insurer, their mathematical mechanisms are completely different:\n\n"
            "### 1. Deductible (A Fixed Rupee Threshold)\n"
            "A deductible is an absolute amount you must pay out-of-pocket *before* the insurance company begins paying a single rupee. Once the deductible is crossed, the insurer covers the remaining eligible claim up to the Sum Insured.\n\n"
            "### 2. Co-payment (A Fixed Percentage on Every Bill)\n"
            "A co-payment is a predefined percentage (e.g. 10%, 20%) that you must pay out of pocket on *every single hospital claim*, no matter how large or small.\n\n"
            "### Rupee Comparison Scenario (₹5,00,000 Hospital Bill):\n"
            "Assume you have a ₹10 Lakh policy and incur a ₹5,00,000 hospital bill:\n\n"
            "• **Scenario A: Policy with ₹25,000 Deductible**\n"
            "  - You pay: ₹25,000\n"
            "  - Insurer pays: ₹4,75,000\n"
            "  - Your out-of-pocket share: **5%**\n\n"
            "• **Scenario B: Policy with 20% Mandatory Co-payment**\n"
            "  - You pay (20% of ₹5,00,000): **₹1,00,000**\n"
            "  - Insurer pays (80% of ₹5,00,000): ₹4,00,000\n"
            "  - Your out-of-pocket share: **20%**\n\n"
            "• **Scenario C: ₹15,00,000 Catastrophic Bill**\n"
            "  - Under ₹25,000 Deductible: You pay ₹25,000, insurer pays ₹9,75,000 (up to SI).\n"
            "  - Under 20% Co-payment: You pay ₹3,00,000 out-of-pocket!\n\n"
            "### Consumer Verdict:\n"
            "> High deductibles are beneficial when buying **Super Top-Up** policies (e.g., a ₹5L deductible matched to your base policy) to dramatically lower premiums.\n"
            "> Conversely, mandatory co-payments on base health insurance are punitive for consumers — avoid policies with co-payments unless insuring senior citizens where no other option is available.",
            "practical_scenario"
        ),
        (
            "What is Room Rent Capping and how does Proportionate Deduction work in India?",
            "Room rent capping is one of the most dangerous hidden clauses in Indian health insurance, responsible for thousands of unexpected claim deductions every year.\n\n"
            "### 1. What is Room Rent Capping?\n"
            "Many traditional policies restrict room rent to **1% of the Sum Insured per day** for normal rooms (or 2% for ICU). For example, with a ₹5,00,000 policy, your daily room rent limit is ₹5,000.\n\n"
            "### 2. The Trap: Proportionate Deduction\n"
            "Hospitals tie all associate charges — doctor consultation fees, surgeon charges, operation theatre (OT) charges, and nursing fees — to the room category. If you choose a room exceeding your eligible cap, insurers apply **proportionate deduction** to ALL associate medical expenses, not just the excess room rent.\n\n"
            "### Real-World Rupee Example:\n"
            "• Sum Insured: ₹5,00,000 (1% room rent limit = ₹5,000/day)\n"
            "• Actual Room Chosen: Single Deluxe at ₹10,000/day (100% above limit)\n"
            "• Hospital Stay: 4 days (Total Room Rent = ₹40,000)\n"
            "• Associate Medical Expenses (Doctor, Surgery, OT): ₹3,00,000\n"
            "• Total Hospital Bill: ₹3,40,000\n\n"
            "**What the Insurer Pays:**\n"
            "1. Room rent: ₹5,000 × 4 days = ₹20,000 (Insurer pays ₹20,000, you pay ₹20,000).\n"
            "2. Associate Charges Proportionate Ratio: Eligible limit (₹5,000) ÷ Actual rate (₹10,000) = **50%**.\n"
            "3. The insurer cuts doctor, surgery, and OT charges by 50%!\n"
            "   - Insurer pays 50% of ₹3,00,000 = ₹1,50,000.\n"
            "   - You must pay ₹1,50,000 out of pocket!\n"
            "• **Final Insurer Settlement**: ₹20,000 + ₹1,50,000 = ₹1,70,000.\n"
            "• **You Pay Out-of-Pocket**: **₹1,70,000 (50% of your total hospital bill)!**\n\n"
            "### The Golden Rule:\n"
            "Always purchase a policy with **'Single Private Room'** eligibility or **No Room Rent Capping**. Modern comprehensive policies (e.g., HDFC ERGO Optima Secure, Care Supreme, Niva Bupa Reassure) have eliminated room rent capping.",
            "practical_scenario"
        ),
        (
            "Individual Health Insurance vs Family Floater: Which should I choose?",
            "Choosing between an Individual policy and a Family Floater depends primarily on the ages and medical risks of your family members.\n\n"
            "### 1. How a Family Floater Works\n"
            "In a floater policy, a single Sum Insured (e.g. ₹15 Lakhs) is shared among all covered members (typically self, spouse, and up to 3 dependent children). Any member can use up to the full ₹15 Lakhs in a policy year.\n\n"
            "• **Advantage**: Substantially cheaper premium than buying 4 separate individual policies.\n"
            "• **Risk**: If one family member experiences a severe medical crisis and exhausts the ₹15 Lakhs pool early in the year, remaining members are left uninsured unless the policy has an automatic restoration benefit.\n\n"
            "### 2. How Individual Policies Work\n"
            "Each person has their own dedicated Sum Insured (e.g., ₹10 Lakhs each). One member's hospital claim has zero impact on another member's cover.\n\n"
            "### 3. The Senior Citizen Trap in Family Floaters\n"
            "**Never add senior parents (aged 55+) to your family floater!**\n"
            "1. Floater premiums are priced according to the **age of the oldest member**. Adding a 62-year-old parent will double or triple the premium for you and your spouse.\n"
            "2. Elderly parents have higher hospitalization probability and may drain the shared sum insured.\n"
            "3. Parents' pre-existing conditions (diabetes, cardiac) impose waiting periods on the shared policy.\n\n"
            "### Recommended Optimal Structure:\n"
            "• **Young Family (Self + Spouse + Kids)**: Family Floater of ₹15–25 Lakhs.\n"
            "• **Parents / In-Laws**: Separate Individual Senior Citizen Policies (₹10–15 Lakhs each) + Super Top-Up.",
            "buyer_advice"
        ),
        (
            "How does Cashless Hospitalization work step-by-step in an Indian hospital?",
            "Cashless hospitalization means you do not have to pay the covered hospital charges upfront; the insurer settles directly with the hospital. Here is the operational process:\n\n"
            "### Planned Hospitalization (Surgery / Treatment scheduled in advance)\n"
            "1. **TPA Desk Visit**: 48 to 72 hours prior to admission, visit the hospital's Third-Party Administrator (TPA) / Insurance desk.\n"
            "2. **Documentation**: Present your digital/physical Health Card, Government ID proof (Aadhaar/PAN), and doctor's admission advice with medical diagnosis.\n"
            "3. **Pre-Authorization Request**: The hospital fills Cashless Form Part-A, your treating doctor fills Part-B, and they transmit it to your insurer.\n"
            "4. **Initial Approval**: Within 2 to 6 hours, the insurer issues an initial pre-authorization sanction letter approving a baseline amount (e.g., ₹80,000 of an estimated ₹1,50,000).\n"
            "5. **Admission**: You are admitted without paying an admission deposit (except refundable incidental deposit, usually ₹5,000–₹10,000).\n"
            "6. **Discharge Settlement**: On discharge, the hospital sends the complete itemized bill. The insurer issues final authorization.\n"
            "7. **Out-of-Pocket Payment**: You only pay for non-covered items: registration fees, gloves, syringes, thermometer (unless covered under a Consumables rider).\n\n"
            "### Emergency Hospitalization (Accident or Sudden Acute Illness)\n"
            "1. Get patient admitted immediately to ICU/emergency ward.\n"
            "2. Submit health card and ID to the TPA desk within **24 hours of admission**.\n"
            "3. Hospital marks request as 'Emergency Pre-Auth' — insurers are mandated by IRDAI to respond within 1 hour.\n\n"
            "### IRDAI 'Cashless Everywhere' (2024 Reform)\n"
            "Under the 2024 IRDAI mandate, you can now avail cashless treatment even at hospitals **outside your insurer's network**, provided you notify the insurer 48 hours prior for planned admission (or 48 hours post-admission for emergencies).",
            "claims_guidance"
        ),
        (
            "What is a Super Top-Up policy and why is it the most cost-effective way to get ₹25+ Lakhs cover?",
            "A Super Top-Up policy provides massive additional health insurance coverage at a fraction of the cost of a standard base policy by utilizing an aggregate **Deductible**.\n\n"
            "### How Super Top-Up Works\n"
            "Unlike a standard Top-Up (which checks the deductible per single claim), a **Super Top-Up** tracks your **cumulative total medical expenses across the entire policy year**.\n"
            "Once your total eligible medical expenses in a year cross the threshold (deductible), the Super Top-Up triggers and pays all subsequent bills up to its Sum Insured.\n\n"
            "### The 1+1 Cost-Saving Hack:\n"
            "Compare these two purchasing strategies for a 32-year-old:\n\n"
            "• **Strategy A: Buying a single ₹25 Lakh Base Health Policy**\n"
            "  - Annual Premium: ~₹22,000 to ₹26,000/year.\n\n"
            "• **Strategy B: ₹5 Lakh Base Policy + ₹20 Lakh Super Top-Up (₹5 Lakh Deductible)**\n"
            "  - ₹5 Lakh Base Policy Premium: ~₹9,500/year.\n  - ₹20 Lakh Super Top-Up Premium: ~₹2,800 to ₹3,500/year.\n  - **Total Cost**: **~₹12,500 to ₹13,000/year (Saving ~45%!)**\n\n"
            "### How Claims Work Under Strategy B:\n"
            "• Claim 1: Bill of ₹4,00,000 in July → Fully paid by your ₹5 Lakh Base Policy. (Remaining base cover: ₹1,00,000).\n"
            "• Claim 2: Bill of ₹8,00,000 in November:\n"
            "  - Base policy pays remaining ₹1,00,000 (exhausting the ₹5L base SI).\n"
            "  - Total hospital bills this year have reached ₹12,00,000, which is well above the ₹5,00,000 deductible.\n"
            "  - The Super Top-Up kicks in immediately and pays the remaining ₹7,00,000!\n"
            "  - You paid ₹0 out of pocket.\n\n"
            "**Recommendation**: Always choose **Super Top-Up** (never a plain 'Top-Up') and ensure the deductible exactly matches your base policy's Sum Insured.",
            "buyer_advice"
        ),
        (
            "What are the Section 80D tax benefits for health insurance in India?",
            "Under Section 80D of the Income Tax Act, premiums paid towards health insurance policies and preventive health check-ups are eligible for substantial tax deductions:\n\n"
            "### Deduction Limits Breakdown:\n"
            "1. **Self, Spouse & Dependent Children** (Age below 60):\n"
            "   - Maximum deduction: **₹25,000 per financial year**.\n\n"
            "2. **Parents below 60 years of age**:\n"
            "   - Additional deduction: **₹25,000**.\n"
            "   - (Total combined tax deduction: ₹50,000).\n\n"
            "3. **Parents who are Senior Citizens (Age 60+)**:\n"
            "   - Additional deduction: **₹50,000**.\n"
            "   - (Total combined tax deduction: ₹25,000 + ₹50,000 = **₹75,000**).\n\n"
            "4. **Both Proposer and Parents are Senior Citizens (Age 60+)**:\n"
            "   - Proposer & Family (Senior): ₹50,000\n"
            "   - Senior Citizen Parents: ₹50,000\n"
            "   - **Maximum Possible Deduction: ₹1,00,000 per financial year**.\n\n"
            "### Preventive Health Check-Up Sub-Limit:\n"
            "• Within the overall limits above, up to **₹5,00,000 (₹5,000)** is deductible for annual preventive health check-ups for self, family, and parents.\n"
            "• Unlike premiums (which must be paid via non-cash modes like UPI, Net Banking, or Debit/Credit card), preventive health check-up expenses **can be paid in cash** and still claimed.\n\n"
            "> **Note**: Section 80D deductions are available under the **Old Tax Regime**. Under the New Tax Regime (Section 115BAC default from FY 2023-24), Section 80D deductions are not available.",
            "regulatory_facts"
        ),
        (
            "What should I do if my health insurance claim is unfairly rejected? Step-by-step grievance guide.",
            "If your health insurance claim is rejected or deducted without clear justification, follow this 3-tier statutory escalation ladder established by IRDAI:\n\n"
            "### Tier 1: Insurer Internal Grievance Cell (GRO)\n"
            "1. Every insurer has a designated Grievance Redressal Officer (GRO).\n"
            "2. Write a formal rebuttal letter referencing your Claim Number and Policy Number. Attach treating doctor certificates, detailed discharge summaries, and specific clause citations showing why the rejection is invalid.\n"
            "3. Send to the insurer's official grievance email ID.\n"
            "4. **IRDAI Mandate**: The insurer must acknowledge your complaint within 3 working days and provide a final written resolution within **15 calendar days**.\n\n"
            "### Tier 2: IRDAI Bima Bharosa Portal\n"
            "If the insurer rejects your review or fails to reply within 15 days:\n"
            "1. Register on the official portal: **bimabharosa.irdai.gov.in** (or call toll-free 155255 / 1800 4254 732).\n"
            "2. Lodge the complaint with all correspondence history.\n"
            "3. IRDAI monitors the ticket directly, compelling the insurer's compliance department to review the case.\n\n"
            "### Tier 3: The Insurance Ombudsman (The Ultimate Consumer Forum)\n"
            "If the dispute remains unresolved or unsatisfactory:\n"
            "1. Approach the **Office of the Insurance Ombudsman** (17 locations across India, online at **cioins.co.in**).\n"
            "2. **Jurisdiction**: Resolves disputes up to ₹30 Lakhs (claim repudiation, partial settlement, premium disputes, delay).\n"
            "3. **Cost**: Completely **FREE** — no lawyers or court fees required.\n"
            "4. **Power**: Ombudsman decisions are **legally binding on the insurer**, but NOT binding on you (if unsatisfied, you can still approach consumer court). The insurer must implement the award within 30 days.",
            "claims_guidance"
        ),
        (
            "Why is Pure Term Insurance better than Endowment plans or ULIPs?",
            "Mixing insurance with investment is the single biggest financial mistake middle-class Indian families make. Here is why pure Term Insurance is vastly superior:\n\n"
            "### The Problem with Endowment Plans & Traditional LIC Policies:\n"
            "1. **Extremely Low Life Protection**: A ₹50,000/year premium in a 20-year endowment policy buys only **₹8 to ₹12 Lakhs** of life cover. If the breadwinner passes away, ₹10 Lakhs is exhausted in just 2 years of family living expenses!\n"
            "2. **Sub-Inflation Returns**: Endowment returns hover around **4% to 5.5% per annum** — lower than inflation (6–7%). Your money loses purchasing power over 20 years.\n"
            "3. **Heavy Surrender Penalties**: Exiting early causes loss of 30% to 70% of your invested capital.\n\n"
            "### The Pure Term Insurance + Mutual Fund Alternative:\n"
            "Instead of paying ₹50,000 into an endowment plan, split your capital:\n\n"
            "• **Part 1: Pure Term Insurance Cover**\n"
            "  - Buy a ₹1 Crore to ₹1.5 Crore Pure Term Plan up to age 60–65.\n  - Annual Cost (age 30, healthy non-smoker): **~₹9,000 to ₹12,000/year**.\n  - If you pass away, your family receives **₹1,00,00,000 in cash**, completely tax-free under Sec 10(10D).\n\n"
            "• **Part 2: Invest the Remaining ₹38,000/year in Index Mutual Funds (Nifty 50)**\n"
            "  - Monthly SIP: ~₹3,200/month.\n  - Over 25 years at a conservative 12% CAGR, this builds a wealth corpus of **₹61,00,000 (₹61 Lakhs)**!\n  - In contrast, the endowment plan would only return ~₹22 Lakhs at maturity.\n\n"
            "### Golden Rule of Personal Finance:\n"
            "> **Insurance is for Protection; Investments are for Wealth Creation.** Never mix them.",
            "concept_explanation"
        )
    ]

    for instruction, output, category in guides:
        examples.append(make_example(instruction=instruction, output=output, category=category))

    logger.info("  → %d comprehensive beginner & core concept guides", len(examples))
    return examples


# ─── 6b. REGULATORY & BUYER ADVICE EXAMPLES ───────────────────────────────────

def build_regulatory_examples() -> List[Dict]:
    """Hard-coded high-quality regulatory QA pairs grounded in IRDAI facts."""
    examples = []

    regulatory_qa = [
        (
            "What is the maximum PED waiting period allowed by IRDAI regulations?",
            "IRDAI updated its guidelines reducing the maximum allowable Pre-Existing Disease (PED) "
            "waiting period from 48 months (4 years) to 36 months (3 years). Any insurer quoting "
            "48 months for PED as of 2024 is non-compliant. Always verify this clause in the "
            "policy wording before purchasing.",
            "regulatory_facts",
        ),
        (
            "How many days before renewal must I apply for health insurance portability in India?",
            "Under IRDAI portability regulations, you must apply for portability at least 45 days "
            "before your renewal date. The new insurer must credit all completed waiting periods "
            "(initial, PED, and specific illness). You cannot lose your accumulated benefits when "
            "you port — this is a legal right guaranteed by IRDAI.",
            "regulatory_facts",
        ),
        (
            "What is the 8-year moratorium clause in Indian health insurance?",
            "After 8 continuous years of coverage (counting ported years), no insurer can reject a "
            "claim citing non-disclosure of pre-existing diseases — except in cases of proven fraud. "
            "This moratorium rule is defined in IRDAI Health Insurance Regulations 2016 and means "
            "long-term policyholders gain significant protection against retrospective claim rejection.",
            "regulatory_facts",
        ),
        (
            "What is IRDAI's 'Cashless Everywhere' initiative?",
            "IRDAI's Cashless Everywhere initiative (2023–2024) mandates that insurers must allow "
            "cashless hospitalization even at non-network hospitals, provided the insured notifies "
            "the insurer at least 48 hours before planned admission (or within 48 hours for emergencies). "
            "This eliminates the old restriction where you had to pay upfront at hospitals outside "
            "the insurer's empanelled network.",
            "regulatory_facts",
        ),
        (
            "What is the Free Look Period for insurance policies in India?",
            "The Free Look Period is a statutory 15 to 30 day cooling-off window starting from the "
            "date you receive your policy document. During this period, you can cancel the policy "
            "for a full refund (minus stamp duty, proportionate risk premium, and medical test costs). "
            "For policies purchased online, the free look period is 30 days. The clock starts on the "
            "date you receive the document, not the payment date.",
            "regulatory_facts",
        ),
        (
            "What is the Insurance Ombudsman in India and how can I file a complaint?",
            "The Insurance Ombudsman is a free, quasi-judicial authority that resolves disputes "
            "between policyholders and insurance companies. There are 17 Ombudsman offices across India. "
            "To file a complaint: (1) First raise an internal grievance with your insurer. (2) If "
            "unresolved within 30 days or if you are unsatisfied, file on the online portal at "
            "cioins.co.in or visit the nearest Ombudsman office. The process is completely free, and "
            "decisions are binding on the insurer for awards up to ₹30 Lakhs.",
            "regulatory_facts",
        ),
        (
            "What is Bima Bharosa and how is it different from the Insurance Ombudsman?",
            "Bima Bharosa (bimabharosa.irdai.gov.in) is IRDAI's integrated online grievance portal "
            "where policyholders can lodge complaints against any IRDAI-regulated insurer. It is the "
            "first step before approaching the Ombudsman. The portal tracks grievance status and mandates "
            "a 15-day response from the insurer. The Insurance Ombudsman is the escalation authority if "
            "Bima Bharosa resolution is unsatisfactory.",
            "regulatory_facts",
        ),
        (
            "What is the difference between Term Insurance and Endowment/ULIP plans?",
            "Term Insurance is pure risk protection — you pay a small annual premium (₹8,000–₹15,000 "
            "for ₹1 Crore cover for a 30-year-old) and your family receives the full Sum Assured only "
            "if you pass away during the policy term. There is no maturity benefit if you survive.\n\n"
            "Endowment/ULIP plans mix insurance with investment — you pay much higher premiums and get "
            "money back at maturity, but the life cover is dangerously low (₹10–15 Lakhs) and returns "
            "are poor (4–5% annualised). The golden rule: Keep insurance and investment separate. Buy "
            "pure Term Insurance for protection and invest savings in mutual funds for wealth creation.",
            "concept_explanation",
        ),
        (
            "Why should I not mix insurance with investment in India?",
            "Mixing insurance and investment in endowment or ULIP plans causes two problems simultaneously:\n"
            "1. Inadequate life cover: A ₹50,000/year endowment plan for 20 years typically provides "
            "only ₹10–15 Lakhs life cover — far too little to replace 10–15 years of lost income for "
            "your dependents.\n"
            "2. Poor returns: The annualised return on endowment plans is 4–5% — well below inflation "
            "(6–7%) and far below equity mutual fund returns (12–15% long-term).\n\n"
            "The right approach: Pay ₹8,000–₹12,000/year for a pure ₹1 Crore term plan and invest "
            "₹38,000–₹42,000/year in index mutual funds. Over 25 years, this combination gives your "
            "family 8× higher life protection and builds substantially more wealth.",
            "buyer_advice",
        ),
        (
            "How much life insurance coverage do I need?",
            "A common rule of thumb is 15 to 20 times your annual take-home income. For example:\n"
            "• Annual income ₹8 Lakhs → Life cover needed: ₹1.2 Crore to ₹1.6 Crore.\n"
            "• Annual income ₹15 Lakhs → Life cover needed: ₹2.25 Crore to ₹3 Crore.\n\n"
            "Additional factors to consider:\n"
            "• Outstanding home loan or car loan (add the outstanding balance to your coverage)\n"
            "• Children's education costs (add ₹50 Lakhs to ₹1 Crore if planning)\n"
            "• Aging dependent parents\n"
            "Buy the coverage early (in your 20s) — premiums are lowest and medical tests are fewest.",
            "buyer_advice",
        ),
        (
            "What is Zero Depreciation in car insurance? Is it worth buying?",
            "Zero Depreciation (also called Bumper-to-Bumper or Nil Depreciation) is an add-on cover "
            "for motor insurance that removes the depreciation deduction when calculating your claim payout.\n\n"
            "Without Zero Depreciation: A 3-year-old car's plastic bumper replacement may only get "
            "₹3,500 payout against a ₹7,000 replacement cost (50% depreciation deducted).\n\n"
            "With Zero Depreciation: The insurer pays ₹7,000 — the full replacement cost.\n\n"
            "Is it worth it? Yes, for cars under 5 years old. The add-on typically costs ₹1,500–₹4,000 "
            "extra per year and can save ₹15,000–₹30,000 in a single accident claim involving plastic, "
            "rubber, and fiber components.",
            "coverage_qa",
        ),
        (
            "Should I buy health insurance for my elderly parents separately or add them to my family floater?",
            "Strongly recommended: Keep elderly parents (above 55–60) on SEPARATE senior citizen policies "
            "rather than adding them to your family floater.\n\n"
            "Why separate is better:\n"
            "1. Premium impact: In a floater policy, the premium is calculated based on the OLDEST member. "
            "Adding a 64-year-old parent can double the premium for your entire family.\n"
            "2. Claim exhaustion risk: Senior citizens make more frequent and expensive claims. Their "
            "hospitalizations can exhaust the shared pool, leaving you and your children under-covered.\n"
            "3. Pre-existing disease complications: If parents have diabetes or hypertension, their PED "
            "waiting period affects the entire floater.\n\n"
            "Smart structure: Floater for young family (₹15–25L) + Separate senior citizen policies "
            "for parents (₹10L each) + Super Top-Up for all.",
            "buyer_advice",
        ),
    ]

    for instruction, output, category in regulatory_qa:
        examples.append(make_example(instruction=instruction, output=output, category=category))

    logger.info("  → %d regulatory/advice examples", len(examples))
    return examples


# ─── 7. DB EXAMPLES (if available) ───────────────────────────────────────────

def build_db_examples() -> List[Dict]:
    """
    Comprehensive DB-grounded training examples from all 75 policies and 30 glossary terms.
    Generates 30+ distinct question types per policy including coverage Q&A, comparisons,
    buyer advice, claims, exclusions, waiting periods, premiums, and glossary deep-dives.
    """
    examples = []
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "backend"))
        from app.core.database import SessionLocal
        from app.models.policy import InsurancePolicy
        from app.models.benefit_exclusion import PolicyBenefit, PolicyExclusion, PolicyWaitingPeriod
        from app.models.fact import PolicyFact
        from app.models.document import DocumentChunk
        from app.models.glossary import GlossaryTerm

        db = SessionLocal()
        logger.info("Building comprehensive examples from PostgreSQL (all 75 policies + 30 glossary terms)...")

        # ── Load all policies ────────────────────────────────────────────────
        policies = db.query(InsurancePolicy).filter(InsurancePolicy.is_active == True).all()
        logger.info("  Found %d active policies", len(policies))

        for p in policies:
            n = p.name
            ins = p.insurer.name if p.insurer else "the insurer"
            cat = p.category.name if p.category else "insurance"
            slug = p.slug or ""

            # ── 1. Full policy snapshot ─────────────────────────────────────
            snap_lines = [f"{n} is a {cat} product offered by {ins}."]
            if p.min_sum_insured and p.max_sum_insured:
                snap_lines.append(f"Sum Insured range: ₹{int(p.min_sum_insured/100000)} Lakhs to ₹{int(p.max_sum_insured/100000)} Lakhs.")
            if p.indicative_annual_premium:
                snap_lines.append(f"Indicative annual premium: approximately ₹{int(p.indicative_annual_premium):,}/year.")
            if p.room_rent_capping:
                snap_lines.append(f"Room rent: {p.room_rent_capping}.")
            if p.copay_percentage is not None:
                snap_lines.append(f"Co-payment: {p.copay_percentage}% {'mandatory co-pay' if p.copay_percentage > 0 else '(zero co-pay — full settlement by insurer)'}.")
            if p.restoration_benefit:
                snap_lines.append(f"Restoration benefit: {p.restoration_benefit}.")
            if p.no_claim_bonus:
                snap_lines.append(f"No Claim Bonus: {p.no_claim_bonus}.")
            if p.pre_hospitalization_days:
                snap_lines.append(f"Pre-hospitalization: {p.pre_hospitalization_days} days covered.")
            if p.post_hospitalization_days:
                snap_lines.append(f"Post-hospitalization: {p.post_hospitalization_days} days covered.")
            if p.cashless_network_size:
                snap_lines.append(f"Cashless network: {p.cashless_network_size:,}+ hospitals across India.")
            if p.ayush_treatment:
                snap_lines.append(f"AYUSH treatment: {p.ayush_treatment}.")
            if p.day_care_procedures:
                snap_lines.append(f"Day care procedures: {p.day_care_procedures}.")
            if p.entry_age_min and p.entry_age_max:
                snap_lines.append(f"Entry age: {p.entry_age_min} to {p.entry_age_max} years.")
            if p.summary:
                snap_lines.append(f"\nSummary: {p.summary[:300]}")

            examples.append(make_example(
                instruction=f"Give me a complete factual overview of the {n} policy.",
                output="\n".join(snap_lines),
                category="coverage_qa",
            ))

            # ── 2. Coverage / benefits list ─────────────────────────────────
            if p.benefits:
                benefit_lines = []
                for b in p.benefits:
                    line = f"• {b.title}: {b.description}"
                    if b.sub_limit:
                        line += f" (Sub-limit: {b.sub_limit})"
                    benefit_lines.append(line)
                benefits_text = "\n".join(benefit_lines)

                examples.append(make_example(
                    instruction=f"What does {n} cover? List all benefits.",
                    output=benefits_text,
                    category="coverage_qa",
                ))
                examples.append(make_example(
                    instruction=f"Is AYUSH / alternative medicine treatment covered under {n}?",
                    output=next(
                        (f"Yes. {b.description} (Sub-limit: {b.sub_limit})" for b in p.benefits if "AYUSH" in b.title.upper()),
                        f"AYUSH coverage details for {n} are not explicitly listed as a standalone benefit. Refer to the official policy wording or contact {ins} directly."
                    ),
                    category="coverage_qa",
                ))
                examples.append(make_example(
                    instruction=f"Does {n} cover daycare or OPD procedures?",
                    output=next(
                        (f"Yes. {b.description} (Sub-limit: {b.sub_limit})" for b in p.benefits if "DAYCARE" in b.title.upper() or "DAY CARE" in b.title.upper() or "OPD" in b.title.upper()),
                        f"{n} covers standard daycare procedures where 24-hour hospitalization is not required due to medical advances. Check the official policy wording for the list of covered procedures."
                    ),
                    category="coverage_qa",
                ))
                examples.append(make_example(
                    instruction=f"What is the ambulance cover provided by {n}?",
                    output=next(
                        (f"{b.description} (Sub-limit: {b.sub_limit})" for b in p.benefits if "AMBULANCE" in b.title.upper()),
                        f"Ambulance cover details for {n} are not separately listed. Standard IRDAI guidelines require all health policies to cover medically necessary ambulance charges; verify in the policy wording from {ins}."
                    ),
                    category="coverage_qa",
                ))

            # ── 3. Exclusions (all types + specific questions) ──────────────
            if p.exclusions:
                excl_lines = [f"• {e.title}: {e.description} (Type: {e.exclusion_type})" for e in p.exclusions]
                examples.append(make_example(
                    instruction=f"What is NOT covered under {n}? List all exclusions.",
                    output=f"The following are not covered under {n}:\n" + "\n".join(excl_lines),
                    category="coverage_qa",
                ))
                examples.append(make_example(
                    instruction=f"Will {n} cover my cosmetic surgery?",
                    output=next(
                        (f"No. {e.description} Cosmetic and aesthetic procedures are a standard permanent exclusion under {n}." for e in p.exclusions if "COSMETIC" in e.title.upper() or "AESTHETIC" in e.title.upper()),
                        f"Cosmetic surgery is generally excluded under Indian health insurance policies including {n}. Only reconstructive surgeries required after accidents or cancer treatment are covered."
                    ),
                    category="coverage_qa",
                ))
                examples.append(make_example(
                    instruction=f"Is alcohol or substance abuse treatment covered under {n}?",
                    output=next(
                        (f"No. {e.description} This is a permanent exclusion." for e in p.exclusions if "ALCOHOL" in e.title.upper() or "SUBSTANCE" in e.title.upper()),
                        f"Alcohol and substance abuse rehabilitation is generally not covered under {n}. This is a standard permanent exclusion under IRDAI guidelines."
                    ),
                    category="coverage_qa",
                ))

            # ── 4. Waiting periods (multiple question styles) ───────────────
            if p.waiting_periods:
                wp_lines = []
                for wp in p.waiting_periods:
                    line = f"• {wp.category} — {wp.duration_months} month(s): {wp.description}"
                    if wp.practical_impact:
                        line += f"\n  Practical Impact: {wp.practical_impact}"
                    wp_lines.append(line)
                wp_text = "\n".join(wp_lines)

                examples.append(make_example(
                    instruction=f"What are the waiting periods for {n}?",
                    output=wp_text,
                    category="regulatory_facts",
                ))
                examples.append(make_example(
                    instruction=f"I have diabetes. When will {n} start covering my condition?",
                    output=next(
                        (
                            f"Under {n}, your diabetes (a Pre-Existing Disease) will be covered after the PED waiting period: {wp.duration_months} months ({wp.duration_months // 12} years) from policy inception.\n\nPractical Impact: {wp.practical_impact or 'Ensure all pre-existing conditions are disclosed truthfully in the proposal form. Non-disclosure can lead to permanent claim rejection.'}"
                            for wp in p.waiting_periods if "PRE" in wp.category.upper() or "PED" in wp.category.upper()
                        ),
                        f"Under {n}, pre-existing diseases like diabetes are typically subject to a waiting period of 24 to 36 months as per IRDAI norms. Please check the official policy wording from {ins} for the exact duration."
                    ),
                    category="regulatory_facts",
                ))
                examples.append(make_example(
                    instruction=f"If I need cataract surgery, how long do I have to wait before {n} covers it?",
                    output=next(
                        (
                            f"Cataract surgery falls under the 'Specific Named Illnesses' waiting period in {n}: {wp.duration_months} months ({wp.duration_months // 12} year{'s' if wp.duration_months > 12 else ''}) from policy commencement.\n\nNote: {wp.practical_impact or 'Planned procedures like cataract surgery, hernia repair, and joint replacements cannot be claimed during this waiting period.'}"
                            for wp in p.waiting_periods if "SPECIFIC" in wp.category.upper() or "NAMED" in wp.category.upper() or "ILLNESS" in wp.category.upper()
                        ),
                        f"Cataract surgery is a specific named illness under {n} and is subject to a 24-month waiting period (standard IRDAI norm). Verify the exact duration in {ins}'s official policy wording."
                    ),
                    category="regulatory_facts",
                ))
                examples.append(make_example(
                    instruction=f"I was just diagnosed with an illness 2 weeks after buying {n}. Will it be covered?",
                    output=next(
                        (
                            f"No. {n} has an Initial Waiting Period of {wp.duration_months} month(s) ({wp.duration_months * 30} days) from the date of policy commencement. During this window, all non-accidental illness hospitalizations are excluded.\n\nException: If the hospitalization is caused by an accidental injury (e.g., a road accident, fall, or burn), it is covered from Day 1. {wp.practical_impact or ''}"
                            for wp in p.waiting_periods if "INITIAL" in wp.category.upper()
                        ),
                        f"Most health insurance policies including {n} have an initial waiting period of 30 days from inception. Illnesses contracted in this window are excluded unless caused by an accidental injury. Please verify in the official policy wording from {ins}."
                    ),
                    category="regulatory_facts",
                ))

            # ── 5. Pros/Cons analysis ───────────────────────────────────────
            if p.pros:
                pros_text = "\n".join(f"✅ {pro}" for pro in p.pros)
                examples.append(make_example(
                    instruction=f"What are the key advantages of choosing {n}?",
                    output=f"Key advantages of {n} ({ins}):\n\n{pros_text}",
                    category="policy_comparison",
                ))
            if p.cons:
                cons_text = "\n".join(f"⚠️ {con}" for con in p.cons)
                examples.append(make_example(
                    instruction=f"What are the drawbacks or limitations of {n}?",
                    output=f"Key limitations of {n} ({ins}):\n\n{cons_text}\n\n> Always read the official policy wording before purchasing. No policy is perfect — choose based on your specific age, city, and medical history.",
                    category="policy_comparison",
                ))
            if p.pros and p.cons:
                examples.append(make_example(
                    instruction=f"Should I buy {n}? Give me a balanced pros and cons analysis.",
                    output=(
                        f"### {n} — Balanced Analysis\n\n"
                        f"**Offered by**: {ins}\n"
                        f"**Category**: {cat}\n\n"
                        f"**Pros (Strengths)**:\n" + "\n".join(f"✅ {pro}" for pro in p.pros) +
                        f"\n\n**Cons (Limitations)**:\n" + "\n".join(f"⚠️ {con}" for con in p.cons) +
                        "\n\n**Verdict**: Whether this policy is right for you depends on your age, sum insured requirement, pre-existing health conditions, and city tier. Compare at least 3 policies before deciding."
                    ),
                    category="policy_comparison",
                ))

            # ── 6. Premium and SI questions ─────────────────────────────────
            if p.indicative_annual_premium and p.min_sum_insured:
                examples.append(make_example(
                    instruction=f"What is the premium for {n}? Is it worth the cost?",
                    output=(
                        f"The indicative annual premium for {n} (by {ins}) is approximately ₹{int(p.indicative_annual_premium):,}/year for a base sum insured starting from ₹{int(p.min_sum_insured/100000)} Lakhs.\n\n"
                        f"Value Assessment:\n"
                        f"• Monthly cost equivalent: ₹{int(p.indicative_annual_premium/12):,}/month.\n"
                        f"• A single 4-day hospitalization (room + surgery + ICU) in a Tier-1 city can easily cost ₹2–5 Lakhs.\n"
                        f"• The premium covers you for up to ₹{int((p.max_sum_insured or p.min_sum_insured)/100000)} Lakhs of medical expenses.\n\n"
                        f"> Premiums increase with age, pre-existing conditions, and sum insured. The indicative rate shown is for a standard healthy adult profile. Request a personalised quote from {ins}."
                    ),
                    category="buyer_advice",
                ))

            # ── 7. Room rent and proportionate deduction ────────────────────
            if p.room_rent_capping:
                examples.append(make_example(
                    instruction=f"What is the room rent policy for {n}? Will I face proportionate deduction?",
                    output=(
                        f"Room Rent Policy for {n} ({ins}):\n{p.room_rent_capping}\n\n"
                        + (
                            "Since there is NO room rent capping, you can choose any hospital room (Single Private AC, Deluxe, or even a suite) without triggering proportionate deductions on your doctor, surgeon, or operation theatre charges. This is a major consumer-friendly feature."
                            if "no room rent" in p.room_rent_capping.lower() or "no capping" in p.room_rent_capping.lower()
                            else
                            "CAUTION: This policy has room rent capping. If you choose a room costing more than the allowed limit, the insurer applies 'proportionate deduction' on ALL associated medical expenses (doctor fees, surgery, OT charges), not just the excess room rent. This can result in you paying 30–60% of your total hospital bill out of pocket."
                        )
                    ),
                    category="coverage_qa",
                ))

            # ── 8. Restoration / NCB / bonus ───────────────────────────────
            if p.restoration_benefit:
                examples.append(make_example(
                    instruction=f"Does {n} have a restoration or refill benefit? How does it work?",
                    output=(
                        f"Yes. {n} includes a restoration benefit:\n{p.restoration_benefit}\n\n"
                        "How it helps: If you exhaust your Sum Insured during the year (e.g., a major surgery uses up ₹10 Lakhs), the restoration benefit automatically refills your cover so subsequent hospitalizations are still covered within the same policy year."
                    ),
                    category="coverage_qa",
                ))
            if p.no_claim_bonus:
                examples.append(make_example(
                    instruction=f"What No Claim Bonus do I get if I don't file any claims under {n}?",
                    output=(
                        f"No Claim Bonus (NCB) under {n} ({ins}):\n{p.no_claim_bonus}\n\n"
                        "The NCB rewards you for every claim-free policy year by increasing your effective Sum Insured without increasing your base premium. Accumulating the NCB over multiple years significantly improves your financial protection as your medical needs increase with age."
                    ),
                    category="buyer_advice",
                ))

            # ── 9. Network hospitals and cashless ──────────────────────────
            if p.cashless_network_size:
                examples.append(make_example(
                    instruction=f"How many cashless hospitals does {n} offer? Is cashless available in my city?",
                    output=(
                        f"{n} by {ins} has a cashless network of {p.cashless_network_size:,}+ empaneled hospitals across India.\n\n"
                        "How to check hospitals in your city:\n"
                        f"1. Visit the official {ins} website.\n"
                        "2. Go to 'Find a Hospital' or 'Network Hospital Locator'.\n"
                        "3. Filter by your city and treatment type.\n\n"
                        "Tip: Always verify the hospital is in-network before admission for planned procedures. In emergencies, IRDAI's 'Cashless Everywhere' directive (2024) allows cashless admission even at non-network hospitals upon 48-hour notification."
                    ),
                    category="claims_guidance",
                ))

            # ── 10. Pre/Post hospitalization ───────────────────────────────
            if p.pre_hospitalization_days or p.post_hospitalization_days:
                pre = p.pre_hospitalization_days or 30
                post = p.post_hospitalization_days or 60
                examples.append(make_example(
                    instruction=f"Does {n} cover medical expenses before and after my hospital stay?",
                    output=(
                        f"Yes. {n} covers pre and post hospitalization expenses:\n\n"
                        f"• Pre-Hospitalization: {pre} days before the admission date.\n"
                        f"  Covers: Doctor consultation fees, diagnostic tests (blood work, MRI, CT scan, X-rays), and prescribed medicines incurred while diagnosing the condition that led to hospitalization.\n\n"
                        f"• Post-Hospitalization: {post} days after the discharge date.\n"
                        f"  Covers: Follow-up doctor visits, medicines, physiotherapy, and investigation reports directly related to the hospitalized condition.\n\n"
                        "How to claim: Collect all original bills, prescriptions, reports, and payment receipts. Submit a reimbursement claim with your discharge summary within 30 days of the post-hospitalization coverage window closing."
                    ),
                    category="claims_guidance",
                ))

            # ── 11. Entry age / eligibility ────────────────────────────────
            if p.entry_age_min and p.entry_age_max:
                examples.append(make_example(
                    instruction=f"Who is eligible to buy {n}? What are the age limits?",
                    output=(
                        f"Eligibility for {n} ({ins}):\n\n"
                        f"• Minimum entry age: {p.entry_age_min} years.\n"
                        f"• Maximum entry age: {p.entry_age_max} years.\n\n"
                        f"{'This policy covers all adults and may include senior citizen coverage — valuable for those aged 60+.' if p.entry_age_max >= 75 else 'Note: The policy has an upper age limit of ' + str(p.entry_age_max) + ' years for new entries. If you are above this age, consider senior citizen-specific policies.'}\n\n"
                        "Lifetime Renewability: Under IRDAI regulations, all individual health insurance policies must offer lifetime renewability and cannot deny renewal solely on the basis of age, deteriorating health, or claim history."
                    ),
                    category="buyer_advice",
                ))

            # ── 12. Summary / introduction question ────────────────────────
            if p.summary:
                examples.append(make_example(
                    instruction=f"Tell me about the {n} insurance plan. Who is it best suited for?",
                    output=(
                        f"{p.summary}\n\n"
                        f"Offered by {ins}, this is a {cat} product.\n\n"
                        f"Best suited for: {'Individuals and families seeking broad health coverage with modern features.' if 'health' in cat.lower() else 'Policyholders requiring ' + cat.lower() + ' protection.'}"
                    ),
                    category="concept_explanation",
                ))

        # ── Cross-policy comparisons (generated from pairs of health policies) ──
        logger.info("  Building cross-policy comparison examples...")
        health_policies = [p for p in policies if p.category and "health" in p.category.name.lower() and p.indicative_annual_premium]
        for i in range(min(len(health_policies), 25)):
            for j in range(i + 1, min(i + 4, len(health_policies))):
                pa, pb = health_policies[i], health_policies[j]
                if not (pa.insurer and pb.insurer):
                    continue
                comp_lines = [f"### {pa.name} vs {pb.name}\n"]
                fields = [
                    ("Room Rent", pa.room_rent_capping, pb.room_rent_capping),
                    ("Co-payment", f"{pa.copay_percentage}%" if pa.copay_percentage is not None else "N/A", f"{pb.copay_percentage}%" if pb.copay_percentage is not None else "N/A"),
                    ("Restoration", pa.restoration_benefit, pb.restoration_benefit),
                    ("No Claim Bonus", pa.no_claim_bonus, pb.no_claim_bonus),
                    ("Pre-hospitalization", f"{pa.pre_hospitalization_days} days" if pa.pre_hospitalization_days else "N/A", f"{pb.pre_hospitalization_days} days" if pb.pre_hospitalization_days else "N/A"),
                    ("Post-hospitalization", f"{pa.post_hospitalization_days} days" if pa.post_hospitalization_days else "N/A", f"{pb.post_hospitalization_days} days" if pb.post_hospitalization_days else "N/A"),
                    ("Cashless Network", f"{pa.cashless_network_size:,}+ hospitals" if pa.cashless_network_size else "N/A", f"{pb.cashless_network_size:,}+ hospitals" if pb.cashless_network_size else "N/A"),
                    ("Indicative Premium", f"₹{int(pa.indicative_annual_premium):,}/yr" if pa.indicative_annual_premium else "N/A", f"₹{int(pb.indicative_annual_premium):,}/yr" if pb.indicative_annual_premium else "N/A"),
                ]
                for label, va, vb in fields:
                    if va and vb:
                        comp_lines.append(f"**{label}**: {pa.name} = {va} | {pb.name} = {vb}")
                comp_lines.append("\n**Buyer Guidance**: Neither policy is universally superior. The best choice depends on your age, city, sum insured requirement, and whether you have pre-existing conditions. Always shortlist 2-3 options and compare official policy wordings before purchasing.")
                examples.append(make_example(
                    instruction=f"Compare {pa.name} and {pb.name}. Which is better?",
                    output="\n".join(comp_lines),
                    category="policy_comparison",
                ))

        # ── Per-field cross-policy comparisons (room rent, co-pay, network) ──
        comparison_fields = [
            ("room_rent_capping", "room rent policy"),
            ("copay_percentage", "co-payment clause"),
            ("cashless_network_size", "cashless hospital network size"),
            ("indicative_annual_premium", "annual premium"),
            ("pre_hospitalization_days", "pre-hospitalization coverage"),
            ("post_hospitalization_days", "post-hospitalization coverage"),
        ]
        for field_attr, field_label in comparison_fields:
            field_lines = []
            for p in health_policies:
                val = getattr(p, field_attr, None)
                if val:
                    field_lines.append(f"• {p.name} ({p.insurer.name if p.insurer else 'N/A'}): {val}")
            if len(field_lines) >= 3:
                examples.append(make_example(
                    instruction=f"Compare the {field_label} across all major health insurance policies in your database.",
                    output="\n".join(field_lines[:20]),
                    category="policy_comparison",
                ))

        # ── 7b. High-confidence verified policy facts ────────────────────────
        logger.info("  Pulling high-confidence PolicyFacts...")
        facts = db.query(PolicyFact).filter(
            PolicyFact.confidence_score >= 0.8,
            PolicyFact.evidence_snippet.isnot(None),
        ).all()

        for fact in facts:
            pol_name = fact.policy.name if fact.policy else "the policy"
            field = fact.field_name.replace("_", " ").title()
            val = fact.normalized_value or fact.field_value
            ev = fact.evidence_snippet

            # Multi-style questions for each fact
            examples.append(make_example(
                instruction=f"What is the {field} for {pol_name}?",
                output=f"{val}\n\nSource evidence: \"{ev}\"" + (f" (Page {fact.page_number})" if fact.page_number else ""),
                category="coverage_qa",
            ))
            examples.append(make_example(
                instruction=f"Can you verify the {field} for {pol_name} with source evidence?",
                output=f"Verified: {val}\n\nEvidence from official policy wording: \"{ev}\"" + (f" (Page {fact.page_number})" if fact.page_number else ""),
                category="coverage_qa",
            ))

        # ── 7c. Document chunks → section-level QA ───────────────────────────
        logger.info("  Building QA from document chunks...")
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.content.isnot(None),
            DocumentChunk.section_title.isnot(None),
        ).all()

        for chunk in chunks:
            if not chunk.content or len(chunk.content) < 120:
                continue
            section = chunk.section_title or "Policy Terms"
            pol_name = chunk.policy.name if chunk.policy else "this insurance policy"
            content = clean(chunk.content[:800])

            examples.append(make_example(
                instruction=f"What does the '{section}' section of {pol_name} say?",
                output=content,
                category="coverage_qa",
            ))
            examples.append(make_example(
                instruction=f"Summarize the {section} clause from the {pol_name} policy wording.",
                output=f"From the {pol_name} official policy wording:\n\n{content}",
                category="coverage_qa",
            ))

        # ── 7d. Glossary terms → multi-style QA ─────────────────────────────
        logger.info("  Building glossary term QA from DB terms...")
        terms = db.query(GlossaryTerm).all()
        for t in terms:
            term = t.term
            what = clean(t.what_does_it_mean or "")
            why = clean(t.why_does_it_matter or "")
            example_text = clean(t.financial_impact_example or "")
            tradeoff = clean(t.trade_off_analysis or "")
            tips = clean(t.watch_out_tips or "")
            aliases = t.aliases or []

            if not what:
                continue

            # Simple definition (multiple phrasings)
            for phrasing in [
                f"What is {term} in Indian insurance?",
                f"Explain {term} in simple terms.",
                f"Define {term} for a first-time insurance buyer in India.",
            ]:
                examples.append(make_example(instruction=phrasing, output=what, category="glossary_definition"))

            # Alias phrasing
            for alias in aliases[:2]:
                examples.append(make_example(
                    instruction=f"What does '{alias}' mean in insurance?",
                    output=f"'{alias}' is another name for '{term}'. {what}",
                    category="glossary_definition",
                ))

            # Why it matters
            if why:
                examples.append(make_example(
                    instruction=f"Why does {term} matter when buying insurance in India?",
                    output=why,
                    category="glossary_definition",
                ))
                examples.append(make_example(
                    instruction=f"How does {term} affect my insurance claim in India?",
                    output=why,
                    category="glossary_definition",
                ))

            # Financial impact example
            if example_text:
                examples.append(make_example(
                    instruction=f"Give me a real ₹ example of how {term} works in India.",
                    output=example_text,
                    category="practical_scenario",
                ))
                examples.append(make_example(
                    instruction=f"How much money could I lose because of {term}? Give a concrete example.",
                    output=example_text,
                    category="practical_scenario",
                ))

            # Trade-off
            if tradeoff:
                examples.append(make_example(
                    instruction=f"What are the trade-offs when choosing a higher vs lower {term}?",
                    output=tradeoff,
                    category="buyer_advice",
                ))

            # Watch-out tips
            if tips:
                examples.append(make_example(
                    instruction=f"What should I watch out for regarding {term} when comparing insurance policies?",
                    output=tips,
                    category="buyer_advice",
                ))
                examples.append(make_example(
                    instruction=f"What are common traps related to {term} in Indian insurance?",
                    output=tips,
                    category="buyer_advice",
                ))

            # Combined deep-dive
            if what and why and example_text:
                full = (
                    f"### {term} — Complete Guide for Indian Insurance Buyers\n\n"
                    f"**What it means**: {what}\n\n"
                    f"**Why it matters**: {why}\n\n"
                    f"**Practical ₹ Example**: {example_text}\n\n"
                    + (f"**Trade-off Analysis**: {tradeoff}\n\n" if tradeoff else "")
                    + (f"**Watch Out For**: {tips}" if tips else "")
                )
                examples.append(make_example(
                    instruction=f"Give me a complete deep-dive on '{term}' for an Indian insurance buyer.",
                    output=full.strip(),
                    category="glossary_definition",
                ))
                examples.append(make_example(
                    instruction=f"I keep hearing '{term}' mentioned — can you explain it thoroughly with examples?",
                    output=full.strip(),
                    category="glossary_definition",
                ))

        db.close()
        logger.info("  → %d comprehensive DB examples generated", len(examples))

    except Exception as e:
        logger.warning("DB examples skipped (DB not reachable): %s", e)

    return examples


# ─── MAIN BUILDER ─────────────────────────────────────────────────────────────

def main():
    logger.info("=" * 60)
    logger.info("BimaGyan LLM Training Dataset Builder")
    logger.info("=" * 60)

    # Import source data directly from Python module
    sys.path.insert(0, str(PROJECT_ROOT / "backend"))
    from app.data.educational_content import GLOSSARY_TERMS_DATA, MODULES_DATA

    all_examples: List[Dict] = []
    category_counts: Dict[str, int] = {}

    # Collect from all sources
    all_examples += build_comprehensive_beginner_guides()
    all_examples += build_glossary_examples(GLOSSARY_TERMS_DATA)
    all_examples += build_module_examples(MODULES_DATA)
    all_examples += build_quiz_examples(MODULES_DATA)
    all_examples += build_regulatory_examples()

    policy_dir = PROJECT_ROOT / "data" / "scraped" / "policies"
    if policy_dir.exists():
        all_examples += build_policy_examples(policy_dir)

    comparison_dir = PROJECT_ROOT / "data" / "scraped" / "comparison"
    if comparison_dir.exists():
        all_examples += build_comparison_examples(comparison_dir, [])

    all_examples += build_db_examples()

    # Remove empty / very short outputs
    all_examples = [e for e in all_examples if e["output"] and len(e["output"]) > 30]

    # Count by category
    for ex in all_examples:
        cat = ex.get("category", "other")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    # Deduplicate by instruction+output
    seen = set()
    unique = []
    for ex in all_examples:
        key = ex["instruction"][:120] + ex["output"][:80]
        if key not in seen:
            seen.add(key)
            unique.append(ex)

    all_examples = unique
    logger.info("Total unique examples after dedup: %d", len(all_examples))

    # Shuffle and split 90/10
    random.seed(42)
    random.shuffle(all_examples)

    split_idx = int(len(all_examples) * 0.9)
    train_examples = all_examples[:split_idx]
    val_examples = all_examples[split_idx:]

    # Write files
    def write_jsonl(path: Path, examples: List[Dict]):
        with open(path, "w", encoding="utf-8") as f:
            for ex in examples:
                f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    write_jsonl(TRAIN_FILE, train_examples)
    write_jsonl(VAL_FILE, val_examples)

    stats = {
        "generated_at": datetime.now().isoformat(),
        "total_examples": len(all_examples),
        "train_examples": len(train_examples),
        "val_examples": len(val_examples),
        "category_breakdown": category_counts,
        "train_file": str(TRAIN_FILE),
        "val_file": str(VAL_FILE),
    }
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    logger.info("")
    logger.info("✅ Dataset built successfully!")
    logger.info("  Train : %s (%d examples)", TRAIN_FILE, len(train_examples))
    logger.info("  Val   : %s (%d examples)", VAL_FILE, len(val_examples))
    logger.info("  Stats : %s", STATS_FILE)
    logger.info("")
    logger.info("Category breakdown:")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        logger.info("  %-30s %d", cat, count)

    return stats


if __name__ == "__main__":
    main()
