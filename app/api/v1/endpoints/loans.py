from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.deps import get_current_user, get_current_admin
from app.models.user import User
from app.schemas.loan import (
    LoanTypeResponse, LoanApplicationCreate, LoanApplicationUpdate,
    LoanApplicationResponse, PaginatedApplications, AnalyticsSummary
)
from app.services.loan_service import (
    get_loan_types, create_application, get_application,
    get_user_applications, get_all_applications, update_application_status, get_analytics
)
import math

router = APIRouter()


@router.get("/types", response_model=list[LoanTypeResponse])
def list_loan_types(db: Session = Depends(get_db)):
    return get_loan_types(db)


# Customer routes
@router.post("/apply", response_model=LoanApplicationResponse)
def apply_for_loan(
    data: LoanApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_application(db, current_user.id, data)


@router.get("/my-applications", response_model=PaginatedApplications)
def my_applications(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = get_user_applications(db, current_user.id, status, page, size)
    return PaginatedApplications(
        items=items, total=total, page=page, size=size,
        pages=math.ceil(total / size) if total else 1,
    )


@router.get("/my-applications/{application_id}", response_model=LoanApplicationResponse)
def get_my_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_application(db, application_id, current_user.id, current_user.role)


# Admin routes
@router.get("/all", response_model=PaginatedApplications)
def all_applications(
    status: Optional[str] = None,
    loan_type_id: Optional[int] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    items, total = get_all_applications(db, status, loan_type_id, search, page, size)
    return PaginatedApplications(
        items=items, total=total, page=page, size=size,
        pages=math.ceil(total / size) if total else 1,
    )


@router.get("/analytics", response_model=AnalyticsSummary)
def analytics(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return get_analytics(db)


@router.get("/{application_id}", response_model=LoanApplicationResponse)
def get_single_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return get_application(db, application_id)


@router.put("/{application_id}", response_model=LoanApplicationResponse)
def update_application(
    application_id: int,
    data: LoanApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return update_application_status(db, application_id, data, current_user.id)
