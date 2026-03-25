"""
Control Design Assessment Tool – FastAPI Backend
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import analyze, fit_gap, global_local, monitoring, transcript_analysis, upload, visualizations

# Global variable to store the framework data
GLOBAL_FRAMEWORK = None

app = FastAPI(
    title="Control Design Assessment API",
    description=(
        "Backend API for the Control Design Assessment tool. "
        "Provides AI-powered process analysis, global/local control management, "
        "fit-gap analysis, and predictive risk monitoring."
    ),
    version="1.0.1",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ---------------------------------------------------------------------------
# CORS – allow requests from the Lovable frontend and local dev
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        *settings.cors_origin_list,
        "https://27549e9b-6605-4b35-bc21-a68953ea7ffc.lovableproject.com",
    ],
    allow_origin_regex=r"https://.*\.(lovable\.app|lovableproject\.com)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(analyze.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(global_local.router, prefix="/api")
app.include_router(fit_gap.router, prefix="/api")
app.include_router(monitoring.router, prefix="/api")
app.include_router(transcript_analysis.router, prefix="/api")
app.include_router(visualizations.router, prefix="/api")


# ---------------------------------------------------------------------------
# Startup - Load global framework data
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def load_global_framework():
    """Load global framework data into memory on startup."""
    global GLOBAL_FRAMEWORK
    try:
        framework_path = Path("global_framework.json")
        if framework_path.exists():
            with open(framework_path, 'r', encoding='utf-8') as f:
                GLOBAL_FRAMEWORK = json.load(f)
            print(f"✅ Global framework loaded successfully: {GLOBAL_FRAMEWORK['process_name']}")
        else:
            print("❌ Global framework file not found")
            GLOBAL_FRAMEWORK = {}
    except Exception as e:
        print(f"❌ Error loading global framework: {e}")
        GLOBAL_FRAMEWORK = {}


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
