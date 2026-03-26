"""
Database API Router - Direct database access endpoints
"""
import json
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException
from psycopg2.extras import RealDictCursor

from app.database import get_db_connection

router = APIRouter(prefix="/database", tags=["Database"])


@router.get("/baselines")
async def get_baselines() -> List[Dict[str, Any]]:
    """Get all baselines from database with counts - SQLite compatible."""
    print("🚨 DATABASE_API BASELINES ENDPOINT HIT")
    conn = get_db_connection()
    if not conn:
        # Fallback to static data
        print("⚠️ Database not available, using fallback baselines")
        return get_fallback_baselines()
    
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT b.*, 
                   (SELECT COUNT(*) FROM baseline_process_steps WHERE baseline_id = b.baseline_id) as steps_count,
                   (SELECT COUNT(*) FROM baseline_risks WHERE baseline_id = b.baseline_id) as risks_count,
                   (SELECT COUNT(*) FROM baseline_controls WHERE baseline_id = b.baseline_id) as controls_count
            FROM baselines b ORDER BY b.baseline_id
        """)
        baselines = cur.fetchall()
        result = [dict(baseline) for baseline in baselines]
        print(f"✅ DATABASE_API: Loaded {len(result)} baselines with counts from database")
        return result
    except Exception as e:
        print(f"❌ Database error, using fallback: {e}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        return get_fallback_baselines()
    finally:
        conn.close()


@router.get("/baselines/{baseline_id}/full")
async def get_baseline_full(baseline_id: str) -> Dict[str, Any]:
    """Get baseline with all Golden Thread data (process steps, risks, controls, compliance)."""
    print(f"🔍 Getting full baseline data for {baseline_id}")
    conn = get_db_connection()
    if not conn:
        return {"error": "Database not available"}
    
    try:
        cur = conn.cursor()
        
        # Get baseline info
        cur.execute("SELECT * FROM baselines WHERE baseline_id = ?", (baseline_id,))
        baseline = cur.fetchone()
        if not baseline:
            return {"error": "Baseline not found"}
        
        baseline_dict = dict(baseline)
        
        # Get process steps
        cur.execute("SELECT * FROM baseline_process_steps WHERE baseline_id = ? ORDER BY step_number", (baseline_id,))
        steps = [dict(step) for step in cur.fetchall()]
        
        # Get risks
        cur.execute("SELECT * FROM baseline_risks WHERE baseline_id = ? ORDER BY risk_id", (baseline_id,))
        risks = []
        for risk in cur.fetchall():
            risk_dict = dict(risk)
            # Parse JSON field
            if risk_dict.get('related_step_numbers'):
                risk_dict['related_step_numbers'] = json.loads(risk_dict['related_step_numbers'])
            risks.append(risk_dict)
        
        # Get controls
        cur.execute("SELECT * FROM baseline_controls WHERE baseline_id = ? ORDER BY control_id", (baseline_id,))
        controls = []
        for control in cur.fetchall():
            control_dict = dict(control)
            # Parse JSON field
            if control_dict.get('risk_ids'):
                control_dict['risk_ids'] = json.loads(control_dict['risk_ids'])
            controls.append(control_dict)
        
        # Get compliance requirements
        cur.execute("SELECT * FROM baseline_compliance_requirements WHERE baseline_id = ? ORDER BY regulation", (baseline_id,))
        compliance = []
        for req in cur.fetchall():
            req_dict = dict(req)
            # Parse JSON field
            if req_dict.get('applicable_regions'):
                req_dict['applicable_regions'] = json.loads(req_dict['applicable_regions'])
            compliance.append(req_dict)
        
        result = {
            **baseline_dict,
            "process_steps": steps,
            "risks": risks,
            "controls": controls,
            "compliance_requirements": compliance,
            "summary": {
                "steps_count": len(steps),
                "risks_count": len(risks),
                "controls_count": len(controls),
                "compliance_count": len(compliance)
            }
        }
        
        print(f"✅ Returning full baseline data: {len(steps)} steps, {len(risks)} risks, {len(controls)} controls, {len(compliance)} compliance")
        return result
        
    except Exception as e:
        print(f"❌ Error getting full baseline: {e}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        return {"error": str(e)}
    finally:
        conn.close()


@router.get("/market-variations/{market_code}/{baseline_id}")
async def get_market_variation(market_code: str, baseline_id: str) -> Dict[str, Any]:
    """Get market variation for a specific market and baseline."""
    print(f"🔍 Getting market variation for {market_code} - {baseline_id}")
    conn = get_db_connection()
    if not conn:
        return {"error": "Database not available"}
    
    try:
        cur = conn.cursor()
        
        # Get main variation record
        cur.execute("""
            SELECT * FROM market_variations 
            WHERE market_code = ? AND baseline_id = ?
        """, (market_code, baseline_id))
        variation = cur.fetchone()
        
        if not variation:
            return {"error": "Market variation not found"}
        
        variation_dict = dict(variation)
        variation_id = variation_dict['id']
        
        # Parse notes JSON
        if variation_dict.get('notes'):
            variation_dict['notes'] = json.loads(variation_dict['notes'])
        
        # Get step overrides
        cur.execute("""
            SELECT * FROM market_step_overrides 
            WHERE variation_id = ? ORDER BY step_number
        """, (variation_id,))
        variation_dict['overrides'] = [dict(row) for row in cur.fetchall()]
        
        # Get additional steps
        cur.execute("""
            SELECT * FROM market_additional_steps 
            WHERE variation_id = ? ORDER BY step_number
        """, (variation_id,))
        additional_steps = []
        for step in cur.fetchall():
            step_dict = dict(step)
            # Parse JSON fields
            if step_dict.get('title'):
                step_dict['title'] = json.loads(step_dict['title'])
            if step_dict.get('description'):
                step_dict['description'] = json.loads(step_dict['description'])
            additional_steps.append(step_dict)
        variation_dict['additional_steps'] = additional_steps
        
        # Get removed steps
        cur.execute("""
            SELECT step_number FROM market_removed_steps 
            WHERE variation_id = ? ORDER BY step_number
        """, (variation_id,))
        variation_dict['removed_step_numbers'] = [row[0] for row in cur.fetchall()]
        
        # Get additional risks
        cur.execute("""
            SELECT * FROM market_additional_risks 
            WHERE variation_id = ? ORDER BY id
        """, (variation_id,))
        additional_risks = []
        for risk in cur.fetchall():
            risk_dict = dict(risk)
            # Parse JSON field
            if risk_dict.get('mitigating_controls'):
                risk_dict['mitigating_controls'] = json.loads(risk_dict['mitigating_controls'])
            additional_risks.append(risk_dict)
        variation_dict['additional_risks'] = additional_risks
        
        # Add summary
        variation_dict['summary'] = {
            "overrides_count": len(variation_dict['overrides']),
            "additional_steps_count": len(variation_dict['additional_steps']),
            "removed_steps_count": len(variation_dict['removed_step_numbers']),
            "additional_risks_count": len(variation_dict['additional_risks'])
        }
        
        print(f"✅ Returning market variation: {len(variation_dict['overrides'])} overrides, {len(variation_dict['additional_steps'])} additional steps")
        return variation_dict
        
    except Exception as e:
        print(f"❌ Error getting market variation: {e}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        return {"error": str(e)}
    finally:
        conn.close()


@router.get("/market-variations")
async def get_all_market_variations() -> List[Dict[str, Any]]:
    """Get all market variations with summary information."""
    print("🔍 Getting all market variations")
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT mv.*, 
                   (SELECT COUNT(*) FROM market_step_overrides WHERE variation_id = mv.id) as overrides_count,
                   (SELECT COUNT(*) FROM market_additional_steps WHERE variation_id = mv.id) as additional_steps_count,
                   (SELECT COUNT(*) FROM market_removed_steps WHERE variation_id = mv.id) as removed_steps_count,
                   (SELECT COUNT(*) FROM market_additional_risks WHERE variation_id = mv.id) as additional_risks_count
            FROM market_variations mv 
            ORDER BY mv.market_code, mv.baseline_id
        """)
        
        variations = []
        for row in cur.fetchall():
            variation_dict = dict(row)
            # Parse notes JSON
            if variation_dict.get('notes'):
                try:
                    variation_dict['notes'] = json.loads(variation_dict['notes'])
                except:
                    variation_dict['notes'] = {"default": "Notes unavailable"}
            variations.append(variation_dict)
        
        print(f"✅ Returning {len(variations)} market variations")
        return variations
        
    except Exception as e:
        print(f"❌ Error getting all market variations: {e}")
        return []
    finally:
        conn.close()


@router.get("/market-variations/market/{market_code}")
async def get_variations_by_market(market_code: str) -> List[Dict[str, Any]]:
    """Get all variations for a specific market."""
    print(f"🔍 Getting variations for market {market_code}")
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM market_variations 
            WHERE market_code = ? 
            ORDER BY baseline_id
        """, (market_code,))
        
        variations = []
        for row in cur.fetchall():
            variation_dict = dict(row)
            # Parse notes JSON
            if variation_dict.get('notes'):
                try:
                    variation_dict['notes'] = json.loads(variation_dict['notes'])
                except:
                    variation_dict['notes'] = {"default": "Notes unavailable"}
            variations.append(variation_dict)
        
        print(f"✅ Returning {len(variations)} variations for market {market_code}")
        return variations
        
    except Exception as e:
        print(f"❌ Error getting variations for market {market_code}: {e}")
        return []
    finally:
        conn.close()


def get_fallback_baselines() -> List[Dict[str, Any]]:
    """Fallback baselines when database is not available."""
    return [
        {
            "baseline_id": "BL-001",
            "baseline_name": "Core Access Management",
            "description": "Fundamental user access provisioning and deprovisioning",
            "maturity_level": "Optimized",
            "control_coverage": "95%"
        },
        {
            "baseline_id": "BL-002",
            "baseline_name": "Segregation of Duties",
            "description": "SoD enforcement and conflict prevention",
            "maturity_level": "Managed",
            "control_coverage": "88%"
        },
        {
            "baseline_id": "BL-003",
            "baseline_name": "Access Certification",
            "description": "Periodic access review and certification",
            "maturity_level": "Defined",
            "control_coverage": "82%"
        },
        {
            "baseline_id": "BL-004",
            "baseline_name": "Emergency Access",
            "description": "Break-glass and emergency access procedures",
            "maturity_level": "Managed",
            "control_coverage": "75%"
        }
    ]


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
