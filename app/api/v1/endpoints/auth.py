from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import decode_token, create_access_token
from app.schemas.user import UserCreate, LoginRequest, Token, UserResponse, ChangePasswordRequest
from app.services.auth_service import register_user, authenticate_user
from app.core.security import verify_password, get_password_hash
from app.models.user import User

router = APIRouter()


@router.post("/register", response_model=Token)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    user = register_user(db, user_data)
    from app.core.security import create_access_token, create_refresh_token
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    return Token(access_token=access_token, refresh_token=refresh_token, user=user)


@router.post("/login", response_model=Token)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    return authenticate_user(db, login_data)


@router.post("/refresh", response_model=dict)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    new_access = create_access_token(data={"sub": str(user.id)})
    return {"access_token": new_access, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    current_user.hashed_password = get_password_hash(data.new_password)
    db.commit()
    return {"message": "Password changed successfully"}
