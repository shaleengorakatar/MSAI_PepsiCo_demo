"""
Fit-Gap Engine – compares a Local Market Variation against its Global Baseline
Control to identify gaps, extra controls, and produce a fit score.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Set

from app.models.schemas import (
    ControlStep,
    FitGapResult,
    GapStatus,
    GlobalBaselineControl,
    LocalMarketVariation,
    StepComparison,
)


def _resolve_local_steps(
    baseline: GlobalBaselineControl,
    variation: LocalMarketVariation,
) -> dict:
    """Build a picture of the local market's effective process."""
    lang = variation.language

    # Start from global steps, apply overrides and removals
    local_step_map: dict[int, dict] = {}
    for step in baseline.process_steps:
        if step.step_number in variation.removed_step_numbers:
            continue
        local_step_map[step.step_number] = {
            "title": step.title.get(lang),
            "description": step.description.get(lang),
            "responsible_role": step.responsible_role,
            "is_mandatory": step.is_mandatory,
        }

    # Apply overrides
    for override in variation.overrides:
        if override.step_number in local_step_map:
            local_step_map[override.step_number][override.field] = override.value

    return local_step_map


def run_fit_gap(
    baseline: GlobalBaselineControl,
    variation: LocalMarketVariation,
) -> FitGapResult:
    """Compare local market variation against global baseline."""

    lang = variation.language
    local_step_map = _resolve_local_steps(baseline, variation)

    comparisons: List[StepComparison] = []
    missing_controls: List[str] = []
    extra_controls: List[str] = []
    recommendations: List[str] = []

    global_step_numbers: Set[int] = {s.step_number for s in baseline.process_steps}
    local_step_numbers: Set[int] = set(local_step_map.keys())

    total_global = len(global_step_numbers)
    aligned_count = 0

    # Compare each global step
    for step in baseline.process_steps:
        sn = step.step_number
        global_title = step.title.get(lang)

        if sn in variation.removed_step_numbers:
            status = GapStatus.FULL_GAP
            comparisons.append(StepComparison(
                step_number=sn,
                global_title=global_title,
                local_title=None,
                status=status,
                details=f"Step removed in market {variation.market_code}",
            ))
            missing_controls.append(global_title)
            if step.is_mandatory:
                recommendations.append(
                    f"CRITICAL: Mandatory step '{global_title}' is missing in {variation.market_code}. "
                    f"Re-evaluate removal or add compensating control."
                )
        elif sn in local_step_map:
            local_info = local_step_map[sn]
            # Check for modifications
            has_override = any(o.step_number == sn for o in variation.overrides)
            if has_override:
                status = GapStatus.PARTIAL_GAP
                comparisons.append(StepComparison(
                    step_number=sn,
                    global_title=global_title,
                    local_title=local_info["title"],
                    status=status,
                    details=f"Step modified locally. Review overrides for compliance.",
                ))
                aligned_count += 0.5
            else:
                status = GapStatus.ALIGNED
                comparisons.append(StepComparison(
                    step_number=sn,
                    global_title=global_title,
                    local_title=local_info["title"],
                    status=status,
                    details="Fully aligned with global baseline.",
                ))
                aligned_count += 1

    # Additional local steps not in global
    for add_step in variation.additional_steps:
        extra_controls.append(add_step.title.get(lang))
        comparisons.append(StepComparison(
            step_number=add_step.step_number,
            global_title="(not in global baseline)",
            local_title=add_step.title.get(lang),
            status=GapStatus.PARTIAL_GAP,
            details=f"Additional local step in {variation.market_code}. "
                    f"Consider promoting to global if broadly applicable.",
        ))

    # Additional local risks
    if variation.additional_risks:
        recommendations.append(
            f"{variation.market_code} has {len(variation.additional_risks)} additional risk(s) "
            f"not in the global baseline. Review for global relevance."
        )

    # Score
    overall_score = (aligned_count / total_global * 100) if total_global > 0 else 100.0

    return FitGapResult(
        baseline_id=baseline.id,
        market_id=variation.id,
        market_code=variation.market_code,
        overall_score=round(overall_score, 1),
        step_comparisons=comparisons,
        missing_controls=missing_controls,
        extra_controls=extra_controls,
        recommendations=recommendations,
        analyzed_at=datetime.utcnow(),
    )
