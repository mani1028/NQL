from nql.matcher import SemanticMatcher
from nql.models import DatabaseSchema, TableSchema, ColumnSchema

schema = DatabaseSchema(tables=[
    TableSchema(name="students", columns=[
        ColumnSchema(name="id", type="INTEGER", primary_key=True),
        ColumnSchema(name="name", type="VARCHAR"),
        ColumnSchema(name="gender", type="VARCHAR", aliases=["sex", "boy", "girl", "male", "female"])
    ], aliases=["students", "pupil"])
])

matcher = SemanticMatcher(schema)
print("Elements in matcher:")
for el in matcher.elements:
    print(f"  {el['name']} ({el['type']})")

question = "only girls"
matches = matcher.match(question)
print(f"\nMatches for '{question}':")
for m in matches:
    print(f"  {m.token} -> {m.table}.{m.column} ({m.score})")
