from typing import Dict, Optional, List
from ..models import QueryPlan

class SessionManager:
    """Manages chat history and contextual query merging."""
    def __init__(self, max_history: int = 5):
        self.sessions: Dict[str, List[QueryPlan]] = {}
        self.max_history = max_history

    def get_last_plan(self, session_id: str) -> Optional[QueryPlan]:
        if session_id in self.sessions and self.sessions[session_id]:
            return self.sessions[session_id][-1]
        return None

    def add_plan(self, session_id: str, plan: QueryPlan):
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        self.sessions[session_id].append(plan)
        if len(self.sessions[session_id]) > self.max_history:
            self.sessions[session_id].pop(0)

    def merge_context(self, session_id: str, current_plan: QueryPlan) -> QueryPlan:
        """Merges current plan with the previous one if it's a refinement."""
        
        # Phase 5: Support context clearing
        last_plan = self.get_last_plan(session_id)
        if not last_plan:
            return current_plan

        # Case 1: Refinement (current plan has no tables but last one did)
        if not current_plan.tables and last_plan.tables:
            current_plan.tables = last_plan.tables
            current_plan.joins = last_plan.joins
            current_plan.select_columns = last_plan.select_columns
        
        # Case 2: Drill-down (sequential filters)
        # If current_plan has same tables as last_plan, it's likely a follow-up filter
        if set(current_plan.tables).issubset(set(last_plan.tables)) or set(last_plan.tables).issubset(set(current_plan.tables)):
            # Inherit tables and joins from last_plan to ensure we don't lose context
            current_plan.tables = list(set(current_plan.tables + last_plan.tables))
            
            # Simple unique joins
            all_joins = current_plan.joins + last_plan.joins
            unique_joins = []
            seen_j = set()
            for j in all_joins:
                k = tuple(sorted([j['left'], j['right']]))
                if k not in seen_j:
                    seen_j.add(k)
                    unique_joins.append(j)
            current_plan.joins = unique_joins

            # Inherit filters from last plan that don't conflict with current ones
            current_cols = {(f.table, f.column) for f in current_plan.filters}
            for f in last_plan.filters:
                if (f.table, f.column) not in current_cols:
                    current_plan.filters.append(f)
                    
            # Inherit select_columns if current query doesn't seem to explicitly request new ones
            # Or if it just requested a column that's being filtered/sorted on
            has_wildcard = any(sc.get('column') == '*' for sc in last_plan.select_columns)
            if has_wildcard and not any(sc.get('column') == '*' for sc in current_plan.select_columns):
                # Add wildcard back if we had one
                current_plan.select_columns = last_plan.select_columns
            
            # Inherit sort if current doesn't have one
            if not current_plan.sort and last_plan.sort:
                current_plan.sort = last_plan.sort

        return current_plan

    def clear_session(self, session_id: str):
        if session_id in self.sessions:
            self.sessions[session_id] = []
