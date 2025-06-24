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
from typing import List, Optional, Dict, Any

from fastapi import (APIRouter, BackgroundTasks, Depends, File, HTTPException,
                     Query, UploadFile)
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.v2.exceptions import BadRequestError, UnprocessableEntityError
from backend.core.rag_document_processor import rag_document_processor
from backend.core.rag_integration import rag_integration
from backend.core.vector_store import vector_store
from backend.infrastructure.database.database import get_db
from backend.schemas.rag_schemas import (RAGDocumentInfo, RAGQueryRequest,
                                         RAGQueryResponse, RAGUploadResponse)

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
    Upload document to RAG system
    """
    try:
        if not file.filename:
            raise BadRequestError("File has no name")
        # Sprawdzenie typu pliku
        allowed_extensions = {".pdf", ".txt", ".docx", ".md", ".rtf"}
        file_extension = os.path.splitext(file.filename)[1].lower()

        if file_extension not in allowed_extensions:
            raise BadRequestError(
                message="Invalid file type",
                details={
                    "filename": file.filename,
                    "allowed_extensions": list(allowed_extensions),
                },
            )

        # Zapisz plik tymczasowo
        temp_dir = Path("/tmp/foodsave_uploads")
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_file_path = str(temp_dir / f"{uuid.uuid4()}_{file.filename}")

        with open(temp_file_path, "wb") as f:
            f.write(await file.read())

        # Przetwarzanie dokumentu w tle
        background_tasks.add_task(
            process_document_background,
            temp_file_path,
            file.filename,
            description or "",
            tags or [],
            directory_path,
        )

        return RAGUploadResponse(
            success=True,
            message="Document upload started.",
            filename=file.filename,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        raise UnprocessableEntityError(
            message="Failed to upload document", details={"error": str(e)}
        )


async def process_document_background(
    file_path: str,
    filename: str,
    description: Optional[str],
    tags: List[str],
    directory_path: Optional[str],
) -> None:
    """Background task to process uploaded document"""
    try:
        # Przygotowanie metadanych
        metadata = {
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
                "message": "Unexpected error syncing database",
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
) -> JSONResponse:
    """
    Search documents in the RAG system
    """
    try:
        results = await rag_integration.search_documents_in_rag(
            query, k, filter_type, min_similarity
        )
        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Search completed successfully",
                "data": results,
            },
        )

    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=None)
async def get_rag_stats() -> JSONResponse:
    """
    Get RAG system statistics
    """
    try:
        stats = await rag_integration.get_rag_stats()
        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "RAG statistics retrieved successfully",
                "data": stats,
            },
        )
    except Exception as e:
        logger.error(f"Error retrieving RAG stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{source_id}", response_model=None)
async def delete_document(source_id: str) -> JSONResponse:
    """
    Delete a document from the RAG system by source ID
    """
    try:
        success = await rag_integration.delete_document_from_rag(source_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return JSONResponse(
            status_code=200, content={"message": "Document deleted successfully"}
        )
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-directory", response_model=None)
async def process_directory(
    directory_path: str = Query(..., description="Path to directory to process"),
    file_extensions: Optional[str] = Query(
        None, description="Comma-separated file extensions"
    ),
    recursive: bool = Query(True, description="Process subdirectories"),
) -> JSONResponse:
    """
    Process all documents in a given directory and add them to RAG
    """
    try:
        # Ensure directory exists
        if not os.path.isdir(directory_path):
            raise BadRequestError(f"Directory not found: {directory_path}")

        # Process files in background
        background_tasks = BackgroundTasks()  # type: ignore
        count = 0
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file_extensions and not any(
                    file.endswith(ext) for ext in file_extensions.split(",")
                ):
                    continue
                file_path = os.path.join(root, file)
                background_tasks.add_task(
                    process_document_background,
                    file_path,
                    file,
                    None,
                    [],
                    directory_path,
                )
                count += 1
            if not recursive:
                break

        if count == 0:
            return JSONResponse(
                status_code=200,
                content={
                    "message": "No documents found to process in the specified directory."
                },
            )
        return JSONResponse(
            status_code=200,
            content={
                "message": f"Started processing {count} documents from {directory_path}"
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing directory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents", response_model=List[RAGDocumentInfo])
async def list_rag_documents(
    db: AsyncSession = Depends(get_db),
) -> List[RAGDocumentInfo]:
    """
    List all RAG documents with their metadata
    """
    try:
        documents = await rag_integration.list_rag_documents(db)
        return documents
    except Exception as e:
        logger.error(f"Error listing RAG documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=RAGQueryResponse)
async def query_rag(
    request: RAGQueryRequest, db: AsyncSession = Depends(get_db)
) -> RAGQueryResponse:
    """
    Query the RAG system
    """
    try:
        response = await rag_integration.query_rag(request.question, db)
        return RAGQueryResponse(
            success=True,
            answer=response.answer,
            sources=response.sources,
            confidence=response.confidence,
        )
    except Exception as e:
        logger.error(f"Error querying RAG system: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{document_id}")
async def delete_rag_document(
    document_id: str, db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Delete a specific RAG document by ID
    """
    try:
        success = await rag_integration.delete_rag_document_by_id(document_id, db)
        if success:
            return {"message": "Document deleted successfully"}
        raise HTTPException(status_code=404, detail="Document not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting RAG document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/directories", response_model=List[str])
async def list_rag_directories() -> List[str]:
    """
    List all known RAG directories
    """
    try:
        directories = await rag_integration.list_rag_directories()
        return directories
    except Exception as e:
        logger.error(f"Error listing RAG directories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-directory", response_model=Dict[str, str])
async def create_rag_directory(
    directory_path: str = Query(..., description="Path of the directory to create")
) -> Dict[str, str]:
    """
    Create a new RAG directory
    """
    try:
        await rag_integration.create_rag_directory(directory_path)
        return {"message": f"Directory {directory_path} created successfully"}
    except Exception as e:
        logger.error(f"Error creating RAG directory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/documents/{document_id}/move", response_model=Dict[str, str])
async def move_document(
    document_id: str,
    new_directory_path: str = Query(
        ..., description="New directory path for the document"
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    """
    Move a RAG document to a new directory
    """
    try:
        success = await rag_integration.move_rag_document(
            document_id, new_directory_path, db
        )
        if success:
            return {"message": "Document moved successfully"}
        raise HTTPException(status_code=404, detail="Document not found or move failed")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error moving document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/bulk-move", response_model=Dict[str, str])
async def bulk_move_documents(
    document_ids: List[str] = Query(..., description="List of document IDs to move"),
    new_directory_path: str = Query(
        ..., description="New directory path for the documents"
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    """
    Move multiple RAG documents to a new directory
    """
    try:
        count = await rag_integration.bulk_move_rag_documents(
            document_ids, new_directory_path, db
        )
        return {"message": f"Moved {count} documents successfully"}
    except Exception as e:
        logger.error(f"Error bulk moving documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/bulk-delete", response_model=Dict[str, str])
async def bulk_delete_documents(
    document_ids: List[str] = Query(..., description="List of document IDs to delete"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    """
    Delete multiple RAG documents by ID
    """
    try:
        count = await rag_integration.bulk_delete_rag_documents(document_ids, db)
        return {"message": f"Deleted {count} documents successfully"}
    except Exception as e:
        logger.error(f"Error bulk deleting documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/directories/{directory_path}", response_model=Dict[str, str])
async def delete_rag_directory(
    directory_path: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    """
    Delete a RAG directory and all its associated documents
    """
    try:
        count = await rag_integration.delete_rag_directory(directory_path, db)
        return {"message": f"Deleted directory {directory_path} and {count} documents"}
    except Exception as e:
        logger.error(f"Error deleting RAG directory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/directories/{old_directory_path}/rename", response_model=Dict[str, str])
async def rename_rag_directory(
    old_directory_path: str,
    new_directory_path: str = Query(..., description="New directory path"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    """
    Rename a RAG directory
    """
    try:
        await rag_integration.rename_rag_directory(
            old_directory_path, new_directory_path, db
        )
        return {
            "message": f"Directory {old_directory_path} renamed to {new_directory_path}"
        }
    except Exception as e:
        logger.error(f"Error renaming RAG directory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/directories/{directory_path}/stats", response_model=Dict[str, Any])
async def get_directory_stats(
    directory_path: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get statistics for a specific RAG directory
    """
    try:
        stats = await rag_integration.get_rag_directory_stats(directory_path, db)
        if stats:
            return stats
        raise HTTPException(status_code=404, detail="Directory not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving directory stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def test_upload_and_search(db: AsyncSession = Depends(get_db)):  # type: ignore
    # Test function - not an endpoint
    # Example usage: await test_upload_and_search(db)
    pass


async def test_full_rag_pipeline(  # type: ignore
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...),
    query: str = Query(...),
):
    # Test function - not an endpoint
    # Example usage: await test_full_rag_pipeline(db, File(...), "your query")
    pass


# NOTE: This is a placeholder for actual document ID handling.
# In a real system, you would get the document_id from the processing result
# and use it for subsequent operations.
# document_id = result.get("document_id")  # F841: local variable 'document_id' is assigned to but never used
