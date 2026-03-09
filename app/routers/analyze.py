"""Router for the /analyze-source AI processing pipeline."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.data.store import store
from app.models.schemas import (
    AnalyzeSourceRequest,
    AnalyzeSourceResponse,
    ControlStep,
    CreateBaselineFromAnalysisRequest,
    GlobalBaselineControl,
    MultiLangText,
    Risk as BaselineRisk,
)
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


@router.post(
    "/analysis-to-baseline",
    response_model=GlobalBaselineControl,
    status_code=201,
    summary="Create a Global Baseline from AI analysis results",
    description=(
        "Converts the output of /analyze-source or /analyze-file into a "
        "Global Baseline Control. Maps AI-extracted process steps and risks "
        "into the baseline format so users don't have to re-enter data manually."
    ),
)
async def create_baseline_from_analysis(request: CreateBaselineFromAnalysisRequest):
    analysis = request.analysis

    # Convert AI process steps → baseline ControlSteps
    control_steps = []
    for step in analysis.process_steps:
        control_steps.append(
            ControlStep(
                step_number=step.step_number,
                title=MultiLangText(default=step.title),
                description=MultiLangText(default=step.description),
                responsible_role=step.responsible_role,
                is_mandatory=True,
            )
        )

    # Convert AI risks → baseline Risks
    baseline_risks = []
    for risk in analysis.risks:
        baseline_risks.append(
            BaselineRisk(
                description=risk.description,
                severity=risk.severity,
                mitigating_controls=risk.mitigating_controls,
            )
        )

    # Build the baseline
    baseline = GlobalBaselineControl(
        name=MultiLangText(default=request.baseline_name),
        description=MultiLangText(
            default=request.baseline_description or analysis.summary
        ),
        process_steps=control_steps,
        risks=baseline_risks,
        version=request.version,
    )

    # Store it
    stored = store.add_baseline(baseline)
    logger.info("Created baseline %s from analysis with %d steps and %d risks",
                stored.id, len(control_steps), len(baseline_risks))
    return stored
