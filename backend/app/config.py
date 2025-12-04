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
    CUSTOM_VISION_MODEL: str = "azure_ai/genailab-maas-Llama-3.2-90B-Vision-Instruct"

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    OLLAMA_VISION_MODEL: str = "llama3.2-vision"

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

    # Council of Agents
    COUNCIL_ENABLED: bool = True
    COUNCIL_DEFAULT_STRATEGY: str = "weighted_confidence"  # weighted_confidence, highest_confidence, majority, synthesis
    COUNCIL_VOTING_STRATEGIES: List[str] = ["weighted_confidence", "highest_confidence", "majority", "synthesis"]
    COUNCIL_MAX_DEBATE_ROUNDS: int = 5
    COUNCIL_MIN_CONSENSUS_THRESHOLD: float = 0.6  # Minimum consensus level for acceptance
    COUNCIL_ENABLE_SYNTHESIS: bool = True
    COUNCIL_ANALYTICAL_WEIGHT: float = 1.0  # Vote weight for AnalyticalVoter
    COUNCIL_CREATIVE_WEIGHT: float = 1.0  # Vote weight for CreativeVoter
    COUNCIL_CRITICAL_WEIGHT: float = 1.0  # Vote weight for CriticalVoter
    COUNCIL_ANALYTICAL_TEMPERATURE: float = 0.3  # Temperature for analytical reasoning
    COUNCIL_CREATIVE_TEMPERATURE: float = 0.9  # Temperature for creative thinking
    COUNCIL_CRITICAL_TEMPERATURE: float = 0.5  # Temperature for critical evaluation
    
    # Council LLM Provider Settings (for each agent)
    COUNCIL_ANALYTICAL_PROVIDER: str = "ollama"  # ollama, custom, openai, deepseek, llama
    COUNCIL_CREATIVE_PROVIDER: str = "ollama"  # ollama, custom, openai, deepseek, llama
    COUNCIL_CRITICAL_PROVIDER: str = "ollama"  # ollama, custom, openai, deepseek, llama
    
    # Future LLM Provider Configurations
    # OpenAI Settings
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    
    # DeepSeek Settings
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_MODEL: str = "deepseek-reasoner"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    
    # Llama Settings
    LLAMA_API_KEY: str = ""
    LLAMA_MODEL: str = "llama-3.3-70b"
    LLAMA_BASE_URL: str = "https://api.llama-api.com/v1"

    # File Upload
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".txt", ".csv", ".docx"]
    UPLOAD_DIR: str = "./uploads"

    # OCR Configuration
    OCR_SUPPORTED_FORMATS: List[str] = [".jpg", ".jpeg", ".png", ".pdf", ".tiff", ".tif", ".bmp", ".webp"]
    OCR_MAX_FILE_SIZE: int = 20971520  # 20MB for images
    OCR_IMAGE_MAX_DIMENSION: int = 2048  # Max width/height for processing
    OCR_CONFIDENCE_THRESHOLD: float = 0.7
    OCR_ENABLE_PREPROCESSING: bool = True
    OCR_PDF_DPI: int = 300  # DPI for PDF to image conversion

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Create necessary directories
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
