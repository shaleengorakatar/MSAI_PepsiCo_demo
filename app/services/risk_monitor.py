"""
Predictive Risk monitoring module.
Analyzes mock performance data to flag potential control failures.
"""
from __future__ import annotations

import random
from datetime import datetime
from typing import List

from app.models.schemas import (
    ControlEffectiveness,
    GlobalBaselineControl,
    MonitoringReport,
    PerformanceDataPoint,
    RiskPrediction,
)


def _compute_trend(values: List[float]) -> str:
    """Simple linear trend from recent data points."""
    if len(values) < 2:
        return "stable"
    recent = values[-3:]  # last 3 points
    diffs = [recent[i + 1] - recent[i] for i in range(len(recent) - 1)]
    avg_diff = sum(diffs) / len(diffs)
    if avg_diff > 0.05:
        return "improving"
    elif avg_diff < -0.05:
        return "degrading"
    return "stable"


def _effectiveness_from_score(score: float) -> ControlEffectiveness:
    if score >= 0.8:
        return ControlEffectiveness.EFFECTIVE
    elif score >= 0.5:
        return ControlEffectiveness.PARTIALLY_EFFECTIVE
    return ControlEffectiveness.INEFFECTIVE


def generate_mock_performance_data(baseline: GlobalBaselineControl) -> List[PerformanceDataPoint]:
    """Generate mock performance data for demonstration purposes."""
    points: List[PerformanceDataPoint] = []
    for step in baseline.process_steps:
        # Generate 5 mock data points per step
        for i in range(5):
            points.append(PerformanceDataPoint(
                control_id=f"{baseline.id}_step_{step.step_number}",
                metric_name="effectiveness_score",
                value=round(random.uniform(0.3, 1.0), 2),
            ))
            points.append(PerformanceDataPoint(
                control_id=f"{baseline.id}_step_{step.step_number}",
                metric_name="execution_time_ratio",
                value=round(random.uniform(0.5, 2.0), 2),
            ))
    return points


def run_predictive_risk_analysis(
    baseline: GlobalBaselineControl,
    performance_data: List[PerformanceDataPoint],
) -> MonitoringReport:
    """Analyze performance data and predict control failures."""

    # Group data by control_id
    control_data: dict[str, List[PerformanceDataPoint]] = {}
    for dp in performance_data:
        control_data.setdefault(dp.control_id, []).append(dp)

    predictions: List[RiskPrediction] = []

    for step in baseline.process_steps:
        control_id = f"{baseline.id}_step_{step.step_number}"
        control_name = step.title.get("en")

        points = control_data.get(control_id, [])

        # Separate metrics
        effectiveness_scores = [
            p.value for p in points if p.metric_name == "effectiveness_score"
        ]
        time_ratios = [
            p.value for p in points if p.metric_name == "execution_time_ratio"
        ]

        if not effectiveness_scores:
            # No data → unknown risk
            predictions.append(RiskPrediction(
                control_id=control_id,
                control_name=control_name,
                current_effectiveness=ControlEffectiveness.PARTIALLY_EFFECTIVE,
                failure_probability=0.5,
                trend="stable",
                risk_factors=["No performance data available"],
                recommended_actions=["Collect baseline performance metrics"],
            ))
            continue

        avg_effectiveness = sum(effectiveness_scores) / len(effectiveness_scores)
        trend = _compute_trend(effectiveness_scores)
        effectiveness = _effectiveness_from_score(avg_effectiveness)

        risk_factors: List[str] = []
        actions: List[str] = []

        # Failure probability heuristic
        failure_prob = max(0.0, min(1.0, 1.0 - avg_effectiveness))

        if trend == "degrading":
            failure_prob = min(1.0, failure_prob + 0.15)
            risk_factors.append("Effectiveness trend is degrading")
            actions.append("Investigate root cause of declining performance")

        if time_ratios:
            avg_time_ratio = sum(time_ratios) / len(time_ratios)
            if avg_time_ratio > 1.5:
                risk_factors.append(
                    f"Execution time {avg_time_ratio:.1f}x above expected duration"
                )
                actions.append("Review process for bottlenecks or resource constraints")
                failure_prob = min(1.0, failure_prob + 0.1)

        if effectiveness == ControlEffectiveness.INEFFECTIVE:
            risk_factors.append("Control effectiveness below acceptable threshold")
            actions.append("Redesign control or add compensating measures")

        if not risk_factors:
            risk_factors.append("No significant risk factors detected")
            actions.append("Continue monitoring at current frequency")

        predictions.append(RiskPrediction(
            control_id=control_id,
            control_name=control_name,
            current_effectiveness=effectiveness,
            failure_probability=round(failure_prob, 2),
            trend=trend,
            risk_factors=risk_factors,
            recommended_actions=actions,
        ))

    # Overall health
    high_risk = [p for p in predictions if p.failure_probability >= 0.6]
    if len(high_risk) >= len(predictions) * 0.5:
        overall_health = "critical"
    elif high_risk:
        overall_health = "at_risk"
    else:
        overall_health = "healthy"

    return MonitoringReport(
        generated_at=datetime.utcnow(),
        predictions=predictions,
        high_risk_count=len(high_risk),
        overall_health=overall_health,
    )
