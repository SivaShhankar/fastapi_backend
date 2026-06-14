from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import os, shutil, uuid
from app.core.database import get_db
from app.core.deps import get_current_user, get_current_admin
from app.core.config import settings
from app.models.loan import Document, LoanApplication
from app.models.user import User
from app.schemas.loan import DocumentResponse

router = APIRouter()

ALLOWED_TYPES = {
    "application/pdf", "image/jpeg", "image/png", "image/jpg",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    application_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="File type not allowed")
    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    if application_id:
        app = db.query(LoanApplication).filter(
            LoanApplication.id == application_id,
            LoanApplication.user_id == current_user.id,
        ).first()
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")

    ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid.uuid4()}{ext}"
    user_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
    os.makedirs(user_dir, exist_ok=True)
    file_path = os.path.join(user_dir, unique_name)

    with open(file_path, "wb") as f:
        f.write(contents)

    doc = Document(
        application_id=application_id,
        user_id=current_user.id,
        document_type=document_type,
        document_name=file.filename,
        file_path=file_path,
        file_size=len(contents),
        mime_type=file.content_type,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.get("/my-documents", response_model=list[DocumentResponse])
def my_documents(
    application_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Document).filter(Document.user_id == current_user.id)
    if application_id:
        query = query.filter(Document.application_id == application_id)
    return query.order_by(Document.uploaded_at.desc()).all()


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.user_id != current_user.id and current_user.role not in ["admin"]:
        raise HTTPException(status_code=403, detail="Access denied")
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    db.delete(doc)
    db.commit()
    return {"message": "Document deleted"}


@router.put("/{document_id}/verify")
def verify_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.is_verified = True
    doc.verified_by = current_user.id
    db.commit()
    return {"message": "Document verified"}
