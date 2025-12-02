"""
Dual LLM Service supporting Custom API and Ollama
"""
from typing import Optional, Dict, Any, List
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_ollama import OllamaLLM, OllamaEmbeddings
import httpx
import requests
import time
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

class LLMService:
    """Service for managing dual LLM providers (Custom API and Ollama)"""

    def __init__(self):
        self.custom_client = None
        self.ollama_client = None
        self.custom_embeddings = None
        self.ollama_embeddings = None
        self._initialize_clients()

    def _initialize_clients(self):
        """Initialize LLM clients"""
        try:
            # Custom API Client (genailab)
            if settings.CUSTOM_LLM_API_KEY:
                client = httpx.Client(verify=False)
                self.custom_client = ChatOpenAI(
                    base_url=settings.CUSTOM_LLM_BASE_URL,
                    model=settings.CUSTOM_LLM_MODEL,
                    api_key=settings.CUSTOM_LLM_API_KEY,
                    http_client=client,
                    temperature=settings.AGENT_TEMPERATURE
                )

                self.custom_embeddings = OpenAIEmbeddings(
                    base_url=settings.CUSTOM_LLM_BASE_URL,
                    model=settings.CUSTOM_EMBEDDING_MODEL,
                    api_key=settings.CUSTOM_LLM_API_KEY,
                    http_client=client
                )
                logger.info("Custom LLM API initialized successfully")
            else:
                logger.warning("Custom LLM API key not provided")

        except Exception as e:
            logger.error(f"Failed to initialize Custom LLM API: {e}")

        try:
            # Ollama Client
            self.ollama_client = OllamaLLM(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.OLLAMA_MODEL,
                temperature=settings.AGENT_TEMPERATURE
            )

            self.ollama_embeddings = OllamaEmbeddings(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.OLLAMA_EMBEDDING_MODEL
            )
            logger.info("Ollama client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Ollama: {e}")

    def get_llm(self, provider: str = "custom"):
        """
        Get LLM instance based on provider

        Args:
            provider: Either "custom" or "ollama"

        Returns:
            LLM instance
        """
        if provider == "custom":
            if self.custom_client is None:
                raise ValueError("Custom LLM API not initialized. Check API key.")
            return self.custom_client
        elif provider == "ollama":
            if self.ollama_client is None:
                raise ValueError("Ollama not initialized. Check if Ollama is running.")
            return self.ollama_client
        else:
            raise ValueError(f"Unknown provider: {provider}. Use 'custom' or 'ollama'")

    def get_embeddings(self, provider: str = "custom"):
        """
        Get embeddings instance based on provider

        Args:
            provider: Either "custom" or "ollama"

        Returns:
            Embeddings instance
        """
        if provider == "custom":
            if self.custom_embeddings is None:
                raise ValueError("Custom embeddings not initialized. Check API key.")
            return self.custom_embeddings
        elif provider == "ollama":
            if self.ollama_embeddings is None:
                raise ValueError("Ollama embeddings not initialized. Check if Ollama is running.")
            return self.ollama_embeddings
        else:
            raise ValueError(f"Unknown provider: {provider}. Use 'custom' or 'ollama'")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def invoke_llm(
        self,
        prompt: str,
        provider: str = "custom",
        system_message: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Invoke LLM with retry logic

        Args:
            prompt: User prompt
            provider: LLM provider to use
            system_message: Optional system message
            **kwargs: Additional arguments for LLM

        Returns:
            LLM response as string
        """
        try:
            llm = self.get_llm(provider)

            if system_message:
                messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ]
                if isinstance(llm, ChatOpenAI):
                    response = llm.invoke(messages, **kwargs)
                else:
                    # Ollama doesn't support message format in the same way
                    full_prompt = f"System: {system_message}\n\nUser: {prompt}"
                    response = llm.invoke(full_prompt, **kwargs)
            else:
                response = llm.invoke(prompt, **kwargs)

            # Extract content from response
            if hasattr(response, 'content'):
                return response.content
            else:
                return str(response)

        except Exception as e:
            logger.error(f"LLM invocation failed: {e}")
            raise

    async def get_embeddings_for_text(
        self,
        text: str,
        provider: str = "custom"
    ) -> List[float]:
        """
        Get embeddings for text

        Args:
            text: Text to embed
            provider: Embeddings provider to use

        Returns:
            List of embedding values
        """
        try:
            # For Ollama, use direct HTTP API for consistency with document embeddings
            if provider == "ollama":
                response = requests.post(
                    f"{settings.OLLAMA_BASE_URL}/api/embeddings",
                    json={
                        "model": settings.OLLAMA_EMBEDDING_MODEL,
                        "prompt": text
                    },
                    timeout=30
                )

                if response.status_code == 200:
                    result = response.json()
                    embedding_vector = result.get("embedding", [])
                    logger.info(f"Generated query embedding via direct HTTP (dim: {len(embedding_vector)})")
                    return embedding_vector
                else:
                    raise Exception(f"HTTP {response.status_code}: {response.text}")
            else:
                # Use LangChain for custom provider
                embeddings = self.get_embeddings(provider)
                embedding_vector = embeddings.embed_query(text)
                return embedding_vector

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise

    async def get_embeddings_for_documents(
        self,
        texts: List[str],
        provider: str = "custom"
    ) -> List[List[float]]:
        """
        Get embeddings for multiple documents

        Args:
            texts: List of texts to embed
            provider: Embeddings provider to use

        Returns:
            List of embedding vectors
        """
        try:
            import time
            logger.info(f"Getting embeddings for {len(texts)} documents using provider: {provider}")
            embeddings = self.get_embeddings(provider)
            logger.info(f"Embeddings instance: {type(embeddings).__name__}")

            # For Ollama, use direct HTTP API to avoid LangChain wrapper issues
            if provider == "ollama":
                logger.info(f"Processing {len(texts)} documents using direct Ollama HTTP API")
                all_embeddings = []

                # Warmup call
                try:
                    logger.info("Warming up Ollama embedding model...")
                    warmup_response = requests.post(
                        f"{settings.OLLAMA_BASE_URL}/api/embeddings",
                        json={"model": settings.OLLAMA_EMBEDDING_MODEL, "prompt": "warmup"},
                        timeout=30
                    )
                    if warmup_response.status_code == 200:
                        logger.info("Warmup successful")
                    time.sleep(0.5)
                except Exception as e:
                    logger.warning(f"Warmup failed (continuing anyway): {e}")

                # Process each document individually using direct HTTP
                for i, text in enumerate(texts):
                    doc_num = i + 1

                    # Retry logic for each document
                    for attempt in range(5):
                        try:
                            # Progressive delay between requests to avoid overwhelming Ollama
                            if i > 0:
                                # Increase delay after failures
                                base_delay = 1.0 if attempt == 0 else 1.5
                                time.sleep(base_delay)

                            # Direct HTTP call to Ollama API
                            response = requests.post(
                                f"{settings.OLLAMA_BASE_URL}/api/embeddings",
                                json={
                                    "model": settings.OLLAMA_EMBEDDING_MODEL,
                                    "prompt": text
                                },
                                timeout=90  # Increased timeout for stability
                            )

                            if response.status_code == 200:
                                result = response.json()
                                vec = result.get("embedding", [])
                                if vec and len(vec) > 0:
                                    all_embeddings.append(vec)
                                    logger.info(f"✓ Embedded document {doc_num}/{len(texts)} (dim: {len(vec)})")
                                    break
                                else:
                                    raise Exception("Empty embedding returned")
                            else:
                                raise Exception(f"HTTP {response.status_code}: {response.text}")

                        except requests.exceptions.Timeout:
                            if attempt < 4:
                                wait_time = (attempt + 1) * 2.0  # Longer waits for timeouts
                                logger.warning(f"Document {doc_num} attempt {attempt+1} timed out, retrying in {wait_time}s")
                                time.sleep(wait_time)
                            else:
                                raise Exception(f"Request timed out after 5 attempts")

                        except Exception as e:
                            if attempt < 4:
                                # Exponential backoff: 2s, 4s, 6s, 8s
                                wait_time = (attempt + 1) * 2.0
                                logger.warning(f"Document {doc_num} attempt {attempt+1} failed, retrying in {wait_time}s: {e}")
                                time.sleep(wait_time)
                            else:
                                error_msg = f"Failed to embed document {doc_num} after 5 attempts: {e}"
                                logger.error(error_msg)
                                raise Exception(error_msg)

                logger.info(f"✓ Successfully embedded all {len(texts)} documents using direct HTTP API")
                return all_embeddings
            else:
                embedding_vectors = embeddings.embed_documents(texts)
                return embedding_vectors

        except Exception as e:
            logger.error(f"Batch embedding generation failed with provider '{provider}': {e}")
            raise

    def check_availability(self, provider: str) -> Dict[str, Any]:
        """
        Check if LLM provider is available

        Args:
            provider: Provider to check

        Returns:
            Status dictionary
        """
        status = {
            "provider": provider,
            "available": False,
            "message": ""
        }

        try:
            llm = self.get_llm(provider)
            # Try a simple test
            response = llm.invoke("test")
            status["available"] = True
            status["message"] = "Provider is available"
        except Exception as e:
            status["message"] = str(e)

        return status

# Global instance
llm_service = LLMService()
