"""Router for Predictive Risk monitoring (nice-to-have)."""
from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, HTTPException

from app.data.store import store
from app.models.schemas import MonitoringReport, PerformanceDataPoint
from app.services.llm_service import generate_ai_summary
from app.services.risk_monitor import generate_mock_performance_data, run_predictive_risk_analysis

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Predictive Risk Monitoring"])


@router.post(
    "/monitoring/ingest",
    summary="Ingest performance data points",
    description="Submit performance data points (effectiveness scores, timing, etc.) for controls.",
)
async def ingest_performance_data(data_points: List[PerformanceDataPoint]):
    count = store.add_performance_data(data_points)
    return {"ingested": count, "total_stored": len(store.performance_data)}


@router.post(
    "/monitoring/generate-mock/{baseline_id}",
    summary="Generate mock performance data for a baseline",
    description="Creates synthetic performance data for demonstration and testing purposes.",
)
async def generate_mock_data(baseline_id: str):
    baseline = store.get_baseline(baseline_id)
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline not found")

    mock_data = generate_mock_performance_data(baseline)
    count = store.add_performance_data(mock_data)
    return {"generated": count, "baseline_id": baseline_id}


@router.get(
    "/monitoring/report/{baseline_id}",
    response_model=MonitoringReport,
    summary="Generate predictive risk report",
    description=(
        "Analyzes stored performance data for a baseline's controls and produces "
        "a predictive risk report with failure probabilities, trends, and recommendations."
    ),
)
async def get_risk_report(baseline_id: str):
    baseline = store.get_baseline(baseline_id)
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline not found")

    perf_data = store.get_performance_data()
    # Filter to data relevant to this baseline
    relevant_data = [
        p for p in perf_data if p.control_id.startswith(baseline_id)
    ]

    report = run_predictive_risk_analysis(baseline, relevant_data)

    # Generate AI summary with source references
    try:
        summary_data = await generate_ai_summary(
            report.model_dump(),
            context_label=f"Predictive Risk report for baseline: {baseline.name.default}",
        )
        report.ai_summary = summary_data.get("ai_summary")
        report.ai_sources = summary_data.get("ai_sources", [])
    except Exception as e:
        logger.warning("AI summary generation failed for monitoring: %s", e)

    return report
