"""
Global Framework Loader - Avoids circular imports
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

# Global variable to store the framework data
GLOBAL_FRAMEWORK: Dict[str, Any] = {}


def load_global_framework() -> Dict[str, Any]:
    """Load global framework data from JSON file."""
    global GLOBAL_FRAMEWORK
    
    if GLOBAL_FRAMEWORK:
        return GLOBAL_FRAMEWORK
    
    # Try multiple possible paths
    possible_paths = [
        Path("global_framework.json"),
        Path("app/global_framework.json"),
        Path("/opt/render/project/src/global_framework.json"),
        Path("/opt/render/project/src/app/global_framework.json")
    ]
    
    for framework_path in possible_paths:
        try:
            if framework_path.exists():
                with open(framework_path, 'r', encoding='utf-8') as f:
                    GLOBAL_FRAMEWORK = json.load(f)
                print(f"✅ Global framework loaded from {framework_path}: {GLOBAL_FRAMEWORK.get('process_name', 'Unknown')}")
                return GLOBAL_FRAMEWORK
        except Exception as e:
            print(f"❌ Error loading from {framework_path}: {e}")
            continue
    
    # If no file found, use embedded fallback data
    print("❌ Global framework file not found, using fallback data")
    GLOBAL_FRAMEWORK = get_fallback_framework()
    return GLOBAL_FRAMEWORK


def get_fallback_framework() -> Dict[str, Any]:
    """Fallback framework data if file loading fails."""
    return {
        "process_name": "User Access Management and Provisioning",
        "process_id": "UAM-001",
        "version": "v2.1",
        "effective_date": "2024-01-01",
        "business_context": "Financial Services - Global Banking Operations",
        "baselines": [
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
        ],
        "process_map": {
            "steps": [
                {
                    "step_id": "UAM-001",
                    "step_name": "Access Request Initiation",
                    "description": "Manager submits user access request through HRIS system",
                    "responsible_role": "Line Manager",
                    "system": "HRIS",
                    "controls": ["Manager authentication required", "Request form validation"],
                    "time_sla": "Immediate"
                }
            ]
        },
        "risk_register": {
            "risks": [
                {
                    "risk_id": "RISK-001",
                    "risk_name": "Unauthorized Access to Sensitive Systems",
                    "description": "Users gain access to systems or data beyond their job requirements",
                    "risk_category": "Security",
                    "impact": "High",
                    "likelihood": "Medium",
                    "risk_score": "15"
                }
            ]
        },
        "mitigating_controls": {
            "manual_controls": [
                {
                    "control_id": "MC-001",
                    "control_name": "Manager Access Review",
                    "description": "Line managers quarterly review all direct reports' access rights",
                    "control_type": "Detective",
                    "frequency": "Quarterly",
                    "effectiveness": "High"
                }
            ],
            "automated_controls": [
                {
                    "control_id": "AC-001",
                    "control_name": "Automated SoD Checking",
                    "description": "Real-time segregation of duties validation in access request workflow",
                    "control_type": "Preventive",
                    "effectiveness": "Very High"
                }
            ],
            "itgc_controls": [
                {
                    "control_id": "ITGC-001",
                    "control_name": "System Access Logs",
                    "description": "Comprehensive logging of all access provisioning activities",
                    "control_type": "Detective",
                    "effectiveness": "High"
                }
            ]
        },
        "compliance_requirements": {
            "sox_404": True,
            "pci_dss": True,
            "gdpr": True,
            "ccpa": True,
            "local_regulations": ["BaFin (Germany)", "BACEN (Brazil)", "FSA (Japan)"]
        }
    }


def get_global_framework() -> Dict[str, Any]:
    """Get the loaded global framework data."""
    return GLOBAL_FRAMEWORK


def is_framework_loaded() -> bool:
    """Check if global framework is loaded."""
    return bool(GLOBAL_FRAMEWORK)
