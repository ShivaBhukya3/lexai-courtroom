"""Evidence analysis API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.connection import get_db
from database import crud

router = APIRouter(prefix="/api/v1/evidence", tags=["evidence"])


@router.get("/{case_id}/list")
async def list_evidence(case_id: str, db: Session = Depends(get_db)):
    """List all evidence items for a case."""
    case = crud.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    documents = crud.get_case_documents(db, case_id)
    return {
        "case_id": case_id,
        "evidence": [
            {
                "id": d.id,
                "file_name": d.file_name,
                "doc_type": d.doc_type,
                "evidence_strength": d.evidence_strength,
                "summary": d.summary,
                "entities": d.entities_json,
                "legal_charges": d.legal_charges_json,
                "vision_analysis": d.vision_analysis_json,
            }
            for d in documents
        ],
        "total": len(documents),
    }


@router.get("/{case_id}/matrix")
async def evidence_matrix(case_id: str, db: Session = Depends(get_db)):
    """Get evidence vs charges matrix."""
    case = crud.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    documents = crud.get_case_documents(db, case_id)
    charges = (case.metadata_json or {}).get("charges", [])

    matrix = {}
    for doc in documents:
        matrix[doc.file_name] = {}
        strength = doc.evidence_strength or 5
        for charge in charges:
            matrix[doc.file_name][charge] = {
                "status": "Supports" if strength >= 6 else "Neutral" if strength >= 4 else "Contradicts",
                "score": strength,
            }

    return {"case_id": case_id, "charges": charges, "matrix": matrix}
