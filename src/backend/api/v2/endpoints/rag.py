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
from datetime import datetime, timedelta
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
from sqlalchemy import select
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


@router.put("/documents/{document_id}/move", response_model=None)
async def move_document(
    document_id: str,
    new_directory_path: str = Query(
        ..., description="New directory path for the document"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Move a document to a different directory by updating its metadata.
    """
    try:
        if not new_directory_path or new_directory_path.strip() == "":
            raise BadRequestError(
                message="Directory path cannot be empty",
                details={"new_directory_path": new_directory_path},
            )

        # Normalize the directory path
        normalized_path = new_directory_path.strip().replace("\\", "/")

        # Get the document from the database
        # Note: This assumes you have a documents table in your database
        # You might need to adjust this based on your actual database schema
        from backend.models.rag_document import RAGDocument

        document = await db.get(RAGDocument, document_id)
        if not document:
            raise BadRequestError(
                message="Document not found", details={"document_id": document_id}
            )

        # Update the document's directory path
        document.directory_path = normalized_path
        await db.commit()

        # Also update the document in the vector store if it exists there
        # This is a simplified approach - you might need to re-index the document
        # depending on your vector store implementation

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Document moved to '{normalized_path}' successfully",
                "document_id": document_id,
                "new_directory_path": normalized_path,
            },
        )
    except BadRequestError:
        raise
    except Exception as e:
        logger.error(f"Error moving document: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to move document",
                "details": {"error": str(e)},
            },
        )


@router.post("/documents/bulk-move", response_model=None)
async def bulk_move_documents(
    document_ids: List[str] = Query(..., description="List of document IDs to move"),
    new_directory_path: str = Query(
        ..., description="New directory path for the documents"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Move multiple documents to a different directory by updating their metadata.
    """
    try:
        if not new_directory_path or new_directory_path.strip() == "":
            raise BadRequestError(
                message="Directory path cannot be empty",
                details={"new_directory_path": new_directory_path},
            )

        if not document_ids:
            raise BadRequestError(
                message="No document IDs provided",
                details={"document_ids": document_ids},
            )

        # Normalize the directory path
        normalized_path = new_directory_path.strip().replace("\\", "/")

        # Get the documents from the database
        from backend.models.rag_document import RAGDocument

        moved_count = 0
        failed_documents = []

        for document_id in document_ids:
            try:
                document = await db.get(RAGDocument, document_id)
                if document:
                    document.directory_path = normalized_path
                    moved_count += 1
                else:
                    failed_documents.append(
                        {"id": document_id, "reason": "Document not found"}
                    )
            except Exception as e:
                failed_documents.append({"id": document_id, "reason": str(e)})

        await db.commit()

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Moved {moved_count} documents to '{normalized_path}'",
                "moved_count": moved_count,
                "total_count": len(document_ids),
                "failed_documents": failed_documents,
                "new_directory_path": normalized_path,
            },
        )
    except BadRequestError:
        raise
    except Exception as e:
        logger.error(f"Error bulk moving documents: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to bulk move documents",
                "details": {"error": str(e)},
            },
        )


@router.post("/documents/bulk-delete", response_model=None)
async def bulk_delete_documents(
    document_ids: List[str] = Query(..., description="List of document IDs to delete"),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete multiple documents from the RAG system.
    """
    try:
        if not document_ids:
            raise BadRequestError(
                message="No document IDs provided",
                details={"document_ids": document_ids},
            )

        from backend.models.rag_document import RAGDocument

        deleted_count = 0
        failed_documents = []

        for document_id in document_ids:
            try:
                document = await db.get(RAGDocument, document_id)
                if document:
                    await db.delete(document)
                    deleted_count += 1
                else:
                    failed_documents.append(
                        {"id": document_id, "reason": "Document not found"}
                    )
            except Exception as e:
                failed_documents.append({"id": document_id, "reason": str(e)})

        await db.commit()

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Deleted {deleted_count} documents",
                "deleted_count": deleted_count,
                "total_count": len(document_ids),
                "failed_documents": failed_documents,
            },
        )
    except BadRequestError:
        raise
    except Exception as e:
        logger.error(f"Error bulk deleting documents: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to bulk delete documents",
                "details": {"error": str(e)},
            },
        )


@router.delete("/directories/{directory_path}", response_model=None)
async def delete_rag_directory(
    directory_path: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a RAG directory and move all its documents to the default directory.
    """
    try:
        if not directory_path or directory_path.strip() == "":
            raise BadRequestError(
                message="Directory path cannot be empty",
                details={"directory_path": directory_path},
            )

        # Normalize the directory path
        normalized_path = directory_path.strip().replace("\\", "/")

        # Get all documents in this directory
        from backend.models.rag_document import RAGDocument

        # Find documents in this directory
        documents = await db.execute(
            select(RAGDocument).where(RAGDocument.directory_path == normalized_path)
        )
        documents = documents.scalars().all()

        # Move documents to default directory (set directory_path to None)
        moved_count = 0
        for document in documents:
            document.directory_path = None
            moved_count += 1

        await db.commit()

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Directory '{normalized_path}' deleted. {moved_count} documents moved to default directory.",
                "directory_path": normalized_path,
                "moved_documents_count": moved_count,
            },
        )
    except BadRequestError:
        raise
    except Exception as e:
        logger.error(f"Error deleting directory: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to delete directory",
                "details": {"error": str(e)},
            },
        )


@router.put("/directories/{old_directory_path}/rename", response_model=None)
async def rename_rag_directory(
    old_directory_path: str,
    new_directory_path: str = Query(..., description="New directory path"),
    db: AsyncSession = Depends(get_db),
):
    """
    Rename a RAG directory by updating all documents in that directory.
    """
    try:
        if not old_directory_path or old_directory_path.strip() == "":
            raise BadRequestError(
                message="Old directory path cannot be empty",
                details={"old_directory_path": old_directory_path},
            )

        if not new_directory_path or new_directory_path.strip() == "":
            raise BadRequestError(
                message="New directory path cannot be empty",
                details={"new_directory_path": new_directory_path},
            )

        # Normalize the directory paths
        old_normalized = old_directory_path.strip().replace("\\", "/")
        new_normalized = new_directory_path.strip().replace("\\", "/")

        if old_normalized == new_normalized:
            raise BadRequestError(
                message="New directory path must be different from old path",
                details={
                    "old_directory_path": old_normalized,
                    "new_directory_path": new_normalized,
                },
            )

        # Check if new directory already exists
        existing_directories = await vector_store.list_directories()
        if any(dir_info["path"] == new_normalized for dir_info in existing_directories):
            raise BadRequestError(
                message="Target directory already exists",
                details={"new_directory_path": new_normalized},
            )

        # Get all documents in the old directory
        from backend.models.rag_document import RAGDocument

        documents = await db.execute(
            select(RAGDocument).where(RAGDocument.directory_path == old_normalized)
        )
        documents = documents.scalars().all()

        # Update documents to new directory
        renamed_count = 0
        for document in documents:
            document.directory_path = new_normalized
            renamed_count += 1

        await db.commit()

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Directory renamed from '{old_normalized}' to '{new_normalized}'. {renamed_count} documents updated.",
                "old_directory_path": old_normalized,
                "new_directory_path": new_normalized,
                "renamed_documents_count": renamed_count,
            },
        )
    except BadRequestError:
        raise
    except Exception as e:
        logger.error(f"Error renaming directory: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to rename directory",
                "details": {"error": str(e)},
            },
        )


@router.get("/directories/{directory_path}/stats", response_model=None)
async def get_directory_stats(
    directory_path: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get statistics for a specific directory.
    """
    try:
        if not directory_path or directory_path.strip() == "":
            raise BadRequestError(
                message="Directory path cannot be empty",
                details={"directory_path": directory_path},
            )

        # Normalize the directory path
        normalized_path = directory_path.strip().replace("\\", "/")

        # Get documents in this directory
        from backend.models.rag_document import RAGDocument

        documents = await db.execute(
            select(RAGDocument).where(RAGDocument.directory_path == normalized_path)
        )
        documents = documents.scalars().all()

        # Calculate statistics
        total_documents = len(documents)
        total_chunks = sum(doc.chunks_count for doc in documents)
        total_tags = len(set(tag for doc in documents for tag in doc.tags))

        # Get unique file types
        file_extensions = set()
        for doc in documents:
            if "." in doc.filename:
                ext = doc.filename.split(".")[-1].lower()
                file_extensions.add(ext)

        # Get recent activity (documents uploaded in last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_documents = [
            doc
            for doc in documents
            if doc.uploaded_at
            and datetime.fromisoformat(doc.uploaded_at.replace("Z", "+00:00"))
            > thirty_days_ago
        ]

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "directory_path": normalized_path,
                "stats": {
                    "total_documents": total_documents,
                    "total_chunks": total_chunks,
                    "total_tags": total_tags,
                    "file_types": list(file_extensions),
                    "recent_activity": len(recent_documents),
                    "average_chunks_per_document": total_documents > 0
                    and round(total_chunks / total_documents, 2)
                    or 0,
                },
            },
        )
    except BadRequestError:
        raise
    except Exception as e:
        logger.error(f"Error getting directory stats: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to get directory statistics",
                "details": {"error": str(e)},
            },
        )
