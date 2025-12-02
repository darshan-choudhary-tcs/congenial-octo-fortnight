"""
Document processing utilities for RAG
"""
from typing import List, Dict, Any, Optional
import os
from pathlib import Path
import pypdf
from docx import Document as DocxDocument
import pandas as pd
from loguru import logger

from app.config import settings

class DocumentProcessor:
    """Process various document formats"""

    @staticmethod
    def extract_text_from_pdf(file_path: str) -> tuple[str, Dict[str, Any]]:
        """
        Extract text from PDF file

        Returns:
            Tuple of (text content, metadata)
        """
        try:
            text_content = []
            metadata = {"pages": 0, "format": "pdf"}

            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                metadata["pages"] = len(pdf_reader.pages)

                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    if text.strip():
                        text_content.append(text)

            full_text = "\n\n".join(text_content)
            logger.info(f"Extracted {len(full_text)} characters from PDF with {metadata['pages']} pages")

            return full_text, metadata

        except Exception as e:
            logger.error(f"Failed to process PDF: {e}")
            raise ValueError(f"PDF processing failed: {str(e)}")

    @staticmethod
    def extract_text_from_docx(file_path: str) -> tuple[str, Dict[str, Any]]:
        """
        Extract text from DOCX file

        Returns:
            Tuple of (text content, metadata)
        """
        try:
            doc = DocxDocument(file_path)
            text_content = []
            metadata = {"paragraphs": 0, "format": "docx"}

            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)

            metadata["paragraphs"] = len(text_content)
            full_text = "\n\n".join(text_content)

            logger.info(f"Extracted {len(full_text)} characters from DOCX with {metadata['paragraphs']} paragraphs")

            return full_text, metadata

        except Exception as e:
            logger.error(f"Failed to process DOCX: {e}")
            raise ValueError(f"DOCX processing failed: {str(e)}")

    @staticmethod
    def extract_text_from_txt(file_path: str) -> tuple[str, Dict[str, Any]]:
        """
        Extract text from TXT file

        Returns:
            Tuple of (text content, metadata)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()

            metadata = {
                "format": "txt",
                "lines": text.count('\n') + 1
            }

            logger.info(f"Extracted {len(text)} characters from TXT with {metadata['lines']} lines")

            return text, metadata

        except Exception as e:
            logger.error(f"Failed to process TXT: {e}")
            raise ValueError(f"TXT processing failed: {str(e)}")

    @staticmethod
    def extract_text_from_csv(file_path: str) -> tuple[str, Dict[str, Any]]:
        """
        Extract text from CSV file (converts to readable format)

        Returns:
            Tuple of (text content, metadata)
        """
        try:
            df = pd.read_csv(file_path)

            # Convert DataFrame to text representation
            text_parts = []

            # Add column headers
            text_parts.append("Column Headers: " + ", ".join(df.columns.tolist()))
            text_parts.append("\n")

            # Add summary statistics for numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if numeric_cols:
                text_parts.append("Numeric Column Statistics:")
                text_parts.append(df[numeric_cols].describe().to_string())
                text_parts.append("\n")

            # Add first few rows as context
            text_parts.append("Sample Data (first 10 rows):")
            text_parts.append(df.head(10).to_string())

            # Add value counts for categorical columns
            categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
            if categorical_cols:
                text_parts.append("\nCategorical Column Value Distributions:")
                for col in categorical_cols[:3]:  # Limit to first 3 categorical columns
                    value_counts = df[col].value_counts().head(5)
                    text_parts.append(f"\n{col}: {value_counts.to_dict()}")

            full_text = "\n".join(text_parts)

            metadata = {
                "format": "csv",
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist(),
                "numeric_columns": numeric_cols,
                "categorical_columns": categorical_cols
            }

            logger.info(f"Extracted {len(full_text)} characters from CSV with {metadata['rows']} rows and {metadata['columns']} columns")

            return full_text, metadata

        except Exception as e:
            logger.error(f"Failed to process CSV: {e}")
            raise ValueError(f"CSV processing failed: {str(e)}")

    @classmethod
    def process_document(cls, file_path: str) -> tuple[str, Dict[str, Any]]:
        """
        Process document based on file extension

        Args:
            file_path: Path to document

        Returns:
            Tuple of (text content, metadata)
        """
        file_ext = Path(file_path).suffix.lower()

        processors = {
            '.pdf': cls.extract_text_from_pdf,
            '.docx': cls.extract_text_from_docx,
            '.txt': cls.extract_text_from_txt,
            '.csv': cls.extract_text_from_csv
        }

        processor = processors.get(file_ext)
        if processor is None:
            raise ValueError(f"Unsupported file format: {file_ext}")

        return processor(file_path)

class TextChunker:
    """Split text into chunks for embedding"""

    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: int = None,
        chunk_overlap: int = None,
        separators: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Split text into chunks with overlap

        Args:
            text: Text to split
            chunk_size: Maximum chunk size
            chunk_overlap: Overlap between chunks
            separators: List of separators to use (in order of preference)

        Returns:
            List of chunk dictionaries with content and metadata
        """
        if chunk_size is None:
            chunk_size = settings.CHUNK_SIZE
        if chunk_overlap is None:
            chunk_overlap = settings.CHUNK_OVERLAP
        if separators is None:
            separators = ["\n\n", "\n", ". ", " ", ""]

        chunks = []
        chunk_index = 0

        # Simple recursive splitting
        def split_text_recursive(text: str, separator_index: int = 0):
            nonlocal chunk_index

            if len(text) <= chunk_size:
                if text.strip():
                    chunks.append({
                        "content": text.strip(),
                        "chunk_index": chunk_index,
                        "num_tokens": len(text.split()),
                        "char_count": len(text)
                    })
                    chunk_index += 1
                return

            if separator_index >= len(separators):
                # Force split at chunk_size
                chunks.append({
                    "content": text[:chunk_size].strip(),
                    "chunk_index": chunk_index,
                    "num_tokens": len(text[:chunk_size].split()),
                    "char_count": chunk_size
                })
                chunk_index += 1
                remaining = text[chunk_size - chunk_overlap:]
                if remaining:
                    split_text_recursive(remaining, 0)
                return

            separator = separators[separator_index]
            if not separator:
                # Force split
                chunks.append({
                    "content": text[:chunk_size].strip(),
                    "chunk_index": chunk_index,
                    "num_tokens": len(text[:chunk_size].split()),
                    "char_count": chunk_size
                })
                chunk_index += 1
                remaining = text[chunk_size - chunk_overlap:]
                if remaining:
                    split_text_recursive(remaining, 0)
                return

            parts = text.split(separator)
            current_chunk = ""

            for part in parts:
                if len(current_chunk) + len(separator) + len(part) <= chunk_size:
                    current_chunk += (separator if current_chunk else "") + part
                else:
                    if current_chunk:
                        split_text_recursive(current_chunk, separator_index + 1)
                    current_chunk = part

            if current_chunk:
                split_text_recursive(current_chunk, separator_index + 1)

        split_text_recursive(text)

        logger.info(f"Split text into {len(chunks)} chunks (avg size: {sum(c['char_count'] for c in chunks) // len(chunks) if chunks else 0} chars)")

        return chunks
