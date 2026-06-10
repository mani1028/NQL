from sqlalchemy import create_engine, inspect
from .models import DatabaseSchema, TableSchema, ColumnSchema
from typing import Optional, List, Dict
import re
import hashlib

# Simple lightweight synonym generator
SYNONYMS: Dict[str, List[str]] = {
    "student": ["students", "pupil", "learner"],
    "course": ["courses", "class", "subject"],
    "enrollment": ["enrollments", "registration", "joined"],
    "fee": ["fees", "payment", "pending fee", "balance"],
    "amount": ["total", "value", "cost"],
    "name": ["title", "label"],
    "gender": ["sex", "boy", "girl", "male", "female"],
    "marks": ["score", "grade", "result"]
}

def generate_aliases(name: str) -> List[str]:
    aliases = []
    # Split by underscore or camel case
    words = re.split(r'_|(?=[A-Z])', name)
    clean_name = " ".join([w.lower() for w in words if w]).strip()
    aliases.append(clean_name)
    
    # Check for synonyms
    for word in words:
        w_low = word.lower()
        if w_low in SYNONYMS:
            aliases.extend(SYNONYMS[w_low])
            
    if name.lower() in SYNONYMS:
        aliases.extend(SYNONYMS[name.lower()])
        
    return list(set(aliases))

class SchemaScanner:
    def __init__(self, connection_url: str):
        self.connection_url = connection_url
        self.engine = create_engine(connection_url)

    def get_schema_hash(self) -> str:
        """Generates a stable hash of the current database structure."""
        inspector = inspect(self.engine)
        fingerprint = []
        for table_name in sorted(inspector.get_table_names()):
            fingerprint.append(f"t:{table_name}")
            for col in sorted(inspector.get_columns(table_name), key=lambda x: x['name']):
                fingerprint.append(f"c:{col['name']}:{col['type']}")
        
        return hashlib.sha256(",".join(fingerprint).encode()).hexdigest()

    def scan(self) -> DatabaseSchema:
        inspector = inspect(self.engine)
        tables = []
        
        for table_name in inspector.get_table_names():
            columns = []
            pk_cols = inspector.get_pk_constraint(table_name).get('constrained_columns', [])
            fks = inspector.get_foreign_keys(table_name)
            
            fk_map = {}
            for fk in fks:
                for col_name, ref_col in zip(fk['constrained_columns'], fk['referred_columns']):
                    fk_map[col_name] = f"{fk['referred_table']}.{ref_col}"
            
            for col in inspector.get_columns(table_name):
                columns.append(ColumnSchema(
                    name=col['name'],
                    type=str(col['type']),
                    primary_key=col['name'] in pk_cols,
                    foreign_key=fk_map.get(col['name']),
                    aliases=generate_aliases(col['name'])
                ))
            
            tables.append(TableSchema(
                name=table_name,
                columns=columns,
                aliases=generate_aliases(table_name)
            ))
            
        return DatabaseSchema(tables=tables)
