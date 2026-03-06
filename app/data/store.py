"""
In-memory data store.
Replace with a real database (PostgreSQL, MongoDB, etc.) for production.
"""
from __future__ import annotations

from typing import Dict, List

from app.models.schemas import (
    GlobalBaselineControl,
    LocalMarketVariation,
    PerformanceDataPoint,
)


class DataStore:
    def __init__(self) -> None:
        self.baselines: Dict[str, GlobalBaselineControl] = {}
        self.variations: Dict[str, LocalMarketVariation] = {}
        self.performance_data: List[PerformanceDataPoint] = []

    # -- Baselines ----------------------------------------------------------
    def add_baseline(self, baseline: GlobalBaselineControl) -> GlobalBaselineControl:
        self.baselines[baseline.id] = baseline
        return baseline

    def get_baseline(self, baseline_id: str) -> GlobalBaselineControl | None:
        return self.baselines.get(baseline_id)

    def list_baselines(self) -> List[GlobalBaselineControl]:
        return list(self.baselines.values())

    def delete_baseline(self, baseline_id: str) -> bool:
        return self.baselines.pop(baseline_id, None) is not None

    # -- Variations ---------------------------------------------------------
    def add_variation(self, variation: LocalMarketVariation) -> LocalMarketVariation:
        self.variations[variation.id] = variation
        return variation

    def get_variation(self, variation_id: str) -> LocalMarketVariation | None:
        return self.variations.get(variation_id)

    def list_variations(self, baseline_id: str | None = None) -> List[LocalMarketVariation]:
        items = list(self.variations.values())
        if baseline_id:
            items = [v for v in items if v.baseline_id == baseline_id]
        return items

    def delete_variation(self, variation_id: str) -> bool:
        return self.variations.pop(variation_id, None) is not None

    # -- Performance data ---------------------------------------------------
    def add_performance_data(self, points: List[PerformanceDataPoint]) -> int:
        self.performance_data.extend(points)
        return len(points)

    def get_performance_data(self, control_id: str | None = None) -> List[PerformanceDataPoint]:
        if control_id:
            return [p for p in self.performance_data if p.control_id == control_id]
        return list(self.performance_data)


store = DataStore()
