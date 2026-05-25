"""Pydantic schemas for argument API endpoints."""

from pydantic import BaseModel, Field


class ArgumentRequest(BaseModel):
    case_id: str
    side: str = Field(..., pattern="^(prosecution|defense)$")
    style: str = Field(default="balanced", pattern="^(aggressive|conservative|balanced)$")


class CrossExamRequest(BaseModel):
    case_id: str
    witness_statement: str
    side: str = Field(default="defense", pattern="^(prosecution|defense)$")


class ArgumentResponse(BaseModel):
    case_id: str
    side: str
    style: str
    opening_statement: str
    closing_statement: str
    argument_strength_score: float
    data: dict
