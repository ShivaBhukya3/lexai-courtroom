"""Pydantic schemas for evidence endpoints."""

from pydantic import BaseModel


class EvidenceResponse(BaseModel):
    doc_id: str
    case_id: str
    file_name: str
    doc_type: str
    evidence_strength: float
    summary: str
    entities: dict
    legal_charges: list[dict]


class EvidenceUploadResponse(BaseModel):
    case_id: str
    uploaded_files: list[str]
    doc_ids: list[str]
    processing_status: str
