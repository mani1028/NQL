from .models import QueryPlan
from typing import List

class SQLBuilder:
    def build(self, plan: QueryPlan) -> str:
        if not plan.tables:
            return ""

        # SELECT
        select_clause = "SELECT "
        if not plan.select_columns:
            select_clause += "*"
        else:
            cols = []
            for sc in plan.select_columns:
                table = sc.get('table')
                column = sc.get('column')
                agg = sc.get('agg')
                
                if column == "*":
                    if agg:
                        # Fix COUNT(table.*) -> COUNT(*)
                        col_str = f"{agg}(*)"
                    else:
                        col_str = f"{table}.*"
                else:
                    col_str = f"{table}.{column}"
                    if agg:
                        col_str = f"{agg}({col_str})"
                
                if col_str not in cols:
                    cols.append(col_str)
            
            select_clause += ", ".join(cols)

        # FROM
        from_clause = f" FROM {plan.tables[0]}"
        
        # JOINs
        join_clause = ""
        for join in plan.joins:
            right_table = join['right'].split('.')[0]
            if right_table not in from_clause and right_table not in join_clause:
                join_clause += f" JOIN {right_table} ON {join['left']} = {join['right']}"

        # WHERE
        where_clause = ""
        if plan.filters:
            conds = []
            for f in plan.filters:
                if f.operator.upper() == "BETWEEN" and isinstance(f.value, list) and len(f.value) == 2:
                    val1 = f"'{f.value[0]}'" if isinstance(f.value[0], str) and not str(f.value[0]).isdigit() else f.value[0]
                    val2 = f"'{f.value[1]}'" if isinstance(f.value[1], str) and not str(f.value[1]).isdigit() else f.value[1]
                    conds.append(f"{f.table}.{f.column} BETWEEN {val1} AND {val2}")
                else:
                    val = f.value
                    if isinstance(val, str) and not str(val).isdigit():
                        val = f"'{val}'"
                    conds.append(f"{f.table}.{f.column} {f.operator} {val}")
            where_clause = " WHERE " + " AND ".join(conds)

        # GROUP BY
        group_by_clause = ""
        aggs = [sc for sc in plan.select_columns if sc.get('agg')]
        non_aggs = [sc for sc in plan.select_columns if not sc.get('agg')]
        if aggs and non_aggs:
            group_cols = [f"{sc.get('table')}.{sc.get('column')}" for sc in non_aggs if sc.get('column') != '*']
            if group_cols:
                group_by_clause = " GROUP BY " + ", ".join(group_cols)

        # ORDER BY
        order_by_clause = ""
        if plan.sort:
            order_by_clause = f" ORDER BY {plan.sort['table']}.{plan.sort['column']} {plan.sort['direction']}"

        # LIMIT
        if plan.limit:
            limit_clause = f" LIMIT {plan.limit}"
        else:
            limit_clause = " LIMIT 100" # Default protection

        return f"{select_clause}{from_clause}{join_clause}{where_clause}{group_by_clause}{order_by_clause}{limit_clause}"
