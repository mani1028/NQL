import json
import os
import argparse

def convert_spider(spider_path, tables_path):
    with open(spider_path, 'r') as f:
        data = json.load(f)
    with open(tables_path, 'r') as f:
        tables_data = json.load(f)
    
    # Map db_id to table and column names
    db_schema = {}
    for db in tables_data:
        db_schema[db['db_id']] = {
            "tables": [t.lower() for t in db['table_names_original']],
            "columns": [[c[0], c[1].lower()] for c in db['column_names_original']]
        }
    
    converted = []
    for item in data:
        db_id = item['db_id']
        schema = db_schema.get(db_id)
        if not schema: continue
        
        table_names = schema['tables']
        col_names = schema['columns']
        
        sql = item['sql']
        # Simplified: get first table
        table_idx = -1
        if sql['from']['table_units']:
            first_unit = sql['from']['table_units'][0]
            if len(first_unit) > 1 and isinstance(first_unit[1], int):
                table_idx = first_unit[1]
        
        if table_idx < 0 or table_idx >= len(table_names):
            continue
            
        entity = table_names[table_idx]
        
        # Determine action
        action = "FIND"
        if sql['select'] and len(sql['select']) > 1 and sql['select'][1]:
            first_sel = sql['select'][1][0]
            if isinstance(first_sel, (list, tuple)) and len(first_sel) > 0:
                agg_id = first_sel[0]
                agg_map = {3: "COUNT", 4: "AVERAGE", 1: "MAX", 2: "MIN", 5: "SUM"}
                action = agg_map.get(agg_id, "FIND")

        # Extract real filters if possible
        filters = []
        if sql['where']:
            for cond in sql['where']:
                if isinstance(cond, (list, tuple)) and len(cond) >= 3:
                    # cond structure: [not_op, op_id, val_unit, val1, val2]
                    op_id = cond[1]
                    op_map = {2: "=", 3: ">", 4: "<", 5: ">=", 6: "<=", 1: "!=", 9: "LIKE", 8: "BETWEEN"}
                    operator = op_map.get(op_id, "=")
                    
                    val_unit = cond[2] # [unit_op, [agg_id, col_id, is_distinct], null]
                    col_info = val_unit[1]
                    column_name = "unknown"
                    if isinstance(col_info, (list, tuple)) and len(col_info) > 1:
                        col_id = col_info[1]
                        if isinstance(col_id, int) and 0 <= col_id < len(col_names):
                            column_name = col_names[col_id][1]
                    
                    filters.append({
                        "column": column_name,
                        "operator": operator
                    })

        plan = {
            "action": action,
            "entity": entity,
            "filters": filters,
            "sort": {"column": "unknown"} if sql['orderBy'] else {},
            "group_by": [],
            "limit": 1 if sql['limit'] else 0
        }
        
        converted.append({
            "query": item['question'],
            "plan": plan,
            "domain": f"Spider_{db_id}"
        })
    return converted

def convert_wikisql(wikisql_path):
    converted = []
    # WikiSQL usually comes in jsonl, but some versions are json
    try:
        with open(wikisql_path, 'r', encoding='utf-8') as f:
            # Detect if it's jsonl
            first_line = f.readline()
            f.seek(0)
            if first_line.strip().startswith('{') and not first_line.strip().startswith('['):
                # JSONL
                for line in f:
                    try:
                        item = json.loads(line)
                        action = "FIND"
                        agg_map = {1: "COUNT", 2: "MIN", 3: "MAX", 4: "AVERAGE", 5: "SUM"}
                        action = agg_map.get(item['sql']['agg'], "FIND")
                        
                        filters = []
                        for cond in item['sql']['conds']:
                            # [col_index, op_index, value]
                            op_map = {0: "=", 1: ">", 2: "<", 3: "OP_UNKNOWN"}
                            filters.append({"column": str(cond[0]), "operator": op_map.get(cond[1], "=")})

                        plan = {
                            "action": action,
                            "entity": item['table_id'],
                            "filters": filters,
                            "sort": {},
                            "group_by": [],
                            "limit": 0
                        }
                        converted.append({
                            "query": item['question'],
                            "plan": plan,
                            "domain": "WikiSQL"
                        })
                    except: continue
            else:
                # Standard JSON
                data = json.load(f)
                for item in data:
                    action = "FIND"
                    agg_map = {1: "COUNT", 2: "MIN", 3: "MAX", 4: "AVERAGE", 5: "SUM"}
                    action = agg_map.get(item['sql']['agg'], "FIND")
                    filters = []
                    for cond in item['sql']['conds']:
                        op_map = {0: "=", 1: ">", 2: "<"}
                        filters.append({"column": str(cond[0]), "operator": op_map.get(cond[1], "=")})
                    
                    converted.append({
                        "query": item['question'],
                        "plan": {
                            "action": action,
                            "entity": item.get('table_id', 'unknown'),
                            "filters": filters,
                            "sort": {},
                            "group_by": [],
                            "limit": 0
                        },
                        "domain": "WikiSQL"
                    })
    except: pass
    return converted

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spider-train", default="/Users/visys/Downloads/spider/train_spider.json")
    parser.add_argument("--spider-tables", default="/Users/visys/Downloads/spider/tables.json")
    parser.add_argument("--wikisql-train", default="/Users/visys/Downloads/wiki/wikisql_train.json")
    parser.add_argument("--output", default="nql/ml/data/extended_dataset.json")
    args = parser.parse_args()
    
    all_data = []
    
    if os.path.exists(args.spider_train):
        print(f"Converting Spider from {args.spider_train}...")
        all_data.extend(convert_spider(args.spider_train, args.spider_tables))
    
    if os.path.exists(args.wikisql_train):
        print(f"Converting WikiSQL from {args.wikisql_train}...")
        all_data.extend(convert_wikisql(args.wikisql_train))
    
    # Mix with current dataset if exists
    if os.path.exists("nql/ml/data/dataset.json"):
        print("Mixing with existing synthetic data...")
        with open("nql/ml/data/dataset.json", 'r') as f:
            all_data.extend(json.load(f))
            
    with open(args.output, 'w') as f:
        json.dump(all_data, f, indent=2)
    print(f"Total samples: {len(all_data)}")
    print(f"Saved to {args.output}")

if __name__ == "__main__":
    main()
