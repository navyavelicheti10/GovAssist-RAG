import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from govassist.config import load_env_file
from govassist.agents.graph import vozhi_orchestrator
from langchain_core.messages import HumanMessage
from fastapi import Request, BackgroundTasks
from pydantic import BaseModel, Field

# Ensure env vars are loaded
load_env_file()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=3, description="User question about schemes")
    top_k: int = Field(default=5, ge=1, le=10, description="Number of results to retrieve")
    session_id: Optional[str] = Field(
        default=None,
        description="Pass the same session_id on follow-up messages to continue the chat",
    )


class ChatResponse(BaseModel):
    session_id: str
    query: str
    answer: str
    matches: list


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Vozhi API (LangGraph Edition)")
    yield
    logger.info("Shutting down Vozhi API")


app = FastAPI(
    title="Government Schemes Assistant API",
    description="RAG backend using FastAPI, Qdrant, sentence-transformers, and Groq.",
    version="1.0.0",
    lifespan=lifespan,
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = PROJECT_ROOT / "web"


@app.get("/health")
def health_check() -> dict:
    return {"status": "OK"}


@app.get("/", include_in_schema=False)
def serve_web_app() -> FileResponse:
    index_file = WEB_ROOT / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Web UI not found. Create web/index.html.")
    return FileResponse(index_file)


@app.post("/chat")
def chat(request: ChatRequest):
    session_id = request.session_id or "default-session"
    config = {"configurable": {"thread_id": session_id}}
    
    # Run the langgraph via streaming or invoke
    state_input = {
        "messages": [HumanMessage(content=request.query)],
        "current_query": request.query
    }
    
    # Get final state after execution
    result_state = vozhi_orchestrator.invoke(state_input, config=config)
    
    # Format response for Web UI
    final_text = result_state.get("final_package", "I am having trouble processing that right now.")
    confidence = result_state.get("confidence_score", 0.0)
    matches = result_state.get("retrieved_schemes", [])
    
    return {
        "session_id": session_id,
        "query": request.query,
        "answer": final_text,
        "confidence": confidence,
        "matches": matches,
    }

from govassist.integrations.twilio import twilio_client
from fastapi import Response

@app.post("/whatsapp")
async def twilio_webhook(request: Request):
    """Handles incoming Twilio WhatsApp messages."""
    form_data = dict(await request.form())
    parsed = twilio_client.parse_incoming_message(form_data)
    
    sender = parsed.get("from")
    body = parsed.get("body", "").strip()
    
    if not sender:
        return Response(content="<Response></Response>", media_type="application/xml")
        
    session_id = sender.replace("whatsapp:", "")
    config = {"configurable": {"thread_id": session_id}}
    
    state_input = {"messages": [HumanMessage(content=body)], "current_query": body}
    
    try:
        result_state = vozhi_orchestrator.invoke(state_input, config=config)
        reply_text = result_state.get("final_package", "System Error while processing.")
    except Exception as e:
        logger.error(f"Error in graph: {e}")
        reply_text = "Sorry, I am currently undergoing maintenance."
        
    twiml_resp = twilio_client.generate_twiml_response(reply_text)
    return Response(content=twiml_resp, media_type="application/xml")
