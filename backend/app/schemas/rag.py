"""RAG and document schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class RAGQuery(BaseModel):
    """Schema for RAG query."""

    query: str = Field(..., min_length=1, max_length=1000)
    include_emails: bool = True
    include_documents: bool = True
    include_meetings: bool = True
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    max_results: int = Field(default=10, ge=1, le=50)


class RAGSource(BaseModel):
    """Schema for RAG source reference."""

    type: str  # email, document, meeting
    id: UUID
    title: str
    snippet: str
    relevance_score: float
    date: Optional[datetime]


class RAGResponse(BaseModel):
    """Schema for RAG query response."""

    answer: str
    sources: List[RAGSource]
    confidence: float
    query_time_ms: int
    llm_provider: str
    llm_model: str


class DocumentUpload(BaseModel):
    """Schema for document upload metadata."""

    filename: str
    source: str = Field(default="upload", pattern="^(upload|url)$")
    source_url: Optional[str] = None


class DocumentResponse(BaseModel):
    """Schema for document response."""

    id: UUID
    user_id: UUID
    email_id: Optional[UUID]
    filename: str
    original_filename: Optional[str]
    file_type: Optional[str]
    mime_type: Optional[str]
    file_size: Optional[int]
    content_summary: Optional[str]
    language: Optional[str]
    page_count: Optional[int]
    word_count: Optional[int]
    source: str
    source_url: Optional[str]
    indexed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for paginated document list response."""

    items: List[DocumentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DocumentContent(BaseModel):
    """Schema for document content response."""

    id: UUID
    filename: str
    content_text: Optional[str]
    content_summary: Optional[str]


class GraphNode(BaseModel):
    """Schema for knowledge graph node."""

    id: str
    type: str  # Person, Company, Project, Email, Document, Meeting, Topic
    name: str
    properties: Dict[str, Any]


class GraphRelationship(BaseModel):
    """Schema for knowledge graph relationship."""

    source_id: str
    target_id: str
    type: str  # SENT, RECEIVED, WORKS_AT, MENTIONS, etc.
    properties: Dict[str, Any]


class GraphQueryResponse(BaseModel):
    """Schema for graph query response."""

    nodes: List[GraphNode]
    relationships: List[GraphRelationship]


class IndexingStatus(BaseModel):
    """Schema for indexing status."""

    total_emails: int
    indexed_emails: int
    total_documents: int
    indexed_documents: int
    total_meetings: int
    indexed_meetings: int
    last_index_time: Optional[datetime]
    is_indexing: bool
