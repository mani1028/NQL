from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional

class ColumnSchema(BaseModel):
    name: str
    type: str
    primary_key: bool = False
    foreign_key: Optional[str] = None
    aliases: List[str] = []

class TableSchema(BaseModel):
    name: str
    columns: List[ColumnSchema]
    aliases: List[str] = []

class DatabaseSchema(BaseModel):
    tables: List[TableSchema]

class MatchResult(BaseModel):
    token: str
    table: Optional[str] = None
    column: Optional[str] = None
    score: float
    type: str  # 'table' or 'column'

class FilterCondition(BaseModel):
    column: str
    table: str
    operator: str
    value: Any

class QueryPlan(BaseModel):
    model_config = ConfigDict(extra='allow')
    
    select_columns: List[Dict[str, Any]] # {"table": "...", "column": "...", "agg": "..."}
    tables: List[str]
    joins: List[Dict[str, Any]] 
    filters: List[FilterCondition] = []
    sort: Optional[Dict[str, Any]] = None # {"column": "...", "direction": "ASC|DESC"}
    limit: Optional[int] = None
    ml_metadata: Optional[Dict[str, Any]] = None
    confidence_score: float = 0.0

class ChatResponse(BaseModel):
    sql: str
    rows: List[Dict[str, Any]]
    confidence: float
    columns: List[str]
    error: Optional[str] = None
    clarification: Optional[Dict[str, Any]] = None # {"question": "...", "options": [...]}
    ml_metadata: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = None
    session_id: Optional[str] = None
