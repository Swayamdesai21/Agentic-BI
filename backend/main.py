"""
FastAPI backend for Agentic BI.
Provides SSE streaming endpoint for the LangGraph agent pipeline.
"""

import asyncio
import json
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from database import init_db, get_schema_info
from schema_rag import schema_rag
from models import QueryRequest
from agents.graph import run_pipeline


# ── App Lifespan ────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and RAG on startup."""
    print("🚀 Starting Agentic BI Backend...")
    init_db()
    schema_rag.initialize()
    print("✅ Backend ready!")
    yield
    print("👋 Shutting down...")


# ── FastAPI App ─────────────────────────────────────────────────────────

app = FastAPI(
    title="Agentic BI",
    description="Natural language to live business dashboard",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Endpoints ───────────────────────────────────────────────────────────

@app.post("/api/query")
async def query_endpoint(request: QueryRequest):
    """
    Main endpoint: accepts a natural language question,
    runs the agent pipeline, and streams results via SSE.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    async def event_generator():
        try:
            async for event in run_pipeline(request.question):
                data = json.dumps(event, default=str)
                yield f"data: {data}\n\n"
                await asyncio.sleep(0.05)  # Small delay for smooth streaming
        except Exception as e:
            error_event = json.dumps({
                "event": "error",
                "agent": "System",
                "data": {"error": str(e)}
            })
            yield f"data: {error_event}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/api/schema")
async def schema_endpoint():
    """Return database schema info for debugging."""
    try:
        schema = get_schema_info()
        return {"schema": schema}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    groq_key = os.getenv("GROQ_API_KEY", "")
    return {
        "status": "healthy",
        "groq_configured": bool(groq_key and groq_key != "your_groq_api_key_here"),
        "database": "ready"
    }


@app.get("/api/suggestions")
async def suggestions_endpoint():
    """Return suggested queries for the UI."""
    return {
        "suggestions": [
            {
                "text": "Show me monthly revenue trends",
                "icon": "📈",
                "category": "Revenue"
            },
            {
                "text": "What are the top 10 best-selling products?",
                "icon": "🏆",
                "category": "Products"
            },
            {
                "text": "Revenue breakdown by category",
                "icon": "📊",
                "category": "Categories"
            },
            {
                "text": "Which regions generate the most revenue?",
                "icon": "🗺️",
                "category": "Geography"
            },
            {
                "text": "Customer segment analysis",
                "icon": "👥",
                "category": "Customers"
            },
            {
                "text": "Show me order status breakdown",
                "icon": "📦",
                "category": "Operations"
            },
            {
                "text": "What are the highest profit margin products?",
                "icon": "💰",
                "category": "Profitability"
            },
            {
                "text": "Average order value by month",
                "icon": "📉",
                "category": "Trends"
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
