from .ml.inference import MLInference
from .models import QueryPlan, MatchResult, FilterCondition
from .graph import RelationshipGraph
from .date_resolver import DateResolver
from typing import List, Set, Optional, Any, Dict, Tuple
import re

class MLPlanner:
    def __init__(self, graph: RelationshipGraph):
        self.graph = graph
        try:
            self.model = MLInference()
        except Exception:
            self.model = None

    def create_plan(self, matches: List[MatchResult], question: str) -> QueryPlan:
        if not self.model:
            return self._fallback_plan(matches, question)

        prediction = self.model.predict(question)
        ml_plan = prediction['plan']
        
        tables = set()
        select_columns = []
        filters = []
        limit = None
        
        # Rule-based aggregation detection
        agg = None
        q_low = question.lower()
        if "how many" in q_low or "count" in q_low: agg = "COUNT"
        elif "total" in q_low or "sum" in q_low: agg = "SUM"
        elif "average" in q_low or "avg" in q_low: agg = "AVG"
        elif "max" in q_low or "highest" in q_low: agg = "MAX"
        elif "min" in q_low or "lowest" in q_low: agg = "MIN"

        # 1. Identify Target Table
        table_matches = [m for m in matches if m.type == 'table']
        target_table = table_matches[0].table if table_matches else (matches[0].table if matches else None)
        if target_table:
            tables.add(target_table)

        # 2. Identify Columns for selection
        if table_matches and not agg:
            select_columns.append({"table": target_table, "column": "*"})
        
        for m in matches:
            if m.type == 'column' and m.table == target_table:
                if agg:
                    select_columns.append({"table": m.table, "column": m.column, "agg": agg})
                elif not any(sc.get('column') == '*' and sc.get('table') == m.table for sc in select_columns):
                    select_columns.append({"table": m.table, "column": m.column, "agg": None})

        if not select_columns and target_table:
            if agg == 'COUNT':
                select_columns.append({"table": target_table, "column": "*", "agg": agg})
            else:
                select_columns.append({"table": target_table, "column": "*"})

        # 3. Handle Dates
        date_res = DateResolver.resolve(question)
        if date_res:
            start_date, end_date, _ = date_res
            date_col = None
            for m in matches:
                col_low = m.column.lower() if m.column else ""
                if any(x in col_low for x in ['date', 'time', 'created', 'joined', 'payment', 'day', 'at', 'dob']):
                    date_col = m
                    break
            
            if date_col:
                if start_date == end_date:
                    filters.append(FilterCondition(table=date_col.table, column=date_col.column, operator="=", value=start_date))
                else:
                    filters.append(FilterCondition(table=date_col.table, column=date_col.column, operator="BETWEEN", value=[start_date, end_date]))
                tables.add(date_col.table)

        # 4. Handle Filters (Regex)
        col_matches = sorted([m for m in matches if m.type == 'column'], key=lambda x: x.score, reverse=True)
        should_check_filters = ml_plan.get('has_filter', False) or any(char.isdigit() for char in question) or any(x in q_low for x in ["boy", "girl", "male", "female"])
        
        if should_check_filters:
            # Map of (match_start, match_end) -> (FilterCondition, score)
            found_filters_by_range: Dict[Tuple[int, int], Tuple[FilterCondition, float]] = {}

            ops = {
                ">": r'(?:above|greater than|more than|>)\s*(\d+)',
                "<": r'(?:below|less than|under|<)\s*(\d+)',
                "=": r'(?:equal to|is|=)\s*(\d+)',
                "!=": r'(?:not equal to|not)\s*(\d+)'
            }

            for m in col_matches:
                token_idx = q_low.find(m.token.lower())
                if token_idx == -1: continue

                # Check Between
                between_match = re.search(r'between\s+(\d+)\s+and\s+(\d+)', q_low)
                if between_match and abs(token_idx - between_match.start()) < 30:
                    rng = (between_match.start(), between_match.end())
                    if rng not in found_filters_by_range:
                        cond = FilterCondition(table=m.table, column=m.column, operator="BETWEEN", value=[int(between_match.group(1)), int(between_match.group(2))])
                        found_filters_by_range[rng] = (cond, m.score)

                # Check Standard Ops
                for op, pattern in ops.items():
                    for val_match in re.finditer(pattern, q_low):
                        if abs(token_idx - val_match.start()) < 30:
                            rng = (val_match.start(), val_match.end())
                            current_best_data = found_filters_by_range.get(rng)
                            
                            is_better = False
                            if not current_best_data:
                                is_better = True
                            else:
                                current_best, current_score = current_best_data
                                if m.table == target_table and current_best.table != target_table:
                                    is_better = True
                                elif m.score > current_score and (m.table == target_table or current_best.table != target_table):
                                    is_better = True
                                    
                            if is_better:
                                cond = FilterCondition(table=m.table, column=m.column, operator=op, value=int(val_match.group(1)))
                                found_filters_by_range[rng] = (cond, m.score)

            # Fallback for single numbers without clear operators
            for val_match in re.finditer(r'(\d+)', q_low):
                rng = (val_match.start(), val_match.end())
                if not any(rng[0] >= r[0] and rng[1] <= r[1] for r in found_filters_by_range.keys()):
                    best_m = None
                    for m in col_matches:
                        token_idx = q_low.find(m.token.lower())
                        if token_idx != -1 and abs(token_idx - val_match.start()) < 30:
                            if not best_m or (m.table == target_table and best_m.table != target_table) or (m.score > best_m.score and (m.table == target_table or best_m.table != target_table)):
                                best_m = m
                    
                    if best_m:
                        pred_op = ml_plan.get('operator', '=')
                        cond = FilterCondition(table=best_m.table, column=best_m.column, operator=pred_op if pred_op != 'NONE' else '=', value=int(val_match.group(1)))
                        found_filters_by_range[rng] = (cond, best_m.score)

            # Categorical Filter Detection (Phase 6)
            for m in col_matches:
                token_l = m.token.lower()
                val = None
                if "girl" in token_l or "female" in token_l: val = "Female"
                elif "boy" in token_l or "male" in token_l: val = "Male"
                
                if val:
                    if not any(f.table == m.table and f.column == m.column for f, s in found_filters_by_range.values()):
                        filters.append(FilterCondition(table=m.table, column=m.column, operator="=", value=val))
                        tables.add(m.table)

            for cond, score in found_filters_by_range.values():
                filters.append(cond)
                tables.add(cond.table)

        # 5. Handle Sort & Limit
        sort = None
        if "highest" in q_low or "top" in q_low or "max" in q_low:
            num_cols = sorted([m for m in col_matches if m.table == target_table], key=lambda x: x.score, reverse=True)
            if num_cols:
                sort = {"table": num_cols[0].table, "column": num_cols[0].column, "direction": "DESC"}
        elif "lowest" in q_low or "bottom" in q_low or "min" in q_low:
            num_cols = sorted([m for m in col_matches if m.table == target_table], key=lambda x: x.score, reverse=True)
            if num_cols:
                sort = {"table": num_cols[0].table, "column": num_cols[0].column, "direction": "ASC"}

        if ml_plan.get('has_limit', False) or 'limit' in q_low or 'top' in q_low:
            limit_match = re.search(r'limit\s+(\d+)|top\s+(\d+)', q_low)
            if limit_match:
                limit = int(next(g for g in limit_match.groups() if g is not None))
            elif ml_plan.get('has_limit', False):
                limit = 10 

        # 6. Final Joins
        joins = self.graph.get_joins_for_tables(tables)
        join_conf = self.graph.calculate_join_confidence(tables, joins)
        
        plan = QueryPlan(
            select_columns=select_columns,
            tables=list(tables),
            joins=joins,
            filters=filters,
            sort=sort,
            limit=limit,
            confidence_score=0.0
        )
        
        plan.ml_metadata = {
            "prediction": prediction,
            "version": "3.1.6-fixed-struct",
            "join_confidence": join_conf,
            "planner_confidence": prediction.get('confidence', 0.5),
            "match_decisions": [
                {"token": m.token, "mapped_to": m.table if m.type == 'table' else f"{m.table}.{m.column}", "type": m.type}
                for m in matches if m.score > 85
            ]
        }
        
        return plan

    def _fallback_plan(self, matches, question):
        from .planner import QueryPlanner
        return QueryPlanner(self.graph).create_plan(matches, question)
