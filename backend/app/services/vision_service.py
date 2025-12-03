"""
Vision Service for OCR and Image Analysis using Vision LLMs
"""
import base64
import requests
import logging
import urllib3
from typing import Optional, Dict, Any, List
from PIL import Image
from io import BytesIO
from app.config import settings

# Disable SSL warnings for internal API
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class VisionService:
    """Service for interacting with vision models for OCR and image understanding"""

    def __init__(self):
        self.custom_base_url = settings.CUSTOM_LLM_BASE_URL
        self.custom_vision_model = settings.CUSTOM_VISION_MODEL
        self.custom_api_key = settings.CUSTOM_LLM_API_KEY
        self.ollama_base_url = settings.OLLAMA_BASE_URL
        self.ollama_vision_model = settings.OLLAMA_VISION_MODEL

    def encode_image_to_base64(self, image_path: str) -> str:
        """
        Encode image file to base64 string

        Args:
            image_path: Path to the image file

        Returns:
            Base64 encoded string of the image
        """
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image to base64: {str(e)}")
            raise

    def encode_pil_image_to_base64(self, image: Image.Image, format: str = "PNG") -> str:
        """
        Encode PIL Image to base64 string

        Args:
            image: PIL Image object
            format: Image format (PNG, JPEG, etc.)

        Returns:
            Base64 encoded string of the image
        """
        try:
            buffered = BytesIO()
            image.save(buffered, format=format)
            return base64.b64encode(buffered.getvalue()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding PIL image to base64: {str(e)}")
            raise

    def call_custom_vision_api(
        self,
        image_base64: str,
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Call Custom API (TCS GenAI Lab) vision model

        Args:
            image_base64: Base64 encoded image
            prompt: Text prompt for the vision model
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Dict with extracted_text, confidence, and metadata
        """
        try:
            logger.info(f"Calling custom vision API: {self.custom_vision_model}")
            url = f"{self.custom_base_url}/v1/chat/completions"

            headers = {
                "Content-Type": "application/json",
            }
            if self.custom_api_key:
                headers["Authorization"] = f"Bearer {self.custom_api_key}"

            payload = {
                "model": self.custom_vision_model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            response = requests.post(
                url,
                json=payload,
                headers=headers,
                verify=False,  # SSL verification disabled for internal API
                timeout=180  # Increased timeout for vision models
            )
            response.raise_for_status()

            result = response.json()
            extracted_text = result["choices"][0]["message"]["content"]
            tokens_used = result.get("usage", {}).get("total_tokens", 0)

            logger.info(f"Custom vision API success - Tokens: {tokens_used}, Text length: {len(extracted_text)}")

            return {
                "extracted_text": extracted_text,
                "confidence": 0.85,  # Vision models don't provide confidence, use default
                "model": self.custom_vision_model,
                "provider": "custom",
                "tokens_used": result.get("usage", {}).get("total_tokens", 0)
            }

        except requests.exceptions.Timeout as e:
            logger.error(f"Custom vision API timeout after 180s: {str(e)}")
            raise TimeoutError("Vision model request timed out. The model may be processing a complex image.")
        except requests.exceptions.SSLError as e:
            logger.error(f"SSL error with custom vision API: {str(e)}")
            raise ConnectionError("SSL certificate error. Try using Ollama provider instead.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error calling custom vision API: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling custom vision API: {str(e)}")
            raise

    def call_ollama_vision(
        self,
        image_base64: str,
        prompt: str,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Call Ollama vision model

        Args:
            image_base64: Base64 encoded image
            prompt: Text prompt for the vision model
            temperature: Sampling temperature

        Returns:
            Dict with extracted_text, confidence, and metadata
        """
        try:
            logger.info(f"Calling Ollama vision: {self.ollama_vision_model} (this may take 2-5 minutes)")
            url = f"{self.ollama_base_url}/api/generate"

            payload = {
                "model": self.ollama_vision_model,
                "prompt": prompt,
                "images": [image_base64],
                "stream": False,
                "options": {
                    "temperature": temperature
                }
            }

            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()

            result = response.json()
            extracted_text = result.get("response", "")
            tokens_used = result.get("eval_count", 0)

            logger.info(f"Ollama vision success - Tokens: {tokens_used}, Text length: {len(extracted_text)}")

            return {
                "extracted_text": extracted_text,
                "confidence": 0.85,  # Vision models don't provide confidence, use default
                "model": self.ollama_vision_model,
                "provider": "ollama",
                "tokens_used": result.get("eval_count", 0)
            }

        except requests.exceptions.Timeout as e:
            logger.error(f"Ollama vision timeout after 300s: {str(e)}")
            raise TimeoutError("Ollama vision model timed out. Try: 1) Using a smaller image, 2) Restarting Ollama, or 3) Using 'custom' provider instead.")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Cannot connect to Ollama: {str(e)}")
            raise ConnectionError("Cannot connect to Ollama. Make sure Ollama is running: 'ollama serve'")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error calling Ollama vision: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Ollama vision: {str(e)}")
            raise

    def extract_text_from_image(
        self,
        image_path: Optional[str] = None,
        image_base64: Optional[str] = None,
        pil_image: Optional[Image.Image] = None,
        provider: str = "custom",
        custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract text from image using vision model

        Args:
            image_path: Path to image file (optional)
            image_base64: Base64 encoded image (optional)
            pil_image: PIL Image object (optional)
            provider: "custom" or "ollama"
            custom_prompt: Custom prompt for OCR (optional)

        Returns:
            Dict with extracted text and metadata
        """
        try:
            # Encode image to base64
            if image_base64:
                encoded_image = image_base64
            elif pil_image:
                encoded_image = self.encode_pil_image_to_base64(pil_image)
            elif image_path:
                encoded_image = self.encode_image_to_base64(image_path)
            else:
                raise ValueError("Must provide either image_path, image_base64, or pil_image")

            # Default OCR prompt
            if not custom_prompt:
                custom_prompt = """Extract ALL text from this image exactly as it appears.

Instructions:
- Preserve the original layout and formatting as much as possible
- Include all visible text, numbers, symbols, and punctuation
- Maintain line breaks and spacing
- If the text is structured (tables, lists, forms), preserve that structure
- If any text is unclear or difficult to read, note it with [unclear]
- Do not add any commentary or interpretation, only the extracted text

Extracted text:"""

            # Call appropriate provider
            if provider == "custom":
                result = self.call_custom_vision_api(encoded_image, custom_prompt)
            elif provider == "ollama":
                result = self.call_ollama_vision(encoded_image, custom_prompt)
            else:
                raise ValueError(f"Unknown provider: {provider}")

            return result

        except Exception as e:
            logger.error(f"Error extracting text from image: {str(e)}")
            raise

    def analyze_image(
        self,
        image_path: Optional[str] = None,
        image_base64: Optional[str] = None,
        pil_image: Optional[Image.Image] = None,
        provider: str = "custom",
        analysis_prompt: str = "Describe what you see in this image in detail."
    ) -> Dict[str, Any]:
        """
        Analyze image content using vision model

        Args:
            image_path: Path to image file (optional)
            image_base64: Base64 encoded image (optional)
            pil_image: PIL Image object (optional)
            provider: "custom" or "ollama"
            analysis_prompt: Custom prompt for analysis

        Returns:
            Dict with analysis results and metadata
        """
        try:
            # Encode image to base64
            if image_base64:
                encoded_image = image_base64
            elif pil_image:
                encoded_image = self.encode_pil_image_to_base64(pil_image)
            elif image_path:
                encoded_image = self.encode_image_to_base64(image_path)
            else:
                raise ValueError("Must provide either image_path, image_base64, or pil_image")

            # Call appropriate provider
            if provider == "custom":
                result = self.call_custom_vision_api(encoded_image, analysis_prompt)
            elif provider == "ollama":
                result = self.call_ollama_vision(encoded_image, analysis_prompt)
            else:
                raise ValueError(f"Unknown provider: {provider}")

            return result

        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            raise

# Singleton instance
vision_service = VisionService()
