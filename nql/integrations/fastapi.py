from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    execute: bool = True
    explain: bool = False

def get_nql_router(bot_instance) -> APIRouter:
    """
    Creates a FastAPI router for an NQL bot instance.
    """
    router = APIRouter(prefix="/nql", tags=["NQL"])

    @router.post("/chat")
    async def chat(request: ChatRequest):
        try:
            response = bot_instance.ask(
                question=request.question,
                session_id=request.session_id,
                execute=request.execute,
                explain=request.explain
            )
            return response.model_dump()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/schema")
    async def schema_report():
        try:
            return bot_instance.get_schema_report()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return router
