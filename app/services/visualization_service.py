"""
Visualization aggregation service.
Computes per-region, per-market chart data from baselines, variations, and fit-gap results.
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Set

from app.data.store import store
from app.models.schemas import (
    GapStatus,
    GlobalBaselineControl,
    LocalMarketVariation,
    RiskSeverity,
)
from app.models.visualization import (
    BenchmarkDashboard,
    BenchmarkDimension,
    ControlStandardizationHeatmap,
    FitGapDashboard,
    GlobalDashboard,
    MarketBenchmark,
    MarketFitGapScore,
    MarketOverview,
    MarketRiskSummary,
    MarketStepStatus,
    RegionBenchmarkAggregate,
    RegionDefinition,
    RegionFitGapAggregate,
    RegionOverview,
    RegionRiskAggregate,
    RiskHeatmapDashboard,
    StepAdoptionEntry,
)
from app.services.fit_gap_engine import run_fit_gap

# ---------------------------------------------------------------------------
# Default region mapping (can be overridden via API)
# ---------------------------------------------------------------------------
DEFAULT_REGIONS: List[RegionDefinition] = [
    RegionDefinition(code="EMEA", name="Europe, Middle East & Africa",
                     market_codes=["GB", "DE", "FR", "IT", "ES", "NL", "BE", "CH", "AT",
                                   "SE", "NO", "DK", "FI", "PL", "CZ", "IE", "PT", "GR",
                                   "AE", "SA", "ZA", "NG", "KE", "EG", "IL", "TR"]),
    RegionDefinition(code="APAC", name="Asia Pacific",
                     market_codes=["CN", "JP", "KR", "IN", "AU", "NZ", "SG", "HK", "TW",
                                   "TH", "MY", "ID", "PH", "VN", "BD", "PK", "LK"]),
    RegionDefinition(code="AMER", name="Americas",
                     market_codes=["US", "CA"]),
    RegionDefinition(code="LATAM", name="Latin America",
                     market_codes=["BR", "MX", "AR", "CL", "CO", "PE", "VE", "EC", "UY"]),
]


def _get_region(market_code: str, regions: List[RegionDefinition]) -> str:
    """Resolve a market code to its region."""
    for r in regions:
        if market_code.upper() in r.market_codes:
            return r.code
    return "OTHER"


def _risk_weight(severity: RiskSeverity) -> float:
    return {"critical": 4.0, "high": 3.0, "medium": 2.0, "low": 1.0}.get(severity.value, 1.0)


# ---------------------------------------------------------------------------
# Fit-Gap Dashboard
# ---------------------------------------------------------------------------

def compute_fit_gap_dashboard(
    baseline: GlobalBaselineControl,
    variations: List[LocalMarketVariation],
    regions: List[RegionDefinition] | None = None,
    filter_region: str | None = None,
    filter_markets: List[str] | None = None,
) -> FitGapDashboard:
    regions = regions or DEFAULT_REGIONS
    market_scores: List[MarketFitGapScore] = []

    for var in variations:
        if var.baseline_id != baseline.id:
            continue

        region_code = _get_region(var.market_code, regions)

        if filter_region and region_code != filter_region.upper():
            continue
        if filter_markets and var.market_code not in filter_markets:
            continue

        result = run_fit_gap(baseline, var)

        aligned = sum(1 for c in result.step_comparisons if c.status == GapStatus.ALIGNED)
        partial = sum(1 for c in result.step_comparisons if c.status == GapStatus.PARTIAL_GAP)
        full = sum(1 for c in result.step_comparisons if c.status == GapStatus.FULL_GAP)

        market_scores.append(MarketFitGapScore(
            market_code=var.market_code,
            market_name=var.market_name,
            region=region_code,
            overall_score=result.overall_score,
            aligned_count=aligned,
            partial_gap_count=partial,
            full_gap_count=full,
            total_steps=len(result.step_comparisons),
        ))

    # Aggregate by region
    region_map: Dict[str, List[MarketFitGapScore]] = {}
    for ms in market_scores:
        region_map.setdefault(ms.region, []).append(ms)

    region_aggs: List[RegionFitGapAggregate] = []
    for rcode, markets in sorted(region_map.items()):
        scores = [m.overall_score for m in markets]
        region_aggs.append(RegionFitGapAggregate(
            region=rcode,
            avg_score=round(sum(scores) / len(scores), 1) if scores else 0,
            min_score=round(min(scores), 1) if scores else 0,
            max_score=round(max(scores), 1) if scores else 0,
            market_count=len(markets),
            markets=markets,
        ))

    all_scores = [m.overall_score for m in market_scores]
    global_avg = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0

    return FitGapDashboard(
        baseline_id=baseline.id,
        baseline_name=baseline.name.default,
        global_avg_score=global_avg,
        total_markets=len(market_scores),
        regions=region_aggs,
        all_markets=market_scores,
    )


# ---------------------------------------------------------------------------
# Control Standardization Heatmap
# ---------------------------------------------------------------------------

def compute_standardization_heatmap(
    baseline: GlobalBaselineControl,
    variations: List[LocalMarketVariation],
    regions: List[RegionDefinition] | None = None,
    filter_region: str | None = None,
    filter_markets: List[str] | None = None,
) -> ControlStandardizationHeatmap:
    regions = regions or DEFAULT_REGIONS
    cells: List[MarketStepStatus] = []
    step_stats: Dict[int, Dict[str, int]] = {}  # step_number -> {adopted, modified, removed}

    # Init step stats
    for step in baseline.process_steps:
        step_stats[step.step_number] = {"adopted": 0, "modified": 0, "removed": 0}

    relevant_vars = [v for v in variations if v.baseline_id == baseline.id]
    if filter_region:
        relevant_vars = [v for v in relevant_vars if _get_region(v.market_code, regions) == filter_region.upper()]
    if filter_markets:
        relevant_vars = [v for v in relevant_vars if v.market_code in filter_markets]

    total_markets = len(relevant_vars)

    for var in relevant_vars:
        region_code = _get_region(var.market_code, regions)
        override_steps: Set[int] = {o.step_number for o in var.overrides}

        for step in baseline.process_steps:
            sn = step.step_number
            if sn in var.removed_step_numbers:
                status = "removed"
                step_stats[sn]["removed"] += 1
            elif sn in override_steps:
                status = "modified"
                step_stats[sn]["modified"] += 1
            else:
                status = "adopted"
                step_stats[sn]["adopted"] += 1

            override_reason = None
            for o in var.overrides:
                if o.step_number == sn:
                    override_reason = o.reason
                    break

            cells.append(MarketStepStatus(
                market_code=var.market_code,
                market_name=var.market_name,
                region=region_code,
                step_number=sn,
                status=status,
                override_reason=override_reason,
            ))

        # Additional local steps
        for add_step in var.additional_steps:
            cells.append(MarketStepStatus(
                market_code=var.market_code,
                market_name=var.market_name,
                region=region_code,
                step_number=add_step.step_number,
                status="additional",
            ))

    # Build step adoption entries
    step_entries: List[StepAdoptionEntry] = []
    total_adopted_or_modified = 0
    total_possible = 0
    for step in baseline.process_steps:
        sn = step.step_number
        stats = step_stats[sn]
        adopted = stats["adopted"] + stats["modified"]
        rate = (adopted / total_markets * 100) if total_markets > 0 else 0
        total_adopted_or_modified += adopted
        total_possible += total_markets

        step_entries.append(StepAdoptionEntry(
            step_number=sn,
            step_title=step.title.get("en"),
            is_mandatory=step.is_mandatory,
            adopted_count=stats["adopted"],
            modified_count=stats["modified"],
            removed_count=stats["removed"],
            total_markets=total_markets,
            adoption_rate=round(rate, 1),
        ))

    overall_rate = (total_adopted_or_modified / total_possible * 100) if total_possible > 0 else 0

    return ControlStandardizationHeatmap(
        baseline_id=baseline.id,
        baseline_name=baseline.name.default,
        steps=step_entries,
        cells=cells,
        overall_standardization_rate=round(overall_rate, 1),
    )


# ---------------------------------------------------------------------------
# Benchmarking Dashboard
# ---------------------------------------------------------------------------

BENCHMARK_DIMENSIONS = [
    "Process Coverage",
    "Risk Mitigation",
    "Control Effectiveness",
    "Automation Level",
    "Documentation Quality",
    "Regulatory Compliance",
]


def compute_benchmark_dashboard(
    baseline: GlobalBaselineControl,
    variations: List[LocalMarketVariation],
    regions: List[RegionDefinition] | None = None,
    filter_region: str | None = None,
    filter_markets: List[str] | None = None,
) -> BenchmarkDashboard:
    regions = regions or DEFAULT_REGIONS
    market_benchmarks: List[MarketBenchmark] = []

    relevant_vars = [v for v in variations if v.baseline_id == baseline.id]
    if filter_region:
        relevant_vars = [v for v in relevant_vars if _get_region(v.market_code, regions) == filter_region.upper()]
    if filter_markets:
        relevant_vars = [v for v in relevant_vars if v.market_code in filter_markets]

    total_global_steps = len(baseline.process_steps)

    for var in relevant_vars:
        region_code = _get_region(var.market_code, regions)
        result = run_fit_gap(baseline, var)

        # Compute benchmark dimensions based on fit-gap data
        adopted = sum(1 for c in result.step_comparisons if c.status == GapStatus.ALIGNED)
        partial = sum(1 for c in result.step_comparisons if c.status == GapStatus.PARTIAL_GAP)

        process_coverage = result.overall_score
        risk_mitigation = max(0, 100 - len(var.additional_risks) * 10 - len(result.missing_controls) * 15)
        control_eff = (adopted + partial * 0.5) / total_global_steps * 100 if total_global_steps > 0 else 0
        automation = max(0, 100 - len(var.overrides) * 5)
        doc_quality = 100 if var.notes else 70
        regulatory = 100 - len(var.removed_step_numbers) * 10

        dims = [
            BenchmarkDimension(dimension="Process Coverage", global_benchmark=100, market_score=round(process_coverage, 1), gap=round(100 - process_coverage, 1)),
            BenchmarkDimension(dimension="Risk Mitigation", global_benchmark=100, market_score=round(max(0, risk_mitigation), 1), gap=round(max(0, 100 - risk_mitigation), 1)),
            BenchmarkDimension(dimension="Control Effectiveness", global_benchmark=100, market_score=round(control_eff, 1), gap=round(100 - control_eff, 1)),
            BenchmarkDimension(dimension="Automation Level", global_benchmark=100, market_score=round(max(0, automation), 1), gap=round(max(0, 100 - automation), 1)),
            BenchmarkDimension(dimension="Documentation Quality", global_benchmark=100, market_score=round(doc_quality, 1), gap=round(100 - doc_quality, 1)),
            BenchmarkDimension(dimension="Regulatory Compliance", global_benchmark=100, market_score=round(max(0, regulatory), 1), gap=round(max(0, 100 - regulatory), 1)),
        ]

        composite = round(sum(d.market_score for d in dims) / len(dims), 1)
        mandatory_steps = {s.step_number for s in baseline.process_steps if s.is_mandatory}
        adopted_mandatory = mandatory_steps - set(var.removed_step_numbers)
        bp_adopted = len(adopted_mandatory)
        bp_total = len(mandatory_steps)
        adoption_pct = (bp_adopted / bp_total * 100) if bp_total > 0 else 100

        market_benchmarks.append(MarketBenchmark(
            market_code=var.market_code,
            market_name=var.market_name,
            region=region_code,
            composite_score=composite,
            dimensions=dims,
            best_practices_adopted=bp_adopted,
            best_practices_total=bp_total,
            adoption_percentage=round(adoption_pct, 1),
        ))

    # Aggregate by region
    region_map: Dict[str, List[MarketBenchmark]] = {}
    for mb in market_benchmarks:
        region_map.setdefault(mb.region, []).append(mb)

    region_aggs: List[RegionBenchmarkAggregate] = []
    for rcode, markets in sorted(region_map.items()):
        composites = [m.composite_score for m in markets]
        adoptions = [m.adoption_percentage for m in markets]
        region_aggs.append(RegionBenchmarkAggregate(
            region=rcode,
            avg_composite_score=round(sum(composites) / len(composites), 1) if composites else 0,
            avg_adoption_percentage=round(sum(adoptions) / len(adoptions), 1) if adoptions else 0,
            market_count=len(markets),
            markets=markets,
        ))

    all_composites = [m.composite_score for m in market_benchmarks]
    global_avg = round(sum(all_composites) / len(all_composites), 1) if all_composites else 0

    return BenchmarkDashboard(
        baseline_id=baseline.id,
        baseline_name=baseline.name.default,
        global_benchmark_dimensions=BENCHMARK_DIMENSIONS,
        global_avg_composite=global_avg,
        regions=region_aggs,
        all_markets=market_benchmarks,
    )


# ---------------------------------------------------------------------------
# Risk Heatmap
# ---------------------------------------------------------------------------

def compute_risk_heatmap(
    baseline: GlobalBaselineControl,
    variations: List[LocalMarketVariation],
    regions: List[RegionDefinition] | None = None,
    filter_region: str | None = None,
    filter_markets: List[str] | None = None,
) -> RiskHeatmapDashboard:
    regions = regions or DEFAULT_REGIONS
    market_risks: List[MarketRiskSummary] = []

    relevant_vars = [v for v in variations if v.baseline_id == baseline.id]
    if filter_region:
        relevant_vars = [v for v in relevant_vars if _get_region(v.market_code, regions) == filter_region.upper()]
    if filter_markets:
        relevant_vars = [v for v in relevant_vars if v.market_code in filter_markets]

    for var in relevant_vars:
        region_code = _get_region(var.market_code, regions)

        # Combine baseline risks + market additional risks
        all_risks = list(baseline.risks) + list(var.additional_risks)

        critical = sum(1 for r in all_risks if r.severity == RiskSeverity.CRITICAL)
        high = sum(1 for r in all_risks if r.severity == RiskSeverity.HIGH)
        medium = sum(1 for r in all_risks if r.severity == RiskSeverity.MEDIUM)
        low = sum(1 for r in all_risks if r.severity == RiskSeverity.LOW)

        risk_score = sum(_risk_weight(r.severity) for r in all_risks)

        # Extra risk from removed mandatory steps
        removed_mandatory = [
            s for s in baseline.process_steps
            if s.step_number in var.removed_step_numbers and s.is_mandatory
        ]
        risk_score += len(removed_mandatory) * 5.0

        market_risks.append(MarketRiskSummary(
            market_code=var.market_code,
            market_name=var.market_name,
            region=region_code,
            total_risks=len(all_risks),
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low,
            risk_score=round(risk_score, 1),
        ))

    # Aggregate by region
    region_map: Dict[str, List[MarketRiskSummary]] = {}
    for mr in market_risks:
        region_map.setdefault(mr.region, []).append(mr)

    region_aggs: List[RegionRiskAggregate] = []
    for rcode, markets in sorted(region_map.items()):
        scores = [m.risk_score for m in markets]
        highest = max(markets, key=lambda m: m.risk_score) if markets else None
        region_aggs.append(RegionRiskAggregate(
            region=rcode,
            total_risks=sum(m.total_risks for m in markets),
            avg_risk_score=round(sum(scores) / len(scores), 1) if scores else 0,
            highest_risk_market=highest.market_code if highest else None,
            markets=markets,
        ))

    return RiskHeatmapDashboard(
        baseline_id=baseline.id,
        baseline_name=baseline.name.default,
        regions=region_aggs,
        all_markets=market_risks,
    )


# ---------------------------------------------------------------------------
# Global Dashboard (combined overview)
# ---------------------------------------------------------------------------

def compute_global_dashboard(
    baseline: GlobalBaselineControl,
    variations: List[LocalMarketVariation],
    regions: List[RegionDefinition] | None = None,
    filter_region: str | None = None,
    filter_markets: List[str] | None = None,
) -> GlobalDashboard:
    regions = regions or DEFAULT_REGIONS

    fitgap = compute_fit_gap_dashboard(baseline, variations, regions, filter_region, filter_markets)
    heatmap = compute_standardization_heatmap(baseline, variations, regions, filter_region, filter_markets)
    benchmark = compute_benchmark_dashboard(baseline, variations, regions, filter_region, filter_markets)
    risk = compute_risk_heatmap(baseline, variations, regions, filter_region, filter_markets)

    # Build combined market overviews
    market_overviews: Dict[str, MarketOverview] = {}

    for m in fitgap.all_markets:
        market_overviews[m.market_code] = MarketOverview(
            market_code=m.market_code,
            market_name=m.market_name,
            region=m.region,
            fit_gap_score=m.overall_score,
        )

    for m in benchmark.all_markets:
        if m.market_code in market_overviews:
            market_overviews[m.market_code].benchmark_score = m.composite_score
            market_overviews[m.market_code].standardization_rate = m.adoption_percentage

    for m in risk.all_markets:
        if m.market_code in market_overviews:
            market_overviews[m.market_code].risk_score = m.risk_score
            if m.risk_score >= 15:
                market_overviews[m.market_code].overall_health = "critical"
            elif m.risk_score >= 8:
                market_overviews[m.market_code].overall_health = "at_risk"

    all_markets = list(market_overviews.values())

    # Aggregate by region
    region_map: Dict[str, List[MarketOverview]] = {}
    for mo in all_markets:
        region_map.setdefault(mo.region, []).append(mo)

    region_overviews: List[RegionOverview] = []
    for rcode, markets in sorted(region_map.items()):
        region_overviews.append(RegionOverview(
            region=rcode,
            market_count=len(markets),
            avg_fit_gap=round(sum(m.fit_gap_score for m in markets) / len(markets), 1) if markets else 0,
            avg_standardization=round(sum(m.standardization_rate for m in markets) / len(markets), 1) if markets else 0,
            avg_benchmark=round(sum(m.benchmark_score for m in markets) / len(markets), 1) if markets else 0,
            avg_risk_score=round(sum(m.risk_score for m in markets) / len(markets), 1) if markets else 0,
            markets=markets,
        ))

    return GlobalDashboard(
        baseline_id=baseline.id,
        baseline_name=baseline.name.default,
        total_markets=len(all_markets),
        total_regions=len(region_overviews),
        global_fit_gap_avg=fitgap.global_avg_score,
        global_standardization_avg=heatmap.overall_standardization_rate,
        global_benchmark_avg=benchmark.global_avg_composite,
        global_risk_avg=round(sum(m.risk_score for m in risk.all_markets) / len(risk.all_markets), 1) if risk.all_markets else 0,
        regions=region_overviews,
    )
