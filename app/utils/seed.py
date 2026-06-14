from sqlalchemy.orm import Session
from app.models.loan import LoanType, LoanApplication, ApplicationStatusHistory
from app.models.user import User
from app.core.security import get_password_hash
from datetime import datetime, timedelta
import random


LOAN_TYPES = [
    {
        "name": "Personal Loan",
        "code": "PERSONAL",
        "interest_rate": 10.5,
        "min_amount": 10000,
        "max_amount": 1000000,
        "min_tenure_months": 12,
        "max_tenure_months": 60,
        "description": "Quick personal loans for your immediate needs — medical, travel, wedding, or any personal expense.",
        "required_documents": ["PAN Card", "Aadhar Card", "Salary Slips (3 months)", "Bank Statement (6 months)"],
    },
    {
        "name": "Home Loan",
        "code": "HOME",
        "interest_rate": 8.5,
        "min_amount": 500000,
        "max_amount": 10000000,
        "min_tenure_months": 60,
        "max_tenure_months": 360,
        "description": "Make your dream home a reality with our affordable home loans at competitive interest rates.",
        "required_documents": ["PAN Card", "Aadhar Card", "Property Documents", "Income Proof", "Bank Statement (12 months)"],
    },
    {
        "name": "Vehicle Loan",
        "code": "VEHICLE",
        "interest_rate": 9.25,
        "min_amount": 50000,
        "max_amount": 2500000,
        "min_tenure_months": 12,
        "max_tenure_months": 84,
        "description": "Drive your dream vehicle home today with flexible two-wheeler and four-wheeler loan options.",
        "required_documents": ["PAN Card", "Aadhar Card", "Vehicle Quotation", "Salary Slips", "Bank Statement"],
    },
    {
        "name": "Business Loan",
        "code": "BUSINESS",
        "interest_rate": 12.0,
        "min_amount": 100000,
        "max_amount": 5000000,
        "min_tenure_months": 12,
        "max_tenure_months": 120,
        "description": "Fuel your business growth with our flexible business loans designed for SMEs and entrepreneurs.",
        "required_documents": ["PAN Card", "Aadhar Card", "Business Registration", "ITR (2 years)", "Bank Statement (12 months)", "GST Returns"],
    },
]


def seed_database(db: Session):
    # Seed loan types
    for lt_data in LOAN_TYPES:
        existing = db.query(LoanType).filter(LoanType.code == lt_data["code"]).first()
        if not existing:
            lt = LoanType(**lt_data)
            db.add(lt)
    db.commit()

    # Create admin
    admin = db.query(User).filter(User.email == "admin@loanportal.com").first()
    if not admin:
        admin = User(
            email="admin@loanportal.com",
            hashed_password=get_password_hash("Admin@1234"),
            first_name="Super",
            last_name="Admin",
            phone="9999999999",
            role="admin",
            is_active=True,
            is_verified=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

    # Create loan officer
    officer = db.query(User).filter(User.email == "officer@loanportal.com").first()
    if not officer:
        officer = User(
            email="officer@loanportal.com",
            hashed_password=get_password_hash("Officer@1234"),
            first_name="Rajesh",
            last_name="Kumar",
            phone="8888888888",
            role="loan_officer",
            is_active=True,
            is_verified=True,
        )
        db.add(officer)
        db.commit()
        db.refresh(officer)

    # Create demo customer
    customer = db.query(User).filter(User.email == "customer@loanportal.com").first()
    if not customer:
        customer = User(
            email="customer@loanportal.com",
            hashed_password=get_password_hash("Customer@1234"),
            first_name="Priya",
            last_name="Sharma",
            phone="7777777777",
            role="customer",
            is_active=True,
            is_verified=True,
            annual_income=600000,
            employment_type="Salaried",
            employer_name="Tech Solutions Pvt Ltd",
            city="Mumbai",
            state="Maharashtra",
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

    # Seed demo applications
    loan_types = db.query(LoanType).all()
    loan_type_map = {lt.code: lt for lt in loan_types}

    demo_apps = [
        {"type": "PERSONAL", "amount": 250000, "tenure": 24, "status": "approved", "purpose": "Medical emergency"},
        {"type": "HOME", "amount": 3500000, "tenure": 240, "status": "under_review", "purpose": "Purchase of flat in Mumbai"},
        {"type": "VEHICLE", "amount": 800000, "tenure": 60, "status": "rejected", "purpose": "Purchase of Honda City"},
        {"type": "BUSINESS", "amount": 1500000, "tenure": 48, "status": "submitted", "purpose": "Business expansion"},
    ]

    import math
    def calc_emi(p, r, n):
        mr = r / (12 * 100)
        if mr == 0: return p / n
        return round(p * mr * math.pow(1 + mr, n) / (math.pow(1 + mr, n) - 1), 2)

    existing_apps = db.query(LoanApplication).filter(LoanApplication.user_id == customer.id).count()
    if existing_apps == 0:
        for i, app_data in enumerate(demo_apps):
            lt = loan_type_map[app_data["type"]]
            emi = calc_emi(app_data["amount"], lt.interest_rate, app_data["tenure"])
            app_num = f"LN{datetime.now().year}{str(i+1).zfill(8)}"
            app = LoanApplication(
                application_number=app_num,
                user_id=customer.id,
                loan_type_id=lt.id,
                amount_requested=app_data["amount"],
                tenure_months=app_data["tenure"],
                purpose=app_data["purpose"],
                status=app_data["status"],
                monthly_income=50000,
                existing_emi=5000,
                emi_amount=emi,
                assigned_officer_id=officer.id if app_data["status"] != "submitted" else None,
                submitted_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                approved_amount=app_data["amount"] if app_data["status"] == "approved" else None,
                approved_at=datetime.utcnow() - timedelta(days=2) if app_data["status"] == "approved" else None,
                credit_score=random.randint(650, 800),
            )
            db.add(app)
            db.flush()
            history = ApplicationStatusHistory(
                application_id=app.id,
                from_status=None,
                to_status="submitted",
                changed_by=customer.id,
                remarks="Application submitted",
            )
            db.add(history)
            if app_data["status"] != "submitted":
                history2 = ApplicationStatusHistory(
                    application_id=app.id,
                    from_status="submitted",
                    to_status=app_data["status"],
                    changed_by=officer.id,
                    remarks=f"Status updated to {app_data['status']}",
                )
                db.add(history2)
        db.commit()

    print("✅ Database seeded successfully!")
    print("   Admin: admin@loanportal.com / Admin@1234")
    print("   Officer: officer@loanportal.com / Officer@1234")
    print("   Customer: customer@loanportal.com / Customer@1234")
