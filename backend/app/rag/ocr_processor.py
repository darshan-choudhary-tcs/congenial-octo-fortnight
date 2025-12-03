"""
OCR Processor for handling image and PDF OCR operations
"""
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from PIL import Image
import io

from app.config import settings
from app.services.vision_service import vision_service

logger = logging.getLogger(__name__)

class OCRProcessor:
    """Process images and PDFs for OCR extraction using vision models"""

    def __init__(self):
        self.supported_formats = settings.OCR_SUPPORTED_FORMATS
        self.max_dimension = settings.OCR_IMAGE_MAX_DIMENSION
        self.confidence_threshold = settings.OCR_CONFIDENCE_THRESHOLD
        self.enable_preprocessing = settings.OCR_ENABLE_PREPROCESSING
        self.pdf_dpi = settings.OCR_PDF_DPI

    def is_supported_format(self, filename: str) -> bool:
        """Check if file format is supported for OCR"""
        ext = Path(filename).suffix.lower()
        return ext in self.supported_formats

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR results

        Args:
            image: PIL Image object

        Returns:
            Preprocessed PIL Image
        """
        try:
            # Convert to RGB if needed
            if image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')

            # Resize if too large
            if self.enable_preprocessing:
                width, height = image.size
                if width > self.max_dimension or height > self.max_dimension:
                    # Calculate new dimensions maintaining aspect ratio
                    if width > height:
                        new_width = self.max_dimension
                        new_height = int(height * (self.max_dimension / width))
                    else:
                        new_height = self.max_dimension
                        new_width = int(width * (self.max_dimension / height))

                    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")

            return image

        except Exception as e:
            logger.error(f"Error preprocessing image: {str(e)}")
            return image  # Return original if preprocessing fails

    def pdf_to_images(self, pdf_path: str) -> List[Image.Image]:
        """
        Convert PDF pages to images

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of PIL Image objects (one per page)
        """
        try:
            from pdf2image import convert_from_path

            images = convert_from_path(
                pdf_path,
                dpi=self.pdf_dpi,
                fmt='png'
            )

            logger.info(f"Converted PDF to {len(images)} images")
            return images

        except ImportError:
            logger.error("pdf2image library not installed. Install with: pip install pdf2image")
            raise ImportError("pdf2image is required for PDF processing. Install with: pip install pdf2image")
        except Exception as e:
            logger.error(f"Error converting PDF to images: {str(e)}")
            raise

    def process_single_image(
        self,
        image_path: Optional[str] = None,
        pil_image: Optional[Image.Image] = None,
        provider: str = "custom",
        custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a single image for OCR

        Args:
            image_path: Path to image file (optional)
            pil_image: PIL Image object (optional)
            provider: "custom" or "ollama"
            custom_prompt: Custom OCR prompt (optional)

        Returns:
            Dict with extracted text and metadata
        """
        try:
            # Load image if path provided
            if image_path:
                pil_image = Image.open(image_path)

            if not pil_image:
                raise ValueError("Must provide either image_path or pil_image")

            # Preprocess image
            processed_image = self.preprocess_image(pil_image)

            # Extract text using vision service
            result = vision_service.extract_text_from_image(
                pil_image=processed_image,
                provider=provider,
                custom_prompt=custom_prompt
            )

            # Add image metadata
            result["image_size"] = pil_image.size
            result["image_mode"] = pil_image.mode
            result["image_format"] = pil_image.format if hasattr(pil_image, 'format') else "Unknown"

            return result

        except Exception as e:
            logger.error(f"Error processing single image: {str(e)}")
            raise

    def process_pdf_with_ocr(
        self,
        pdf_path: str,
        provider: str = "custom",
        custom_prompt: Optional[str] = None,
        process_all_pages: bool = True,
        max_pages: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process PDF file with OCR on each page

        Args:
            pdf_path: Path to PDF file
            provider: "custom" or "ollama"
            custom_prompt: Custom OCR prompt (optional)
            process_all_pages: Process all pages or just first page
            max_pages: Maximum number of pages to process (optional)

        Returns:
            Dict with extracted text per page and combined text
        """
        try:
            # Convert PDF to images
            images = self.pdf_to_images(pdf_path)

            # Limit pages if specified
            if not process_all_pages:
                images = images[:1]
            elif max_pages:
                images = images[:max_pages]

            logger.info(f"Processing {len(images)} pages from PDF")

            # Process each page
            pages_results = []
            all_text = []
            total_tokens = 0

            for idx, image in enumerate(images, start=1):
                logger.info(f"Processing page {idx}/{len(images)}")

                result = self.process_single_image(
                    pil_image=image,
                    provider=provider,
                    custom_prompt=custom_prompt
                )

                pages_results.append({
                    "page_number": idx,
                    "extracted_text": result["extracted_text"],
                    "confidence": result["confidence"],
                    "image_size": result["image_size"],
                    "tokens_used": result.get("tokens_used", 0)
                })

                all_text.append(f"--- Page {idx} ---\n{result['extracted_text']}\n")
                total_tokens += result.get("tokens_used", 0)

            combined_text = "\n".join(all_text)

            return {
                "total_pages": len(images),
                "processed_pages": len(pages_results),
                "pages": pages_results,
                "combined_text": combined_text,
                "total_tokens_used": total_tokens,
                "provider": provider,
                "model": pages_results[0].get("model") if pages_results else "unknown"
            }

        except Exception as e:
            logger.error(f"Error processing PDF with OCR: {str(e)}")
            raise

    def process_file(
        self,
        file_path: str,
        provider: str = "custom",
        custom_prompt: Optional[str] = None,
        process_all_pdf_pages: bool = True,
        max_pdf_pages: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process any supported file (image or PDF) for OCR

        Args:
            file_path: Path to file
            provider: "custom" or "ollama"
            custom_prompt: Custom OCR prompt (optional)
            process_all_pdf_pages: For PDFs, process all pages or just first
            max_pdf_pages: Maximum PDF pages to process (optional)

        Returns:
            Dict with OCR results and metadata
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            ext = Path(file_path).suffix.lower()

            if not self.is_supported_format(file_path):
                raise ValueError(f"Unsupported file format: {ext}")

            # Process based on file type
            if ext == '.pdf':
                result = self.process_pdf_with_ocr(
                    pdf_path=file_path,
                    provider=provider,
                    custom_prompt=custom_prompt,
                    process_all_pages=process_all_pdf_pages,
                    max_pages=max_pdf_pages
                )
                result["file_type"] = "pdf"
            else:
                # Image file
                result = self.process_single_image(
                    image_path=file_path,
                    provider=provider,
                    custom_prompt=custom_prompt
                )
                result["file_type"] = "image"

            # Add common metadata
            result["file_name"] = Path(file_path).name
            result["file_size"] = os.path.getsize(file_path)
            result["file_extension"] = ext

            return result

        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            raise

    def batch_process_files(
        self,
        file_paths: List[str],
        provider: str = "custom",
        custom_prompt: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Batch process multiple files for OCR

        Args:
            file_paths: List of file paths
            provider: "custom" or "ollama"
            custom_prompt: Custom OCR prompt (optional)

        Returns:
            List of OCR results (one per file)
        """
        results = []

        for file_path in file_paths:
            try:
                result = self.process_file(
                    file_path=file_path,
                    provider=provider,
                    custom_prompt=custom_prompt
                )
                result["status"] = "success"
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
                results.append({
                    "file_name": Path(file_path).name,
                    "status": "failed",
                    "error": str(e)
                })

        return results

# Singleton instance
ocr_processor = OCRProcessor()
