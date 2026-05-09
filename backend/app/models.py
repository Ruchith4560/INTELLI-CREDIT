from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"
    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String, unique=True, index=True, nullable=False)
    name            = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role            = Column(String, default="credit_officer")  # credit_officer | manager
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    documents       = relationship("UploadedDocument", back_populates="owner")


class UploadedDocument(Base):
    __tablename__ = "uploaded_documents"
    id             = Column(Integer, primary_key=True, index=True)
    user_id        = Column(Integer, ForeignKey("users.id"))
    filename       = Column(String, nullable=False)
    file_path      = Column(String, nullable=False)
    doc_type       = Column(String)   # annual_report | gst | bank_statement | csv | other
    company_name   = Column(String)
    session_id     = Column(String, index=True)
    status         = Column(String, default="uploaded")  # uploaded | processing | processed | failed
    extracted_text = Column(Text)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    owner          = relationship("User", back_populates="documents")


class ExtractedFeature(Base):
    __tablename__ = "extracted_features"
    id                = Column(Integer, primary_key=True, index=True)
    session_id        = Column(String, index=True)
    company_name      = Column(String)
    feature_data      = Column(JSON)
    financial_ratios  = Column(JSON)
    gst_data          = Column(JSON)
    qualitative_notes = Column(Text)
    created_at        = Column(DateTime(timezone=True), server_default=func.now())


class RiskScore(Base):
    __tablename__ = "risk_scores"
    id              = Column(Integer, primary_key=True, index=True)
    session_id      = Column(String, index=True, unique=True)
    company_name    = Column(String)
    risk_score      = Column(Float)
    decision        = Column(String)   # APPROVE | REVIEW | REJECT
    loan_amount     = Column(Float)
    interest_rate   = Column(Float)
    risk_breakdown  = Column(JSON)
    shap_values     = Column(JSON)
    llm_explanation = Column(Text)
    news_sentiment  = Column(JSON)
    litigation_risk = Column(JSON)
    scoring_method  = Column(String, default="Rule-Based")
    created_at      = Column(DateTime(timezone=True), server_default=func.now())


class ExplainabilityLog(Base):
    __tablename__ = "explainability_logs"
    id               = Column(Integer, primary_key=True, index=True)
    session_id       = Column(String, index=True)
    decision         = Column(String)
    shap_features    = Column(JSON)
    explanation_text = Column(Text)
    audit_trail      = Column(JSON)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())


class OfficerFeedback(Base):
    __tablename__ = "officer_feedback"
    id                   = Column(Integer, primary_key=True, index=True)
    session_id           = Column(String, index=True)
    user_id              = Column(Integer, ForeignKey("users.id"))
    agreed_with_decision = Column(Boolean)
    actual_decision      = Column(String)
    comments             = Column(Text)
    created_at           = Column(DateTime(timezone=True), server_default=func.now())


class CAMReport(Base):
    __tablename__ = "cam_reports"
    id           = Column(Integer, primary_key=True, index=True)
    session_id   = Column(String, index=True)
    company_name = Column(String)
    file_path    = Column(String)
    report_data  = Column(JSON)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
