# Project Overview: NQL (Natural Query Language)

This document provides essential context for agents and developers working on the `NQL` project.

## Core Mission
`NQL` aims to provide a lightweight, high-performance, and privacy-focused Natural Language to SQL engine that runs entirely offline.

**"Ask questions in plain English. Get safe SQL and results."**

### Performance Targets
- **Model Size:** 20–40 MB (Quantized)
- **RAM Footprint:** 150–300 MB
- **Inference Latency:** <100ms on standard CPUs (P50 goal)
- **Environment:** Low-resource compatible (VPS, Docker, Raspberry Pi)

## Architectural Philosophy: "ML for Intent, Code for SQL"
To ensure 100% reliability and zero hallucinations, the project follows a strict separation of concerns:
1.  **Semantic Matcher (Enhanced):** Uses Alias Mapping, N-Gram matching, and optional Data Profiling to link user terms to schema entities. No embeddings or Vector DBs.
2.  **ML Intent Planner (Decoupled):** Understands *intent* (Action, presence of Filters/Sort/Limit). Predicted via a quantized MiniLM multi-task encoder.
3.  **Deterministic Builder:** A rule-based engine that assembles the final SQL string.
4.  **SQL Validator (Safety Net):** A final security layer that blocks dangerous keywords and validates schema references before execution.

## System Architecture

### 1. Backend Components (`nql/`)
- **Engine (`engine.py`):** Exposes `ERPBot`, the main entry point. Orchestrates the flow. Includes a **Clarification Engine** for low-confidence queries.
- **Scanner (`scanner.py`):** Introspects database schemas, calculates a schema hash, and automatically generates aliases/synonyms.
- **Graph (`graph.py`):** Maintains a relationship graph and uses Dijkstra's algorithm for shortest-path Join Discovery.
- **Matcher (`matcher.py`):** Performs multi-word (N-Gram) semantic matching with fuzzy fallback.
- **Planner (`ml_planner.py` / `planner.py`):** Combines ML intents with matcher entities. Handles regex-based filters, date resolution, and categorical filters.
- **Validator (`validator.py`):** Ensures generated SQL is safe and valid.
- **Confidence Engine (`confidence.py`):** Calculates unified scores using a 0.5/0.3/0.2 weighted formula.
- **Executor (`executor.py`):** Safely executes SQL via SQLAlchemy, enforcing limits and timeouts.
- **Memory (`enterprise/memory.py`):** Manages multi-turn conversations and inherited context.

### 2. ML Stack (`nql/ml/`)
- **Model (v3.1.0):** Based on `all-MiniLM-L6-v2`. Intent-only encoder.
- **Optimization:** Quantized to `qint8` and traced via TorchScript.

## Development Workflows

### Environment Setup
- Python: `pip install -e .`
- JS: `cd frontend && npm install`

### Training & Benchmarking
- **Retrain:** `python -m nql.ml.train`
- **Benchmark:** `python benchmark.py` (Crucial for validating accuracy and latency claims)

### Running Tests
```bash
pytest
```

## Roadmap & Priorities

1.  **Phase 4: Rigorous Benchmarking:** Expand the dataset of 500+ queries in `benchmarks/` to measure SQL correctness, result accuracy, and P95 latency.
2.  **Phase 5: ERP Validation:** Test specifically against complex ERP schemas via plugins (`SchoolERP`, `HRMS`, `Inventory`).
3.  **Phase 6: Advanced Clarification:** Refine interactive ambiguity-resolution workflows in the frontend based on the API's structured output.

## Conventions
- **Naming:** Follow PEP 8 for Python. Use `nql` for package naming.
- **Safety:** Never execute raw SQL without passing through the `Executor`, `Scanner`, and `Validator` layers.
- **Simplicity:** Prefer deterministic code over ML for logic. Keep RAM < 300MB. DO NOT introduce heavy agent workflows or LLM SQL generation.
