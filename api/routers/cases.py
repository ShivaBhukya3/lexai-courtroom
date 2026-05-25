"""Case management API routes."""

import uuid
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from loguru import logger

from database.connection import get_db
from database import crud
from api.schemas.case_schema import CaseCreateRequest, CaseResponse, CaseListResponse

router = APIRouter(prefix="/api/v1/cases", tags=["cases"])

UPLOAD_DIR = Path("data/cases/uploaded")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Lazy imports to avoid circular dependency at startup
def _get_processor():
    from src.document_processor import MultimodalDocumentProcessor
    return MultimodalDocumentProcessor()


@router.post("/create", response_model=CaseResponse)
async def create_case(request: CaseCreateRequest, db: Session = Depends(get_db)):
    """Create a new case entry."""
    case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
    case_data = {
        "case_id": case_id,
        "case_name": request.case_name,
        "case_type": request.case_type,
        "sub_type": request.sub_type,
        "court": request.court,
        "judge": request.judge,
        "charges": request.charges,
        "jurisdiction": request.jurisdiction,
        "status": "Active",
        "filing_date": request.filing_date,
        "plaintiff": {"name": request.plaintiff_name},
        "defendant": {"name": request.defendant_name},
    }
    case = crud.create_case(db, case_data)
    return CaseResponse(
        case_id=case.id,
        case_name=case.case_name,
        case_type=case.case_type,
        status=case.status,
        created_at=case.created_at.isoformat(),
    )


@router.post("/{case_id}/upload")
async def upload_case_files(
    case_id: str,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """Upload and process case documents."""
    case = crud.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    case_dir = UPLOAD_DIR / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    processor = _get_processor()
    doc_ids = []
    uploaded = []

    for file in files:
        file_path = case_dir / file.filename
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        try:
            result = processor.process_document(str(file_path))
            doc = crud.add_document(db, case_id, result)
            doc_ids.append(doc.id)
            uploaded.append(file.filename)
            logger.info(f"Processed: {file.filename} for case {case_id}")
        except Exception as e:
            logger.error(f"Failed to process {file.filename}: {e}")

    return {
        "case_id": case_id,
        "uploaded_files": uploaded,
        "doc_ids": doc_ids,
        "processing_status": "completed",
    }


@router.get("/list", response_model=CaseListResponse)
async def list_cases(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """List all cases with pagination."""
    cases = crud.list_cases(db, skip=skip, limit=limit)
    return CaseListResponse(
        cases=[
            CaseResponse(
                case_id=c.id,
                case_name=c.case_name,
                case_type=c.case_type,
                status=c.status,
                created_at=c.created_at.isoformat(),
            )
            for c in cases
        ],
        total=len(cases),
        page=skip // limit + 1,
        page_size=limit,
    )


@router.get("/{case_id}")
async def get_case(case_id: str, db: Session = Depends(get_db)):
    """Get full case details including all documents."""
    case = crud.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    documents = crud.get_case_documents(db, case_id)
    verdict = crud.get_latest_verdict(db, case_id)

    return {
        "case_id": case.id,
        "case_name": case.case_name,
        "case_type": case.case_type,
        "court": case.court,
        "status": case.status,
        "metadata": case.metadata_json or {},
        "documents": [
            {
                "id": d.id,
                "file_name": d.file_name,
                "doc_type": d.doc_type,
                "evidence_strength": d.evidence_strength,
                "summary": d.summary,
                "processing_status": d.processing_status,
            }
            for d in documents
        ],
        "verdict_prediction": {
            "verdict": verdict.verdict,
            "conviction_probability": verdict.conviction_probability,
            "confidence_level": verdict.confidence_level,
        } if verdict else None,
    }
