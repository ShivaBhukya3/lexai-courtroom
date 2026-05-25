"""Argument generation API routes."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from loguru import logger

from database.connection import get_db
from database import crud
from api.schemas.argument_schema import ArgumentRequest, CrossExamRequest, ArgumentResponse

router = APIRouter(prefix="/api/v1/arguments", tags=["arguments"])


def _get_generator():
    from src.argument_generator import LegalArgumentGenerator
    return LegalArgumentGenerator()


def _get_retriever():
    from rag.legal_retriever import LegalRAGRetriever
    return LegalRAGRetriever()


@router.post("/generate", response_model=ArgumentResponse)
async def generate_argument(request: ArgumentRequest, db: Session = Depends(get_db)):
    """Generate prosecution or defense arguments for a case."""
    case = crud.get_case(db, request.case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {request.case_id} not found")

    case_data = {"metadata": case.metadata_json or {}}
    documents = crud.get_case_documents(db, request.case_id)
    evidence_analyses = [
        {
            "file_name": d.file_name,
            "doc_type": d.doc_type,
            "summary": d.summary,
            "evidence_strength": d.evidence_strength,
            "entities": d.entities_json,
        }
        for d in documents
    ]

    retriever = _get_retriever()
    charges = (case.metadata_json or {}).get("charges", [])
    legal_context = retriever.get_legal_context(" ".join(charges))

    if request.side == "prosecution":
        precedents = retriever.get_prosecution_precedents(charges)
    else:
        precedents = retriever.get_defense_precedents(charges)

    generator = _get_generator()
    if request.side == "prosecution":
        args = generator.generate_prosecution_argument(
            case_data, evidence_analyses, legal_context, precedents, request.style
        )
    else:
        args = generator.generate_defense_argument(
            case_data, evidence_analyses, legal_context, precedents, request.style
        )

    crud.save_argument(db, request.case_id, args)

    return ArgumentResponse(
        case_id=request.case_id,
        side=request.side,
        style=request.style,
        opening_statement=args.get("opening_statement", ""),
        closing_statement=args.get("closing_statement", ""),
        argument_strength_score=args.get("argument_strength_score", 6.5),
        data=args,
    )


@router.post("/cross-examine")
async def generate_cross_examination(request: CrossExamRequest, db: Session = Depends(get_db)):
    """Generate cross-examination questions for a witness."""
    case = crud.get_case(db, request.case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {request.case_id} not found")

    meta = case.metadata_json or {}
    case_context = f"Case: {meta.get('case_type', '')} — Charges: {', '.join(meta.get('charges', []))}"

    generator = _get_generator()
    questions = generator.generate_cross_examination(
        request.witness_statement, case_context, request.side
    )

    return {"case_id": request.case_id, "side": request.side, "questions": questions}
