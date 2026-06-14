from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Enum, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class LoanType(Base):
    __tablename__ = "loan_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    interest_rate = Column(Float, nullable=False)
    min_amount = Column(Float, nullable=False)
    max_amount = Column(Float, nullable=False)
    min_tenure_months = Column(Integer, nullable=False)
    max_tenure_months = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    required_documents = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    applications = relationship("LoanApplication", back_populates="loan_type")


class LoanApplication(Base):
    __tablename__ = "loan_applications"

    id = Column(Integer, primary_key=True, index=True)
    application_number = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    loan_type_id = Column(Integer, ForeignKey("loan_types.id"), nullable=False)
    amount_requested = Column(Float, nullable=False)
    tenure_months = Column(Integer, nullable=False)
    purpose = Column(Text, nullable=True)
    status = Column(
        Enum("draft", "submitted", "under_review", "approved", "rejected", "disbursed", "closed"),
        default="submitted",
        nullable=False,
    )
    assigned_officer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    monthly_income = Column(Float, nullable=True)
    existing_emi = Column(Float, nullable=True, default=0)
    credit_score = Column(Integer, nullable=True)
    collateral_details = Column(Text, nullable=True)
    remarks = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    approved_amount = Column(Float, nullable=True)
    approved_interest_rate = Column(Float, nullable=True)
    approved_tenure_months = Column(Integer, nullable=True)
    emi_amount = Column(Float, nullable=True)
    disbursement_date = Column(DateTime(timezone=True), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    applicant = relationship("User", back_populates="loan_applications", foreign_keys=[user_id])
    assigned_officer = relationship("User", back_populates="assigned_applications", foreign_keys=[assigned_officer_id])
    loan_type = relationship("LoanType", back_populates="applications")
    documents = relationship("Document", back_populates="application")
    status_history = relationship("ApplicationStatusHistory", back_populates="application")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("loan_applications.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_type = Column(String(100), nullable=False)
    document_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    is_verified = Column(Boolean, default=False)
    verified_by = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    application = relationship("LoanApplication", back_populates="documents")
    user = relationship("User", back_populates="documents")


class ApplicationStatusHistory(Base):
    __tablename__ = "application_status_history"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("loan_applications.id"), nullable=False)
    from_status = Column(String(50), nullable=True)
    to_status = Column(String(50), nullable=False)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    application = relationship("LoanApplication", back_populates="status_history")
