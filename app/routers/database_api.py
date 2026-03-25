"""
Database API Router - Direct database access for baselines, tools, and regions
"""
from __future__ import annotations

from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException
from psycopg2.extras import RealDictCursor

from app.database import get_db_connection

router = APIRouter(prefix="/database", tags=["Database"])


@router.get("/baselines")
async def get_baselines() -> List[Dict[str, Any]]:
    """Get all baselines from database."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database connection failed")
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM baselines ORDER BY baseline_id")
            baselines = cur.fetchall()
            return [dict(baseline) for baseline in baselines]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        conn.close()


@router.get("/tools")
async def get_tools() -> List[Dict[str, Any]]:
    """Get all tools from database."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database connection failed")
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM tools ORDER BY tool_id")
            tools = cur.fetchall()
            return [dict(tool) for tool in tools]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        conn.close()


@router.get("/regions")
async def get_regions() -> List[Dict[str, Any]]:
    """Get all regions from database."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database connection failed")
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM regions ORDER BY region_id")
            regions = cur.fetchall()
            return [dict(region) for region in regions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        conn.close()


@router.post("/seed")
async def seed_database():
    """Manually seed the database with demo data."""
    from app.database import seed_all_data
    
    try:
        success = seed_all_data()
        if success:
            return {"status": "success", "message": "Database seeded successfully"}
        else:
            raise HTTPException(status_code=500, detail="Database seeding failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Seeding error: {e}")


@router.get("/status")
async def get_database_status():
    """Get database status and counts."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database connection failed")
    
    try:
        status = {}
        
        with conn.cursor() as cur:
            # Count baselines
            cur.execute("SELECT COUNT(*) FROM baselines")
            status["baselines_count"] = cur.fetchone()[0]
            
            # Count tools
            cur.execute("SELECT COUNT(*) FROM tools")
            status["tools_count"] = cur.fetchone()[0]
            
            # Count regions
            cur.execute("SELECT COUNT(*) FROM regions")
            status["regions_count"] = cur.fetchone()[0]
            
            # Check framework
            cur.execute("SELECT COUNT(*) FROM framework")
            status["framework_count"] = cur.fetchone()[0]
            
            status["database_connected"] = True
            
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        conn.close()
