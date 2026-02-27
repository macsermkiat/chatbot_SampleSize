"""File upload API -- POST /api/upload."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile

from app.models import FileUploadResponse
from app.services.file_processor import process_file

router = APIRouter(prefix="/api", tags=["files"])

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile):
    """Upload a file (PDF, DOCX, image, or text) and extract its text content."""

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds 20 MB limit.")

    mime = file.content_type or "application/octet-stream"
    result = process_file(contents, file.filename, mime)

    return FileUploadResponse(
        filename=result.filename,
        mime_type=result.mime_type,
        extracted_text=result.extracted_text,
        char_count=result.char_count,
    )
