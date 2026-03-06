"""
Pydantic schemas for API requests and responses.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Single chat message"""
    role: MessageRole
    content: str
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)
    citations: Optional[List[Dict[str, Any]]] = None


class ChatRequest(BaseModel):
    """Chat request from user"""
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    history: Optional[List[ChatMessage]] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """Chat response from assistant"""
    message: ChatMessage
    session_id: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    rag_compliant: bool = True
    processing_time_ms: float


class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    type: str  # "message", "typing", "error", "complete"
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class FundBase(BaseModel):
    """Base fund information"""
    fund_name: str
    category: Optional[str] = None
    amc: Optional[str] = None
    risk_level: Optional[str] = None
    expense_ratio: Optional[str] = None
    benchmark: Optional[str] = None


class FundDetail(FundBase):
    """Detailed fund information"""
    exit_load: Optional[str] = None
    minimum_sip: Optional[str] = None
    lock_in_period: Optional[str] = None
    source_url: str
    nav: Optional[str] = None
    fund_size: Optional[str] = None


class FundListResponse(BaseModel):
    """Paginated fund list response"""
    funds: List[FundDetail]
    total: int
    page: int
    page_size: int


class FundSearchRequest(BaseModel):
    """Fund search request"""
    query: str = Field(..., min_length=1)
    category: Optional[str] = None
    risk_level: Optional[str] = None


class FeedbackRequest(BaseModel):
    """User feedback request"""
    message_id: str
    rating: int = Field(..., ge=1, le=5)
    helpful: Optional[bool] = None
    comments: Optional[str] = None


class HealthStatus(BaseModel):
    """System health status"""
    status: str
    timestamp: datetime
    services: Dict[str, str]
    version: str = "1.0.0"


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
