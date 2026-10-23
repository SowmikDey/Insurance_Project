import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.glossary import GlossaryTerm
from app.schemas.glossary import HighlightedTermMatch

class GlossaryService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_terms(self, category: Optional[str] = None) -> List[GlossaryTerm]:
        query = self.db.query(GlossaryTerm)
        if category and category.lower() != "all":
            query = query.filter(GlossaryTerm.category.ilike(category))
        return query.order_by(GlossaryTerm.term.asc()).all()

    def get_term_by_slug(self, slug: str) -> Optional[GlossaryTerm]:
        return self.db.query(GlossaryTerm).filter(GlossaryTerm.slug == slug).first()

    def find_terms_in_text(self, text: str) -> List[HighlightedTermMatch]:
        """
        Scans an arbitrary insurance text snippet (e.g. benefit description, exclusion clause)
        and detects known glossary terms to enable Zerodha Varsity-style interactive cards.
        """
        if not text:
            return []
        
        all_terms = self.db.query(GlossaryTerm).all()
        found_matches: List[HighlightedTermMatch] = []
        seen_slugs = set()

        for gt in all_terms:
            patterns = set()
            # Clean base term (e.g. "Co-payment (Co-pay)" -> "Co-payment")
            clean_term = re.sub(r'\(.*?\)', '', gt.term).strip()
            patterns.add(clean_term)
            
            # If term contains hyphen, also add space and merged versions
            if "-" in clean_term:
                patterns.add(clean_term.replace("-", " "))
                patterns.add(clean_term.replace("-", ""))

            if gt.aliases:
                for alias in gt.aliases:
                    if alias:
                        patterns.add(alias.strip())
                        if "-" in alias:
                            patterns.add(alias.replace("-", " ").strip())
                            patterns.add(alias.replace("-", "").strip())
            
            # Add plural / singular variants
            expanded_patterns = set(patterns)
            for p in patterns:
                if p.endswith("s"):
                    expanded_patterns.add(p[:-1])
                else:
                    expanded_patterns.add(p + "s")

            # Sort longer patterns first to match greedy phrases (e.g. "room rent capping" before "room rent")
            sorted_patterns = sorted(expanded_patterns, key=len, reverse=True)
            escaped = [re.escape(p) for p in sorted_patterns if len(p) >= 3]
            
            if not escaped:
                continue

            combined_pattern = r'\b(' + '|'.join(escaped) + r')\b'
            match = re.search(combined_pattern, text, re.IGNORECASE)
            
            if match and gt.slug not in seen_slugs:
                seen_slugs.add(gt.slug)
                found_matches.append(HighlightedTermMatch(
                    term=gt.term,
                    slug=gt.slug,
                    matched_text=match.group(0),
                    summary_preview=gt.what_does_it_mean[:140] + ("..." if len(gt.what_does_it_mean) > 140 else "")
                ))
                
        return found_matches
