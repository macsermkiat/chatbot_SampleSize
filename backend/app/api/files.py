"""File upload API -- POST /api/upload."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, UploadFile

from app.models import FileUploadResponse
from app.services.file_processor import process_file

_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["files"])

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB

_MAX_AGENT_CHARS = 30_000  # Must match helpers._MAX_FILE_CHARS

_QUALITY_WARNINGS: dict[str, str] = {
    "empty": (
        "No text could be extracted from this file. It may be a scanned document "
        "or image-only PDF. The assistant will have limited ability to read its content."
    ),
    "partial": (
        "Only a small amount of text was extracted. Some content may be missing."
    ),
    "metadata_only": (
        "Only image metadata was extracted. The assistant cannot read text from images yet."
    ),
}

_ALLOWED_MIME_PREFIXES = (
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/zip",
    "text/plain",
    "image/",
)


def _is_allowed_mime(mime: str) -> bool:
    return any(mime.startswith(prefix) for prefix in _ALLOWED_MIME_PREFIXES)


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile):
    """Upload a file (PDF, DOCX, image, or text) and extract its text content."""

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    mime = file.content_type or "application/octet-stream"

    if not _is_allowed_mime(mime):
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{mime}'. Accepted: PDF, DOCX, TXT, and images.",
        )

    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds 20 MB limit.")

    try:
        result = process_file(contents, file.filename, mime)
    except Exception as exc:
        _logger.warning("File processing failed for %s: %s", file.filename, exc)
        raise HTTPException(
            status_code=422,
            detail=f"Could not process '{file.filename}'. The file may be corrupt or in an unsupported format.",
        ) from exc

    warning = _QUALITY_WARNINGS.get(result.extraction_quality)
    if not warning and result.char_count > _MAX_AGENT_CHARS:
        warning = (
            f"This document is large ({result.char_count:,} characters). "
            f"The assistant will use the first {_MAX_AGENT_CHARS:,} characters."
        )

    return FileUploadResponse(
        filename=result.filename,
        mime_type=result.mime_type,
        extracted_text=result.extracted_text,
        char_count=result.char_count,
        has_tables=result.has_tables,
        extraction_quality=result.extraction_quality,
        warning=warning,
    )
