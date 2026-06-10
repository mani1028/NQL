<div align="center">
  
# 🧠 NQL (Natural Query Language)

**Ask questions in plain English. Get safe SQL and results.**

[![PyPI version](https://badge.fury.io/py/nql.svg)](https://badge.fury.io/py/nql)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

NQL is a lightweight, offline-first Python framework that converts natural language into safe, deterministic SQL queries. It empowers developers to build intelligent ERP chatbots and analytics interfaces across PostgreSQL, MySQL, SQLite, MariaDB, and SQL Server using **less than 300MB of RAM**.

Unlike LLM-based SQL generators that hallucinate or require expensive cloud APIs, NQL relies on a strict separation of concerns: an optimized ML intent planner combined with a deterministic, rule-based SQL builder and a robust security validator.

## ✨ Key Features

- **🔒 Offline & Private:** Runs entirely locally on your CPU. No data ever leaves your servers. No cloud dependencies or API keys required.
- **⚡ Ultra-Lightweight:** Fits comfortably in <300MB RAM. Designed for Docker, VPS, and edge deployments (including Raspberry Pi).
- **🛡️ Enterprise Safe:** A built-in SQL Validator actively prevents SQL injections (blocking `DROP`, `DELETE`, `UPDATE`, etc.) and enforces strict schema integrity before execution.
- **🧠 Multi-Turn Memory:** Drill down into your data conversationally. NQL remembers context, allowing follow-up questions like *"show students"* ➔ *"only girls"* ➔ *"highest marks"*.
- **🤝 Smart Clarifications:** When ambiguity arises, NQL doesn't guess. It returns structured clarification options for your frontend to display (e.g., *"Did you mean students or employees?"*).
- **🔌 Plug-and-Play ERP Support:** Comes with pre-built domain plugins for `SchoolERP`, `HRMS`, `Inventory`, and `Hospital` systems to instantly understand industry-specific synonyms.
- **🗄️ Database Agnostic:** Built on top of SQLAlchemy. If SQLAlchemy supports it, NQL can query it.

---

## 📦 Installation

Install NQL directly from PyPI:

```bash
pip install nql
```

*Note: Python 3.11 or higher is required.*

---

## 🚀 Quick Start

Connect NQL to your database and start asking questions in three lines of code.

```python
from nql import ERPBot

# 1. Initialize the bot with your database connection string
bot = ERPBot(connection_url="sqlite:///my_database.db")

# 2. Ask a question in plain English
response = bot.ask("show students with pending fees")

# 3. Access the results
print(response.sql)   # SELECT students.* FROM students JOIN fees ON ...
print(response.rows)  # [{'id': 1, 'name': 'Alice', 'status': 'pending'}, ...]
```

### 🛠 Execution Modes

NQL supports flexible execution modes for different architectural needs:

**SQL Export Mode:** Need the SQL but want to execute it yourself?
```python
response = bot.ask("total fees collected this year", execute=False)
print(response.sql) # Generates SQL but does not hit the database
```

**Explain Mode:** Want to understand exactly how NQL interpreted the query?
```python
response = bot.ask("top 10 students", explain=True)
print(response.explanation) 
# Outputs: "I am looking for students. (Matched: 'students' → students) I've limited the results to the first 10 records."
```

---

## ⚙️ Advanced Configuration

NQL provides a robust `Config` object to fine-tune its behavior, set guardrails, and manage performance in production environments.

```python
from nql import ERPBot, Config

config = Config(
    default_limit=100,         # Automatic cost protection: Append LIMIT 100 if none specified
    max_rows_per_query=1000,   # Hard cap on in-memory row retrieval
    query_timeout=5,           # Maximum execution time in seconds
    confidence_auto=0.85,      # Threshold to automatically execute the query
    confidence_confirm=0.65,   # Threshold to request user confirmation
    enable_cache=True,         # Enable schema hashing and metadata caching for fast startup
    enable_profiler=False      # (Optional) Profile data for advanced categorical matching
)

bot = ERPBot(connection_url="postgresql://user:pass@localhost:5432/erp_db", config=config)
```

---

## 🌐 FastAPI Integration

Building a web service? NQL includes a ready-to-use FastAPI router.

```python
from fastapi import FastAPI
from nql import ERPBot
from nql.integrations import get_nql_router

app = FastAPI()
bot = ERPBot(connection_url="postgresql://user:pass@localhost/db")

# Mounts /nql/chat and /nql/schema endpoints automatically
app.include_router(get_nql_router(bot))
```

### API Endpoints Provided:
- `POST /nql/chat`: Accepts `{"question": "...", "session_id": "user_1"}` and returns a `ChatResponse` JSON.
- `GET /nql/schema`: Returns a health report of the connected database (table count, aliases generated, status).

---

## 🧩 Plugin System

Improve NQL's understanding of your specific domain instantly by using official plugins. Plugins inject domain-specific synonyms and N-Grams into the semantic matcher.

```python
from nql.plugins import SchoolERPPlugin
from nql.enterprise.plugins import registry

# Register the plugin globally before initializing the bot
registry.register_matcher(SchoolERPPlugin())

# Now NQL understands that "pupil" means "student" and "dues" means "fee"
```

---

## 🏗 Architecture Overview

NQL achieves high accuracy and zero hallucinations through a deterministic pipeline:

1. **Schema Scanner & Cacher:** Introspects the database, generates aliases (e.g., `payment_status` ➔ `payment status`), and caches a SHA-256 hash for fast subsequent startups.
2. **Semantic Matcher:** Uses N-Gram and Fuzzy matching to link English words to exact schema entities (Tables/Columns).
3. **ML Intent Planner:** A quantized MiniLM model predicts the *structural intent* (e.g., `SELECT`, `COUNT`, filters, sort) without generating raw SQL.
4. **Relationship Graph:** Dijkstra's shortest path algorithm automatically discovers the most logical `JOIN` paths between required tables.
5. **Deterministic Builder:** Assembles the final SQL string using rule-based logic.
6. **Security Validator:** Scans the final query for dangerous operations and schema mismatches before execution.

---

## 🤝 Contributing

We welcome contributions! Whether it's adding new ERP plugins, improving the ML planner, or expanding database dialect support, your help makes NQL better.

1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

Please ensure all tests pass (`pytest`) before submitting a PR.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
