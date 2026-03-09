"""Router for file-upload-based analysis."""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.models.schemas import AnalyzeSourceResponse
from app.services.file_extractor import extract_text
from app.services.llm_service import analyze_source_text

logger = logging.getLogger(__name__)
router = APIRouter(tags=["File Upload Analysis"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post(
    "/analyze-file",
    response_model=AnalyzeSourceResponse,
    summary="Upload a document (PDF, DOCX, TXT) and analyze with LLM",
    description=(
        "Accepts a file upload containing interview transcripts, SOPs, or process "
        "documents. Extracts the text, then runs the same AI analysis pipeline as "
        "/analyze-source. Supported formats: PDF, DOCX, TXT, MD."
    ),
)
async def analyze_file(
    file: UploadFile = File(..., description="PDF, DOCX, or TXT file to analyze"),
    language: str = Form(default="en", description="ISO-639-1 language code"),
    context: Optional[str] = Form(default=None, description="Optional context about the process domain"),
):
    # Validate file size
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(file_bytes)} bytes). Maximum is {MAX_FILE_SIZE} bytes (10 MB).",
        )

    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Extract text from file
    try:
        text = await extract_text(
            file_bytes=file_bytes,
            filename=file.filename or "unknown",
            content_type=file.content_type,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    logger.info("Extracted %d chars from %s, sending to LLM", len(text), file.filename)

    # Run through the same LLM analysis pipeline
    try:
        result = await analyze_source_text(
            text=text,
            context=context,
            language=language,
        )

        return AnalyzeSourceResponse(
            process_steps=result.get("process_steps", []),
            risks=result.get("risks", []),
            inefficiencies=result.get("inefficiencies", []),
            change_impacts=result.get("change_impacts", []),
            future_current_state_map=result.get("future_current_state_map", []),
            summary=result.get("summary", ""),
            source_language=language,
        )
    except Exception as e:
        logger.exception("LLM analysis failed for uploaded file %s", file.filename)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
