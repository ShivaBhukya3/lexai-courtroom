"""Health check endpoints."""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "LexAI Courtroom Intelligence API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/")
async def root():
    return {
        "message": "Welcome to LexAI — Multimodal Courtroom Intelligence Platform",
        "docs": "/docs",
        "health": "/api/v1/health",
        "version": "1.0.0",
    }
