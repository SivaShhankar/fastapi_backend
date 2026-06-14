from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_
from fastapi import HTTPException
from datetime import datetime
import random
import string
import math

from app.models.loan import LoanApplication, LoanType, ApplicationStatusHistory, Document
from app.models.user import User
from app.schemas.loan import LoanApplicationCreate, LoanApplicationUpdate, AnalyticsSummary


def generate_application_number() -> str:
    prefix = "LN"
    year = datetime.now().strftime("%Y")
    random_part = "".join(random.choices(string.digits, k=8))
    return f"{prefix}{year}{random_part}"


def calculate_emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    monthly_rate = annual_rate / (12 * 100)
    if monthly_rate == 0:
        return principal / tenure_months
    emi = principal * monthly_rate * math.pow(1 + monthly_rate, tenure_months)
    emi /= math.pow(1 + monthly_rate, tenure_months) - 1
    return round(emi, 2)


def get_loan_types(db: Session):
    return db.query(LoanType).filter(LoanType.is_active == True).all()


def create_application(db: Session, user_id: int, data: LoanApplicationCreate) -> LoanApplication:
    loan_type = db.query(LoanType).filter(LoanType.id == data.loan_type_id).first()
    if not loan_type:
        raise HTTPException(status_code=404, detail="Loan type not found")
    if not (loan_type.min_amount <= data.amount_requested <= loan_type.max_amount):
        raise HTTPException(
            status_code=400,
            detail=f"Amount must be between ₹{loan_type.min_amount:,.0f} and ₹{loan_type.max_amount:,.0f}",
        )
    if not (loan_type.min_tenure_months <= data.tenure_months <= loan_type.max_tenure_months):
        raise HTTPException(
            status_code=400,
            detail=f"Tenure must be between {loan_type.min_tenure_months} and {loan_type.max_tenure_months} months",
        )
    emi = calculate_emi(data.amount_requested, loan_type.interest_rate, data.tenure_months)
    app_number = generate_application_number()
    while db.query(LoanApplication).filter(LoanApplication.application_number == app_number).first():
        app_number = generate_application_number()

    application = LoanApplication(
        application_number=app_number,
        user_id=user_id,
        loan_type_id=data.loan_type_id,
        amount_requested=data.amount_requested,
        tenure_months=data.tenure_months,
        purpose=data.purpose,
        monthly_income=data.monthly_income,
        existing_emi=data.existing_emi or 0,
        collateral_details=data.collateral_details,
        status="submitted",
        emi_amount=emi,
        submitted_at=datetime.utcnow(),
    )
    db.add(application)
    db.flush()

    history = ApplicationStatusHistory(
        application_id=application.id,
        from_status=None,
        to_status="submitted",
        changed_by=user_id,
        remarks="Application submitted",
    )
    db.add(history)
    db.commit()
    db.refresh(application)
    return application


def get_application(db: Session, application_id: int, user_id: int = None, role: str = None) -> LoanApplication:
    query = (
        db.query(LoanApplication)
        .options(
            joinedload(LoanApplication.loan_type),
            joinedload(LoanApplication.applicant),
            joinedload(LoanApplication.assigned_officer),
            joinedload(LoanApplication.documents),
            joinedload(LoanApplication.status_history),
        )
        .filter(LoanApplication.id == application_id)
    )
    if role == "customer":
        query = query.filter(LoanApplication.user_id == user_id)
    app = query.first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


def get_user_applications(db: Session, user_id: int, status: str = None, page: int = 1, size: int = 10):
    query = (
        db.query(LoanApplication)
        .options(joinedload(LoanApplication.loan_type), joinedload(LoanApplication.assigned_officer))
        .filter(LoanApplication.user_id == user_id)
    )
    if status:
        query = query.filter(LoanApplication.status == status)
    total = query.count()
    items = query.order_by(LoanApplication.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return items, total


def get_all_applications(
    db: Session, status: str = None, loan_type_id: int = None,
    search: str = None, page: int = 1, size: int = 10
):
    query = (
        db.query(LoanApplication)
        .options(
            joinedload(LoanApplication.loan_type),
            joinedload(LoanApplication.applicant),
            joinedload(LoanApplication.assigned_officer),
        )
    )
    if status:
        query = query.filter(LoanApplication.status == status)
    if loan_type_id:
        query = query.filter(LoanApplication.loan_type_id == loan_type_id)
    if search:
        query = query.join(User, LoanApplication.user_id == User.id).filter(
            User.first_name.ilike(f"%{search}%")
            | User.last_name.ilike(f"%{search}%")
            | User.email.ilike(f"%{search}%")
            | LoanApplication.application_number.ilike(f"%{search}%")
        )
    total = query.count()
    items = query.order_by(LoanApplication.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return items, total


def update_application_status(
    db: Session, application_id: int, data: LoanApplicationUpdate, officer_id: int
) -> LoanApplication:
    app = db.query(LoanApplication).filter(LoanApplication.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    old_status = app.status
    if data.status:
        app.status = data.status
        if data.status in ("approved", "rejected"):
            app.reviewed_at = datetime.utcnow()
        if data.status == "approved":
            app.approved_at = datetime.utcnow()
            if data.approved_amount:
                app.approved_amount = data.approved_amount
            if data.approved_interest_rate:
                app.approved_interest_rate = data.approved_interest_rate
            if data.approved_tenure_months:
                app.approved_tenure_months = data.approved_tenure_months
            loan_type = db.query(LoanType).filter(LoanType.id == app.loan_type_id).first()
            rate = data.approved_interest_rate or loan_type.interest_rate
            amt = data.approved_amount or app.amount_requested
            tenure = data.approved_tenure_months or app.tenure_months
            app.emi_amount = calculate_emi(amt, rate, tenure)

    if data.assigned_officer_id is not None:
        app.assigned_officer_id = data.assigned_officer_id
        if app.status == "submitted":
            app.status = "under_review"
    if data.remarks:
        app.remarks = data.remarks
    if data.rejection_reason:
        app.rejection_reason = data.rejection_reason
    if data.credit_score:
        app.credit_score = data.credit_score

    if old_status != app.status:
        history = ApplicationStatusHistory(
            application_id=app.id,
            from_status=old_status,
            to_status=app.status,
            changed_by=officer_id,
            remarks=data.remarks or data.rejection_reason,
        )
        db.add(history)

    db.commit()
    db.refresh(app)
    return app


def get_analytics(db: Session) -> AnalyticsSummary:
    total = db.query(func.count(LoanApplication.id)).scalar()
    pending = db.query(func.count(LoanApplication.id)).filter(
        LoanApplication.status.in_(["submitted", "under_review"])
    ).scalar()
    approved = db.query(func.count(LoanApplication.id)).filter(LoanApplication.status == "approved").scalar()
    rejected = db.query(func.count(LoanApplication.id)).filter(LoanApplication.status == "rejected").scalar()
    disbursed = db.query(func.count(LoanApplication.id)).filter(LoanApplication.status == "disbursed").scalar()
    total_amount = db.query(func.sum(LoanApplication.amount_requested)).scalar() or 0
    approved_amount = db.query(func.sum(LoanApplication.approved_amount)).filter(
        LoanApplication.approved_amount != None
    ).scalar() or 0
    total_customers = db.query(func.count(User.id)).filter(User.role == "customer").scalar()
    this_month = db.query(func.count(LoanApplication.id)).filter(
        func.month(LoanApplication.created_at) == datetime.utcnow().month,
        func.year(LoanApplication.created_at) == datetime.utcnow().year,
    ).scalar()

    return AnalyticsSummary(
        total_applications=total,
        pending_applications=pending,
        approved_applications=approved,
        rejected_applications=rejected,
        disbursed_applications=disbursed,
        total_loan_amount=float(total_amount),
        approved_loan_amount=float(approved_amount),
        total_customers=total_customers,
        applications_this_month=this_month,
    )
