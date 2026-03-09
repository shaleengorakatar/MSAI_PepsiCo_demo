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
    CreateVariationFromAnalysisRequest,
    GlobalBaselineControl,
    ImplementationPlan,
    LocalMarketVariation,
    LocalOverride,
    MultiLangText,
    Risk as BaselineRisk,
)
from app.services.fit_gap_engine import run_fit_gap
from app.services.llm_service import (
    analyze_source_text,
    compare_analysis_to_baseline,
    generate_implementation_plan,
)

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


@router.post(
    "/analysis-to-variation",
    response_model=LocalMarketVariation,
    status_code=201,
    summary="Auto-create a Local Variation by comparing AI analysis against a Global Baseline",
    description=(
        "Takes the AI analysis of a local market's interviews/documents and compares "
        "it against an existing Global Baseline using LLM. Automatically detects "
        "overrides, removed steps, additional steps, and additional risks."
    ),
)
async def create_variation_from_analysis(request: CreateVariationFromAnalysisRequest):
    # Verify baseline exists
    baseline = store.get_baseline(request.baseline_id)
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline not found")

    # Use LLM to compare local analysis vs global baseline
    try:
        comparison = await compare_analysis_to_baseline(
            analysis_data=request.analysis.model_dump(),
            baseline_data=baseline.model_dump(),
            market_code=request.market_code,
        )
    except Exception as e:
        logger.exception("LLM comparison failed")
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")

    # Build overrides
    overrides = []
    for o in comparison.get("overrides", []):
        overrides.append(LocalOverride(
            step_number=o["step_number"],
            field=o.get("field", "description"),
            value=o.get("value", ""),
            reason=o.get("reason"),
        ))

    # Build additional steps
    additional_steps = []
    for s in comparison.get("additional_steps", []):
        additional_steps.append(ControlStep(
            step_number=s["step_number"],
            title=MultiLangText(default=s.get("title", "")),
            description=MultiLangText(default=s.get("description", "")),
            responsible_role=s.get("responsible_role"),
            is_mandatory=s.get("is_mandatory", True),
        ))

    # Build additional risks
    additional_risks = []
    for r in comparison.get("additional_risks", []):
        additional_risks.append(BaselineRisk(
            description=r.get("description", ""),
            severity=r.get("severity", "medium"),
            mitigating_controls=r.get("mitigating_controls", []),
        ))

    # Build notes
    notes_text = comparison.get("notes", "")
    notes = MultiLangText(default=notes_text) if notes_text else None

    # Create the variation
    variation = LocalMarketVariation(
        market_code=request.market_code,
        market_name=request.market_name,
        baseline_id=request.baseline_id,
        language=request.language,
        overrides=overrides,
        additional_steps=additional_steps,
        removed_step_numbers=comparison.get("removed_step_numbers", []),
        additional_risks=additional_risks,
        notes=notes,
    )

    stored = store.add_variation(variation)
    logger.info(
        "Created variation %s for market %s: %d overrides, %d removed, %d additional steps, %d additional risks",
        stored.id, request.market_code,
        len(overrides), len(variation.removed_step_numbers),
        len(additional_steps), len(additional_risks),
    )
    return stored


@router.get(
    "/implementation-plan/{variation_id}",
    response_model=ImplementationPlan,
    summary="Generate an AI implementation plan for a market",
    description=(
        "Given a Local Market Variation, runs fit-gap against its baseline, "
        "then uses AI to generate a prioritized implementation strategy "
        "with alternative mitigations where standard controls can't be applied."
    ),
)
async def get_implementation_plan(variation_id: str):
    # Get variation
    variation = store.get_variation(variation_id)
    if not variation:
        raise HTTPException(status_code=404, detail="Variation not found")

    # Get baseline
    baseline = store.get_baseline(variation.baseline_id)
    if not baseline:
        raise HTTPException(status_code=404, detail="Parent baseline not found")

    # Run fit-gap
    fit_gap_result = run_fit_gap(baseline, variation)

    # Generate implementation plan via LLM
    try:
        plan_data = await generate_implementation_plan(
            baseline_data=baseline.model_dump(),
            variation_data=variation.model_dump(),
            fit_gap_data=fit_gap_result.model_dump(),
            market_code=variation.market_code,
        )
    except Exception as e:
        logger.exception("Implementation plan generation failed")
        raise HTTPException(status_code=500, detail=f"Plan generation failed: {str(e)}")

    return ImplementationPlan(
        variation_id=variation_id,
        market_code=variation.market_code,
        market_name=variation.market_name,
        baseline_id=baseline.id,
        baseline_name=baseline.name.default,
        fit_gap_score=fit_gap_result.overall_score,
        executive_summary=plan_data.get("executive_summary", ""),
        steps=plan_data.get("steps", []),
        alternative_mitigations=plan_data.get("alternative_mitigations", []),
        estimated_total_effort=plan_data.get("estimated_total_effort", ""),
    )
