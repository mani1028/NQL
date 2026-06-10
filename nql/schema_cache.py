import json
import os
from typing import Optional, Dict, Any
from .models import DatabaseSchema

class SchemaCache:
    def __init__(self, cache_path: str = "schema_cache.json"):
        self.cache_path = cache_path

    def save(self, schema: DatabaseSchema, schema_hash: str):
        payload = {
            "hash": schema_hash,
            "schema": schema.model_dump()
        }
        with open(self.cache_path, 'w') as f:
            json.dump(payload, f, indent=2)

    def load(self, current_hash: str) -> Optional[DatabaseSchema]:
        if not os.path.exists(self.cache_path):
            return None
        try:
            with open(self.cache_path, 'r') as f:
                data = json.load(f)
                if data.get("hash") != current_hash:
                    return None # Cache is stale
                return DatabaseSchema.model_validate(data.get("schema"))
        except Exception:
            return None
