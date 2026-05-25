"""Pydantic schemas for case API endpoints."""

from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime


class CaseCreateRequest(BaseModel):
    case_name: str = Field(..., description="Descriptive case name")
    case_type: str = Field(..., description="Civil or Criminal")
    sub_type: str = Field(default="", description="Property Dispute, Fraud, etc.")
    jurisdiction: str = Field(default="India")
    court: str = Field(default="")
    judge: str = Field(default="")
    charges: list[str] = Field(default_factory=list)
    plaintiff_name: str = Field(default="")
    defendant_name: str = Field(default="")
    filing_date: str = Field(default="")


class CaseResponse(BaseModel):
    case_id: str
    case_name: str
    case_type: str
    sub_type: str = ""
    court: str = ""
    status: str
    created_at: str

    class Config:
        from_attributes = True


class CaseDetailResponse(BaseModel):
    case_id: str
    case_name: str
    case_type: str
    court: str
    status: str
    metadata: dict
    documents: list[dict] = []
    verdict_prediction: dict | None = None

    class Config:
        from_attributes = True


class CaseListResponse(BaseModel):
    cases: list[CaseResponse]
    total: int
    page: int
    page_size: int
