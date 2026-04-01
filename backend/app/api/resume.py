from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.auth import AuthUser, get_current_user
from app.core.embeddings import generate_embedding
from app.core.resume_parser import parse_resume
from app.core.resume_store import get_resume as get_stored_resume
from app.core.resume_store import save_resume

router = APIRouter(prefix="/resume", tags=["resume"])

MAX_RESUME_BYTES = 10 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    user: AuthUser = Depends(get_current_user),
) -> dict[str, object]:
    filename = file.filename or ""
    extension = f".{filename.rsplit('.', 1)[-1].lower()}" if "." in filename else ""
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF and DOCX/DOC files are supported")

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid content type")

    data = await file.read()
    if len(data) > MAX_RESUME_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File exceeds 10MB limit")

    resume_id = str(uuid.uuid4())
    parsed = parse_resume(filename)
    document = {
        "id": resume_id,
        "owner": user.email,
        "file_name": filename,
        "file_size": len(data),
        "content_type": file.content_type,
        "parsed": parsed,
        "embedding": generate_embedding(
            " ".join(
                [
                    str(parsed.get("target_role", "")),
                    " ".join(parsed.get("skills", [])),
                    str(parsed.get("summary", "")),
                ]
            )
        ),
    }
    return save_resume(resume_id, document)


@router.get("/{resume_id}", status_code=200)
def get_resume(resume_id: str, user: AuthUser = Depends(get_current_user)) -> dict[str, object]:
    resume = get_stored_resume(resume_id)
    if resume is None or resume.get("owner") != user.email:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    return resume
