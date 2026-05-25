"""Pydantic schemas for verdict prediction endpoints."""

from pydantic import BaseModel, Field


class VerdictRequest(BaseModel):
    case_id: str
    features: dict | None = None


class SimulateScenarioRequest(BaseModel):
    case_id: str
    scenario: dict = Field(..., description="Feature overrides for what-if simulation")


class VerdictResponse(BaseModel):
    case_id: str
    verdict: str
    conviction_probability: float
    acquittal_probability: float
    confidence: float
    confidence_level: str
    key_factors: list[str]
    sentence_estimate: dict | None
    bail_recommendation: str
    appeal_grounds: list[str]
