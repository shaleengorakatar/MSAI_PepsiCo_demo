"""Router for the Fit-Gap Engine."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.data.store import store
from app.models.schemas import FitGapRequest, FitGapResult
from app.services.fit_gap_engine import run_fit_gap
from app.services.llm_service import generate_ai_summary

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Fit-Gap Engine"])


@router.post(
    "/fit-gap",
    response_model=FitGapResult,
    summary="Run Fit-Gap analysis",
    description=(
        "Compares a Local Market Variation against its Global Baseline Control "
        "to identify gaps, partial alignments, extra controls, and produces "
        "a fit score (0-100) with actionable recommendations. "
        "Includes an AI-generated narrative summary with clickable source references."
    ),
)
async def fit_gap_analysis(request: FitGapRequest):
    baseline = store.get_baseline(request.baseline_id)
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline not found")

    variation = store.get_variation(request.market_id)
    if not variation:
        raise HTTPException(status_code=404, detail="Market variation not found")

    if variation.baseline_id != baseline.id:
        raise HTTPException(
            status_code=400,
            detail="Market variation does not belong to the specified baseline",
        )

    result = run_fit_gap(baseline, variation)

    # Generate AI summary with source references
    try:
        summary_data = await generate_ai_summary(
            result.model_dump(),
            context_label=f"Fit-Gap analysis: {variation.market_code} vs baseline {baseline.name.default}",
        )
        result.ai_summary = summary_data.get("ai_summary")
        result.ai_sources = summary_data.get("ai_sources", [])
    except Exception as e:
        logger.warning("AI summary generation failed for fit-gap: %s", e)

    return result
