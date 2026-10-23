from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from app.models.base import TimeStampedModel

class DocumentSource(TimeStampedModel):
    __tablename__ = "document_sources"
    
    title = Column(String(255), nullable=False)
    source_type = Column(String(50), default="PDF") # PDF, HTML, IRDAI_NOTICE, MANUAL_UPLOAD
    source_url = Column(String(500), nullable=True)
    file_path = Column(String(500), nullable=True)
    sha256_hash = Column(String(64), nullable=True, index=True)
    file_size_bytes = Column(Integer, default=0)
    version = Column(String(50), default="1.0")
    
    insurer_name = Column(String(100), nullable=True)
    policy_name = Column(String(150), nullable=True)
    extracted_text_summary = Column(Text, nullable=True)
    chunk_count = Column(Integer, default=0)
    is_processed = Column(Boolean, default=False)
    metadata_json = Column(JSON, default=dict)
    
    chunks = relationship("DocumentChunk", back_populates="document_source", cascade="all, delete-orphan")

class DocumentChunk(TimeStampedModel):
    __tablename__ = "document_chunks"
    
    document_source_id = Column(Integer, ForeignKey("document_sources.id"), nullable=False)
    policy_id = Column(Integer, ForeignKey("insurance_policies.id"), nullable=True)
    policy_version_id = Column(Integer, ForeignKey("policy_versions.id", ondelete="SET NULL"), nullable=True)
    
    chunk_index = Column(Integer, default=0)
    page_number = Column(Integer, nullable=True)
    section_title = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)
    embedding_json = Column(JSON, nullable=True)
    metadata_json = Column(JSON, default=dict)
    
    document_source = relationship("DocumentSource", back_populates="chunks")
    policy = relationship("InsurancePolicy", back_populates="chunks")
    policy_version = relationship("PolicyVersion")
