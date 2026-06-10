from typing import List, Dict, Set
from ..models import DatabaseSchema
from rapidfuzz import fuzz

class SmartJoinPlanner:
    """Detects semantic relationships between tables when foreign keys are missing."""
    def __init__(self, schema: DatabaseSchema, threshold: float = 85.0):
        self.schema = schema
        self.threshold = threshold

    def suggest_joins(self, tables: Set[str]) -> List[Dict[str, str]]:
        if len(tables) < 2:
            return []
            
        joins = []
        table_list = list(tables)
        
        for i in range(len(table_list)):
            for j in range(i + 1, len(table_list)):
                t1_name = table_list[i]
                t2_name = table_list[j]
                
                t1 = next(t for t in self.schema.tables if t.name == t1_name)
                t2 = next(t for t in self.schema.tables if t.name == t2_name)
                
                # Look for column name overlaps or semantic similarities
                # e.g., student.id and attendance.student_id
                for c1 in t1.columns:
                    for c2 in t2.columns:
                        score = fuzz.ratio(c1.name, c2.name)
                        
                        # Direct match or partial match (like student_id and id)
                        if score > self.threshold or \
                           (c1.name == 'id' and c2.name == f"{t1_name.rstrip('s')}_id") or \
                           (c2.name == 'id' and c1.name == f"{t2_name.rstrip('s')}_id"):
                            
                            joins.append({
                                "left": f"{t1_name}.{c1.name}",
                                "right": f"{t2_name}.{c2.name}",
                                "confidence": score / 100.0,
                                "type": "semantic"
                            })
                            
        return joins
