"""
Baselines Router - Simple baselines endpoint without database dependency
"""
from __future__ import annotations

from typing import List, Dict, Any

from fastapi import APIRouter

router = APIRouter(prefix="/baselines", tags=["Baselines"])


@router.get("")
async def get_baselines() -> List[Dict[str, Any]]:
    """Get baselines - always works without database."""
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
