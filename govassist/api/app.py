import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from govassist.config import load_env_file
from govassist.rag.pipeline import GovernmentSchemesRAG, resolve_data_file

load_env_file()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

rag_pipeline: GovernmentSchemesRAG | None = None


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
    global rag_pipeline

    logger.info("Starting Government Schemes RAG API")
    rag_pipeline = GovernmentSchemesRAG()

    data_file = resolve_data_file()
    auto_ingest = os.getenv("AUTO_INGEST", "true").lower() == "true"
    force_recreate = os.getenv("FORCE_RECREATE_COLLECTION", "false").lower() == "true"

    if auto_ingest:
        logger.info("Auto-ingesting scheme data from %s", data_file)
        inserted = rag_pipeline.ingest_schemes(
            data_file=data_file,
            force_recreate=force_recreate,
        )
        logger.info("Ingestion complete. Inserted %s schemes.", inserted)

    yield

    logger.info("Shutting down Government Schemes RAG API")


app = FastAPI(
    title="Government Schemes Assistant API",
    description="RAG backend using FastAPI, Qdrant, sentence-transformers, and Groq.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
def health_check() -> dict:
    return {"status": "OK"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    if rag_pipeline is None:
        raise HTTPException(status_code=503, detail="RAG pipeline is not ready yet.")

    try:
        session_id = request.session_id
        if session_id in {None, "", "null", "None", "string"}:
            session_id = None

        result = rag_pipeline.answer_query(
            query=request.query,
            top_k=request.top_k,
            session_id=session_id,
        )
        return ChatResponse(**result)
    except Exception as exc:
        logger.exception("Chat request failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/sessions/{session_id}")
def get_session(session_id: str) -> dict:
    if rag_pipeline is None:
        raise HTTPException(status_code=503, detail="RAG pipeline is not ready yet.")

    history = rag_pipeline.checkpointer.get_history(session_id)
    return {
        "session_id": session_id,
        "history": history,
    }
