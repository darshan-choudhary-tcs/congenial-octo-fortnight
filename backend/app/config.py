"""
Application configuration using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "RAG Multi-Agent System"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Database
    DATABASE_URL: str = "sqlite:///./data/data_store.db"

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Custom LLM API
    CUSTOM_LLM_BASE_URL: str = "https://genailab.tcs.in"
    CUSTOM_LLM_MODEL: str = "azure_ai/genailab-maas-DeepSeek-V3-0324"
    CUSTOM_LLM_API_KEY: str = ""
    CUSTOM_EMBEDDING_MODEL: str = "azure/genailab-maas-text-embedding-3-large"

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "rag_documents"

    # RAG
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MAX_RETRIEVAL_DOCS: int = 5
    SIMILARITY_THRESHOLD: float = 0.01

    # Agents
    MAX_AGENT_ITERATIONS: int = 10
    AGENT_TEMPERATURE: float = 0.7
    ENABLE_AGENT_MEMORY: bool = True

    # Explainability
    EXPLAINABILITY_LEVEL: str = "detailed"  # basic, detailed, debug
    ENABLE_CONFIDENCE_SCORING: bool = True
    ENABLE_SOURCE_ATTRIBUTION: bool = True
    ENABLE_REASONING_CHAINS: bool = True

    # File Upload
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".txt", ".csv", ".docx"]
    UPLOAD_DIR: str = "./uploads"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Create necessary directories
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
