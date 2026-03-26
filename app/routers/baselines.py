"""
Baselines Router - Simple baselines endpoint without database dependency
"""
from __future__ import annotations

from typing import List, Dict, Any

from fastapi import APIRouter

router = APIRouter(prefix="/baselines", tags=["Baselines"])


@router.get("/test")
async def test_baselines():
    """Test endpoint to verify baselines work."""
    return {"status": "working", "message": "Baselines endpoint is functional"}


@router.get("")
async def get_baselines() -> List[Dict[str, Any]]:
    """Get baselines from database."""
    print("� BASELINES ENDPOINT HIT - THIS SHOULD ALWAYS APPEAR")
    print("�🔍 /api/baselines endpoint called")
    try:
        from app.database import get_db_connection
        
        print("🔄 Getting database connection...")
        conn = get_db_connection()
        if not conn:
            print("❌ Database connection failed for baselines endpoint")
            return []
        
        print("✅ Database connection successful, executing query...")
        cur = conn.cursor()
        cur.execute("SELECT * FROM baselines ORDER BY baseline_id")
        rows = cur.fetchall()
        
        print(f"🔍 Query returned {len(rows)} rows")
        # Convert SQLite Row objects to dictionaries
        baselines = [dict(row) for row in rows]
        print(f"✅ Returning {len(baselines)} baselines from database")
        return baselines
        
    except Exception as e:
        print(f"❌ Error loading baselines from database: {e}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()
            print("🔄 Database connection closed")


@router.get("/tools")
async def get_tools() -> List[Dict[str, Any]]:
    """Get tools - always works without database."""
    return [
        {
            "tool_id": "TL-001",
            "tool_name": "SAP GRC Access Control",
            "tool_type": "Compliance Management",
            "description": "Automated SoD analysis and risk remediation for SAP systems",
            "vendor": "SAP"
        },
        {
            "tool_id": "TL-002",
            "tool_name": "Oracle Identity Manager",
            "tool_type": "Identity Management",
            "description": "Enterprise identity and access management with automated provisioning",
            "vendor": "Oracle"
        }
    ]
