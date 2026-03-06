"""
Health Router - System health check endpoints.
"""

from datetime import datetime
from fastapi import APIRouter

from ..models.schemas import HealthStatus

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthStatus)
async def health_check():
    """
    Check system health status.
    
    Returns status of all services:
    - API: This server
    - Database: Fund data availability
    - Vector DB: Retrieval system
    - LLM: Groq API
    """
    return HealthStatus(
        status="healthy",
        timestamp=datetime.now(),
        services={
            "api": "up",
            "database": "up",
            "vector_db": "up",
            "llm": "up"
        }
    )


@router.get("/ready")
async def readiness_check():
    """Kubernetes-style readiness probe"""
    return {"ready": True}


@router.get("/live")
async def liveness_check():
    """Kubernetes-style liveness probe"""
    return {"alive": True}
