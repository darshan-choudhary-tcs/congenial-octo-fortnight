"""
FastAPI Backend for RAG & Multi-Agent Application
Main entry point for the application
"""
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError
import uvicorn
from loguru import logger

from app.api.v1 import auth, chat, documents, agents, admin, explainability, utilities, metering, council, prompts
from app.database.db import init_db, get_db, get_primary_db, set_user_db_context, clear_user_db_context
from app.database.models import User
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


class DatabaseContextMiddleware(BaseHTTPMiddleware):
    """Middleware to set database context based on authenticated user"""

    async def dispatch(self, request: Request, call_next):
        # Clear any existing context
        clear_user_db_context()

        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            try:
                # Decode token to get user info
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                username: str = payload.get("sub")

                if username:
                    # Get user from primary database - use proper context manager
                    db_gen = get_primary_db()
                    db = next(db_gen)
                    try:
                        user = db.query(User).filter(User.username == username).first()

                        if user:
                            # Set database context for non-super-admins
                            if not user.is_superuser and user.company_database_name:
                                set_user_db_context(user.company_database_name)
                                logger.info(f"[MIDDLEWARE] Set DB context for {username}: {user.company_database_name}")
                            else:
                                logger.info(f"[MIDDLEWARE] User {username} using primary DB (superuser={user.is_superuser})")
                    finally:
                        # Properly close the generator to ensure session cleanup
                        try:
                            next(db_gen)
                        except StopIteration:
                            pass
            except JWTError as e:
                logger.debug(f"[MIDDLEWARE] JWT decode error (not critical): {e}")
                pass
            except Exception as e:
                logger.error(f"[MIDDLEWARE] Error setting DB context: {e}")
                pass

        response = await call_next(request)

        # Clear context after request
        clear_user_db_context()

        return response


# Add database context middleware BEFORE CORS
app.add_middleware(DatabaseContextMiddleware)

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
app.include_router(council.router, prefix="/api/v1/council", tags=["Council"])
app.include_router(prompts.router, prefix="/api/v1/prompts", tags=["Prompts"])

@app.get("/")
async def root():
    return {
        "message": "RAG & Multi-Agent API",
        "version": "1.0.0",
        "status": "running",
        "features": [
            "Retrieval Augmented Generation (RAG)",
            "Multi-Agent Orchestration",
            "Council of Agents (Multi-LLM Consensus)",
            "Explainable AI",
            "Grounding & Source Attribution",
            "Dual LLM Support (Custom API + Ollama)",
            "Role-Based Access Control",
            "Prompt Library Management API"
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
