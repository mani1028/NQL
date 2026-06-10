from .models import QueryPlan, MatchResult, FilterCondition
from .graph import RelationshipGraph
from typing import List, Set, Dict, Any
import re

class QueryPlanner:
    def __init__(self, graph: RelationshipGraph):
        self.graph = graph

    def create_plan(self, matches: List[MatchResult], question: str) -> QueryPlan:
        tables = set()
        select_columns = []
        filters = []
        limit = None

        # Identify tables and columns from matches
        for m in matches:
            if m.type == 'table':
                tables.add(m.table)
            elif m.type == 'column':
                tables.add(m.table)
                select_columns.append({"table": m.table, "column": m.column})

        # If no select columns matched, but tables did, select all from those tables
        if not select_columns and tables:
            for table_name in tables:
                select_columns.append({"table": table_name, "column": "*"})

        # Heuristic for LIMIT
        limit_match = re.search(r'limit\s+(\d+)|top\s+(\d+)|first\s+(\d+)', question.lower())
        if limit_match:
            limit = int(next(g for g in limit_match.groups() if g is not None))

        # Heuristic for FILTERS
        operators = {
            "above": ">", "greater than": ">", "more than": ">", ">": ">",
            "below": "<", "less than": "<", "<": "<",
            "equal to": "=", "is": "=", "=": "=",
            "not": "!="
        }
        
        for m in matches:
            if m.type == 'column':
                pattern = rf"{m.token}\s*(?:{'|'.join(operators.keys())})?\s*(\d+)"
                val_match = re.search(pattern, question.lower())
                if val_match:
                    op_found = "="
                    for op_text, op_sym in operators.items():
                        if op_text in question.lower().split(m.token)[1][:20]:
                            op_found = op_sym
                            break
                    filters.append(FilterCondition(
                        table=m.table,
                        column=m.column,
                        operator=op_found,
                        value=val_match.group(1)
                    ))

        joins = self.graph.get_joins_for_tables(tables)

        return QueryPlan(
            select_columns=select_columns,
            tables=list(tables),
            joins=joins,
            filters=filters,
            limit=limit,
            confidence_score=0.0
        )
