"""Router for the /analyze-source AI processing pipeline."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import AnalyzeSourceRequest, AnalyzeSourceResponse
from app.services.llm_service import analyze_source_text

logger = logging.getLogger(__name__)
router = APIRouter(tags=["AI Analysis"])


@router.post(
    "/analyze-source",
    response_model=AnalyzeSourceResponse,
    summary="Analyze source text (interviews/SOPs) with LLM",
    description=(
        "Ingests raw text from interviews, SOPs, or process documents and uses an LLM "
        "to extract standardized process steps, risks with mitigating controls, and "
        "inefficiencies (bottlenecks). Supports multi-language input."
    ),
)
async def analyze_source(request: AnalyzeSourceRequest):
    try:
        result = await analyze_source_text(
            text=request.text,
            context=request.context,
            language=request.language,
        )

        return AnalyzeSourceResponse(
            process_steps=result.get("process_steps", []),
            risks=result.get("risks", []),
            inefficiencies=result.get("inefficiencies", []),
            change_impacts=result.get("change_impacts", []),
            future_current_state_map=result.get("future_current_state_map", []),
            summary=result.get("summary", ""),
            source_language=request.language,
        )
    except Exception as e:
        logger.exception("LLM analysis failed")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
