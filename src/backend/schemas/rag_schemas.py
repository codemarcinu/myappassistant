from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RAGUploadResponse(BaseModel):
    """Response model for RAG document upload"""

    success: bool
    filename: str
    message: str


class RAGDocumentInfo(BaseModel):
    """Model for RAG document information"""

    document_id: str
    filename: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    directory_path: str = "default"
    chunks_count: int = 0
    uploaded_at: Optional[datetime] = None


class RAGQueryRequest(BaseModel):
    """Request model for RAG queries"""

    question: str = Field(..., description="Question to ask the RAG system")
    max_results: Optional[int] = Field(
        5, description="Maximum number of results to return"
    )


class RAGQueryResponse(BaseModel):
    """Response model for RAG queries"""

    success: bool
    answer: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score of the answer"
    )


class RAGDocumentMetadata(BaseModel):
    """Model for RAG document metadata"""

    document_id: str
    filename: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    directory_path: str = "default"
    source: str = "upload"
    content_type: Optional[str] = None
    file_size: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)


class RAGDirectoryInfo(BaseModel):
    """Model for RAG directory information"""

    path: str
    name: str
    document_count: int = 0
    created_at: Optional[datetime] = None


class RAGChunkInfo(BaseModel):
    """Model for RAG document chunk information"""

    chunk_id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding_vector: Optional[List[float]] = None


class RAGProcessingStatus(BaseModel):
    """Model for RAG document processing status"""

    document_id: str
    status: str = Field(description="processing, completed, failed")
    progress: float = Field(
        0.0, ge=0.0, le=1.0, description="Processing progress (0-1)"
    )
    message: Optional[str] = None
    error: Optional[str] = None
    chunks_processed: int = 0
    total_chunks: Optional[int] = None


class RAGSystemStats(BaseModel):
    """Model for RAG system statistics"""

    total_documents: int
    total_chunks: int
    total_embeddings: int
    storage_size_mb: float
    last_updated: datetime
    vector_store_type: str
    embedding_model: str
