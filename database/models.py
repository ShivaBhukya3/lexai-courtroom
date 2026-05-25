"""SQLAlchemy ORM models for LexAI database."""

from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime,
    Text, JSON, ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()


class CaseStatus(str, enum.Enum):
    ACTIVE = "Active"
    CLOSED = "Closed"
    APPEALED = "Appealed"
    PENDING = "Pending"


class DocumentType(str, enum.Enum):
    PDF = "pdf"
    DOCX = "docx"
    IMAGE = "image"
    AUDIO = "audio"
    TEXT = "text"


class Case(Base):
    __tablename__ = "cases"

    id = Column(String(50), primary_key=True)
    case_name = Column(String(255), nullable=False)
    case_type = Column(String(100))
    sub_type = Column(String(100))
    court = Column(String(255))
    judge = Column(String(255))
    jurisdiction = Column(String(100), default="India")
    status = Column(String(50), default="Active")
    filing_date = Column(String(50))
    next_hearing = Column(String(50))
    metadata_json = Column(JSON)
    verdict_prediction_json = Column(JSON)
    prosecution_args_json = Column(JSON)
    defense_args_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    documents = relationship("CaseDocument", back_populates="case", cascade="all, delete-orphan")
    parties = relationship("Party", back_populates="case", cascade="all, delete-orphan")


class CaseDocument(Base):
    __tablename__ = "case_documents"

    id = Column(String(100), primary_key=True)
    case_id = Column(String(50), ForeignKey("cases.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500))
    doc_type = Column(String(50))
    file_size_bytes = Column(Integer)
    processing_status = Column(String(50), default="pending")
    extracted_text = Column(Text)
    summary = Column(Text)
    entities_json = Column(JSON)
    legal_charges_json = Column(JSON)
    evidence_strength = Column(Float)
    vision_analysis_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="documents")


class Party(Base):
    __tablename__ = "parties"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(50), ForeignKey("cases.id"), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(100))  # plaintiff/defendant/complainant/accused/witness
    age = Column(Integer)
    occupation = Column(String(255))
    address = Column(Text)
    advocate = Column(String(255))

    case = relationship("Case", back_populates="parties")


class VerdictPrediction(Base):
    __tablename__ = "verdict_predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(50), ForeignKey("cases.id"), nullable=False)
    verdict = Column(String(50))
    conviction_probability = Column(Float)
    confidence = Column(Float)
    confidence_level = Column(String(20))
    key_factors_json = Column(JSON)
    feature_values_json = Column(JSON)
    shap_values_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class LegalArgument(Base):
    __tablename__ = "legal_arguments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(50), ForeignKey("cases.id"), nullable=False)
    side = Column(String(20))  # prosecution/defense
    style = Column(String(30))
    opening_statement = Column(Text)
    closing_statement = Column(Text)
    argument_data_json = Column(JSON)
    argument_strength_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
