"""
Visualization data models – structured for frontend charting libraries.
All models support per-region filtering.
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Region / Market metadata
# ---------------------------------------------------------------------------

class RegionDefinition(BaseModel):
    """Maps markets to regions for roll-up visualizations."""
    code: str = Field(..., description="Region code, e.g. 'EMEA', 'APAC', 'AMER', 'LATAM'")
    name: str
    market_codes: List[str] = Field(default_factory=list, description="ISO-3166-1 alpha-2 codes in this region")


# ---------------------------------------------------------------------------
# Fit-Gap Visualization
# ---------------------------------------------------------------------------

class MarketFitGapScore(BaseModel):
    market_code: str
    market_name: str
    region: str
    overall_score: float = Field(..., ge=0, le=100)
    aligned_count: int = 0
    partial_gap_count: int = 0
    full_gap_count: int = 0
    total_steps: int = 0


class RegionFitGapAggregate(BaseModel):
    region: str
    avg_score: float = Field(..., ge=0, le=100)
    min_score: float = Field(..., ge=0, le=100)
    max_score: float = Field(..., ge=0, le=100)
    market_count: int = 0
    markets: List[MarketFitGapScore] = Field(default_factory=list)


class FitGapDashboard(BaseModel):
    """Dashboard data for fit-gap visualization across all regions."""
    baseline_id: str
    baseline_name: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    global_avg_score: float = Field(default=0, ge=0, le=100)
    total_markets: int = 0
    regions: List[RegionFitGapAggregate] = Field(default_factory=list)
    all_markets: List[MarketFitGapScore] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Control Standardization / Variation Heatmap
# ---------------------------------------------------------------------------

class StepAdoptionEntry(BaseModel):
    """How a single global step is adopted across markets."""
    step_number: int
    step_title: str
    is_mandatory: bool = True
    adopted_count: int = 0
    modified_count: int = 0
    removed_count: int = 0
    total_markets: int = 0
    adoption_rate: float = Field(default=0, ge=0, le=100, description="Percentage of markets that adopt this step (fully or modified)")


class MarketStepStatus(BaseModel):
    market_code: str
    market_name: str
    region: str
    step_number: int
    status: str = Field(..., description="'adopted' | 'modified' | 'removed' | 'additional'")
    override_reason: Optional[str] = None


class ControlStandardizationHeatmap(BaseModel):
    """Heatmap data: rows = global steps, columns = markets, cells = adoption status."""
    baseline_id: str
    baseline_name: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    steps: List[StepAdoptionEntry] = Field(default_factory=list)
    cells: List[MarketStepStatus] = Field(default_factory=list)
    overall_standardization_rate: float = Field(default=0, ge=0, le=100)


# ---------------------------------------------------------------------------
# Benchmarking / Best Practice Adoption
# ---------------------------------------------------------------------------

class BenchmarkDimension(BaseModel):
    """Single dimension in a radar/spider chart for benchmarking."""
    dimension: str = Field(..., description="e.g. 'Process Coverage', 'Risk Mitigation', 'Automation Level'")
    global_benchmark: float = Field(..., ge=0, le=100, description="Global best-practice score")
    market_score: float = Field(..., ge=0, le=100)
    gap: float = Field(default=0, description="benchmark - market_score")


class MarketBenchmark(BaseModel):
    market_code: str
    market_name: str
    region: str
    composite_score: float = Field(default=0, ge=0, le=100)
    dimensions: List[BenchmarkDimension] = Field(default_factory=list)
    best_practices_adopted: int = 0
    best_practices_total: int = 0
    adoption_percentage: float = Field(default=0, ge=0, le=100)


class RegionBenchmarkAggregate(BaseModel):
    region: str
    avg_composite_score: float = Field(default=0, ge=0, le=100)
    avg_adoption_percentage: float = Field(default=0, ge=0, le=100)
    market_count: int = 0
    markets: List[MarketBenchmark] = Field(default_factory=list)


class BenchmarkDashboard(BaseModel):
    """Benchmarking dashboard across regions."""
    baseline_id: str
    baseline_name: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    global_benchmark_dimensions: List[str] = Field(default_factory=list)
    global_avg_composite: float = Field(default=0, ge=0, le=100)
    regions: List[RegionBenchmarkAggregate] = Field(default_factory=list)
    all_markets: List[MarketBenchmark] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Risk Heatmap (per region)
# ---------------------------------------------------------------------------

class MarketRiskSummary(BaseModel):
    market_code: str
    market_name: str
    region: str
    total_risks: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    risk_score: float = Field(default=0, ge=0, description="Weighted risk score")


class RegionRiskAggregate(BaseModel):
    region: str
    total_risks: int = 0
    avg_risk_score: float = 0
    highest_risk_market: Optional[str] = None
    markets: List[MarketRiskSummary] = Field(default_factory=list)


class RiskHeatmapDashboard(BaseModel):
    """Risk heatmap data across regions and markets."""
    baseline_id: str
    baseline_name: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    regions: List[RegionRiskAggregate] = Field(default_factory=list)
    all_markets: List[MarketRiskSummary] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Combined Overview
# ---------------------------------------------------------------------------

class MarketOverview(BaseModel):
    market_code: str
    market_name: str
    region: str
    fit_gap_score: float = Field(default=0, ge=0, le=100)
    standardization_rate: float = Field(default=0, ge=0, le=100)
    benchmark_score: float = Field(default=0, ge=0, le=100)
    risk_score: float = Field(default=0)
    overall_health: str = "healthy"


class RegionOverview(BaseModel):
    region: str
    market_count: int = 0
    avg_fit_gap: float = Field(default=0, ge=0, le=100)
    avg_standardization: float = Field(default=0, ge=0, le=100)
    avg_benchmark: float = Field(default=0, ge=0, le=100)
    avg_risk_score: float = Field(default=0)
    markets: List[MarketOverview] = Field(default_factory=list)


class GlobalDashboard(BaseModel):
    """Top-level dashboard combining all visualization dimensions."""
    baseline_id: str
    baseline_name: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    total_markets: int = 0
    total_regions: int = 0
    global_fit_gap_avg: float = Field(default=0, ge=0, le=100)
    global_standardization_avg: float = Field(default=0, ge=0, le=100)
    global_benchmark_avg: float = Field(default=0, ge=0, le=100)
    global_risk_avg: float = Field(default=0)
    regions: List[RegionOverview] = Field(default_factory=list)
