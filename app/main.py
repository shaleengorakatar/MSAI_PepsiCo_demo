"""
Control Design Assessment Tool – FastAPI Backend
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import analyze, fit_gap, global_local, monitoring, visualizations

app = FastAPI(
    title="Control Design Assessment API",
    description=(
        "Backend API for the Control Design Assessment tool. "
        "Provides AI-powered process analysis, global/local control management, "
        "fit-gap analysis, and predictive risk monitoring."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ---------------------------------------------------------------------------
# CORS – allow requests from the Lovable frontend and local dev
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"https://.*\.lovable\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(analyze.router, prefix="/api")
app.include_router(global_local.router, prefix="/api")
app.include_router(fit_gap.router, prefix="/api")
app.include_router(monitoring.router, prefix="/api")
app.include_router(visualizations.router, prefix="/api")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "control-design-assessment-api",
        "version": "1.0.0",
    }
