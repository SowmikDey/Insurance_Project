import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.fact import PolicyFact, PolicyVersion
from app.models.document import DocumentSource

logger = logging.getLogger(__name__)

class FactExtractionStatus:
    EXTRACTED = "EXTRACTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    VERIFIED = "VERIFIED"
    CONFLICTING = "CONFLICTING"
    UNAVAILABLE = "UNAVAILABLE"

class PolicyFactExtractor:
    """
    Deterministic rule-based and regex extractor for insurance policy terms and conditions.
    Every fact requires exact textual evidence citation (section heading, page number, snippet).
    Extracted facts default to EXTRACTED or NEEDS_REVIEW status; never automatically VERIFIED.
    """

    PATTERNS = {
        "uin_number": [
            r'(?:IRDAI\s+UIN|UIN\s*[:\.\-]\s*|Unique\s+Identification\s+Number\s*[:\.\-]\s*)([A-Z0-9]{3,}[A-Z0-9\/\-]+[Vv]?[0-9]*)',
            r'(?:UIN\s+No\.\s*[:\.\-]?\s*)([A-Z0-9\/]+)',
            r'([A-Z]{3,4}\/HLT\/[A-Z0-9\/\-]+)',
            r'(ICIHLIP[0-9]+V[0-9]+)'
        ],
        "room_rent_capping": [
            r'(?:room\s+rent|room\s+charges|room\s+category)[\s\w,:]*?\b(no\s+(?:sub[\s-]?limit|capping)|single\s+private\s+(?:a\/?c\s+)?room|up\s+to\s+1%\s+of\s+sum\s+insured|up\s+to\s+₹?\s*[\d,]+|actuals)\b',
            r'(?:room\s+rent\s+limit\s*[:\-]\s*)([^\.\n;]{5,60})'
        ],
        "icu_sub_limit": [
            r'(?:ICU|Intensive\s+Care\s+Unit)[\s\w,:]*?\b(no\s+(?:sub[\s-]?limit|capping)|up\s+to\s+2%\s+of\s+sum\s+insured|actuals|up\s+to\s+₹?\s*[\d,]+)\b',
            r'(?:ICU\s+charges\s*[:\-]\s*)([^\.\n;]{5,60})'
        ],
        "copay_percentage": [
            r'\b(?:co[\s-]?payment|copay|co[\s-]?pay)\b[\s\w,:]*?\b(\d{1,2})%\b',
            r'\b(no\s+co[\s-]?payment|0%\s+co[\s-]?pay|nil\s+copay)\b'
        ],
        "pre_hospitalization_days": [
            r'\b(?:pre[\s-]hospitali[sz]ation)\b[\s\w,:]*?\b(\d{1,3})\s*days\b'
        ],
        "post_hospitalization_days": [
            r'\b(?:post[\s-]hospitali[sz]ation)\b[\s\w,:]*?\b(\d{1,3})\s*days\b'
        ],
        "initial_waiting_period": [
            r'(?:initial\s+waiting\s+period|waiting\s+period\s+for\s+any\s+illness)[\s\w,:]*?\b(\d{1,3}\s*days|\d{1,2}\s*months)\b',
            r'\bfirst\s+(\d{1,3}\s*days)\s+waiting\s+period\b'
        ],
        "ped_waiting_period": [
            r'(?:pre[\s-]existing\s+diseases?|PED)[\s\w,:\(\)\-]*?(?:waiting\s+period)[\s\w,:\(\)\-]*?\b(\d{1,2}\s*(?:months|years))\b',
            r'\b(\d{1,2}\s*(?:months|years))\s+(?:waiting\s+period\s+for\s+pre[\s-]existing)\b',
            r'(?:waiting\s+period\s+for\s+pre[\s-]existing)[\s\w,:\(\)\-]*?\b(\d{1,2}\s*(?:months|years))\b'
        ],
        "specific_illness_waiting_period": [
            r'(?:specific\s+(?:named\s+)?(?:ailments|diseases|illnesses))[\s\w,:\(\)\-]*?(?:waiting\s+period)[\s\w,:\(\)\-]*?\b(\d{1,2}\s*(?:months|years))\b',
            r'\b(\d{1,2}\s*(?:months|years))\s+(?:waiting\s+period\s+for\s+specific)\b'
        ],
        "ambulance_cover": [
            r'(?:road\s+ambulance|ambulance\s+(?:charges|cover|expenses))[\s\w,:]*?\b(up\s+to\s+₹?\s*[\d,]+|actuals|covered\s+up\s+to\s+sum\s+insured)\b'
        ],
        "restoration_benefit": [
            r'\b(?:restoration|recharge|refill|reset)\b[\s\w,:]*?\b(100%\s+of\s+sum\s+insured|up\s+to\s+sum\s+insured|available\s+once\s+per\s+year|unlimited\s+restoration)\b'
        ],
        "no_claim_bonus": [
            r'\b(?:cumulative\s+bonus|no\s+claim\s+bonus|NCB)\b[\s\w,:]*?\b(\d{1,2}%\s+per\s+(?:claim[\s-]free\s+)?year\s+up\s+to\s+\d{2,3}%|\d{1,2}%\s+every\s+year)\b'
        ]
    }

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def extract_facts(
        self,
        sections: List[Dict[str, Any]],
        document_source_id: Optional[int] = None,
        source_url: Optional[str] = None,
        policy_id: Optional[int] = None,
        policy_version_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extracts structured policy facts from text sections.
        Each fact retains exact quote evidence, page number, section heading, and extraction status.
        """
        found_facts = []
        discovered_fields = set()

        for s in sections:
            content = s.get("content", "")
            heading = s.get("heading", "General")
            page_num = s.get("page_number")

            if not content:
                continue

            # Check each field pattern
            for field_name, patterns in self.PATTERNS.items():
                if field_name in discovered_fields:
                    continue # First high-confidence occurrence preferred

                for pattern in patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        raw_val = match.group(1).strip()
                        
                        # Extract exact snippet (sentence or surrounding 120 chars)
                        start_pos = max(0, match.start() - 40)
                        end_pos = min(len(content), match.end() + 80)
                        evidence = content[start_pos:end_pos].replace("\n", " ").strip()
                        if start_pos > 0:
                            evidence = "..." + evidence
                        if end_pos < len(content):
                            evidence = evidence + "..."

                        normalized = self._normalize_field_value(field_name, raw_val)
                        verification_status = FactExtractionStatus.EXTRACTED

                        fact_record = {
                            "policy_id": policy_id,
                            "policy_version_id": policy_version_id,
                            "field_name": field_name,
                            "field_value": raw_val,
                            "normalized_value": normalized,
                            "evidence_snippet": evidence,
                            "section_heading": heading[:200],
                            "page_number": page_num,
                            "source_url": source_url,
                            "document_source_id": document_source_id,
                            "extraction_method": "DETERMINISTIC_REGEX",
                            "verification_status": verification_status,
                            "confidence_score": 0.90,
                            "notes": f"Deterministic match on pattern: {pattern[:40]}"
                        }
                        found_facts.append(fact_record)
                        discovered_fields.add(field_name)
                        break

        # Explicitly track unavailable fields
        for expected_field in self.PATTERNS.keys():
            if expected_field not in discovered_fields:
                found_facts.append({
                    "policy_id": policy_id,
                    "policy_version_id": policy_version_id,
                    "field_name": expected_field,
                    "field_value": None,
                    "normalized_value": None,
                    "evidence_snippet": "Clause not detected in provided document sections.",
                    "section_heading": "Document Analysis",
                    "page_number": None,
                    "source_url": source_url,
                    "document_source_id": document_source_id,
                    "extraction_method": "ANALYSIS_ABSENT",
                    "verification_status": FactExtractionStatus.UNAVAILABLE,
                    "confidence_score": 1.0,
                    "notes": "Field absent or not found in source text."
                })

        return found_facts

    def save_facts(
        self,
        facts: List[Dict[str, Any]],
        db: Session,
        policy_id: int,
        policy_version_id: Optional[int] = None
    ) -> List[PolicyFact]:
        """
        Persists extracted policy facts into policy_facts table.
        Does not insert UNAVAILABLE items into policy_facts to preserve database cleanliness,
        while returning all evidenced facts.
        """
        saved_facts = []
        for f in facts:
            if f.get("verification_status") == FactExtractionStatus.UNAVAILABLE:
                continue # Do not persist unavailable placeholders to DB
            
            fact_obj = PolicyFact(
                policy_id=policy_id,
                policy_version_id=policy_version_id,
                field_name=f["field_name"],
                field_value=f.get("field_value"),
                normalized_value=f.get("normalized_value"),
                evidence_snippet=f["evidence_snippet"],
                section_heading=f.get("section_heading"),
                page_number=f.get("page_number"),
                source_url=f.get("source_url"),
                document_source_id=f.get("document_source_id"),
                extraction_method=f.get("extraction_method", "DETERMINISTIC_REGEX"),
                verification_status=f.get("verification_status", FactExtractionStatus.EXTRACTED),
                confidence_score=f.get("confidence_score", 0.90),
                notes=f.get("notes")
            )
            db.add(fact_obj)
            saved_facts.append(fact_obj)

        db.commit()
        return saved_facts

    def _normalize_field_value(self, field_name: str, raw_value: str) -> str:
        """Standardizes extracted values into structured representations."""
        val = raw_value.strip()
        if field_name == "copay_percentage":
            if "no" in val.lower() or "0" in val or "nil" in val.lower():
                return "0%"
            digits = re.findall(r'\d+', val)
            return f"{digits[0]}%" if digits else val

        if field_name in ("pre_hospitalization_days", "post_hospitalization_days"):
            digits = re.findall(r'\d+', val)
            return f"{digits[0]} Days" if digits else val

        if field_name in ("ped_waiting_period", "specific_illness_waiting_period"):
            digits = re.findall(r'\d+', val)
            if digits:
                num = int(digits[0])
                if "year" in val.lower():
                    return f"{num * 12} Months"
                return f"{num} Months"
            return val

        return val
