from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.core.database import engine, SessionLocal
from app.models import user, loan  # noqa — registers models
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    from app.core.database import Base
    Base.metadata.create_all(bind=engine)
    # Seed database
    db = SessionLocal()
    try:
        from app.utils.seed import seed_database
        seed_database(db)
    finally:
        db.close()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.PROJECT_NAME}
