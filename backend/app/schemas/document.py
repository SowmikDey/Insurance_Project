from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class DocumentSourceSchema(BaseModel):
    id: int
    title: str
    source_type: str
    source_url: Optional[str] = None
    file_path: Optional[str] = None
    sha256_hash: Optional[str] = None
    file_size_bytes: int
    version: str
    insurer_name: Optional[str] = None
    policy_name: Optional[str] = None
    chunk_count: int
    is_processed: bool
    created_at: datetime

    class Config:
        from_attributes = True

class IngestionStatusResponse(BaseModel):
    total_sources: int
    total_chunks: int
    processed_sources: int
    recent_sources: List[DocumentSourceSchema]
