"""CRUD operations for LexAI database."""

import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from loguru import logger

from database.models import Case, CaseDocument, Party, VerdictPrediction, LegalArgument


# ── Case operations ───────────────────────────────────────────────────────

def create_case(db: Session, case_data: dict) -> Case:
    case_id = case_data.get("case_id", f"CASE-{uuid.uuid4().hex[:8].upper()}")
    case = Case(
        id=case_id,
        case_name=case_data.get("case_name", case_data.get("case_id", "Unnamed")),
        case_type=case_data.get("case_type", ""),
        sub_type=case_data.get("sub_type", ""),
        court=case_data.get("court", ""),
        judge=case_data.get("judge", ""),
        status=case_data.get("status", "Active"),
        filing_date=case_data.get("filing_date", ""),
        next_hearing=case_data.get("next_hearing", ""),
        metadata_json=case_data,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    logger.info(f"Case created: {case_id}")
    return case


def get_case(db: Session, case_id: str) -> Case | None:
    return db.query(Case).filter(Case.id == case_id).first()


def list_cases(db: Session, skip: int = 0, limit: int = 20) -> list[Case]:
    return db.query(Case).offset(skip).limit(limit).all()


def update_case(db: Session, case_id: str, updates: dict) -> Case | None:
    case = get_case(db, case_id)
    if not case:
        return None
    for key, val in updates.items():
        if hasattr(case, key):
            setattr(case, key, val)
    case.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(case)
    return case


# ── Document operations ───────────────────────────────────────────────────

def add_document(db: Session, case_id: str, doc_data: dict) -> CaseDocument:
    doc_id = f"{case_id}-{uuid.uuid4().hex[:8]}"
    doc = CaseDocument(
        id=doc_id,
        case_id=case_id,
        file_name=doc_data.get("file_name", "unknown"),
        file_path=doc_data.get("file_path", ""),
        doc_type=doc_data.get("doc_type", ""),
        file_size_bytes=doc_data.get("file_size_bytes"),
        processing_status="completed",
        extracted_text=doc_data.get("text", "")[:50000],
        summary=str(doc_data.get("summary", ""))[:2000],
        entities_json=doc_data.get("entities", {}),
        legal_charges_json=doc_data.get("legal_charges", []),
        evidence_strength=float(doc_data.get("evidence_strength", 5.0)),
        vision_analysis_json=doc_data.get("vision_analysis", {}),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def get_case_documents(db: Session, case_id: str) -> list[CaseDocument]:
    return db.query(CaseDocument).filter(CaseDocument.case_id == case_id).all()


# ── Verdict operations ────────────────────────────────────────────────────

def save_verdict_prediction(db: Session, case_id: str, prediction: dict, features: dict) -> VerdictPrediction:
    vp = VerdictPrediction(
        case_id=case_id,
        verdict=prediction.get("verdict", ""),
        conviction_probability=prediction.get("conviction_probability", 0.5),
        confidence=prediction.get("confidence", 0.5),
        confidence_level=prediction.get("confidence_level", "Medium"),
        key_factors_json=prediction.get("key_factors", []),
        feature_values_json=features,
    )
    db.add(vp)
    db.commit()
    db.refresh(vp)
    return vp


def get_latest_verdict(db: Session, case_id: str) -> VerdictPrediction | None:
    return (
        db.query(VerdictPrediction)
        .filter(VerdictPrediction.case_id == case_id)
        .order_by(VerdictPrediction.created_at.desc())
        .first()
    )


# ── Argument operations ───────────────────────────────────────────────────

def save_argument(db: Session, case_id: str, arg_data: dict) -> LegalArgument:
    arg = LegalArgument(
        case_id=case_id,
        side=arg_data.get("side", ""),
        style=arg_data.get("style", "balanced"),
        opening_statement=arg_data.get("opening_statement", ""),
        closing_statement=arg_data.get("closing_statement", ""),
        argument_data_json=arg_data,
        argument_strength_score=float(arg_data.get("argument_strength_score", 6.5)),
    )
    db.add(arg)
    db.commit()
    db.refresh(arg)
    return arg


def get_case_arguments(db: Session, case_id: str) -> list[LegalArgument]:
    return db.query(LegalArgument).filter(LegalArgument.case_id == case_id).all()
