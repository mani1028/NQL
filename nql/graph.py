from .models import DatabaseSchema
from typing import List, Dict, Set, Optional, Tuple, Any

class RelationshipGraph:
    def __init__(self, schema: DatabaseSchema):
        self.schema = schema
        self.adj = self._build_adjacency_list()

    def _build_adjacency_list(self):
        adj = {}
        for table in self.schema.tables:
            if table.name not in adj:
                adj[table.name] = []
            for col in table.columns:
                if col.foreign_key:
                    ref_table, ref_col = col.foreign_key.split('.')
                    
                    # Edge: table -> ref_table
                    adj[table.name].append({
                        "to": ref_table,
                        "from_table": table.name,
                        "from_col": col.name,
                        "to_col": ref_col,
                        "weight": 1.0 # direct FK
                    })
                    
                    # Edge: ref_table -> table
                    if ref_table not in adj:
                        adj[ref_table] = []
                    adj[ref_table].append({
                        "to": table.name,
                        "from_table": ref_table,
                        "from_col": ref_col,
                        "to_col": col.name,
                        "weight": 1.0 # direct FK reverse
                    })
        return adj

    def find_path(self, start_table: str, end_table: str) -> Optional[List[Dict]]:
        if start_table == end_table:
            return []
            
        import heapq
        
        # Dijkstra's shortest path
        pq = [(0.0, start_table, [])]
        visited = set()
        
        while pq:
            cost, current, path = heapq.heappop(pq)
            
            if current == end_table:
                return path
                
            if current in visited:
                continue
            visited.add(current)
            
            for edge in self.adj.get(current, []):
                if edge['to'] not in visited:
                    new_path = path + [edge]
                    heapq.heappush(pq, (cost + edge.get('weight', 1.0), edge['to'], new_path))
                    
        return None

    def get_joins_for_tables(self, tables: Set[str]) -> List[Dict[str, Any]]:
        if len(tables) <= 1:
            return []
            
        table_list = list(tables)
        root = table_list[0]
        joins = []
        visited = {root}
        to_visit = set(table_list[1:])
        
        while to_visit:
            best_path = None
            best_target = None
            
            for start in visited:
                for target in to_visit:
                    path = self.find_path(start, target)
                    if path is not None:
                        if not best_path or len(path) < len(best_path):
                            best_path = path
                            best_target = target
                            
            if best_path is not None:
                for edge in best_path:
                    joins.append({
                        "left": f"{edge['from_table']}.{edge['from_col']}",
                        "right": f"{edge['to']}.{edge['to_col']}"
                    })
                    visited.add(edge['to'])
                to_visit.remove(best_target)
            else:
                break
                
        # Deduplicate joins
        unique_joins = []
        seen = set()
        for j in joins:
            key = tuple(sorted([j['left'], j['right']]))
            if key not in seen:
                seen.add(key)
                unique_joins.append(j)
                
        return unique_joins

    def calculate_join_confidence(self, tables: Set[str], joins: List[Dict[str, Any]]) -> float:
        if len(tables) <= 1:
            return 1.0
            
        # Count connected tables in joins
        connected = set()
        for j in joins:
            connected.add(j['left'].split('.')[0])
            connected.add(j['right'].split('.')[0])
            
        if len(connected.intersection(tables)) < len(tables):
            return 0.0 # Some requested tables are disconnected
            
        # Penalty for intermediate tables
        total_edges = len(joins)
        min_edges = len(tables) - 1
        if total_edges > min_edges:
            return max(0.0, 1.0 - 0.1 * (total_edges - min_edges))
            
        return 1.0
