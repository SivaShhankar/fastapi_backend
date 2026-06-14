from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import timedelta
from app.models.user import User
from app.schemas.user import UserCreate, LoginRequest, Token
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token


def register_user(db: Session, user_data: UserCreate) -> User:
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        role="customer",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, login_data: LoginRequest) -> Token:
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is inactive")
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user,
    )
