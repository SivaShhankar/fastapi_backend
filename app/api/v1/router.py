from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, loans, documents

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(loans.router, prefix="/loans", tags=["Loans"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
