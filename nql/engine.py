from .scanner import SchemaScanner
from .matcher import SemanticMatcher
from .graph import RelationshipGraph
from .ml_planner import MLPlanner
from .builder import SQLBuilder
from .executor import QueryExecutor
from .models import ChatResponse, DatabaseSchema
from .enterprise.memory import SessionManager
from .enterprise.explanation import QueryExplainer
from .enterprise.monitoring import ProductionMonitor
from .enterprise.plugins import registry
from .confidence import ConfidenceEngine
from .validator import SQLValidator
from .schema_cache import SchemaCache
from .config import Config
from typing import Optional, Dict, Any, Union
import uuid
import json
import os
import datetime

monitor = ProductionMonitor()

class QueryLogger:
    def __init__(self, log_path: str = "query_logs.jsonl"):
        self.log_path = log_path

    def log(self, question: str, response: Any):
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "question": question,
            "sql": response.sql,
            "confidence": response.confidence,
            "has_error": response.error is not None,
            "session_id": response.session_id
        }
        # Only log if path exists
        if self.log_path:
            try:
                with open(self.log_path, 'a') as f:
                    f.write(json.dumps(entry) + "\n")
            except Exception as e:
                print(f"Warning: Could not write to log file: {e}")

class ERPBot:
    def __init__(self, connection_url: str, config: Optional[Config] = None):
        self.connection_url = connection_url
        self.config = config or Config()
        
        self.scanner = SchemaScanner(connection_url)
        self.cache = SchemaCache(self.config.cache_path)
        self.logger = QueryLogger(self.config.log_path)
        
        # Load from cache if valid, otherwise scan
        current_hash = self.scanner.get_schema_hash()
        cached_schema = self.cache.load(current_hash) if self.config.enable_cache else None
        
        if cached_schema:
            self.schema = cached_schema
        else:
            self.schema = self.scanner.scan()
            if self.config.enable_cache:
                self.cache.save(self.schema, current_hash)
        
        # Profiler is optional
        self.data_profile = {}
        if self.config.enable_profiler:
            try:
                from .profiler import DataProfiler
                self.profiler = DataProfiler(connection_url)
                self.data_profile = self.profiler.profile([t.name for t in self.schema.tables])
            except Exception as e:
                print(f"Warning: Could not run profiler: {e}")
        
        self.graph = RelationshipGraph(self.schema)
        self.matcher = SemanticMatcher(self.schema, data_profile=self.data_profile)
        self.planner = MLPlanner(self.graph)
        self.builder = SQLBuilder()
        self.executor = QueryExecutor(connection_url, max_rows=self.config.max_rows_per_query)
        self.validator = SQLValidator(self.schema)
        
        # Enterprise Modules
        self.memory = SessionManager(max_history=self.config.max_session_history)
        self.explainer = QueryExplainer()

    def get_schema_report(self) -> Dict[str, Any]:
        """Generates a health report of the connected database schema."""
        table_count = len(self.schema.tables)
        column_count = sum(len(t.columns) for t in self.schema.tables)
        fk_count = sum(1 for t in self.schema.tables for c in t.columns if c.foreign_key)
        alias_count = sum(len(t.aliases) for t in self.schema.tables) + \
                      sum(len(c.aliases) for t in self.schema.tables for c in t.columns)
        
        return {
            "tables": table_count,
            "columns": column_count,
            "foreign_keys": fk_count,
            "aliases_generated": alias_count,
            "status": "Healthy" if table_count > 0 else "No tables found"
        }

    @monitor.track_performance()
    def ask(self, question: str, session_id: Optional[str] = None, execute: bool = True, explain: bool = False) -> ChatResponse:
        if not session_id:
            session_id = str(uuid.uuid4())
            
        if question.lower().strip() in ["reset", "forget", "clear"]:
            self.memory.clear_session(session_id)
            return ChatResponse(
                sql="",
                rows=[],
                confidence=1.0,
                columns=[],
                explanation="I have cleared our conversation history. How can I help you starting fresh?",
                session_id=session_id
            )
            
        try:
            for m_plugin in registry.matchers:
                question = m_plugin(question)

            matches = self.matcher.match(question)
            
            if not matches and not self.memory.get_last_plan(session_id):
                resp = ChatResponse(
                    sql="", rows=[], confidence=0.0, columns=[],
                    error="I couldn't find any relevant tables or columns.",
                    session_id=session_id
                )
                self.logger.log(question, resp)
                return resp
            
            plan = self.planner.create_plan(matches, question)
            
            # Confidence Engine
            matcher_score = sum(m.score for m in matches) / len(matches) if matches else 0.0
            ml_meta = getattr(plan, 'ml_metadata', {})
            planner_conf = ml_meta.get('planner_confidence', 0.5)
            join_conf = ml_meta.get('join_confidence', 1.0)
            
            confidence = ConfidenceEngine.calculate(matcher_score, planner_conf, join_conf)
            plan.confidence_score = confidence
            
            # Tiered Confidence Logic
            if confidence < self.config.confidence_confirm and not self.memory.get_last_plan(session_id):
                # Clarify (Low confidence)
                options = []
                if matches:
                    seen = set()
                    for m in matches[:5]:
                        name = m.table if m.type == 'table' else f"{m.table}.{m.column}"
                        if name not in seen:
                            options.append(name)
                            seen.add(name)
                
                resp = ChatResponse(
                    sql="", rows=[], confidence=confidence, columns=[],
                    error="I'm not quite sure what you mean.",
                    clarification={
                        "question": "Which data would you like to see?",
                        "options": options,
                        "type": "clarification" if confidence < self.config.confidence_clarify else "confirmation"
                    },
                    session_id=session_id
                )
                self.logger.log(question, resp)
                return resp

            plan = self.memory.merge_context(session_id, plan)
            
            # Global Cost Protection: Apply default limit if none specified
            if not plan.limit:
                plan.limit = self.config.default_limit
            
            self.memory.add_plan(session_id, plan)
            
            sql = self.builder.build(plan)
            
            # Validator
            val_errors = self.validator.validate(sql, plan)
            val_errors.extend(registry.run_validators(sql, plan) or [])
            if val_errors:
                resp = ChatResponse(
                    sql=sql, rows=[], confidence=0.0, columns=[],
                    error="; ".join(val_errors),
                    session_id=session_id
                )
                self.logger.log(question, resp)
                return resp
            
            rows, columns = [], []
            if execute:
                rows, columns = self.executor.execute(sql, timeout=self.config.query_timeout)
                
            explanation_text = None
            if explain:
                explanation_text = self.explainer.explain(plan)
            
            resp = ChatResponse(
                sql=sql,
                rows=rows,
                confidence=round(confidence, 2),
                columns=columns,
                ml_metadata=ml_meta,
                explanation=explanation_text,
                session_id=session_id
            )
            self.logger.log(question, resp)
            return resp
        except Exception as e:
            resp = ChatResponse(
                sql="", rows=[], confidence=0.0, columns=[], error=str(e)
            )
            self.logger.log(question, resp)
            return resp

    def refresh_schema(self):
        self.schema = self.scanner.scan()
        current_hash = self.scanner.get_schema_hash()
        self.cache.save(self.schema, current_hash)
        
        if self.config.enable_profiler:
            try:
                from .profiler import DataProfiler
                profiler = DataProfiler(self.connection_url)
                self.data_profile = profiler.profile([t.name for t in self.schema.tables])
            except Exception:
                self.data_profile = {}
        
        self.graph = RelationshipGraph(self.schema)
        self.matcher = SemanticMatcher(self.schema, data_profile=self.data_profile)
        self.planner = MLPlanner(self.graph)

