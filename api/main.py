from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from nql import ChatSQL, ChatResponse
from typing import Optional, List, Dict, Any
import os

app = FastAPI(title="nql API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global store for the engine instance
# In a real production app, you might use a more robust session/storage mechanism
engines: Dict[str, ChatSQL] = {}

class ConnectRequest(BaseModel):
    connection_url: str

class AskRequest(BaseModel):
    connection_url: str
    question: str
    session_id: Optional[str] = None

class FeedbackRequest(BaseModel):
    question: str
    predicted_plan: Dict[str, Any]
    user_correction: Optional[Dict[str, Any]] = None
    rating: int

@app.post("/connect")
async def connect(req: ConnectRequest):
    try:
        engine = ChatSQL(req.connection_url)
        engines[req.connection_url] = engine
        return {"status": "connected", "schema": engine.schema}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/ask", response_model=ChatResponse)
async def ask(req: AskRequest):
    if req.connection_url not in engines:
        try:
            engines[req.connection_url] = ChatSQL(req.connection_url)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to connect: {str(e)}")
    
    engine = engines[req.connection_url]
    return engine.ask(req.question, session_id=req.session_id)

@app.post("/feedback")
async def feedback(req: FeedbackRequest):
    from nql.enterprise.learning import FeedbackManager
    fm = FeedbackManager()
    fm.record_feedback(req.question, req.predicted_plan, req.user_correction, req.rating)
    return {"status": "recorded"}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
