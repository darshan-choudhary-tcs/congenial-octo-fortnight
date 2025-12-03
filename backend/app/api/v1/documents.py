"""
Document management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
import os
import uuid
from loguru import logger

from app.database.db import get_db
from app.database.models import User, Document, DocumentChunk
from app.auth.security import get_current_active_user, require_permission, require_role
from app.rag.document_processor import DocumentProcessor, TextChunker
from app.rag.ocr_processor import ocr_processor
from app.services.vector_store import vector_store_service
from app.config import settings

router = APIRouter()

class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    title: Optional[str]
    is_processed: bool
    processing_status: str
    num_chunks: int
    uploaded_at: str
    scope: Optional[str] = "user"

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    provider: str = Form("custom"),
    scope: str = Form("user"),
    current_user: User = Depends(require_permission("documents:create")),
    db: Session = Depends(get_db)
):
    """Upload and process a document (user scope)"""

    logger.info(f"Document upload started - File: {file.filename}, Provider: {provider}")

    try:
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {settings.ALLOWED_EXTENSIONS}"
            )

        # Save file
        file_uuid = str(uuid.uuid4())
        file_path = os.path.join(settings.UPLOAD_DIR, f"{file_uuid}{file_ext}")

        with open(file_path, "wb") as f:
            content = await file.read()
            if len(content) > settings.MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE} bytes"
                )
            f.write(content)

        # Create document record
        document = Document(
            filename=file.filename,
            file_path=file_path,
            file_type=file_ext.replace('.', ''),
            file_size=len(content),
            title=title or file.filename,
            description=description,
            category=category,
            uploaded_by_id=current_user.id,
            scope=scope,
            processing_status="processing"
        )
        db.add(document)
        db.flush()

        # Process document
        try:
            # Extract text
            text_content, metadata = DocumentProcessor.process_document(file_path)

            # Chunk text
            chunks = TextChunker.chunk_text(text_content)

            # Generate embeddings and store in vector DB
            chunk_texts = [chunk['content'] for chunk in chunks]
            chunk_metadatas = [
                {
                    'document_id': document.uuid,
                    'document_title': document.title,
                    'chunk_index': chunk['chunk_index'],
                    'file_type': document.file_type,
                    'category': category or 'general',
                    'user_id': str(current_user.id),
                    'uploaded_by_id': str(current_user.id),
                    'scope': scope
                }
                for chunk in chunks
            ]

            # Add to vector store
            logger.info(f"Adding documents to vector store with provider: {provider}, scope: {scope}, user: {current_user.id}")
            chunk_ids = await vector_store_service.add_documents(
                texts=chunk_texts,
                metadatas=chunk_metadatas,
                provider=provider,
                scope=scope,
                user_id=current_user.id
            )

            # Save chunks to database
            for chunk, chunk_id in zip(chunks, chunk_ids):
                doc_chunk = DocumentChunk(
                    document_id=document.id,
                    content=chunk['content'],
                    chunk_index=chunk['chunk_index'],
                    num_tokens=chunk['num_tokens'],
                    embedding_id=chunk_id
                )
                db.add(doc_chunk)

            # Update document
            document.is_processed = True
            document.processing_status = "completed"
            document.num_chunks = len(chunks)
            document.num_tokens = sum(chunk['num_tokens'] for chunk in chunks)

            db.commit()
            db.refresh(document)

            logger.info(f"Document processed: {file.filename} ({len(chunks)} chunks)")

            return DocumentResponse(
                id=document.uuid,
                filename=document.filename,
                file_type=document.file_type,
                file_size=document.file_size,
                title=document.title,
                is_processed=document.is_processed,
                processing_status=document.processing_status,
                num_chunks=document.num_chunks,
                uploaded_at=document.uploaded_at.isoformat(),
                scope=document.scope
            )

        except Exception as e:
            document.processing_status = "failed"
            document.error_message = str(e)
            db.commit()
            logger.error(f"Document processing failed: {e}")

            # Provide helpful error message for authentication issues
            error_detail = str(e)
            if "RBAC: access denied" in error_detail or "access denied" in error_detail.lower():
                error_detail = (
                    "Authentication failed with the custom LLM API. "
                    "Please check your CUSTOM_LLM_API_KEY in the .env file. "
                    "Alternatively, switch to Ollama by using provider='ollama' and ensure Ollama is running locally."
                )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Document processing failed: {error_detail}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    current_user: User = Depends(require_permission("documents:read")),
    db: Session = Depends(get_db)
):
    """List documents - admins see all, users see only their own + global"""

    # Check if user is admin
    is_admin = any(role.name == "admin" for role in current_user.roles)

    if is_admin:
        # Admins see all documents
        documents = db.query(Document).order_by(Document.uploaded_at.desc()).all()
    else:
        # Regular users see only their own documents + global documents
        documents = db.query(Document).filter(
            (Document.uploaded_by_id == current_user.id) | (Document.scope == "global")
        ).order_by(Document.uploaded_at.desc()).all()

    return [
        DocumentResponse(
            id=doc.uuid,
            filename=doc.filename,
            file_type=doc.file_type,
            file_size=doc.file_size,
            title=doc.title,
            is_processed=doc.is_processed,
            processing_status=doc.processing_status,
            num_chunks=doc.num_chunks,
            uploaded_at=doc.uploaded_at.isoformat(),
            scope=doc.scope or "user"
        )
        for doc in documents
    ]

@router.get("/{document_id}")
async def get_document(
    document_id: str,
    current_user: User = Depends(require_permission("documents:read")),
    db: Session = Depends(get_db)
):
    """Get document details"""

    document = db.query(Document).filter(Document.uuid == document_id).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    return {
        'id': document.uuid,
        'filename': document.filename,
        'file_type': document.file_type,
        'file_size': document.file_size,
        'title': document.title,
        'description': document.description,
        'category': document.category,
        'is_processed': document.is_processed,
        'processing_status': document.processing_status,
        'num_chunks': document.num_chunks,
        'num_tokens': document.num_tokens,
        'uploaded_at': document.uploaded_at.isoformat(),
        'uploaded_by': document.uploaded_by.username if document.uploaded_by else None,
        'scope': document.scope or 'user'
    }

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    provider: str = "custom",
    current_user: User = Depends(require_permission("documents:delete")),
    db: Session = Depends(get_db)
):
    """Delete a document"""

    document = db.query(Document).filter(Document.uuid == document_id).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Delete from vector store
    chunk_ids = [chunk.embedding_id for chunk in document.chunks if chunk.embedding_id]
    if chunk_ids:
        await vector_store_service.delete_documents(
            chunk_ids,
            provider,
            scope=document.scope or "user",
            user_id=document.uploaded_by_id
        )

    # Delete file
    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    # Delete from database
    db.delete(document)
    db.commit()

    logger.info(f"Document deleted: {document.filename}")

    return {"message": "Document deleted successfully"}

@router.post("/global/upload", response_model=DocumentResponse)
async def upload_global_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    provider: str = Form("custom"),
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """Upload and process a document to global knowledge base (admin only)"""

    logger.info(f"Global document upload started - File: {file.filename}, Provider: {provider}, Admin: {current_user.username}")

    try:
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {settings.ALLOWED_EXTENSIONS}"
            )

        # Save file
        file_uuid = str(uuid.uuid4())
        file_path = os.path.join(settings.UPLOAD_DIR, f"{file_uuid}{file_ext}")

        with open(file_path, "wb") as f:
            content = await file.read()
            if len(content) > settings.MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE} bytes"
                )
            f.write(content)

        # Create document record with global scope
        document = Document(
            filename=file.filename,
            file_path=file_path,
            file_type=file_ext.replace('.', ''),
            file_size=len(content),
            title=title or file.filename,
            description=description,
            category=category,
            uploaded_by_id=current_user.id,
            scope="global",
            processing_status="processing"
        )
        db.add(document)
        db.flush()

        # Process document
        try:
            # Extract text
            text_content, metadata = DocumentProcessor.process_document(file_path)

            # Chunk text
            chunks = TextChunker.chunk_text(text_content)

            # Generate embeddings and store in vector DB (global collection)
            chunk_texts = [chunk['content'] for chunk in chunks]
            chunk_metadatas = [
                {
                    'document_id': document.uuid,
                    'document_title': document.title,
                    'chunk_index': chunk['chunk_index'],
                    'file_type': document.file_type,
                    'category': category or 'general',
                    'uploaded_by_id': str(current_user.id),
                    'scope': 'global'
                }
                for chunk in chunks
            ]

            # Add to vector store (global collection, no user_id)
            logger.info(f"Adding documents to GLOBAL vector store with provider: {provider}")
            chunk_ids = await vector_store_service.add_documents(
                texts=chunk_texts,
                metadatas=chunk_metadatas,
                provider=provider,
                scope="global",
                user_id=None
            )

            # Save chunks to database
            for chunk, chunk_id in zip(chunks, chunk_ids):
                doc_chunk = DocumentChunk(
                    document_id=document.id,
                    content=chunk['content'],
                    chunk_index=chunk['chunk_index'],
                    num_tokens=chunk['num_tokens'],
                    embedding_id=chunk_id
                )
                db.add(doc_chunk)

            # Update document
            document.is_processed = True
            document.processing_status = "completed"
            document.num_chunks = len(chunks)
            document.num_tokens = sum(chunk['num_tokens'] for chunk in chunks)

            db.commit()
            db.refresh(document)

            logger.info(f"Global document processed: {file.filename} ({len(chunks)} chunks)")

            return DocumentResponse(
                id=document.uuid,
                filename=document.filename,
                file_type=document.file_type,
                file_size=document.file_size,
                title=document.title,
                is_processed=document.is_processed,
                processing_status=document.processing_status,
                num_chunks=document.num_chunks,
                uploaded_at=document.uploaded_at.isoformat(),
                scope="global"
            )

        except Exception as e:
            document.processing_status = "failed"
            document.error_message = str(e)
            db.commit()
            logger.error(f"Global document processing failed: {e}")

            # Provide helpful error message for authentication issues
            error_detail = str(e)
            if "RBAC: access denied" in error_detail or "access denied" in error_detail.lower():
                error_detail = (
                    "Authentication failed with the custom LLM API. "
                    "Please check your CUSTOM_LLM_API_KEY in the .env file. "
                    "Alternatively, switch to Ollama by using provider='ollama' and ensure Ollama is running locally."
                )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Global document processing failed: {error_detail}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Global document upload failed: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


class OCRRequest(BaseModel):
    provider: str = "custom"
    process_all_pages: bool = True
    max_pages: Optional[int] = None
    custom_prompt: Optional[str] = None
    save_to_vector_store: bool = False
    title: Optional[str] = None
    scope: str = "user"


class OCRPageResult(BaseModel):
    page_number: int
    extracted_text: str
    confidence: float
    image_size: List[int]
    tokens_used: int


class OCRResponse(BaseModel):
    file_name: str
    file_type: str
    file_size: int
    provider: str
    model: str
    extracted_text: str
    total_tokens_used: int

    # For PDFs
    total_pages: Optional[int] = None
    processed_pages: Optional[int] = None
    pages: Optional[List[OCRPageResult]] = None

    # For images
    image_size: Optional[List[int]] = None
    image_mode: Optional[str] = None
    confidence: Optional[float] = None

    # Optional: Document ID if saved to vector store
    document_id: Optional[str] = None


@router.post("/ocr", response_model=OCRResponse)
async def perform_ocr(
    file: UploadFile = File(...),
    provider: str = Form("custom"),
    process_all_pages: bool = Form(True),
    max_pages: Optional[int] = Form(None),
    custom_prompt: Optional[str] = Form(None),
    save_to_vector_store: bool = Form(False),
    title: Optional[str] = Form(None),
    scope: str = Form("user"),
    current_user: User = Depends(require_permission("documents:create")),
    db: Session = Depends(get_db)
):
    """
    Perform OCR on uploaded image or PDF using vision models

    Args:
        file: Image or PDF file
        provider: "custom" (Azure Vision LLM) or "ollama" (Llama Vision)
        process_all_pages: For PDFs, process all pages or just first
        max_pages: Maximum number of PDF pages to process
        custom_prompt: Custom prompt for OCR extraction
        save_to_vector_store: Whether to save extracted text to vector store
        title: Title for document if saving to vector store
        scope: "user" or "global" (requires admin for global)

    Returns:
        OCRResponse with extracted text and metadata
    """
    logger.info(f"OCR request - File: {file.filename}, Provider: {provider}")

    try:
        # Validate provider
        if provider not in ["custom", "ollama"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provider must be 'custom' or 'ollama'"
            )

        # Validate scope (only admins can use global scope)
        if scope == "global" and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can use global scope"
            )

        # Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        if not ocr_processor.is_supported_format(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format: {file_ext}. Supported: {settings.OCR_SUPPORTED_FORMATS}"
            )

        # Validate file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning

        if file_size > settings.OCR_MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed ({settings.OCR_MAX_FILE_SIZE} bytes)"
            )

        # Save uploaded file temporarily
        file_id = str(uuid.uuid4())
        file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}{file_ext}")

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        logger.info(f"File saved temporarily: {file_path}")

        try:
            # Process file with OCR
            ocr_result = ocr_processor.process_file(
                file_path=file_path,
                provider=provider,
                custom_prompt=custom_prompt,
                process_all_pdf_pages=process_all_pages,
                max_pdf_pages=max_pages
            )

            logger.info(f"OCR processing completed for {file.filename}")

            # Prepare response based on file type
            if ocr_result["file_type"] == "pdf":
                response_data = {
                    "file_name": file.filename,
                    "file_type": "pdf",
                    "file_size": file_size,
                    "provider": provider,
                    "model": ocr_result.get("model", "unknown"),
                    "extracted_text": ocr_result["combined_text"],
                    "total_tokens_used": ocr_result["total_tokens_used"],
                    "total_pages": ocr_result["total_pages"],
                    "processed_pages": ocr_result["processed_pages"],
                    "pages": [
                        OCRPageResult(
                            page_number=page["page_number"],
                            extracted_text=page["extracted_text"],
                            confidence=page["confidence"],
                            image_size=list(page["image_size"]),
                            tokens_used=page["tokens_used"]
                        )
                        for page in ocr_result["pages"]
                    ]
                }
            else:
                # Image file
                response_data = {
                    "file_name": file.filename,
                    "file_type": "image",
                    "file_size": file_size,
                    "provider": provider,
                    "model": ocr_result.get("model", "unknown"),
                    "extracted_text": ocr_result["extracted_text"],
                    "total_tokens_used": ocr_result.get("tokens_used", 0),
                    "image_size": list(ocr_result["image_size"]),
                    "image_mode": ocr_result["image_mode"],
                    "confidence": ocr_result["confidence"]
                }

            # Optionally save to vector store
            document_id = None
            if save_to_vector_store:
                logger.info(f"Saving OCR result to vector store with scope: {scope}")

                # Create document record
                document = Document(
                    uuid=str(uuid.uuid4()),
                    user_id=current_user.uuid if scope == "user" else None,
                    filename=file.filename,
                    file_type=file_ext,
                    file_size=file_size,
                    title=title or f"OCR: {file.filename}",
                    scope=scope,
                    processing_status="processing"
                )
                db.add(document)
                db.commit()

                try:
                    # Chunk the extracted text
                    text_chunker = TextChunker()
                    chunks = text_chunker.chunk_text(response_data["extracted_text"])

                    logger.info(f"Created {len(chunks)} chunks from OCR text")

                    # Generate embeddings and store
                    collection_name = f"{provider}_{scope}"
                    vector_store_service.add_documents(
                        collection_name=collection_name,
                        texts=[chunk["content"] for chunk in chunks],
                        metadatas=[
                            {
                                "document_id": document.uuid,
                                "user_id": current_user.uuid if scope == "user" else None,
                                "filename": file.filename,
                                "chunk_index": chunk["chunk_index"],
                                "source": "ocr",
                                "scope": scope
                            }
                            for chunk in chunks
                        ],
                        provider=provider
                    )

                    # Update document record
                    document.is_processed = True
                    document.processing_status = "completed"
                    document.num_chunks = len(chunks)
                    db.commit()

                    document_id = document.uuid
                    logger.info(f"OCR result saved to vector store: {document_id}")

                except Exception as e:
                    document.processing_status = "failed"
                    document.error_message = str(e)
                    db.commit()
                    logger.error(f"Failed to save OCR result to vector store: {e}")
                    raise

            response_data["document_id"] = document_id

            return OCRResponse(**response_data)

        finally:
            # Clean up temporary file
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Temporary file removed: {file_path}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR processing failed: {str(e)}"
        )
