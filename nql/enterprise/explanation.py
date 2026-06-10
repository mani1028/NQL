from ..models import QueryPlan

class QueryExplainer:
    """Translates SQL query plans into natural language explanations."""
    def explain(self, plan: QueryPlan) -> str:
        if not plan.tables:
            return "I couldn't identify what you want to look for."

        # Action & Entity
        tables_str = ", ".join(plan.tables)
        explanation = f"I am looking for {tables_str}."

        # Selection
        if plan.select_columns:
            # Handle dicts safely
            cols = [f"{c.get('column')} from {c.get('table')}" for c in plan.select_columns if c.get('column') != '*']
            if cols:
                explanation = f"I am retrieving {', '.join(cols)} from {tables_str}."

        # Joins
        if plan.joins:
            explanation += f" I've connected these tables using their relationships."

        # Transparent Match Decisions (Phase 5 Extension)
        ml_meta = getattr(plan, 'ml_metadata', {})
        decisions = ml_meta.get('match_decisions', [])
        if decisions:
            match_str = ", ".join([f"'{d['token']}' → {d['mapped_to']}" for d in decisions[:3]])
            explanation += f" (Matched: {match_str})"

        # Filters
        if plan.filters:
            filter_strs = [f"{f.table}.{f.column} is {f.operator} {f.value}" for f in plan.filters]
            explanation += f" I am filtering for records where {' and '.join(filter_strs)}."

        # Limit
        if plan.limit:
            explanation += f" I've limited the results to the first {plan.limit} records."

        return explanation
