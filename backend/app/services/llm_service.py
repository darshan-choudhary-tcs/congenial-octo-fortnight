"""
Dual LLM Service supporting Custom API and Ollama
"""
from typing import Optional, Dict, Any, List
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_ollama import OllamaLLM, OllamaEmbeddings
import httpx
import requests
import time
import json
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
        Invoke LLM with retry logic (legacy method - returns only content)

        Args:
            prompt: User prompt
            provider: LLM provider to use
            system_message: Optional system message
            **kwargs: Additional arguments for LLM

        Returns:
            LLM response as string
        """
        result = await self.generate_response(prompt, provider, system_message, **kwargs)
        return result["content"]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_response(
        self,
        prompt: str,
        provider: str = "custom",
        system_message: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate LLM response with token usage tracking

        Args:
            prompt: User prompt
            provider: LLM provider to use
            system_message: Optional system message
            **kwargs: Additional arguments for LLM

        Returns:
            Dictionary with 'content' and 'token_usage' keys
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
                content = response.content
            else:
                content = str(response)

            # Extract token usage from response metadata
            token_usage = self._extract_token_usage(response, provider, prompt, content)

            return {
                "content": content,
                "token_usage": token_usage
            }

        except Exception as e:
            logger.error(f"LLM invocation failed: {e}")
            raise

    async def generate_document_summary(
        self,
        text: str,
        provider: str = "custom",
        max_length: int = 10000
    ) -> Dict[str, Any]:
        """
        Generate a concise summary of a document using LLM

        Args:
            text: Document text content
            provider: LLM provider to use
            max_length: Maximum text length to process (tokens)

        Returns:
            Dictionary with 'summary' and 'token_usage' keys
        """
        try:
            # Truncate text if too long (approximate: 1 token ≈ 4 chars)
            if len(text) > max_length * 4:
                text = text[:max_length * 4]
                logger.warning(f"Document text truncated to {max_length * 4} characters for summarization")

            system_message = (
                "You are an expert document analyst. Create concise, informative succinct summary. "
                "Output ONLY the summary text, no preamble, no explanations, no meta-commentary. "
                "Start directly with the content summary."
            )

            prompt = f"""Summarize the following document in 200-300 words. Include main points and key information. Write in clear, professional language. Output ONLY the summary, nothing else.

Document:
{text}

Summary:"""

            result = await self.generate_response(
                prompt=prompt,
                provider=provider,
                system_message=system_message
            )

            # Clean up common preamble patterns
            summary = result["content"].strip()

            # Remove common preamble phrases
            preamble_patterns = [
                "Unfortunately, you haven't provided the full document. However, based on the information given, here's a concise summary:",
                "Here's a concise summary:",
                "Here is a summary:",
                "Summary:",
                "Based on the information provided:",
                "Based on the document:",
            ]

            for pattern in preamble_patterns:
                if summary.startswith(pattern):
                    summary = summary[len(pattern):].strip()

            return {
                "summary": summary,
                "token_usage": result["token_usage"]
            }

        except Exception as e:
            logger.error(f"Failed to generate document summary: {e}")
            raise

    async def extract_keywords(
        self,
        text: str,
        provider: str = "custom",
        max_keywords: int = 10,
        max_length: int = 10000
    ) -> Dict[str, Any]:
        """
        Extract relevant keywords from document text using LLM

        Args:
            text: Document text content
            provider: LLM provider to use
            max_keywords: Maximum number of keywords to extract
            max_length: Maximum text length to process

        Returns:
            Dictionary with 'keywords' (list) and 'token_usage' keys
        """
        try:
            # Truncate text if too long
            if len(text) > max_length * 4:
                text = text[:max_length * 4]

            system_message = (
                "You are an expert at analyzing documents and extracting key terms. "
                "Extract the most important and relevant keywords that represent the core topics "
                "and concepts in the document. Return ONLY a JSON array of keywords, nothing else."
            )

            prompt = f"""Extract {max_keywords} most important keywords from this document.
Return them as a JSON array like: ["keyword1", "keyword2", "keyword3"]

Document:
{text}

Keywords (JSON array only):"""

            result = await self.generate_response(
                prompt=prompt,
                provider=provider,
                system_message=system_message
            )

            # Parse the JSON response
            content = result["content"].strip()

            # Try to extract JSON array from response
            try:
                # Look for JSON array pattern
                if content.startswith('[') and content.endswith(']'):
                    keywords = json.loads(content)
                else:
                    # Try to find JSON array in the content
                    import re
                    json_match = re.search(r'\[.*?\]', content, re.DOTALL)
                    if json_match:
                        keywords = json.loads(json_match.group())
                    else:
                        # Fallback: split by commas or newlines
                        keywords = [k.strip(' "\n-*') for k in content.split(',') if k.strip()]
                        keywords = keywords[:max_keywords]
            except json.JSONDecodeError:
                # Fallback parsing
                keywords = [k.strip(' "\n-*') for k in content.split(',') if k.strip()]
                keywords = keywords[:max_keywords]

            return {
                "keywords": keywords,
                "token_usage": result["token_usage"]
            }

        except Exception as e:
            logger.error(f"Failed to extract keywords: {e}")
            raise

    async def classify_topics(
        self,
        text: str,
        provider: str = "custom",
        max_topics: int = 5,
        max_length: int = 10000
    ) -> Dict[str, Any]:
        """
        Classify document into main topics/categories using LLM

        Args:
            text: Document text content
            provider: LLM provider to use
            max_topics: Maximum number of topics to identify
            max_length: Maximum text length to process

        Returns:
            Dictionary with 'topics' (list) and 'token_usage' keys
        """
        try:
            # Truncate text if too long
            if len(text) > max_length * 4:
                text = text[:max_length * 4]

            system_message = (
                "You are an expert document classifier. Analyze the document and identify "
                "the main topics or themes it covers. Return ONLY a JSON array of topics, nothing else."
            )

            prompt = f"""Identify the {max_topics} main topics or themes in this document.
Return them as a JSON array like: ["topic1", "topic2", "topic3"]

Document:
{text}

Topics (JSON array only):"""

            result = await self.generate_response(
                prompt=prompt,
                provider=provider,
                system_message=system_message
            )

            # Parse the JSON response
            content = result["content"].strip()

            # Try to extract JSON array from response
            try:
                if content.startswith('[') and content.endswith(']'):
                    topics = json.loads(content)
                else:
                    # Try to find JSON array in the content
                    import re
                    json_match = re.search(r'\[.*?\]', content, re.DOTALL)
                    if json_match:
                        topics = json.loads(json_match.group())
                    else:
                        # Fallback: split by commas or newlines
                        topics = [t.strip(' "\n-*') for t in content.split(',') if t.strip()]
                        topics = topics[:max_topics]
            except json.JSONDecodeError:
                # Fallback parsing
                topics = [t.strip(' "\n-*') for t in content.split(',') if t.strip()]
                topics = topics[:max_topics]

            return {
                "topics": topics,
                "token_usage": result["token_usage"]
            }

        except Exception as e:
            logger.error(f"Failed to classify topics: {e}")
            raise

    async def determine_content_type(
        self,
        text: str,
        provider: str = "custom",
        max_length: int = 5000
    ) -> Dict[str, Any]:
        """
        Determine the content type/genre of a document

        Args:
            text: Document text content
            provider: LLM provider to use
            max_length: Maximum text length to process

        Returns:
            Dictionary with 'content_type' and 'token_usage' keys
        """
        try:
            # Truncate text if too long
            if len(text) > max_length * 4:
                text = text[:max_length * 4]

            system_message = (
                "You are a document classifier. Classify the document into one of these categories: "
                "technical, legal, financial, academic, business, medical, general. "
                "Return ONLY the category name, nothing else."
            )

            prompt = f"""Classify this document into one category: technical, legal, financial, academic, business, medical, or general.

Document:
{text}

Category:"""

            result = await self.generate_response(
                prompt=prompt,
                provider=provider,
                system_message=system_message
            )

            content_type = result["content"].strip().lower()
            # Clean up the response
            valid_types = ["technical", "legal", "financial", "academic", "business", "medical", "general"]
            if content_type not in valid_types:
                # Try to find a valid type in the response
                for valid_type in valid_types:
                    if valid_type in content_type:
                        content_type = valid_type
                        break
                else:
                    content_type = "general"

            return {
                "content_type": content_type,
                "token_usage": result["token_usage"]
            }

        except Exception as e:
            logger.error(f"Failed to determine content type: {e}")
            raise

    def _extract_token_usage(
        self,
        response: Any,
        provider: str,
        prompt: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Extract token usage from LLM response

        Args:
            response: Raw LLM response object
            provider: Provider used (custom or ollama)
            prompt: Input prompt (for estimation)
            content: Response content (for estimation)

        Returns:
            Dictionary with token usage information
        """
        token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }

        try:
            # For ChatOpenAI (custom provider), extract from response_metadata
            if hasattr(response, 'response_metadata') and response.response_metadata:
                metadata = response.response_metadata
                if 'token_usage' in metadata:
                    usage = metadata['token_usage']
                    token_usage["prompt_tokens"] = usage.get('prompt_tokens', 0)
                    token_usage["completion_tokens"] = usage.get('completion_tokens', 0)
                    token_usage["total_tokens"] = usage.get('total_tokens', 0)
                    logger.debug(f"Extracted token usage from metadata: {token_usage}")
                    return token_usage

            # For Ollama or if metadata not available, estimate tokens
            # Using rough estimation: ~4 characters per token
            if provider == "ollama" or token_usage["total_tokens"] == 0:
                estimated_prompt = len(prompt) // 4
                estimated_completion = len(content) // 4
                token_usage["prompt_tokens"] = estimated_prompt
                token_usage["completion_tokens"] = estimated_completion
                token_usage["total_tokens"] = estimated_prompt + estimated_completion
                logger.debug(f"Estimated token usage for {provider}: {token_usage}")

        except Exception as e:
            logger.warning(f"Could not extract token usage: {e}")

        return token_usage

    async def get_embeddings_for_text(
        self,
        text: str,
        provider: str = "custom"
    ) -> List[float]:
        """
        Get embeddings for text (legacy method - returns only embeddings)

        Args:
            text: Text to embed
            provider: Embeddings provider to use

        Returns:
            List of embedding values
        """
        result = await self.generate_embeddings(text, provider)
        return result["embeddings"]

    async def generate_embeddings(
        self,
        text: str,
        provider: str = "custom"
    ) -> Dict[str, Any]:
        """
        Generate embeddings with token usage tracking

        Args:
            text: Text to embed
            provider: Embeddings provider to use

        Returns:
            Dictionary with 'embeddings' and 'token_usage' keys
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

                    # Estimate embedding tokens (rough approximation)
                    embedding_tokens = len(text) // 4

                    return {
                        "embeddings": embedding_vector,
                        "token_usage": {
                            "embedding_tokens": embedding_tokens,
                            "total_tokens": embedding_tokens
                        }
                    }
                else:
                    raise Exception(f"HTTP {response.status_code}: {response.text}")
            else:
                # Use LangChain for custom provider
                embeddings = self.get_embeddings(provider)
                embedding_vector = embeddings.embed_query(text)

                # Estimate embedding tokens
                embedding_tokens = len(text) // 4

                return {
                    "embeddings": embedding_vector,
                    "token_usage": {
                        "embedding_tokens": embedding_tokens,
                        "total_tokens": embedding_tokens
                    }
                }

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
