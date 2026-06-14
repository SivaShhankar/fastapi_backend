from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.deps import get_current_user, get_current_admin, get_current_super_admin
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, UserListResponse

router = APIRouter()


@router.get("/", response_model=List[UserListResponse])
def list_users(
    role: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if search:
        query = query.filter(
            User.first_name.ilike(f"%{search}%")
            | User.last_name.ilike(f"%{search}%")
            | User.email.ilike(f"%{search}%")
        )
    return query.order_by(User.created_at.desc()).offset((page - 1) * size).limit(size).all()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "customer" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/me/profile", response_model=UserResponse)
def update_profile(
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/{user_id}/status")
def update_user_status(
    user_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_super_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = is_active
    db.commit()
    return {"message": f"User {'activated' if is_active else 'deactivated'} successfully"}


@router.post("/loan-officers", response_model=UserResponse)
def create_loan_officer(
    data: dict,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_super_admin),
):
    from app.core.security import get_password_hash
    existing = db.query(User).filter(User.email == data["email"]).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    officer = User(
        email=data["email"],
        hashed_password=get_password_hash(data["password"]),
        first_name=data["first_name"],
        last_name=data["last_name"],
        phone=data.get("phone"),
        role="loan_officer",
        is_active=True,
        is_verified=True,
    )
    db.add(officer)
    db.commit()
    db.refresh(officer)
    return officer


@router.get("/officers/list", response_model=List[UserListResponse])
def list_officers(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return db.query(User).filter(User.role.in_(["admin", "loan_officer"]), User.is_active == True).all()
