"""Router for Global Baseline Controls and Local Market Variations CRUD."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.data.store import store
from app.models.schemas import GlobalBaselineControl, LocalMarketVariation

router = APIRouter(tags=["Global / Local Controls"])


# ---------------------------------------------------------------------------
# Global Baseline Controls
# ---------------------------------------------------------------------------

@router.post(
    "/baselines",
    response_model=GlobalBaselineControl,
    status_code=201,
    summary="Create a Global Baseline Control",
)
async def create_baseline(baseline: GlobalBaselineControl):
    return store.add_baseline(baseline)


@router.get(
    "/baselines",
    response_model=List[GlobalBaselineControl],
    summary="List all Global Baseline Controls",
)
async def list_baselines():
    return store.list_baselines()


@router.get(
    "/baselines/{baseline_id}",
    response_model=GlobalBaselineControl,
    summary="Get a Global Baseline Control by ID",
)
async def get_baseline(baseline_id: str):
    baseline = store.get_baseline(baseline_id)
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline not found")
    return baseline


@router.put(
    "/baselines/{baseline_id}",
    response_model=GlobalBaselineControl,
    summary="Update a Global Baseline Control",
)
async def update_baseline(baseline_id: str, updated: GlobalBaselineControl):
    existing = store.get_baseline(baseline_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Baseline not found")
    updated.id = baseline_id
    updated.updated_at = datetime.utcnow()
    store.baselines[baseline_id] = updated
    return updated


@router.delete(
    "/baselines/{baseline_id}",
    status_code=204,
    summary="Delete a Global Baseline Control",
)
async def delete_baseline(baseline_id: str):
    if not store.delete_baseline(baseline_id):
        raise HTTPException(status_code=404, detail="Baseline not found")


# ---------------------------------------------------------------------------
# Local Market Variations
# ---------------------------------------------------------------------------

@router.post(
    "/variations",
    response_model=LocalMarketVariation,
    status_code=201,
    summary="Create a Local Market Variation",
    description="Creates a local variation that inherits from a Global Baseline and can override steps.",
)
async def create_variation(variation: LocalMarketVariation):
    # Verify parent baseline exists
    if not store.get_baseline(variation.baseline_id):
        raise HTTPException(status_code=404, detail="Parent baseline not found")
    return store.add_variation(variation)


@router.get(
    "/variations",
    response_model=List[LocalMarketVariation],
    summary="List Local Market Variations",
)
async def list_variations(baseline_id: Optional[str] = Query(None)):
    return store.list_variations(baseline_id)


@router.get(
    "/variations/{variation_id}",
    response_model=LocalMarketVariation,
    summary="Get a Local Market Variation by ID",
)
async def get_variation(variation_id: str):
    variation = store.get_variation(variation_id)
    if not variation:
        raise HTTPException(status_code=404, detail="Variation not found")
    return variation


@router.put(
    "/variations/{variation_id}",
    response_model=LocalMarketVariation,
    summary="Update a Local Market Variation",
)
async def update_variation(variation_id: str, updated: LocalMarketVariation):
    existing = store.get_variation(variation_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Variation not found")
    updated.id = variation_id
    updated.updated_at = datetime.utcnow()
    store.variations[variation_id] = updated
    return updated


@router.delete(
    "/variations/{variation_id}",
    status_code=204,
    summary="Delete a Local Market Variation",
)
async def delete_variation(variation_id: str):
    if not store.delete_variation(variation_id):
        raise HTTPException(status_code=404, detail="Variation not found")
