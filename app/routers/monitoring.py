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
        "a predictive risk report with failure probabilities, trends, and recommendations. "
        "If no performance data exists, automatically generates mock data for demonstration."
    ),
)
async def get_risk_report(baseline_id: str, generate_mock: bool = True):
    baseline = store.get_baseline(baseline_id)
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline not found")

    perf_data = store.get_performance_data()
    # Filter to data relevant to this baseline
    relevant_data = [
        p for p in perf_data if p.control_id.startswith(baseline_id)
    ]

    # Auto-generate mock data if none exists and generate_mock is True
    if not relevant_data and generate_mock:
        logger.info(f"No performance data found for baseline {baseline_id}. Generating mock data...")
        mock_data = generate_mock_performance_data(baseline)
        store.add_performance_data(mock_data)
        relevant_data = mock_data
        logger.info(f"Generated {len(mock_data)} mock performance data points")

    if not relevant_data:
        raise HTTPException(
            status_code=404, 
            detail=f"No monitoring data has been ingested for baseline {baseline_id}. "
                   f"Use POST /monitoring/generate-mock/{baseline_id} to generate sample data."
        )

    report = run_predictive_risk_analysis(baseline, relevant_data)

    # Add data source information
    report.ai_summary = report.ai_summary or f"Risk report generated for baseline {baseline.name.default} "
    if not relevant_data:
        report.ai_summary += "using simulated performance data."
    else:
        report.ai_summary += f"based on {len(relevant_data)} performance data points."

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


@router.get(
    "/monitoring/status/{baseline_id}",
    summary="Check monitoring data status for baseline",
    description="Returns information about available performance data for a baseline.",
)
async def get_monitoring_status(baseline_id: str):
    baseline = store.get_baseline(baseline_id)
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline not found")

    perf_data = store.get_performance_data()
    relevant_data = [
        p for p in perf_data if p.control_id.startswith(baseline_id)
    ]

    return {
        "baseline_id": baseline_id,
        "baseline_name": baseline.name.default,
        "has_data": len(relevant_data) > 0,
        "data_points_count": len(relevant_data),
        "latest_timestamp": max([p.timestamp for p in relevant_data]) if relevant_data else None,
        "can_generate_report": True,
        "recommendation": "Use GET /monitoring/report/{baseline_id} to generate risk report" if len(relevant_data) > 0 
                           else "Use POST /monitoring/generate-mock/{baseline_id} to generate sample data first"
    }
