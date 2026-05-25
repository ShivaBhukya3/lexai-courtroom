"""Legal research API routes."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from database import crud

router = APIRouter(prefix="/api/v1/research", tags=["research"])


class PrecedentRequest(BaseModel):
    query: str
    top_k: int = 8


class SectionsRequest(BaseModel):
    query: str
    top_k: int = 5


class AskRequest(BaseModel):
    question: str
    case_id: str | None = None


def _get_retriever():
    from rag.legal_retriever import LegalRAGRetriever
    return LegalRAGRetriever()


@router.post("/precedents")
async def search_precedents(request: PrecedentRequest):
    """Search for relevant case precedents."""
    retriever = _get_retriever()
    results = retriever.search_precedents(request.query, top_k=request.top_k)
    return {"query": request.query, "results": results, "count": len(results)}


@router.post("/sections")
async def search_sections(request: SectionsRequest):
    """Search for applicable IPC/CrPC sections."""
    retriever = _get_retriever()
    results = retriever.search_legal_sections(request.query, top_k=request.top_k)
    return {"query": request.query, "results": results, "count": len(results)}


@router.post("/ask")
async def ask_legal_question(request: AskRequest, db: Session = Depends(get_db)):
    """Chat with the legal AI assistant."""
    case_context = ""
    if request.case_id:
        case = crud.get_case(db, request.case_id)
        if case:
            meta = case.metadata_json or {}
            case_context = f"Case: {meta.get('case_type', '')} — {', '.join(meta.get('charges', []))}"

    retriever = _get_retriever()
    answer = retriever.ask_legal_question(request.question, case_context)
    return {"question": request.question, "answer": answer, "case_id": request.case_id}


@router.post("/rebuild-index")
async def rebuild_index():
    """Rebuild the FAISS legal index."""
    retriever = _get_retriever()
    retriever.build_legal_index()
    return {"status": "success", "message": "Legal index rebuilt successfully"}
