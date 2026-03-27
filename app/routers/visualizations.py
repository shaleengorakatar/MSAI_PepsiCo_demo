"""
Router for visualization endpoints.
All endpoints support per-region filtering via query parameters.
"""
from __future__ import annotations

import json
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query

from app.database import get_db_connection
from app.visualization_functions import (
    DEFAULT_REGIONS,
    get_market_variations_with_details,
    compute_dashboard_data,
    compute_fit_gap_data,
    compute_standardization_data,
    compute_benchmark_data,
    compute_risk_heatmap_data,
)

router = APIRouter(prefix="/visualizations", tags=["Visualizations"])

@router.get(
    "/regions",
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
    print(f"🔍 Dashboard for baseline {baseline_id}, region: {region}, markets: {markets}")
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        cur = conn.cursor()
        
        # Get baseline info
        cur.execute("SELECT * FROM baselines WHERE baseline_id = ?", (baseline_id,))
        baseline = cur.fetchone()
        if not baseline:
            raise HTTPException(status_code=404, detail="Baseline not found")
        
        baseline_dict = dict(baseline)
        
        # Get market variations
        query = "SELECT * FROM market_variations WHERE baseline_id = ?"
        params = [baseline_id]
        
        if region:
            # Filter by region
            region_markets = []
            for r in DEFAULT_REGIONS:
                if r["code"] == region:
                    region_markets = r["markets"]
                    break
            if region_markets:
                query += " AND market_code IN ({})".format(",".join(["?" for _ in region_markets]))
                params.extend(region_markets)
        
        if markets:
            # Filter by specific markets
            market_list = [m.strip() for m in markets.split(",")]
            if region:
                query += " AND market_code IN ({})".format(",".join(["?" for _ in market_list]))
            else:
                query += " AND market_code IN ({})".format(",".join(["?" for _ in market_list]))
            params.extend(market_list)
        
        cur.execute(query, params)
        variations = [dict(row) for row in cur.fetchall()]
        
        # Compute dashboard data
        dashboard_data = compute_dashboard_data(baseline_dict, variations, region, markets)
        
        print(f"✅ Dashboard computed for {len(variations)} variations")
        return dashboard_data
        
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Fit-Gap Visualization
# ---------------------------------------------------------------------------

@router.get(
    "/fit-gap/{baseline_id}",
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
    print(f"🔍 Fit-gap for baseline {baseline_id}, region: {region}, markets: {markets}")
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        cur = conn.cursor()
        
        # Get baseline info
        cur.execute("SELECT * FROM baselines WHERE baseline_id = ?", (baseline_id,))
        baseline = cur.fetchone()
        if not baseline:
            raise HTTPException(status_code=404, detail="Baseline not found")
        
        baseline_dict = dict(baseline)
        
        # Get market variations with detailed data
        variations = get_market_variations_with_details(cur, baseline_id, region, markets)
        
        # Compute fit-gap data
        fit_gap_data = compute_fit_gap_data(baseline_dict, variations, region, markets)
        
        print(f"✅ Fit-gap computed for {len(variations)} variations")
        return fit_gap_data
        
    except Exception as e:
        print(f"❌ Fit-gap error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Control Standardization Heatmap
# ---------------------------------------------------------------------------

@router.get(
    "/standardization/{baseline_id}",
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
    print(f"🔍 Standardization for baseline {baseline_id}, region: {region}, markets: {markets}")
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        cur = conn.cursor()
        
        # Get baseline info
        cur.execute("SELECT * FROM baselines WHERE baseline_id = ?", (baseline_id,))
        baseline = cur.fetchone()
        if not baseline:
            raise HTTPException(status_code=404, detail="Baseline not found")
        
        baseline_dict = dict(baseline)
        
        # Get market variations with detailed data
        variations = get_market_variations_with_details(cur, baseline_id, region, markets)
        
        # Compute standardization data
        standardization_data = compute_standardization_data(baseline_dict, variations, region, markets)
        
        print(f"✅ Standardization computed for {len(variations)} variations")
        return standardization_data
        
    except Exception as e:
        print(f"❌ Standardization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Benchmarking / Best Practice Adoption
# ---------------------------------------------------------------------------

@router.get(
    "/benchmark/{baseline_id}",
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
    print(f"🔍 Benchmark for baseline {baseline_id}, region: {region}, markets: {markets}")
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        cur = conn.cursor()
        
        # Get baseline info
        cur.execute("SELECT * FROM baselines WHERE baseline_id = ?", (baseline_id,))
        baseline = cur.fetchone()
        if not baseline:
            raise HTTPException(status_code=404, detail="Baseline not found")
        
        baseline_dict = dict(baseline)
        
        # Get market variations with detailed data
        variations = get_market_variations_with_details(cur, baseline_id, region, markets)
        
        # Compute benchmark data
        benchmark_data = compute_benchmark_data(baseline_dict, variations, region, markets)
        
        print(f"✅ Benchmark computed for {len(variations)} variations")
        return benchmark_data
        
    except Exception as e:
        print(f"❌ Benchmark error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Risk Heatmap
# ---------------------------------------------------------------------------

@router.get(
    "/risk-heatmap/{baseline_id}",
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
    print(f"🔍 Risk heatmap for baseline {baseline_id}, region: {region}, markets: {markets}")
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        cur = conn.cursor()
        
        # Get baseline info
        cur.execute("SELECT * FROM baselines WHERE baseline_id = ?", (baseline_id,))
        baseline = cur.fetchone()
        if not baseline:
            raise HTTPException(status_code=404, detail="Baseline not found")
        
        baseline_dict = dict(baseline)
        
        # Get market variations with detailed data
        variations = get_market_variations_with_details(cur, baseline_id, region, markets)
        
        # Compute risk heatmap data
        risk_data = compute_risk_heatmap_data(baseline_dict, variations, region, markets)
        
        print(f"✅ Risk heatmap computed for {len(variations)} variations")
        return risk_data
        
    except Exception as e:
        print(f"❌ Risk heatmap error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
