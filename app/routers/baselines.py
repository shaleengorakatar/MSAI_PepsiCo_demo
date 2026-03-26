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
    print("� /api/baselines endpoint called")
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


@router.get("/{baseline_id}/full")
async def get_baseline_full(baseline_id: str) -> Dict[str, Any]:
    """Get baseline with all Golden Thread data (process steps, risks, controls, compliance)."""
    print(f"🔍 BASELINES ROUTER: Getting full baseline data for {baseline_id}")
    try:
        from app.database import get_db_connection
        import json
        
        print("🔄 Getting database connection...")
        conn = get_db_connection()
        if not conn:
            print("❌ Database connection failed")
            return {"error": "Database not available"}
        
        print("✅ Database connection successful")
        try:
            cur = conn.cursor()
            
            # First, check if baseline exists
            print(f"🔍 Checking if baseline {baseline_id} exists...")
            cur.execute("SELECT * FROM baselines WHERE baseline_id = ?", (baseline_id,))
            baseline = cur.fetchone()
            if not baseline:
                print(f"❌ Baseline {baseline_id} not found")
                return {"error": "Baseline not found"}
            
            print(f"✅ Found baseline: {baseline[1]}")
            baseline_dict = dict(baseline)
            
            # Check if Golden Thread tables exist and have data
            print("🔍 Checking Golden Thread tables...")
            
            # Get process steps
            print("🔄 Getting process steps...")
            try:
                cur.execute("SELECT * FROM baseline_process_steps WHERE baseline_id = ? ORDER BY step_number", (baseline_id,))
                steps = [dict(step) for step in cur.fetchall()]
                print(f"✅ Found {len(steps)} process steps")
            except Exception as e:
                print(f"❌ Error getting process steps: {e}")
                steps = []
            
            # Get risks
            print("🔄 Getting risks...")
            try:
                cur.execute("SELECT * FROM baseline_risks WHERE baseline_id = ? ORDER BY risk_id", (baseline_id,))
                risks = []
                for risk in cur.fetchall():
                    risk_dict = dict(risk)
                    # Parse JSON field
                    if risk_dict.get('related_step_numbers'):
                        try:
                            risk_dict['related_step_numbers'] = json.loads(risk_dict['related_step_numbers'])
                        except:
                            risk_dict['related_step_numbers'] = []
                    risks.append(risk_dict)
                print(f"✅ Found {len(risks)} risks")
            except Exception as e:
                print(f"❌ Error getting risks: {e}")
                risks = []
            
            # Get controls
            print("🔄 Getting controls...")
            try:
                cur.execute("SELECT * FROM baseline_controls WHERE baseline_id = ? ORDER BY control_id", (baseline_id,))
                controls = []
                for control in cur.fetchall():
                    control_dict = dict(control)
                    # Parse JSON field
                    if control_dict.get('risk_ids'):
                        try:
                            control_dict['risk_ids'] = json.loads(control_dict['risk_ids'])
                        except:
                            control_dict['risk_ids'] = []
                    controls.append(control_dict)
                print(f"✅ Found {len(controls)} controls")
            except Exception as e:
                print(f"❌ Error getting controls: {e}")
                controls = []
            
            # Get compliance requirements
            print("🔄 Getting compliance requirements...")
            try:
                cur.execute("SELECT * FROM baseline_compliance_requirements WHERE baseline_id = ? ORDER BY regulation", (baseline_id,))
                compliance = []
                for req in cur.fetchall():
                    req_dict = dict(req)
                    # Parse JSON field
                    if req_dict.get('applicable_regions'):
                        try:
                            req_dict['applicable_regions'] = json.loads(req_dict['applicable_regions'])
                        except:
                            req_dict['applicable_regions'] = []
                    compliance.append(req_dict)
                print(f"✅ Found {len(compliance)} compliance requirements")
            except Exception as e:
                print(f"❌ Error getting compliance: {e}")
                compliance = []
            
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
            
            print(f"✅ BASELINES ROUTER: Returning full baseline data: {len(steps)} steps, {len(risks)} risks, {len(controls)} controls, {len(compliance)} compliance")
            return result
            
        except Exception as e:
            print(f"❌ Error getting full baseline: {e}")
            import traceback
            print(f"❌ Full traceback: {traceback.format_exc()}")
            return {"error": str(e)}
        finally:
            conn.close()
            print("🔄 Database connection closed")
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        import traceback
        print(f"❌ Connection error traceback: {traceback.format_exc()}")
        return {"error": "Database connection failed"}


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
