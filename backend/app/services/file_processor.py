"""File upload processing -- extract text from PDF, DOCX, plain-text, and images.

Matches the n8n Switch4 node which routes files by MIME type:
  PDF        -> PyPDF2
  Plain Text -> direct read
  Image      -> base64 (for vision models)
  DOCX       -> python-docx (n8n handles via application/zip)
"""

from __future__ import annotations

import io
from dataclasses import dataclass

from docx import Document as DocxDocument
from PIL import Image
from PyPDF2 import PdfReader


@dataclass(frozen=True)
class ExtractedFile:
    filename: str
    mime_type: str
    extracted_text: str
    char_count: int


def extract_pdf(file_bytes: bytes, filename: str) -> ExtractedFile:
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n\n".join(pages).strip()
    return ExtractedFile(
        filename=filename,
        mime_type="application/pdf",
        extracted_text=text,
        char_count=len(text),
    )


def extract_docx(file_bytes: bytes, filename: str) -> ExtractedFile:
    doc = DocxDocument(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    text = "\n\n".join(paragraphs).strip()
    return ExtractedFile(
        filename=filename,
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        extracted_text=text,
        char_count=len(text),
    )


def extract_plain_text(file_bytes: bytes, filename: str) -> ExtractedFile:
    text = file_bytes.decode("utf-8", errors="replace").strip()
    return ExtractedFile(
        filename=filename,
        mime_type="text/plain",
        extracted_text=text,
        char_count=len(text),
    )


def extract_image_description(file_bytes: bytes, filename: str) -> ExtractedFile:
    """Return basic image metadata.  Actual OCR / vision analysis is deferred
    to the LLM (which receives the base64-encoded image)."""
    img = Image.open(io.BytesIO(file_bytes))
    description = f"Image: {filename} ({img.format}, {img.size[0]}x{img.size[1]})"
    return ExtractedFile(
        filename=filename,
        mime_type=f"image/{(img.format or 'unknown').lower()}",
        extracted_text=description,
        char_count=len(description),
    )


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

_MIME_HANDLERS = {
    "application/pdf": extract_pdf,
    "text/plain": extract_plain_text,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": extract_docx,
    "application/zip": extract_docx,  # n8n treats DOCX uploads as zip
}


def process_file(file_bytes: bytes, filename: str, mime_type: str) -> ExtractedFile:
    """Route *file_bytes* to the correct extractor based on *mime_type*."""

    if mime_type in _MIME_HANDLERS:
        return _MIME_HANDLERS[mime_type](file_bytes, filename)

    if mime_type.startswith("image/"):
        return extract_image_description(file_bytes, filename)

    # Fallback: treat as plain text
    return extract_plain_text(file_bytes, filename)
