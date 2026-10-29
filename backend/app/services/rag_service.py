import time
import re
import math
import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
import httpx
from sqlalchemy.orm import Session
from app.models.document import DocumentChunk, DocumentSource
from app.models.policy import InsurancePolicy
from app.models.fact import PolicyFact
from app.models.review import OfficialDisputeRecord
from app.models.glossary import GlossaryTerm
from app.schemas.assistant import AssistantQueryRequest, AssistantQueryResponse, CitationItem
from app.core.config import settings

logger = logging.getLogger(__name__)

# Minimum relevance score for a retrieved chunk to be considered "on-topic".
# Below this threshold the deterministic synthesizer will say "not enough info"
# rather than presenting irrelevant chunks as an answer.
RELEVANCE_THRESHOLD = 0.12

# In-memory query cache: {query_key: (timestamp, AssistantQueryResponse)}
# Saves ~4-10 seconds on repeated/similar queries; returns in < 5ms.
_QUERY_CACHE: Dict[str, Tuple[float, AssistantQueryResponse]] = {}
CACHE_TTL_SECONDS = 3600  # 1 hour TTL


class RAGService:
    def __init__(self, db: Session):
        self.db = db

    def _tokenize(self, text: str) -> List[str]:
        words = re.findall(r'\b[a-z0-9_]{2,}\b', text.lower())
        stop_words = {
            "the", "and", "is", "in", "to", "of", "for", "with", "on", "at", "by",
            "from", "up", "about", "into", "through", "after", "before", "an", "this",
            "that", "these", "those", "can", "will", "are", "as", "be", "has", "have",
            "what", "how", "which", "why", "where", "who", "whom", "does", "policy", "insurance"
        }
        return [w for w in words if w not in stop_words]

    def _cosine_similarity(self, vec1: Counter, vec2: Counter) -> float:
        intersection = set(vec1.keys()) & set(vec2.keys())
        numerator = sum([vec1[x] * vec2[x] for x in intersection])
        sum1 = sum([val ** 2 for val in vec1.values()])
        sum2 = sum([val ** 2 for val in vec2.values()])
        denominator = math.sqrt(sum1) * math.sqrt(sum2)
        if not denominator:
            return 0.0
        return float(numerator) / denominator

    def _chunks_are_relevant(self, chunks: List[Dict[str, Any]], query_tokens: List[str]) -> bool:
        """
        Returns True only if the top retrieved chunks are genuinely about the query topic.
        Prevents irrelevant chunks (e.g. 'waiting period' docs surfaced by the shared word
        'period' when the user asks about 'maturity period') from being presented as answers.
        """
        if not chunks:
            return False
        top_score = chunks[0].get("score", 0)
        if top_score < RELEVANCE_THRESHOLD:
            return False

        # Extra guard: If user is asking a broad beginner or concept question,
        # specific policy micro-facts (like UIN, or waiting period of a single rider)
        # must NOT be presented as the answer.
        GENERIC_CONCEPT_TRIGGERS = [
            "beginner", "explain health insurance", "how does health insurance work",
            "what is health insurance", "basics of health insurance", "first-time buyer",
            "new to insurance", "floater vs individual", "cashless vs reimbursement",
            "difference between cashless", "section 80d"
        ]
        # Check if query matches a generic concept trigger and does NOT name a specific policy
        query_str = " ".join(query_tokens)
        if any(trigger in query_str for trigger in GENERIC_CONCEPT_TRIGGERS):
            return False

        # Extra guard: if query has a distinct domain keyword that doesn't appear in ANY
        # top chunk's section/title, the chunks are off-topic.
        # E.g. "maturity" not in any "Waiting Period" chunk title → not relevant.
        DOMAIN_KEYWORDS = {
            "maturity": ["maturity", "endowment", "sum assured", "life"],
            "surrender": ["surrender", "lapse", "paid-up"],
            "premium": ["premium", "payment"],
            "claim": ["claim", "reimbursement", "cashless"],
            "nomination": ["nominee", "nomination"],
            "bonus": ["bonus", "reversionary", "terminal"],
            "annuity": ["annuity", "pension"],
            "ulip": ["ulip", "unit", "nav", "fund"],
        }

        for kw, synonyms in DOMAIN_KEYWORDS.items():
            if kw in query_tokens:
                # At least one top chunk must reference the domain
                found = any(
                    any(s in (c.get("section", "") + c.get("title", "") + c.get("content", "")).lower()
                        for s in synonyms)
                    for c in chunks[:2]
                )
                if not found:
                    return False

        return True

    def retrieve_relevant_chunks(self, query: str, policy_id: Optional[int] = None, top_k: int = 4) -> List[Dict[str, Any]]:
        """
        Retrieves top relevant chunks from indexed document chunks, verified policy facts,
        benefits, exclusions, waiting periods, and official dispute records.
        """
        query_tokens = self._tokenize(query)
        if not query_tokens:
            query_tokens = query.lower().split()
        query_vec = Counter(query_tokens)
        scored_chunks = []

        # 1. Fetch chunks from DB
        chunk_query = self.db.query(DocumentChunk).join(DocumentSource)
        if policy_id:
            chunk_query = chunk_query.filter(
                (DocumentChunk.policy_id == policy_id) | (DocumentChunk.policy_id == None)
            )
        chunks = chunk_query.all()

        for c in chunks:
            text = f"{c.section_title or ''} {c.content}"
            doc_tokens = self._tokenize(text)
            doc_vec = Counter(doc_tokens)
            score = self._cosine_similarity(query_vec, doc_vec)

            if policy_id and c.policy_id == policy_id:
                score *= 1.3

            if score > 0.05:
                scored_chunks.append({
                    "chunk": c,
                    "score": score,
                    "title": c.document_source.title if c.document_source else "Official Policy Document",
                    "section": c.section_title or "Coverage & Terms",
                    "content": c.content,
                    "source_url": c.document_source.source_url if c.document_source else None,
                    "source_type": c.document_source.source_type if c.document_source else "Policy Document",
                    "policy_name": c.policy.name if c.policy else (c.document_source.policy_name if c.document_source else None)
                })

        # 2. Search in structured PolicyFacts (Verifiable Evidence)
        fact_query = self.db.query(PolicyFact)
        if policy_id:
            fact_query = fact_query.filter(PolicyFact.policy_id == policy_id)
        facts = fact_query.limit(30).all()
        for f in facts:
            f_text = f"{f.field_name} {f.field_value or ''} {f.normalized_value or ''} {f.evidence_snippet} {f.section_heading or ''}"
            f_vec = Counter(self._tokenize(f_text))
            score = self._cosine_similarity(query_vec, f_vec)
            if score > 0.05:
                scored_chunks.append({
                    "chunk": None,
                    "score": score * 1.25,
                    "title": f"Verified Fact: {f.field_name.replace('_', ' ').title()}",
                    "section": f.section_heading or "Official Terms",
                    "content": f"{f.normalized_value or f.field_value}: \"{f.evidence_snippet}\" (Page {f.page_number or 'N/A'})",
                    "source_url": f.source_url,
                    "source_type": f"Verified Policy Fact ({f.verification_status})",
                    "policy_name": f.policy.name if f.policy else None
                })

        # 3. Search in Official Dispute records if relevant to disputes or regulatory matters
        if any(w in query.lower() for w in ["complaint", "dispute", "ombudsman", "grievance", "fraud", "settlement", "court", "verdict"]):
            disputes = self.db.query(OfficialDisputeRecord).limit(15).all()
            for d in disputes:
                d_text = f"{d.authority_name} {d.provider_slug} {d.allegation} {d.official_findings} {d.decision_outcome}"
                d_vec = Counter(self._tokenize(d_text))
                score = self._cosine_similarity(query_vec, d_vec)
                if score > 0.05:
                    scored_chunks.append({
                        "chunk": None,
                        "score": score * 1.35,
                        "title": f"Official Dispute Finding: {d.dispute_reference} ({d.authority_name})",
                        "section": f"Decision: {d.decision_outcome}",
                        "content": f"Consumer Allegation: {d.allegation}\nOfficial Findings: {d.official_findings}\nOutcome: {d.decision_outcome} (Award: ₹{d.award_amount or 0})",
                        "source_url": d.source_url,
                        "source_type": "Official Regulatory Dispute Record",
                        "policy_name": d.product_name_stated or d.provider_slug
                    })

        # 4. Search in Policy models (benefits, exclusions, waiting periods)
        pol_query = self.db.query(InsurancePolicy)
        if policy_id:
            pol_query = pol_query.filter(InsurancePolicy.id == policy_id)
        policies = pol_query.all()

        for p in policies:
            for b in p.benefits:
                b_text = f"{p.name} {b.title} {b.description} {b.sub_limit}"
                b_vec = Counter(self._tokenize(b_text))
                score = self._cosine_similarity(query_vec, b_vec)
                if score > 0.08:
                    scored_chunks.append({
                        "chunk": None,
                        "score": score,
                        "title": f"{p.name} - Official Prospectus",
                        "section": f"Benefit: {b.title}",
                        "content": f"{b.description} (Sub-limit: {b.sub_limit})",
                        "source_url": p.official_brochure_url or p.policy_wording_url,
                        "source_type": "Official Prospectus",
                        "policy_name": p.name
                    })

            for ex in p.exclusions:
                ex_text = f"{p.name} exclusion {ex.title} {ex.description}"
                ex_vec = Counter(self._tokenize(ex_text))
                score = self._cosine_similarity(query_vec, ex_vec)
                if score > 0.08:
                    scored_chunks.append({
                        "chunk": None,
                        "score": score,
                        "title": f"{p.name} - Policy Wordings",
                        "section": f"Exclusion: {ex.title}",
                        "content": f"{ex.description} (Type: {ex.exclusion_type})",
                        "source_url": p.policy_wording_url,
                        "source_type": "Policy Wordings",
                        "policy_name": p.name
                    })

            for wp in p.waiting_periods:
                wp_text = f"{p.name} waiting period {wp.category} {wp.description} {wp.duration_months}"
                wp_vec = Counter(self._tokenize(wp_text))
                score = self._cosine_similarity(query_vec, wp_vec)
                if score > 0.08:
                    scored_chunks.append({
                        "chunk": None,
                        "score": score,
                        "title": f"{p.name} - Waiting Periods",
                        "section": f"Waiting Period: {wp.category}",
                        "content": f"{wp.duration_months} Months - {wp.description}. Impact: {wp.practical_impact or 'N/A'}",
                        "source_url": p.policy_wording_url,
                        "source_type": "Policy Wordings",
                        "policy_name": p.name
                    })

        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:top_k]

    def _find_related_glossary_terms(self, text: str) -> List[str]:
        terms = self.db.query(GlossaryTerm.term).all()
        found = []
        lower_text = text.lower()
        for (t,) in terms:
            if re.search(r'\b' + re.escape(t.lower()) + r'\b', lower_text):
                found.append(t)
        return found[:4]

    def _call_bimagyan_model(self, prompt: str) -> Optional[str]:
        """
        Calls the Cloudflare Workers AI edge inference endpoint.
        Requires HF_INFERENCE_URL to be configured in environment.
        """
        if not settings.HF_INFERENCE_URL:
            return None
        try:
            headers = {"Content-Type": "application/json"}
            if settings.HF_API_TOKEN and not settings.HF_API_TOKEN.startswith("hf_your_"):
                headers["Authorization"] = f"Bearer {settings.HF_API_TOKEN}"

            url = settings.HF_INFERENCE_URL
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 400,
                    "temperature": 0.2,
                    "do_sample": False,
                    "return_full_text": False,
                }
            }

            res = httpx.post(url, headers=headers, json=payload, timeout=45.0)

            if res.status_code == 200:
                data = res.json()
                if isinstance(data, dict):
                    text = data.get("generated_text") or data.get("response") or ""
                    if text.strip():
                        return text.strip()
                elif isinstance(data, list) and data:
                    text = data[0].get("generated_text") or ""
                    if text.strip():
                        return text.strip()
            else:
                logger.debug("BimaGyan AI returned status %s: %s", res.status_code, res.text[:200])

        except Exception as e:
            logger.info("BimaGyan AI edge endpoint unavailable: %s", e)
        return None

    def generate_response(self, req: AssistantQueryRequest) -> AssistantQueryResponse:
        # ── 1. Check in-memory query cache (< 5ms response on hit) ───────────────
        cache_key = f"{req.query.strip().lower()}_{req.policy_id or 'all'}"
        now = time.time()
        if cache_key in _QUERY_CACHE:
            cached_time, cached_resp = _QUERY_CACHE[cache_key]
            if now - cached_time < CACHE_TTL_SECONDS:
                logger.info("Serving query from cache (< 5ms): %s", req.query[:50])
                return cached_resp

        query_tokens = self._tokenize(req.query)
        chunks = self.retrieve_relevant_chunks(req.query, req.policy_id, top_k=4)
        citations = []
        for c in chunks:
            citations.append(CitationItem(
                title=c["title"],
                section=c["section"],
                snippet=c["content"][:240] + ("..." if len(c["content"]) > 240 else ""),
                source_type=c["source_type"],
                source_url=c["source_url"],
                policy_name=c["policy_name"]
            ))

        related_terms = self._find_related_glossary_terms(req.query)

        # Check if retrieved chunks are actually relevant to the query
        chunks_relevant = self._chunks_are_relevant(chunks, query_tokens)

        # Build evidence context block (only include if relevant)
        context_str = ""
        if chunks_relevant:
            context_str = "\n\n".join([
                f"Source [{i+1}] ({c['title']} - {c['section']}):\n{c['content']}"
                for i, c in enumerate(chunks)
            ])

        system_instruction = (
            "You are BimaGyan AI, an objective, evidence-grounded research and educational assistant for Indian insurance policies.\n"
            "STRICT RULES:\n"
            "1. Ground your answer strictly in the provided Source context.\n"
            "2. If the context does not have verified evidence to answer the question, clearly say so and provide general educational context from your training knowledge.\n"
            "3. Cite source titles and sections where relevant.\n"
            "4. Never claim any policy is 'objectively the best'; explain pros, cons, and trade-offs neutrally.\n\n"
            + (f"VERIFIED EVIDENCE CONTEXT:\n{context_str}\n\n" if context_str else "NOTE: No verified policy documents found for this specific query. Answer from general insurance knowledge.\n\n")
            + f"USER QUERY: {req.query}"
        )

        answer = None
        provider_used = "deterministic"

        # 1. Primary: Cloudflare Workers AI edge model
        answer = self._call_bimagyan_model(system_instruction)
        if answer:
            provider_used = "bimagyan"

        # 2. Graceful deterministic fallback — runs if edge endpoint is offline/warming up
        if not answer:
            answer = self._synthesize_grounded_answer(req.query, chunks, chunks_relevant)

        resp = AssistantQueryResponse(
            answer=answer,
            citations=citations if chunks_relevant else [],
            related_glossary_terms=related_terms,
            provider_used=provider_used,
            disclaimer="Grounded in Indian insurance policy wordings, IRDAI master circulars, and official insurer filings. Educational support only."
        )
        # Store in query cache
        _QUERY_CACHE[cache_key] = (time.time(), resp)
        return resp

    def _synthesize_grounded_answer(self, query: str, chunks: List[Dict[str, Any]], chunks_relevant: bool) -> str:
        """
        Pure deterministic fallback — only runs when all LLM providers are unavailable.
        Only presents chunks if they are actually relevant to the query.
        """
        q_lower = query.lower()

        # ── If we have no relevant context, give an honest educational response ──
        if not chunks_relevant or not chunks:
            return self._educational_fallback(query)

        # ── Relevant chunks found — format them appropriately ──
        if any(w in q_lower for w in ["difference", "compare", "vs", "better", "suggest", "recommend", "which"]):
            lines = [
                "### Comparison & Recommendations Based on Indexed Policy Documents\n",
                "Here is what the indexed policy filings show for your query:\n"
            ]
            for c in chunks:
                lines.append(f"- **{c['policy_name'] or c['title']} ({c['section']})**:\n  {c['content']}\n")
            lines.append("\n**Practical Buyer Guidance:**")
            lines.append("Look beyond the headline premium: check whether room rent has a 1% capping or unlimited single private room, and whether the restoration benefit requires complete or partial sum insured exhaustion.")
            return "\n".join(lines)

        elif any(w in q_lower for w in ["exclusion", "not covered", "reject"]):
            lines = [
                "### Exclusions & Policy Limitations Notice\n",
                "The following exclusions and limitations are explicitly documented in the indexed policy wordings:\n"
            ]
            for c in chunks:
                lines.append(f"• **{c['section']}**: {c['content']}")
            lines.append("\n\n> **Important:** Non-disclosure of pre-existing conditions is the single most common cause for claim repudiation in India. Always disclose all past diagnoses and treatments truthfully upon proposal.")
            return "\n".join(lines)

        elif any(w in q_lower for w in ["waiting", "ped", "pre-existing"]):
            lines = [
                "### Waiting Period Breakdown\n",
                "In India, health insurance waiting periods operate in three distinct stages:\n"
            ]
            for c in chunks:
                lines.append(f"- **{c['section']}**: {c['content']}")
            lines.append("\nDuring the initial 30 days, only accidental emergencies are covered. Specific illnesses (like cataracts, hernia, or joint replacements) usually have a 24-month waiting period, while pre-existing diseases (PED) take 24 to 36 months.")
            return "\n".join(lines)

        elif any(w in q_lower for w in ["complaint", "dispute", "ombudsman", "grievance"]):
            lines = [
                "### Official Dispute & Ombudsman Records Notice\n",
                "Based on public regulatory and Ombudsman findings:\n"
            ]
            for c in chunks:
                lines.append(f"• **{c['title']}** ({c['section']}):\n  {c['content']}\n")
            lines.append("\nNote: Individual complaints and allegations must not be confused with adjudicated verdicts. Always refer to official authority citations.")
            return "\n".join(lines)

        else:
            lines = [
                "### Policy Information Summary\n",
                "According to official policy wordings and regulatory filings:\n"
            ]
            for c in chunks:
                lines.append(f"• **{c['section']}** ({c['title']}):\n  {c['content']}\n")
            return "\n".join(lines)

    def _educational_fallback(self, query: str) -> str:
        """
        Returns a well-structured educational response when no relevant policy documents
        are found for the query. Covers common insurance concepts from general knowledge.
        """
        q_lower = query.lower()

        # ── 1. Beginner / General Health Insurance Guide ──
        if any(w in q_lower for w in ["beginner", "explain health insurance", "how does health insurance work", "what is health insurance", "basics of health insurance"]):
            return (
                "### Understanding Health Insurance: A Complete Beginner's Guide\n\n"
                "Health insurance is a financial safety net designed to protect your savings from being wiped out by unexpected hospitalizations and high medical inflation in India.\n\n"
                "#### 1. The Core Concept: How It Works\n"
                "• **Premium**: You pay an annual fee (e.g. ₹10,000–₹16,000/year for a ₹10–15 Lakh cover for a healthy 30-year-old).\n"
                "• **Sum Insured (SI)**: The maximum hospital bill amount your insurer will pay in a policy year.\n"
                "• **Inpatient & Day Care**: If you are admitted for 24+ hours (or undergo modern daycare procedures like chemotherapy or cataract surgery), the insurer pays for room rent, ICU, doctor fees, tests, and medicines.\n\n"
                "#### 2. Cashless vs Reimbursement Claims\n"
                "• **Cashless Hospitalization**: You show your health card at an empaneled network hospital. The insurer pays the hospital directly upon pre-authorization — you only pay for personal non-medical items.\n"
                "• **Reimbursement**: If admitted to a non-network hospital, you pay the bills upfront and submit original bills, discharge summary, and pharmacy receipts within 15–30 days for a full refund.\n\n"
                "#### 3. The 3 Essential Rules Before Buying\n"
                "1. **No Room Rent Capping**: Avoid policies with a 1% room rent limit. Selecting a higher room triggers 'proportionate deductions', slashing surgery, OT, and doctor fee payouts by up to 40–50%!\n"
                "2. **Zero Co-payment**: Avoid mandatory co-pay (like 20% co-pay), which forces you to pay 20% of every hospital bill out of your own pocket.\n"
                "3. **Check Waiting Periods**: By IRDAI rules, Pre-Existing Diseases (PED) waiting periods are capped at 36 months (3 years). Accidental injuries are covered from Day 1.\n\n"
                "> **Pro-Tip**: Buy early in your 20s or early 30s. Premiums are lowest, medical check-ups are rarely required, and you serve waiting periods while in peak health."
            )

        # ── 2. Cashless vs Reimbursement ──
        if any(w in q_lower for w in ["cashless vs", "reimbursement vs", "difference between cashless"]):
            return (
                "### Cashless vs Reimbursement Claims: Complete Comparison\n\n"
                "| Feature | Cashless Claim | Reimbursement Claim |\n"
                "|---|---|---|\n"
                "| **Where Available** | Empaneled Network Hospitals | Any registered hospital across India |\n"
                "| **Upfront Payment** | ₹0 (Only non-medical consumables) | You pay 100% of the hospital bill upfront |\n"
                "| **Pre-Authorization** | Required (48h before planned, 24h after emergency) | Not mandatory before admission |\n"
                "| **Settlement Time** | Instant at discharge (2–4 hours) | 15–30 days after submitting documents |\n"
                "| **Paperwork Needed** | Health Card + ID Proof at TPA Desk | Original bills, discharge summary, test reports, prescriptions |\n\n"
                "> Under the IRDAI **'Cashless Everywhere'** initiative (2024), policyholders can now request cashless treatment even at non-network hospitals upon 48-hour prior notification."
            )

        # ── 3. Family Floater vs Individual ──
        if any(w in q_lower for w in ["floater", "family floater", "individual vs"]):
            return (
                "### Family Floater vs Individual Health Insurance\n\n"
                "• **Family Floater**: A single Sum Insured (e.g. ₹15 Lakhs) is shared among self, spouse, and children. Highly cost-effective for young families with similar health risks.\n"
                "• **Individual Policy**: Each person has their own dedicated Sum Insured. One member's claim does not affect another's cover.\n\n"
                "**Crucial Advice for Senior Parents:**\n"
                "Never add senior parents (aged 55+) to your family floater. Floater premiums are priced on the **age of the oldest member** — adding a 60-year-old parent will double or triple your family's premium. Keep parents on separate senior citizen plans."
            )

        # ── 4. Maturity period / life insurance concepts ──
        if any(w in q_lower for w in ["maturity", "maturity period", "mature"]):
            return (
                "### What is a Maturity Period in Insurance?\n\n"
                "**Maturity period** is a term primarily used in **life insurance** (not health insurance). "
                "It refers to the date on which a policy *matures* — i.e. the insured amount (Sum Assured) plus any bonuses are paid out to the policyholder, "
                "provided the policy is still in force and the insured is alive.\n\n"
                "**Key points:**\n"
                "- **Endowment plans**, **money-back plans**, and **ULIPs** have maturity periods — typically 10, 15, 20, or 30 years.\n"
                "- **Pure term insurance** has *no maturity benefit* — it pays only on death during the policy term.\n"
                "- **Health insurance** does **not** have a maturity period — it renews annually and has no lump-sum payout on maturity.\n\n"
                "**Why 'maturity period' doesn't apply to health insurance:**\n"
                "> Health insurance is an annual indemnity contract — you pay a premium each year for coverage. "
                "If you don't claim, there is no maturity payout. What health insurers offer instead is a **No Claim Bonus (NCB)** — "
                "an increase in Sum Insured (typically 10–50%) for every claim-free year.\n\n"
                "**If you meant 'renewal' or 'lifetime renewability':**\n"
                "IRDAI mandates that all individual health insurance policies must offer **lifetime renewability** — "
                "insurers cannot deny renewal solely due to age or deteriorating health (post IRDAI circular 2013). "
                "Policies like Care Supreme, Niva Bupa Reassure 2.0, and Star Comprehensive are known for strong lifetime renewability features.\n\n"
                "> **Note:** This answer is based on general IRDAI-regulated insurance principles. "
                "For specific policy details, please refer to the official policy wordings of the insurer."
            )

        # ── Surrender value ──
        if any(w in q_lower for w in ["surrender", "surrender value"]):
            return (
                "### Surrender Value in Insurance\n\n"
                "**Surrender value** is the amount an insurer pays you if you decide to exit a life insurance policy before its maturity date.\n\n"
                "- **Guaranteed Surrender Value (GSV)**: A minimum amount prescribed by IRDAI regulations, typically available after 3 years of premium payment.\n"
                "- **Special Surrender Value (SSV)**: Often higher than GSV, calculated based on the accrued benefits and fund value.\n\n"
                "> Health insurance policies generally have **no surrender value** — premiums are fully earned once the coverage period starts.\n\n"
                "This answer is from general insurance regulatory knowledge. Verify exact values in your policy document."
            )

        # ── Generic "no data found" fallback ──
        return (
            "### Query Outside Current Document Index\n\n"
            "Our verified document index did not return relevant policy clauses for your specific query.\n\n"
            "**What you can do:**\n"
            "- Browse the **Explore Policies** section to compare indexed plans side by side.\n"
            "- Visit the **Learn Insurance** modules for concept-level explanations.\n"
            "- Ask a more specific question, e.g. *'What is the waiting period in Care Supreme?'* or *'Compare Optima Secure vs Niva Bupa Reassure'*.\n"
            "- For official information, visit [IRDAI's consumer portal](https://irdai.gov.in) or the insurer's official website.\n\n"
            "> This platform covers health insurance policies indexed from official IRDAI filings. "
            "Life insurance concepts (endowments, ULIPs, annuities) are not fully indexed yet."
        )
