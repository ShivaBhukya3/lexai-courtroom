"""Verdict prediction API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.connection import get_db
from database import crud
from api.schemas.verdict_schema import VerdictRequest, SimulateScenarioRequest, VerdictResponse

router = APIRouter(prefix="/api/v1/verdict", tags=["verdict"])


def _get_predictor():
    from src.verdict_predictor import VerdictPredictor
    return VerdictPredictor()


def _build_features(case_data: dict, documents: list) -> dict:
    """Build feature dict from case data and documents."""
    charges = case_data.get("charges", [])
    severity_map = {"IPC 302": 5, "IPC 376": 5, "IPC 307": 4, "IPC 420": 3, "IPC 498A": 3}
    charge_severity = max(
        (severity_map.get(c.split("—")[0].strip(), 3) for c in charges),
        default=3,
    )

    strengths = [d.evidence_strength for d in documents if d.evidence_strength]
    avg_strength = sum(strengths) / len(strengths) if strengths else 5.0

    return {
        "evidence_count": len(documents),
        "evidence_strength_avg": avg_strength,
        "witness_count": len(case_data.get("witnesses", [])),
        "witness_credibility_avg": 6.5,
        "precedent_match_score": 0.6,
        "charge_severity": charge_severity,
        "defense_argument_score": 6.0,
        "prosecution_argument_score": 6.5,
        "ipc_section_severity": charge_severity,
        "case_duration_days": 365,
        "judge_type": "sessions",
        "bail_status": int(case_data.get("accused", {}).get("bail_status", "").lower() == "bail"),
        "confession_present": 0,
        "documentary_evidence": int(any(d.doc_type in ("pdf", "docx") for d in documents)),
        "forensic_evidence": 0,
    }


@router.post("/predict", response_model=VerdictResponse)
async def predict_verdict(request: VerdictRequest, db: Session = Depends(get_db)):
    """Predict verdict for a case."""
    case = crud.get_case(db, request.case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {request.case_id} not found")

    documents = crud.get_case_documents(db, request.case_id)
    meta = case.metadata_json or {}

    features = request.features or _build_features(meta, documents)

    predictor = _get_predictor()
    prediction = predictor.predict_verdict(features)

    crud.save_verdict_prediction(db, request.case_id, prediction, features)

    sentence = prediction.get("sentence_estimate")
    return VerdictResponse(
        case_id=request.case_id,
        verdict=prediction["verdict"],
        conviction_probability=prediction["conviction_probability"],
        acquittal_probability=prediction["acquittal_probability"],
        confidence=prediction["confidence"],
        confidence_level=prediction["confidence_level"],
        key_factors=prediction["key_factors"],
        sentence_estimate=sentence if isinstance(sentence, dict) else None,
        bail_recommendation=prediction["bail_recommendation"],
        appeal_grounds=prediction["appeal_grounds"],
    )


@router.post("/simulate")
async def simulate_scenario(request: SimulateScenarioRequest, db: Session = Depends(get_db)):
    """Simulate what-if scenarios for verdict prediction."""
    case = crud.get_case(db, request.case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {request.case_id} not found")

    documents = crud.get_case_documents(db, request.case_id)
    meta = case.metadata_json or {}
    base_features = _build_features(meta, documents)

    predictor = _get_predictor()
    result = predictor.sensitivity_analysis({**base_features, **request.scenario})
    return {"case_id": request.case_id, **result}


@router.get("/explain/{case_id}")
async def explain_verdict(case_id: str, db: Session = Depends(get_db)):
    """Get SHAP-style feature importance explanation."""
    case = crud.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    documents = crud.get_case_documents(db, case_id)
    features = _build_features(case.metadata_json or {}, documents)

    predictor = _get_predictor()
    explanation = predictor.explain_prediction(features)
    return {"case_id": case_id, "feature_importance": explanation}
