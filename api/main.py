"""LexAI FastAPI application — main entry point."""

import os
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # ── Startup ──────────────────────────────────────────────────────────
    logger.info("=" * 50)
    logger.info("  LexAI API Starting...")
    logger.info("=" * 50)

    # Initialize database
    try:
        from database.connection import init_db
        init_db()
        logger.info("[✓] Database initialized")
    except Exception as e:
        logger.error(f"[✗] Database init failed: {e}")

    # Pre-train / load ML models
    try:
        from src.verdict_predictor import VerdictPredictor
        predictor = VerdictPredictor()
        if not predictor._models_trained:
            logger.info("Training ML models...")
            predictor.train_model()
        app.state.predictor = predictor
        logger.info("[✓] ML models ready")
    except Exception as e:
        logger.error(f"[✗] ML model init failed: {e}")

    # Build/load legal index
    try:
        from rag.legal_retriever import LegalRAGRetriever
        retriever = LegalRAGRetriever()
        app.state.retriever = retriever
        logger.info("[✓] Legal RAG index ready")
    except Exception as e:
        logger.error(f"[✗] RAG index init failed: {e}")

    logger.info("[✓] LexAI API ready — visit /docs for API documentation")
    logger.info("=" * 50)

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────
    logger.info("LexAI API shutting down...")


app = FastAPI(
    title="LexAI — Multimodal Courtroom Intelligence API",
    description=(
        "AI-powered legal assistant combining document analysis, "
        "image evidence processing, audio transcription, legal precedent "
        "retrieval, verdict prediction, and AI argument generation."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request logging middleware ─────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    logger.debug(f"{request.method} {request.url.path} — {response.status_code} ({duration:.3f}s)")
    return response

# ── API Key auth (optional — disabled by default for demo) ────────────────
# Uncomment to enable API key authentication:
# API_KEY = os.getenv("API_KEY", "lexai_secret_key")
# @app.middleware("http")
# async def verify_api_key(request: Request, call_next):
#     if request.url.path not in ("/", "/docs", "/redoc", "/openapi.json", "/api/v1/health"):
#         key = request.headers.get("X-API-Key")
#         if key != API_KEY:
#             return JSONResponse({"error": "Unauthorized"}, status_code=401)
#     return await call_next(request)

# ── Register routers ──────────────────────────────────────────────────────
from api.routers import health, cases, arguments, verdict, research, evidence

app.include_router(health.router)
app.include_router(cases.router)
app.include_router(arguments.router)
app.include_router(verdict.router)
app.include_router(research.router)
app.include_router(evidence.router)

# ── Exception handlers ────────────────────────────────────────────────────
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        {"error": exc.detail, "status_code": exc.status_code},
        status_code=exc.status_code,
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        {"error": "Internal server error", "detail": str(exc)},
        status_code=500,
    )


@app.get("/")
async def root():
    web_dir = Path(__file__).parent.parent / "dashboard_web"
    if web_dir.exists():
        return RedirectResponse(url="/dashboard/")
    return {
        "message": "Welcome to LexAI — Multimodal Courtroom Intelligence Platform",
        "docs": "/docs",
        "health": "/api/v1/health",
        "version": "1.0.0",
    }


# Mount web dashboard static files (must be after all API routes)
_web_dir = Path(__file__).parent.parent / "dashboard_web"
if _web_dir.exists():
    app.mount("/dashboard", StaticFiles(directory=str(_web_dir), html=True), name="dashboard")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=9000,
        reload=True,
        log_level="info",
    )
