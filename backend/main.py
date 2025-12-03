"""
FastAPI Backend for RAG & Multi-Agent Application
Main entry point for the application
"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.api.v1 import auth, chat, documents, agents, admin, explainability, utilities, metering
from app.database.db import init_db, get_db
from app.config import settings

tiktoken_cache_dir = r"token"
os.environ["TIKTOKEN_CACHE_DIR"] = tiktoken_cache_dir

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and resources on startup"""
    print("🚀 Initializing RAG & Multi-Agent Application...")
    init_db()
    print("✅ Database initialized")
    yield
    print("🛑 Shutting down application...")

app = FastAPI(
    title="RAG & Multi-Agent API",
    description="Advanced AI system with RAG, Multi-Agent orchestration, and Explainable AI",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["Agents"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(explainability.router, prefix="/api/v1/explain", tags=["Explainability"])
app.include_router(utilities.router, prefix="/api/v1/utilities", tags=["Utilities"])
app.include_router(metering.router, prefix="/api/v1/metering", tags=["Metering"])

@app.get("/")
async def root():
    return {
        "message": "RAG & Multi-Agent API",
        "version": "1.0.0",
        "status": "running",
        "features": [
            "Retrieval Augmented Generation (RAG)",
            "Multi-Agent Orchestration",
            "Explainable AI",
            "Grounding & Source Attribution",
            "Dual LLM Support (Custom API + Ollama)",
            "Role-Based Access Control"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
