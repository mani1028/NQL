from pydantic import BaseModel, Field
from typing import Optional

class Config(BaseModel):
    """Configuration for the nql engine."""
    default_limit: int = 100
    max_limit: int = 1000
    
    # Confidence Tiers
    confidence_auto: float = 0.85
    confidence_confirm: float = 0.65
    confidence_clarify: float = 0.45
    
    # Safety
    query_timeout: int = 5
    max_rows_per_query: int = 1000
    
    # Features
    enable_profiler: bool = False
    enable_cache: bool = True
    cache_path: str = "schema_cache.json"
    log_path: str = "query_logs.jsonl"
    
    # Context
    max_session_history: int = 5
