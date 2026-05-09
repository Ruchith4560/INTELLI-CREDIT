from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import os, uuid, shutil, logging
from app.database import get_db
from app import models
from app.utils.auth import get_current_user
from app.services.document_parser import parse_document
from app.services.data_validator import validate_document

router     = APIRouter()
UPLOAD_DIR = "uploads"
logger     = logging.getLogger(__name__)
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".csv", ".xlsx", ".xls", ".txt"}


def _detect_doc_type(filename: str, ext: str) -> str:
    name = filename.lower()
    if "gst" in name or "gstr" in name:
        return "gst"
    if "bank" in name or "statement" in name or "ledger" in name:
        return "bank_statement"
    if "annual" in name or "report" in name or "ar " in name:
        return "annual_report"
    if ext in (".csv", ".xlsx", ".xls"):
        return "csv"
    return "other"


@router.post("/upload-documents")
async def upload_documents(
    files:        List[UploadFile]  = File(...),
    company_name: str               = Form(...),
    session_id:   Optional[str]     = Form(None),
    db:           Session           = Depends(get_db),
    current_user: models.User       = Depends(get_current_user),
):
    if not session_id:
        session_id = str(uuid.uuid4())

    uploaded = []
    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            uploaded.append({"filename": file.filename, "status": "rejected", "reason": f"Unsupported type: {ext}"})
            continue

        unique_name = f"{uuid.uuid4()}_{file.filename}"
        file_path   = os.path.join(UPLOAD_DIR, unique_name)

        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        doc_type = _detect_doc_type(file.filename, ext)

        doc = models.UploadedDocument(
            user_id=current_user.id,
            filename=file.filename,
            file_path=file_path,
            doc_type=doc_type,
            company_name=company_name,
            session_id=session_id,
            status="uploaded",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Parse document (sync — fast enough for demo)
        try:
            extracted  = parse_document(file_path, doc_type, ext)
            validation = validate_document(extracted, doc_type)
            doc.extracted_text = extracted.get("text", "")[:50000]   # cap at 50 KB
            doc.status         = "processed"
            db.commit()
            logger.info(f"✅ Parsed {file.filename} | confidence={validation.get('confidence_score')}")
        except Exception as e:
            doc.status = "failed"
            db.commit()
            logger.error(f"Parse failed for {file.filename}: {e}")

        uploaded.append({
            "id":         doc.id,
            "filename":   file.filename,
            "doc_type":   doc_type,
            "status":     doc.status,
            "session_id": session_id,
        })

    return {"session_id": session_id, "documents": uploaded, "company_name": company_name}


@router.get("/session/{session_id}")
def get_session_docs(
    session_id:   str,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    docs = db.query(models.UploadedDocument).filter(
        models.UploadedDocument.session_id == session_id
    ).all()
    return {
        "documents": [
            {"id": d.id, "filename": d.filename, "doc_type": d.doc_type, "status": d.status}
            for d in docs
        ]
    }


@router.get("/my-sessions")
def get_my_sessions(
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    docs     = db.query(models.UploadedDocument).filter(
        models.UploadedDocument.user_id == current_user.id
    ).order_by(models.UploadedDocument.created_at.desc()).all()
    sessions: dict = {}
    for d in docs:
        if d.session_id not in sessions:
            sessions[d.session_id] = {
                "session_id":   d.session_id,
                "company_name": d.company_name,
                "created_at":   str(d.created_at),
                "doc_count":    0,
            }
        sessions[d.session_id]["doc_count"] += 1
    return {"sessions": list(sessions.values())}
