import json
import random
import os

class DatasetGenerator:
    def __init__(self):
        self.domains = {
            "Education": {
                "entities": ["students", "courses", "grades", "teachers", "classrooms"],
                "columns": ["id", "name", "marks", "title", "subject", "salary", "room_number"],
                "actions": ["show", "find", "count", "list", "who"],
            },
            "HR": {
                "entities": ["employees", "departments", "salaries", "roles", "leave_requests"],
                "columns": ["id", "full_name", "department", "salary_amount", "position", "join_date"],
                "actions": ["get", "list", "find", "show", "search"],
            },
            "CRM": {
                "entities": ["customers", "orders", "leads", "contacts", "tickets"],
                "columns": ["id", "company", "status", "value", "created_at", "email"],
                "actions": ["retrieve", "show", "get", "find", "filter"],
            },
            "Inventory": {
                "entities": ["products", "categories", "stock", "suppliers", "warehouses"],
                "columns": ["id", "sku", "quantity", "price", "location", "vendor"],
                "actions": ["check", "list", "search", "find", "show"],
            },
            "Finance": {
                "entities": ["transactions", "accounts", "balances", "invoices", "payments"],
                "columns": ["id", "amount", "type", "date", "status", "currency"],
                "actions": ["get", "show", "list", "summarize", "find"],
            }
        }

    def _generate_filter(self, domain_name):
        col = random.choice(self.domains[domain_name]["columns"])
        ops = [">", "<", "=", "!=", "LIKE"]
        op = random.choice(ops)
        val = random.randint(1, 1000) if op in [">", "<"] else f"value_{random.randint(1, 10)}"
        return {"column": col, "operator": op, "value": val}

    def generate_sample(self):
        domain_name = random.choice(list(self.domains.keys()))
        domain = self.domains[domain_name]
        
        action = random.choice(domain["actions"])
        entity = random.choice(domain["entities"])
        
        # Build query string
        templates = [
            f"{action} {entity}",
            f"{action} all {entity}",
            f"can you {action} the {entity}",
            f"please {action} {entity} for me",
            f"i want to {action} {entity}"
        ]
        query = random.choice(templates)
        
        filters = []
        if random.random() > 0.5:
            f = self._generate_filter(domain_name)
            filters.append(f)
            query += f" where {f['column']} {f['operator']} {f['value']}"

        sort = {}
        if random.random() > 0.7:
            sort_col = random.choice(domain["columns"])
            direction = random.choice(["ASC", "DESC"])
            sort = {"column": sort_col, "direction": direction}
            query += f" sorted by {sort_col} {direction}"

        limit = 0
        if random.random() > 0.8:
            limit = random.randint(1, 100)
            query += f" limit to {limit}"

        plan = {
            "action": action.upper(),
            "entity": entity,
            "filters": filters,
            "sort": sort,
            "group_by": [],
            "limit": limit
        }
        
        return {"query": query, "plan": plan, "domain": domain_name}

    def generate_dataset(self, size=10000, output_path="nql/ml/data/dataset.json"):
        dataset = []
        for _ in range(size):
            dataset.append(self.generate_sample())
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(dataset, f, indent=2)
        print(f"Generated {size} samples at {output_path}")

if __name__ == "__main__":
    gen = DatasetGenerator()
    gen.generate_dataset(10000)
