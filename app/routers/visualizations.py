"""
Router for visualization endpoints.
All endpoints support per-region filtering via query parameters.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.data.store import store
from app.models.visualization import (
    BenchmarkDashboard,
    ControlStandardizationHeatmap,
    FitGapDashboard,
    GlobalDashboard,
    RegionDefinition,
    RiskHeatmapDashboard,
)
from app.services.visualization_service import (
    DEFAULT_REGIONS,
    compute_benchmark_dashboard,
    compute_fit_gap_dashboard,
    compute_global_dashboard,
    compute_risk_heatmap,
    compute_standardization_heatmap,
)

router = APIRouter(prefix="/visualizations", tags=["Visualizations"])


# ---------------------------------------------------------------------------
# Region definitions
# ---------------------------------------------------------------------------

@router.get(
    "/regions",
    response_model=List[RegionDefinition],
    summary="List available region definitions",
    description="Returns the default region-to-market mapping used for aggregation and filtering.",
)
async def list_regions():
    return DEFAULT_REGIONS


# ---------------------------------------------------------------------------
# Global Dashboard (combined overview)
# ---------------------------------------------------------------------------

@router.get(
    "/dashboard/{baseline_id}",
    response_model=GlobalDashboard,
    summary="Global dashboard overview",
    description=(
        "Combined overview of fit-gap, standardization, benchmarking, and risk "
        "across all regions and markets. Filterable by region and specific markets."
    ),
)
async def global_dashboard(
    baseline_id: str,
    region: Optional[str] = Query(None, description="Filter by region code (e.g. EMEA, APAC, AMER, LATAM)"),
    markets: Optional[str] = Query(None, description="Comma-separated market codes to filter (e.g. US,GB,DE)"),
):
    baseline = store.get_baseline(baseline_id)
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline not found")

    variations = store.list_variations(baseline_id)
    market_list = [m.strip() for m in markets.split(",")] if markets else None

    return compute_global_dashboard(baseline, variations, filter_region=region, filter_markets=market_list)


# ---------------------------------------------------------------------------
# Fit-Gap Visualization
# ---------------------------------------------------------------------------

@router.get(
    "/fit-gap/{baseline_id}",
    response_model=FitGapDashboard,
    summary="Fit-gap scores per region and market",
    description=(
        "Bar/map chart data showing fit-gap alignment scores for each market, "
        "aggregated by region. Use to visualize which regions/markets deviate from the global baseline."
    ),
)
async def fit_gap_dashboard(
    baseline_id: str,
    region: Optional[str] = Query(None, description="Filter by region code"),
    markets: Optional[str] = Query(None, description="Comma-separated market codes"),
):
    baseline = store.get_baseline(baseline_id)
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline not found")

    variations = store.list_variations(baseline_id)
    market_list = [m.strip() for m in markets.split(",")] if markets else None

    return compute_fit_gap_dashboard(baseline, variations, filter_region=region, filter_markets=market_list)


# ---------------------------------------------------------------------------
# Control Standardization Heatmap
# ---------------------------------------------------------------------------

@router.get(
    "/standardization/{baseline_id}",
    response_model=ControlStandardizationHeatmap,
    summary="Control standardization heatmap",
    description=(
        "Heatmap data where rows are global control steps and columns are markets. "
        "Each cell shows whether the step is adopted, modified, removed, or additional. "
        "Filterable by region to see standardization within a specific geography."
    ),
)
async def standardization_heatmap(
    baseline_id: str,
    region: Optional[str] = Query(None, description="Filter by region code"),
    markets: Optional[str] = Query(None, description="Comma-separated market codes"),
):
    baseline = store.get_baseline(baseline_id)
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline not found")

    variations = store.list_variations(baseline_id)
    market_list = [m.strip() for m in markets.split(",")] if markets else None

    return compute_standardization_heatmap(baseline, variations, filter_region=region, filter_markets=market_list)


# ---------------------------------------------------------------------------
# Benchmarking / Best Practice Adoption
# ---------------------------------------------------------------------------

@router.get(
    "/benchmark/{baseline_id}",
    response_model=BenchmarkDashboard,
    summary="Benchmarking & best practice adoption (radar/spider chart data)",
    description=(
        "Radar chart data comparing each market against global best-practice benchmarks "
        "across dimensions like Process Coverage, Risk Mitigation, Automation Level, etc. "
        "Aggregated by region for roll-up views."
    ),
)
async def benchmark_dashboard(
    baseline_id: str,
    region: Optional[str] = Query(None, description="Filter by region code"),
    markets: Optional[str] = Query(None, description="Comma-separated market codes"),
):
    baseline = store.get_baseline(baseline_id)
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline not found")

    variations = store.list_variations(baseline_id)
    market_list = [m.strip() for m in markets.split(",")] if markets else None

    return compute_benchmark_dashboard(baseline, variations, filter_region=region, filter_markets=market_list)


# ---------------------------------------------------------------------------
# Risk Heatmap
# ---------------------------------------------------------------------------

@router.get(
    "/risk-heatmap/{baseline_id}",
    response_model=RiskHeatmapDashboard,
    summary="Risk heatmap per region and market",
    description=(
        "Heatmap/treemap data showing risk distribution across markets and regions. "
        "Shows risk counts by severity and a weighted risk score per market."
    ),
)
async def risk_heatmap(
    baseline_id: str,
    region: Optional[str] = Query(None, description="Filter by region code"),
    markets: Optional[str] = Query(None, description="Comma-separated market codes"),
):
    baseline = store.get_baseline(baseline_id)
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline not found")

    variations = store.list_variations(baseline_id)
    market_list = [m.strip() for m in markets.split(",")] if markets else None

    return compute_risk_heatmap(baseline, variations, filter_region=region, filter_markets=market_list)
