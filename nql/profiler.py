from sqlalchemy import create_engine, text
from typing import Dict, List

class DataProfiler:
    def __init__(self, connection_url: str):
        self.engine = create_engine(connection_url)
        self.cache: Dict[str, Dict[str, List[str]]] = {}

    def profile(self, tables: List[str]) -> Dict[str, Dict[str, List[str]]]:
        if self.cache:
            return self.cache

        with self.engine.connect() as conn:
            # We use inspector directly or from schema?
            # Let's just do a basic distinct for string columns
            from sqlalchemy import inspect
            inspector = inspect(self.engine)
            for table_name in tables:
                self.cache[table_name] = {}
                for col in inspector.get_columns(table_name):
                    # Only profile string-like types for value matching
                    if str(col['type']).startswith('VARCHAR') or str(col['type']).startswith('TEXT'):
                        try:
                            # Sample values
                            res = conn.execute(text(f'SELECT DISTINCT "{col["name"]}" FROM "{table_name}" WHERE "{col["name"]}" IS NOT NULL LIMIT 20'))
                            values = [str(r[0]) for r in res.fetchall() if r[0]]
                            self.cache[table_name][col['name']] = values
                        except Exception:
                            self.cache[table_name][col['name']] = []
        return self.cache
