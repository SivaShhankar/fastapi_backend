from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class UserRole(str, enum.Enum):
    customer = "customer"
    admin = "admin"
    loan_officer = "loan_officer"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    role = Column(Enum("customer", "admin", "loan_officer"), default="customer", nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(10), nullable=True)
    pan_number = Column(String(20), nullable=True)
    aadhar_number = Column(String(20), nullable=True)
    date_of_birth = Column(String(20), nullable=True)
    annual_income = Column(Integer, nullable=True)
    employment_type = Column(String(50), nullable=True)
    employer_name = Column(String(200), nullable=True)
    profile_image = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    loan_applications = relationship("LoanApplication", back_populates="applicant", foreign_keys="LoanApplication.user_id")
    assigned_applications = relationship("LoanApplication", back_populates="assigned_officer", foreign_keys="LoanApplication.assigned_officer_id")
    documents = relationship("Document", back_populates="user")
