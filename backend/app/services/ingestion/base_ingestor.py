import hashlib
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseIngestor(ABC):
    """
    Abstract Base Ingestor providing respectful rate-limiting,
    hashing, and error resilience for collecting public insurance documents.
    """
    def __init__(self, request_interval_sec: float = 1.0):
        self.request_interval = request_interval_sec
        self.last_request_time = 0.0

    def _rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_interval:
            time.sleep(self.request_interval - elapsed)
        self.last_request_time = time.time()

    def compute_sha256(self, content_bytes: bytes) -> str:
        return hashlib.sha256(content_bytes).hexdigest()

    @abstractmethod
    def ingest(self, source_target: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Ingests the target document, extracts structured text and metadata.
        """
        pass
