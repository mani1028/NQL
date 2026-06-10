# nql Enterprise Platform (v3.0)

Welcome to the commercial-grade enterprise edition of **nql**. This version extends the core offline NL-to-SQL engine into a fully-featured data platform.

## Enterprise Features

### 1. Contextual Chat Memory
The engine now maintains conversation state. You can ask follow-up questions without repeating the subject.
- *User*: "Show all students."
- *User*: "Only those with marks above 80."
- *Engine*: Automatically merges filters and maintains the table context.

### 2. Semantic Query Explanation
Every generated SQL query is accompanied by a natural language explanation, allowing non-technical stakeholders to verify the logic.

### 3. Smart Join Planner
V3 uses semantic similarity and naming conventions (e.g., `user_id` -> `id`) to automatically proposal JOIN paths between tables even when explicit foreign keys are missing.

### 4. Learning Engine & Feedback Loop
Users can provide thumbs-up/down feedback or submit corrections. This data is stored in `nql/ml/data/feedback_v3.jsonl` and can be used to retrain the MiniLM model for domain-specific accuracy.

### 5. Production Monitoring
Built-in telemetry tracks planning latency, execution time, and success rates. Logs are available for auditing and performance tuning.

### 6. Developer Plugin Architecture
Extend the engine with custom logic:
- `register_matcher`: Custom token mapping.
- `register_validator`: Custom SQL safety checks.
- `register_planner_hook`: Modify plans before execution.

## Deployment

### Packaging
Build the production-ready wheel:
```bash
python setup.py sdist bdist_wheel
```

### CI/CD
A GitHub Action is included in `.github/workflows/main.yml` that handles:
- Multi-version Python testing.
- Syntax linting.
- Package building.

## Advanced Usage

```python
from nql import ChatSQL
from nql.enterprise.plugins import registry

# Register a custom validator
@registry.register_validator
def limit_max_rows(sql, plan):
    if "LIMIT" not in sql:
        return "All enterprise queries must have a LIMIT clause for safety."
    return None

bot = ChatSQL("sqlite:///enterprise.db")
response = bot.ask("Show top sales", session_id="user_123")
```

---
© 2026 nql Enterprise
