from sqlalchemy import Column, String, Text, JSON, Integer, ForeignKey
from app.models.base import TimeStampedModel

class GlossaryTerm(TimeStampedModel):
    __tablename__ = "glossary_terms"
    
    slug = Column(String(100), unique=True, index=True, nullable=False)
    term = Column(String(150), nullable=False)
    aliases = Column(JSON, default=list) # e.g. ["copay", "co-pay", "co payment"]
    category = Column(String(50), default="General") # Health, Life, Motor, Claims, Underwriting
    
    # The 5 Core Varsity-Style Pillars
    what_does_it_mean = Column(Text, nullable=False)
    why_does_it_matter = Column(Text, nullable=False)
    financial_impact_example = Column(Text, nullable=False) # Concrete numerical Indian Rupee example
    trade_off_analysis = Column(Text, nullable=False) # Is higher or lower better? Trade-offs analysis
    watch_out_tips = Column(Text, nullable=False) # Traps, sub-limits, hidden clauses
    
    # Navigation link to related educational module
    related_module_slug = Column(String(100), nullable=True)
    official_reference_source = Column(String(255), default="IRDAI (Health Insurance Regulations) / General Insurance Council")
