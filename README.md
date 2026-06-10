# NQL — Natural Query Language

**Ask questions in plain English. Get safe SQL and results.**

NQL (Natural Query Language) is a lightweight, offline-first Python framework that converts natural language into safe SQL queries. It powers ERP chatbots across PostgreSQL, MySQL, SQLite, MariaDB, and SQL Server using less than 300MB RAM.

## Features

- **Offline-First:** Runs entirely locally on CPU. No cloud dependencies or LLM APIs.
- **Low Resource:** Fits in <300MB RAM. Designed for Docker, VPS, and edge deployment.
- **Database Agnostic:** Connects to any standard SQL database via SQLAlchemy.
- **Enterprise Safe:** Built-in SQL Validator prevents injections (`DROP`, `DELETE`, etc.) and enforces schema integrity.
- **Multi-Turn Memory:** Drill down into results with follow-up questions contextually.
- **Smart Clarifications:** Detects ambiguous queries and offers interactive suggestions.
- **Plugins Ready:** Comes with stubs for `SchoolERP`, `HRMS`, `Inventory`, and `Hospital` systems.

## Installation

```bash
pip install nql
```

## Quick Start

```python
from nql import ERPBot

bot = ERPBot(
    connection_url="sqlite:///school.db"
)

# Standard Query
response = bot.ask("show students with pending fees")
print(response.sql)
print(response.rows)

# SQL Export Mode (Only returns SQL, does not execute)
response = bot.ask("total fees collected this year", execute=False)
print(response.sql)

# Explain Mode (See exactly why decisions were made)
response = bot.ask("top 10 students", explain=True)
print(response.explanation)
```

## Advanced Configuration

NQL provides a robust configuration object to fine-tune its behavior for your production environment:

```python
from nql import ERPBot, Config

config = Config(
    default_limit=100,      # Automatic cost protection limit
    query_timeout=5,        # Maximum execution time (seconds)
    confidence_auto=0.85,   # Auto-execute threshold
    confidence_confirm=0.65,# Requires confirmation threshold
    enable_cache=True       # Schema hashing and caching
)

bot = ERPBot(connection_url="postgresql://user:pass@localhost/db", config=config)
```

## FastAPI Integration

Easily embed NQL into your web services:

```python
from fastapi import FastAPI
from nql import ERPBot
from nql.integrations import get_nql_router

app = FastAPI()
bot = ERPBot(connection_url="sqlite:///test.db")

app.include_router(get_nql_router(bot))
```
