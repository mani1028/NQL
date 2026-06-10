import re
from typing import List
from .models import QueryPlan, DatabaseSchema

class SQLValidator:
    def __init__(self, schema: DatabaseSchema):
        self.schema = schema
        self.valid_tables = set(t.name for t in schema.tables)
        self.valid_columns = {t.name: set(c.name for c in t.columns) for t in schema.tables}

    def validate(self, sql: str, plan: QueryPlan) -> List[str]:
        errors = []
        dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "GRANT", "REVOKE"]
        for kw in dangerous_keywords:
            if re.search(rf'\b{kw}\b', sql.upper()):
                errors.append(f"Dangerous SQL operation detected: {kw}")
                
        for t in plan.tables:
            if t not in self.valid_tables:
                errors.append(f"Invalid table reference: {t}")
                
        for sc in plan.select_columns:
            table = sc.get('table')
            column = sc.get('column')
            if table in self.valid_tables and column != "*":
                if column not in self.valid_columns.get(table, set()):
                    errors.append(f"Invalid column reference: {table}.{column}")
                    
        for f in plan.filters:
            if f.table in self.valid_tables:
                if f.column not in self.valid_columns.get(f.table, set()):
                    errors.append(f"Invalid column in filter: {f.table}.{f.column}")

        if sql.count('(') != sql.count(')'):
            errors.append("Unbalanced parentheses in generated SQL.")
        if (sql.count("'") % 2) != 0:
            errors.append("Unbalanced quotes in generated SQL.")
            
        return errors
