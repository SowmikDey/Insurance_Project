import re
import math
import logging
from typing import List, Dict, Any, Optional
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

    def _call_ollama(self, prompt: str) -> Optional[str]:
        """Calls the configured local Ollama endpoint (e.g. Qwen3-4B-Instruct-2507)."""
        try:
            url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
            res = httpx.post(
                url,
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.2, "top_p": 0.9}
                },
                timeout=12.0
            )
            if res.status_code == 200:
                data = res.json()
                return data.get("response", "").strip()
        except Exception as e:
            logger.info("Local Ollama inference unavailable (%s): %s", settings.OLLAMA_MODEL, e)
        return None

    def _call_gemini(self, prompt: str) -> Optional[str]:
        """Calls the Gemini REST API when GEMINI_API_KEY is configured."""
        if not settings.GEMINI_API_KEY:
            return None
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1000}
            }
            res = httpx.post(url, json=payload, timeout=12.0)
            if res.status_code == 200:
                data = res.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
        except Exception as e:
            logger.info("Gemini API call failed: %s", e)
        return None

    def generate_response(self, req: AssistantQueryRequest) -> AssistantQueryResponse:
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

        # Build evidence context block
        context_str = "\n\n".join([
            f"Source [{i+1}] ({c['title']} - {c['section']}):\n{c['content']}"
            for i, c in enumerate(chunks)
        ])

        system_instruction = (
            "You are BimaGyan AI, an objective, evidence-grounded research and educational assistant for Indian insurance policies.\n"
            "STRICT RULES:\n"
            "1. Ground your answer strictly in the provided Source context.\n"
            "2. If the context does not have verified evidence to answer the question, state clearly that official evidence is insufficient and recommend reviewing the insurer's prospectus. Do NOT invent premiums, waiting periods, sub-limits, or claim outcomes.\n"
            "3. Cite source titles and sections where relevant.\n"
            "4. Never claim any policy is 'objectively the best'; explain pros, cons, and trade-offs neutrally.\n\n"
            f"VERIFIED EVIDENCE CONTEXT:\n{context_str}\n\n"
            f"USER QUERY: {req.query}"
        )

        answer = None
        provider = (settings.LLM_PROVIDER or "hybrid").lower()

        # Route by configured provider
        if provider in ("ollama", "local", "qwen"):
            answer = self._call_ollama(system_instruction)
        elif provider in ("gemini",):
            answer = self._call_gemini(system_instruction)
        elif provider in ("hybrid",):
            # Try local Qwen first, then Gemini if key available, then fallback
            answer = self._call_ollama(system_instruction)
            if not answer and settings.GEMINI_API_KEY:
                answer = self._call_gemini(system_instruction)

        # Graceful deterministic fallback
        if not answer:
            answer = self._synthesize_grounded_answer(req.query, chunks, context_str)

        return AssistantQueryResponse(
            answer=answer,
            citations=citations,
            related_glossary_terms=related_terms,
            disclaimer="Grounded in Indian insurance policy wordings, IRDAI master circulars, and official insurer filings. Educational support only."
        )

    def _synthesize_grounded_answer(self, query: str, chunks: List[Dict[str, Any]], context: str) -> str:
        q_lower = query.lower()
        
        if not chunks:
            return (
                "Based on the official insurance documents and IRDAI regulations currently indexed in our system, "
                "we could not find specific verified clauses for your query.\n\n"
                "To protect you from unverified assumptions, we recommend reviewing the insurer's official policy document "
                "or visiting our **Learn Insurance** section to explore core guidelines."
            )

        if any(w in q_lower for w in ["explain", "what is", "how does", "meaning", "beginner"]):
            lines = [
                f"### Understanding: {query.strip().title()}\n",
                "Based on verified Indian insurance policy documentation and IRDAI standards:\n"
            ]
            for i, c in enumerate(chunks):
                lines.append(f"• **{c['section']}** ({c['title']}):\n  {c['content']}\n")
            
            lines.append("\n**Key Takeaway for First-Time Buyers:**")
            lines.append("Always verify if your policy includes sub-limits or mandatory co-payments, as these determine what portion of the hospital bill you must pay from your own pocket.")
            return "\n".join(lines)

        elif any(w in q_lower for w in ["difference", "compare", "vs"]):
            lines = [
                "### Comparison Analysis Based on Policy Documents\n",
                "Here is how the referenced policies and clauses compare based on verified filings:\n"
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
