from sqlalchemy import create_engine, text
from typing import List, Dict, Any, Tuple

class QueryExecutor:
    def __init__(self, connection_url: str, max_rows: int = 1000):
        self.engine = create_engine(connection_url)
        self.max_rows = max_rows

    def execute(self, sql: str, timeout: int = 5) -> Tuple[List[Dict[str, Any]], List[str]]:
        if not sql:
            return [], []
            
        with self.engine.connect() as conn:
            # Note: Timeout implementation varies by dialect. 
            # We attempt standard execution_options where supported.
            try:
                conn = conn.execution_options(timeout=timeout)
            except Exception:
                pass # Fallback for dialects that don't support it directly
                
            result = conn.execute(text(sql))
            columns = list(result.keys())
            # Enforce max rows protection
            rows = []
            for i, row in enumerate(result):
                if i >= self.max_rows:
                    break
                rows.append(dict(zip(columns, row)))
            return rows, columns
