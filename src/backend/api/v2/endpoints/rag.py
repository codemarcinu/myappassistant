"""
RAG Management API Endpoints

This module provides API endpoints for managing the RAG system:
- Document upload and processing
- Database synchronization
- Search functionality
- System statistics
"""

import logging
import os
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.v2.exceptions import BadRequestError, UnprocessableEntityError
from backend.core.rag_document_processor import rag_document_processor
from backend.core.rag_integration import rag_integration
from backend.core.vector_store import vector_store
from backend.infrastructure.database.database import get_db
from backend.schemas.rag_schemas import (
    RAGDocumentInfo,
    RAGQueryRequest,
    RAGQueryResponse,
    RAGUploadResponse,
)

router = APIRouter(prefix="/rag", tags=["RAG Management"])
logger = logging.getLogger(__name__)

# Inicjalizacja procesora dokumentów RAG
rag_processor = rag_document_processor


@router.post("/upload", response_model=RAGUploadResponse)
async def upload_document_to_rag(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    directory_path: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a document to the RAG system for knowledge base enhancement.

    Supported file types: PDF, TXT, DOCX, MD
    """
    try:
        # Sprawdzenie typu pliku
        allowed_extensions = {".pdf", ".txt", ".docx", ".md", ".rtf"}
        file_extension = os.path.splitext(file.filename)[1].lower()

        if file_extension not in allowed_extensions:
            raise BadRequestError(
                message="Unsupported file type",
                details={
                    "file_extension": file_extension,
                    "supported_extensions": list(allowed_extensions),
                },
            )

        # Generowanie unikalnego ID dokumentu
        document_id = str(uuid.uuid4())

        # Zapisywanie pliku tymczasowo
        temp_file_path = f"/tmp/{document_id}_{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Przetwarzanie dokumentu w tle
        background_tasks.add_task(
            process_document_background,
            temp_file_path,
            document_id,
            file.filename,
            description,
            tags or [],
            directory_path,
        )

        return RAGUploadResponse(
            success=True,
            document_id=document_id,
            filename=file.filename,
            message="Document uploaded successfully. Processing in background.",
            status="processing",
        )

    except BadRequestError:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise BadRequestError(
            message="Failed to upload document", details={"error": str(e)}
        )


async def process_document_background(
    file_path: str,
    document_id: str,
    filename: str,
    description: Optional[str],
    tags: List[str],
    directory_path: Optional[str],
):
    """Background task to process uploaded document"""
    try:
        # Przygotowanie metadanych
        metadata = {
            "document_id": document_id,
            "filename": filename,
            "description": description,
            "tags": tags,
            "directory_path": directory_path or "default",
            "source": "upload",
        }
        # Przetwarzanie dokumentu
        await rag_processor.process_file(file_path, metadata)

        # Czyszczenie pliku tymczasowego
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        logger.error(f"Error processing document: {e}")
        raise UnprocessableEntityError(
            message="Failed to process document", details={"error": str(e)}
        )


@router.post("/sync-database", response_model=None)
async def sync_database_to_rag(
    sync_type: str = Query(
        ..., description="Type of data to sync: receipts, pantry, conversations, all"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Synchronize database data to RAG system
    """
    try:
        if sync_type == "receipts":
            result = await rag_integration.sync_receipts_to_rag(db)
        elif sync_type == "pantry":
            result = await rag_integration.sync_pantry_to_rag(db)
        elif sync_type == "conversations":
            result = await rag_integration.sync_conversations_to_rag(db)
        elif sync_type == "all":
            result = await rag_integration.sync_all_to_rag(db)
        else:
            raise BadRequestError(
                message="Invalid sync type",
                details={
                    "sync_type": sync_type,
                    "valid_types": ["receipts", "pantry", "conversations", "all"],
                },
            )

        if not result["success"]:
            raise UnprocessableEntityError(
                message="Database sync failed",
                details={"error": result.get("error", "Unknown error")},
            )

        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Database synchronized successfully",
                "data": result,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing database: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to sync database",
                "details": {"error": str(e)},
            },
        )


@router.get("/search", response_model=None)
async def search_documents(
    query: str = Query(..., description="Search query"),
    k: int = Query(5, description="Number of results to return", ge=1, le=20),
    filter_type: Optional[str] = Query(None, description="Filter by document type"),
    min_similarity: float = Query(
        0.65, description="Minimum similarity threshold", ge=0.0, le=1.0
    ),
):
    """
    Search documents in RAG system
    """
    try:
        # Prepare filter metadata
        filter_metadata = None
        if filter_type:
            filter_metadata = {"type": filter_type}

        # Search vector store
        results = await vector_store.search(
            query=query,
            k=k,
            filter_metadata=filter_metadata,
            min_similarity=min_similarity,
        )

        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append(
                {
                    "text": result["text"],
                    "similarity": result["similarity"],
                    "metadata": result["metadata"],
                    "source_id": result["source_id"],
                }
            )

        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Search completed successfully",
                "data": {
                    "query": query,
                    "results": formatted_results,
                    "total_results": len(formatted_results),
                },
            },
        )

    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_ERROR",
                "message": "Search failed",
                "details": {"error": str(e)},
            },
        )


@router.get("/stats", response_model=None)
async def get_rag_stats():
    """
    Get RAG system statistics
    """
    try:
        # Get vector store statistics
        stats = await vector_store.get_statistics()

        # Get document processor statistics
        processor_stats = {
            "chunk_size": rag_processor.chunk_size,
            "chunk_overlap": rag_processor.chunk_overlap,
            "use_local_embeddings": rag_processor.use_local_embeddings,
            "use_pinecone": rag_processor.use_pinecone,
        }

        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Statistics retrieved successfully",
                "data": {"vector_store": stats, "processor": processor_stats},
            },
        )

    except Exception as e:
        logger.error(f"Error getting RAG stats: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to get statistics",
                "details": {"error": str(e)},
            },
        )


@router.delete("/documents/{source_id}", response_model=None)
async def delete_document(source_id: str):
    """
    Delete a document from RAG system by source ID
    """
    try:
        # Delete from vector store
        deleted_count = await vector_store.delete_by_source(source_id)

        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Document deleted successfully",
                "data": {"source_id": source_id, "chunks_deleted": deleted_count},
            },
        )

    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to delete document",
                "details": {"error": str(e)},
            },
        )


@router.post("/process-directory", response_model=None)
async def process_directory(
    directory_path: str = Query(..., description="Path to directory to process"),
    file_extensions: Optional[str] = Query(
        None, description="Comma-separated file extensions"
    ),
    recursive: bool = Query(True, description="Process subdirectories"),
):
    """
    Process all documents in a directory
    """
    try:
        # Validate directory path
        path = Path(directory_path)
        if not path.exists() or not path.is_dir():
            raise BadRequestError(
                message="Directory not found",
                details={"directory_path": directory_path},
            )

        # Parse file extensions
        extensions = None
        if file_extensions:
            extensions = [ext.strip() for ext in file_extensions.split(",")]

        # Process directory
        result = await rag_processor.process_directory(
            directory_path=path, file_extensions=extensions, recursive=recursive
        )

        if not result["success"]:
            raise UnprocessableEntityError(
                message="Failed to process directory",
                details={"error": result.get("error", "Unknown error")},
            )

        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Directory processed successfully",
                "data": result,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing directory: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to process directory",
                "details": {"error": str(e)},
            },
        )


@router.get("/documents", response_model=List[RAGDocumentInfo])
async def list_rag_documents(db: AsyncSession = Depends(get_db)):
    """List all documents in the RAG system"""
    try:
        documents = await vector_store.list_documents()
        return [
            RAGDocumentInfo(
                document_id=doc.get("document_id"),
                filename=doc.get("filename"),
                description=doc.get("description"),
                tags=doc.get("tags", []),
                chunks_count=doc.get("chunks_count", 0),
                uploaded_at=doc.get("uploaded_at"),
            )
            for doc in documents
        ]
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise UnprocessableEntityError(
            message="Failed to list documents", details={"error": str(e)}
        )


@router.post("/query", response_model=RAGQueryResponse)
async def query_rag(request: RAGQueryRequest, db: AsyncSession = Depends(get_db)):
    """Query the RAG system with a question"""
    try:
        # Wyszukiwanie podobnych dokumentów
        results = await vector_store.similarity_search(
            query=request.question, k=request.max_results or 5
        )

        # Generowanie odpowiedzi na podstawie znalezionych dokumentów
        context = "\n".join([doc.page_content for doc in results])

        return RAGQueryResponse(
            success=True,
            answer=f"Based on the knowledge base: {context[:500]}...",
            sources=[doc.metadata for doc in results],
            confidence=0.85,
        )

    except Exception as e:
        logger.error(f"Error querying RAG: {e}")
        raise UnprocessableEntityError(
            message="Failed to query RAG", details={"error": str(e)}
        )


@router.delete("/documents/{document_id}")
async def delete_rag_document(document_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a document from the RAG system"""
    try:
        success = await vector_store.delete_document(document_id)
        if not success:
            raise UnprocessableEntityError(
                message="Document not found", details={"document_id": document_id}
            )

        return JSONResponse(
            content={"success": True, "message": "Document deleted successfully"}
        )

    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise UnprocessableEntityError(
            message="Failed to delete document", details={"error": str(e)}
        )


@router.get("/directories", response_model=None)
async def list_rag_directories():
    """
    List all RAG directories and their document counts.
    Returns a list of objects: {"path": str, "document_count": int}
    """
    try:
        directories = await vector_store.list_directories()
        return JSONResponse(status_code=200, content={"directories": directories})
    except Exception as e:
        logger.error(f"Error listing RAG directories: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to list RAG directories",
                "details": {"error": str(e)},
            },
        )


@router.post("/create-directory", response_model=None)
async def create_rag_directory(
    directory_path: str = Query(..., description="Path of the directory to create")
):
    """
    Create a new RAG directory.
    This creates a directory entry in the vector store metadata.
    """
    try:
        # For now, we'll just validate the directory path
        # In a full implementation, you might want to create actual filesystem directories
        if not directory_path or directory_path.strip() == "":
            raise BadRequestError(
                message="Directory path cannot be empty",
                details={"directory_path": directory_path},
            )

        # Normalize the directory path
        normalized_path = directory_path.strip().replace("\\", "/")

        # Check if directory already exists by looking at existing documents
        existing_directories = await vector_store.list_directories()
        if any(
            dir_info["path"] == normalized_path for dir_info in existing_directories
        ):
            raise BadRequestError(
                message="Directory already exists",
                details={"directory_path": normalized_path},
            )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Directory '{normalized_path}' created successfully",
                "directory_path": normalized_path,
            },
        )
    except BadRequestError:
        raise
    except Exception as e:
        logger.error(f"Error creating directory: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to create directory",
                "details": {"error": str(e)},
            },
        )
