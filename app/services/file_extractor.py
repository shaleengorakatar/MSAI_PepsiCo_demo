"""
File text extraction service — supports PDF, DOCX, and plain text files.
"""
from __future__ import annotations

import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".text", ".md"}
SUPPORTED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
    "text/markdown",
}


def _extract_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file."""
    import pdfplumber

    text_parts: list[str] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n\n".join(text_parts)


def _extract_docx(file_bytes: bytes) -> str:
    """Extract text from a Word .docx file."""
    from docx import Document

    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def _extract_txt(file_bytes: bytes) -> str:
    """Decode plain text bytes, trying utf-8 first then latin-1."""
    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return file_bytes.decode("latin-1")


async def extract_text(
    file_bytes: bytes,
    filename: str,
    content_type: Optional[str] = None,
) -> str:
    """
    Extract text from an uploaded file.

    Supports:
      - PDF (.pdf)
      - Word (.docx)
      - Plain text (.txt, .md, .text)

    Returns the extracted text as a string.
    Raises ValueError if the file type is unsupported or extraction fails.
    """
    ext = ""
    if filename:
        ext = ("." + filename.rsplit(".", 1)[-1]).lower() if "." in filename else ""

    logger.info("Extracting text from file=%s ext=%s content_type=%s", filename, ext, content_type)

    # Determine type by extension first, then content_type
    if ext == ".pdf" or content_type == "application/pdf":
        text = _extract_pdf(file_bytes)
    elif ext in {".docx", ".doc"} or content_type in {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    }:
        text = _extract_docx(file_bytes)
    elif ext in {".txt", ".text", ".md"} or (content_type and content_type.startswith("text/")):
        text = _extract_txt(file_bytes)
    else:
        raise ValueError(
            f"Unsupported file type: {filename} ({content_type}). "
            f"Supported formats: PDF, DOCX, TXT, MD"
        )

    text = text.strip()
    if not text:
        raise ValueError(f"No text could be extracted from {filename}. The file may be empty or image-based.")

    logger.info("Extracted %d characters from %s", len(text), filename)
    return text
