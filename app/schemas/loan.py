from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class LoanTypeResponse(BaseModel):
    id: int
    name: str
    code: str
    interest_rate: float
    min_amount: float
    max_amount: float
    min_tenure_months: int
    max_tenure_months: int
    description: Optional[str] = None
    required_documents: Optional[Any] = None
    is_active: bool

    class Config:
        from_attributes = True


class LoanApplicationCreate(BaseModel):
    loan_type_id: int
    amount_requested: float
    tenure_months: int
    purpose: Optional[str] = None
    monthly_income: Optional[float] = None
    existing_emi: Optional[float] = 0
    collateral_details: Optional[str] = None


class LoanApplicationUpdate(BaseModel):
    status: Optional[str] = None
    assigned_officer_id: Optional[int] = None
    remarks: Optional[str] = None
    rejection_reason: Optional[str] = None
    approved_amount: Optional[float] = None
    approved_interest_rate: Optional[float] = None
    approved_tenure_months: Optional[int] = None
    credit_score: Optional[int] = None


class ApplicantSummary(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None

    class Config:
        from_attributes = True


class OfficerSummary(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str

    class Config:
        from_attributes = True


class StatusHistoryResponse(BaseModel):
    id: int
    from_status: Optional[str] = None
    to_status: str
    remarks: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: int
    document_type: str
    document_name: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    is_verified: bool
    uploaded_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LoanApplicationResponse(BaseModel):
    id: int
    application_number: str
    loan_type_id: int
    loan_type: Optional[LoanTypeResponse] = None
    amount_requested: float
    tenure_months: int
    purpose: Optional[str] = None
    status: str
    monthly_income: Optional[float] = None
    existing_emi: Optional[float] = None
    credit_score: Optional[int] = None
    collateral_details: Optional[str] = None
    remarks: Optional[str] = None
    rejection_reason: Optional[str] = None
    approved_amount: Optional[float] = None
    approved_interest_rate: Optional[float] = None
    approved_tenure_months: Optional[int] = None
    emi_amount: Optional[float] = None
    applicant: Optional[ApplicantSummary] = None
    assigned_officer: Optional[OfficerSummary] = None
    documents: Optional[List[DocumentResponse]] = []
    status_history: Optional[List[StatusHistoryResponse]] = []
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaginatedApplications(BaseModel):
    items: List[LoanApplicationResponse]
    total: int
    page: int
    size: int
    pages: int


class AnalyticsSummary(BaseModel):
    total_applications: int
    pending_applications: int
    approved_applications: int
    rejected_applications: int
    disbursed_applications: int
    total_loan_amount: float
    approved_loan_amount: float
    total_customers: int
    applications_this_month: int
