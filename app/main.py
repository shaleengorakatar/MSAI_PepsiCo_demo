"""
Control Design Assessment Tool – FastAPI Backend
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import analyze, ai_endpoints, baselines, database_api, fit_gap, global_local, monitoring, transcript_analysis, upload, visualizations

app = FastAPI(
    title="Control Design Assessment API",
    description=(
        "Backend API for the Control Design Assessment tool. "
        "Provides AI-powered process analysis, global/local control management, "
        "fit-gap analysis, predictive risk monitoring, and advanced AI endpoints "
        "including form prefilling, security triage, and enhanced source analysis."
    ),
    version="1.0.2",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ADD THIS IMMEDIATELY AFTER app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(analyze.router, prefix="/api")
app.include_router(ai_endpoints.router)
app.include_router(upload.router, prefix="/api")
app.include_router(global_local.router, prefix="/api")
app.include_router(fit_gap.router, prefix="/api")
app.include_router(monitoring.router, prefix="/api")
app.include_router(transcript_analysis.router, prefix="/api")
app.include_router(database_api.router, prefix="/api")
app.include_router(baselines.router, prefix="/api")
app.include_router(visualizations.router, prefix="/api")


# ---------------------------------------------------------------------------
# Startup - Load global framework data and seed database
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup_tasks():
    """Initialize application on startup."""
    print("🚀 Starting application startup tasks...")
    from app.services.framework_loader import load_global_framework
    from app.database import seed_all_data
    
    try:
        # Seed database with demo data
        print("🌱 Starting database seeding...")
        seed_success = seed_all_data()
        print(f"🔄 Database seeding result: {seed_success}")
        
        if seed_success:
            # Load framework into memory
            framework = load_global_framework()
            if framework:
                print(f"✅ Application started successfully: {framework.get('process_name', 'Unknown')}")
                print(f"📊 Loaded {len(framework.get('baselines', []))} baselines from database")
            else:
                print("❌ Failed to load framework after seeding")
        else:
            print("❌ Database seeding failed, using fallback data")
            
    except Exception as e:
        print(f"❌ Startup error: {e}")
        # Try to load fallback data
        try:
            framework = load_global_framework()
            if framework:
                print(f"✅ Fallback loaded: {framework.get('process_name', 'Unknown')}")
        except Exception as fallback_error:
            print(f"❌ Even fallback failed: {fallback_error}")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
async def health_check():
    from app.config import settings
    
    health_data = {
        "status": "healthy",
        "service": "control-design-assessment-api",
        "version": "1.0.1",
        "database_configured": bool(settings.database_url),
        "database_url_length": len(settings.database_url) if settings.database_url else 0
    }
    
    # Test database connection
    if settings.database_url:
        try:
            from app.database import get_db_connection
            conn = get_db_connection()
            if conn:
                health_data["database_connected"] = True
                conn.close()
            else:
                health_data["database_connected"] = False
        except Exception as e:
            health_data["database_connected"] = False
            health_data["database_error"] = str(e)
    else:
        health_data["database_connected"] = False
    
    return health_data
