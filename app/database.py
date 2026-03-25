"""
Database setup and seeding for PepsiCo Control Design Assessment
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Dict, Any, List

import psycopg2
from psycopg2.extras import RealDictCursor

from app.config import settings


def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(settings.database_url)
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None


def create_tables():
    """Create database tables"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            # Create baselines table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS baselines (
                    id SERIAL PRIMARY KEY,
                    baseline_id VARCHAR(20) UNIQUE NOT NULL,
                    baseline_name VARCHAR(200) NOT NULL,
                    description TEXT,
                    maturity_level VARCHAR(50),
                    control_coverage VARCHAR(10),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create tools table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tools (
                    id SERIAL PRIMARY KEY,
                    tool_id VARCHAR(20) UNIQUE NOT NULL,
                    tool_name VARCHAR(200) NOT NULL,
                    tool_type VARCHAR(50),
                    description TEXT,
                    vendor VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create regions table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS regions (
                    id SERIAL PRIMARY KEY,
                    region_id VARCHAR(20) UNIQUE NOT NULL,
                    region_name VARCHAR(100) NOT NULL,
                    country VARCHAR(100),
                    compliance_score INTEGER,
                    risk_level VARCHAR(20),
                    interviewee VARCHAR(200),
                    position VARCHAR(200),
                    interview_date DATE,
                    language VARCHAR(50),
                    transcript_content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create framework table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS framework (
                    id SERIAL PRIMARY KEY,
                    process_name VARCHAR(200),
                    process_id VARCHAR(20),
                    version VARCHAR(20),
                    effective_date DATE,
                    business_context TEXT,
                    process_map JSONB,
                    risk_register JSONB,
                    mitigating_controls JSONB,
                    compliance_requirements JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            print("✅ Tables created successfully")
            return True
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def seed_baselines():
    """Seed baselines data"""
    conn = get_db_connection()
    if not conn:
        return False
    
    baselines_data = [
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
    
    try:
        with conn.cursor() as cur:
            for baseline in baselines_data:
                cur.execute("""
                    INSERT INTO baselines (baseline_id, baseline_name, description, maturity_level, control_coverage)
                    VALUES (%(baseline_id)s, %(baseline_name)s, %(description)s, %(maturity_level)s, %(control_coverage)s)
                    ON CONFLICT (baseline_id) DO UPDATE SET
                        baseline_name = EXCLUDED.baseline_name,
                        description = EXCLUDED.description,
                        maturity_level = EXCLUDED.maturity_level,
                        control_coverage = EXCLUDED.control_coverage,
                        updated_at = CURRENT_TIMESTAMP
                """, baseline)
            
            conn.commit()
            print("✅ Baselines seeded successfully")
            return True
            
    except Exception as e:
        print(f"❌ Error seeding baselines: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def seed_tools():
    """Seed tools data"""
    conn = get_db_connection()
    if not conn:
        return False
    
    tools_data = [
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
    
    try:
        with conn.cursor() as cur:
            for tool in tools_data:
                cur.execute("""
                    INSERT INTO tools (tool_id, tool_name, tool_type, description, vendor)
                    VALUES (%(tool_id)s, %(tool_name)s, %(tool_type)s, %(description)s, %(vendor)s)
                    ON CONFLICT (tool_id) DO UPDATE SET
                        tool_name = EXCLUDED.tool_name,
                        tool_type = EXCLUDED.tool_type,
                        description = EXCLUDED.description,
                        vendor = EXCLUDED.vendor,
                        updated_at = CURRENT_TIMESTAMP
                """, tool)
            
            conn.commit()
            print("✅ Tools seeded successfully")
            return True
            
    except Exception as e:
        print(f"❌ Error seeding tools: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def seed_regions():
    """Seed regions data"""
    conn = get_db_connection()
    if not conn:
        return False
    
    regions_data = [
        {
            "region_id": "GER-001",
            "region_name": "Germany",
            "country": "Germany",
            "compliance_score": 85,
            "risk_level": "Low",
            "interviewee": "Hans Mueller",
            "position": "Regional IT Manager",
            "interview_date": "2024-03-15",
            "language": "English",
            "transcript_content": """Interviewer: Can you walk me through your current user access management process?

Hans: Ja, our process is quite standardized, mostly following the global framework. We use the main HRIS system for access requests, and the automated SoD checks work well. However, we have one specific deviation - our tax reporting system uses a localized German tax software called 'SteuerPro' that is not integrated with the global IT infrastructure. For this system, we have a manual workaround where the tax team submits paper forms to IT, and we manually create accounts."""
        },
        {
            "region_id": "BRA-001",
            "region_name": "Brazil",
            "country": "Brazil",
            "compliance_score": 35,
            "risk_level": "Critical",
            "interviewee": "Carlos Silva",
            "position": "Operations Manager",
            "interview_date": "2024-03-18",
            "language": "Portuguese (translated to English)",
            "transcript_content": """Interviewer: Can you describe your user access management process?

Carlos: Look, to be honest, our process is very different from the global standard. The main system is very slow - sometimes it takes 3-4 days just to get a simple access request approved. Our team can't wait that long, so we've developed our own workarounds. For most access requests, we use shared administrator accounts."""
        },
        {
            "region_id": "JPN-001",
            "region_name": "Japan",
            "country": "Japan",
            "compliance_score": 78,
            "risk_level": "Medium",
            "interviewee": "Takeshi Yamamoto",
            "position": "Compliance Officer",
            "interview_date": "2024-03-20",
            "language": "Japanese/English Mix",
            "transcript_content": """Interviewer: Can you explain your user access management process?

Takeshi: はい、yes. Our process follows global framework but with important Japanese adaptations. In Japan, we have strict local regulations from the Financial Services Agency (FSA) that sometimes conflict with global standards."""
        },
        {
            "region_id": "USA-001",
            "region_name": "United States",
            "country": "United States",
            "compliance_score": 92,
            "risk_level": "Low",
            "interviewee": "Jennifer Thompson",
            "position": "IT Security Director",
            "interview_date": "2024-03-22",
            "language": "English",
            "transcript_content": """Interviewer: Can you describe your current user access management process?

Jennifer: We're actually the pilot region for the new global framework, so we're pretty close to the standard. We've fully implemented the automated provisioning system and our SoD compliance is at 98%."""
        },
        {
            "region_id": "IND-001",
            "region_name": "India",
            "country": "India",
            "compliance_score": 45,
            "risk_level": "High",
            "interviewee": "Raj Patel",
            "position": "Regional Operations Head",
            "interview_date": "2024-03-25",
            "language": "English",
            "transcript_content": """Interviewer: Can you walk me through your user access management process?

Raj: In India, we face some unique challenges. The global system works well for our corporate functions, but our manufacturing plants have different requirements. Many of our plant systems are on-premise and not connected to the global network."""
        },
        {
            "region_id": "UK-001",
            "region_name": "United Kingdom",
            "country": "United Kingdom",
            "compliance_score": 88,
            "risk_level": "Low",
            "interviewee": "David Chen",
            "position": "Risk Manager",
            "interview_date": "2024-03-28",
            "language": "English",
            "transcript_content": """Interviewer: Can you describe your user access management process?

David: We follow the global framework quite closely, with some adaptations for UK regulations. The main difference is our approach to GDPR compliance - we have additional data privacy controls that go beyond the global standard."""
        }
    ]
    
    try:
        with conn.cursor() as cur:
            for region in regions_data:
                cur.execute("""
                    INSERT INTO regions (region_id, region_name, country, compliance_score, risk_level, interviewee, position, interview_date, language, transcript_content)
                    VALUES (%(region_id)s, %(region_name)s, %(country)s, %(compliance_score)s, %(risk_level)s, %(interviewee)s, %(position)s, %(interview_date)s, %(language)s, %(transcript_content)s)
                    ON CONFLICT (region_id) DO UPDATE SET
                        region_name = EXCLUDED.region_name,
                        country = EXCLUDED.country,
                        compliance_score = EXCLUDED.compliance_score,
                        risk_level = EXCLUDED.risk_level,
                        interviewee = EXCLUDED.interviewee,
                        position = EXCLUDED.position,
                        interview_date = EXCLUDED.interview_date,
                        language = EXCLUDED.language,
                        transcript_content = EXCLUDED.transcript_content,
                        updated_at = CURRENT_TIMESTAMP
                """, region)
            
            conn.commit()
            print("✅ Regions seeded successfully")
            return True
            
    except Exception as e:
        print(f"❌ Error seeding regions: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def seed_framework():
    """Seed framework data"""
    conn = get_db_connection()
    if not conn:
        return False
    
    framework_data = {
        "process_name": "User Access Management and Provisioning",
        "process_id": "UAM-001",
        "version": "v2.1",
        "effective_date": "2024-01-01",
        "business_context": "Financial Services - Global Banking Operations",
        "process_map": {
            "steps": [
                {
                    "step_id": "UAM-001",
                    "step_name": "Access Request Initiation",
                    "description": "Manager submits user access request through HRIS system",
                    "responsible_role": "Line Manager",
                    "system": "HRIS",
                    "controls": ["Manager authentication required", "Request form validation", "Business justification required"],
                    "time_sla": "Immediate"
                },
                {
                    "step_id": "UAM-002",
                    "step_name": "Business Approval",
                    "description": "Department head reviews and approves access request",
                    "responsible_role": "Department Head",
                    "system": "Workflow Engine",
                    "controls": ["Segregation of Duties (SoD) check", "Access level validation", "Approval audit trail"],
                    "time_sla": "24 hours"
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
                    "risk_score": "15",
                    "affected_systems": ["Core Banking", "CRM", "Financial Reporting"],
                    "potential_loss": "$2.5M - $10M"
                },
                {
                    "risk_id": "RISK-002",
                    "risk_name": "Segregation of Duties (SoD) Violations",
                    "description": "Single user has conflicting permissions that could enable fraud",
                    "risk_category": "Compliance",
                    "impact": "High",
                    "likelihood": "Medium",
                    "risk_score": "15",
                    "affected_systems": ["Payment Processing", "General Ledger", "Trade Execution"],
                    "potential_loss": "$1M - $5M"
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
                    "test_procedure": "Sample 10% of users and validate access against job descriptions",
                    "effectiveness": "High"
                }
            ],
            "automated_controls": [
                {
                    "control_id": "AC-001",
                    "control_name": "Automated SoD Checking",
                    "description": "Real-time segregation of duties validation in access request workflow",
                    "control_type": "Preventive",
                    "system": "Identity Management System",
                    "test_procedure": "Test SoD rules with sample conflicting role combinations",
                    "effectiveness": "Very High"
                }
            ],
            "itgc_controls": [
                {
                    "control_id": "ITGC-001",
                    "control_name": "System Access Logs",
                    "description": "Comprehensive logging of all access provisioning activities",
                    "control_type": "Detective",
                    "system": "Identity Management System",
                    "test_procedure": "Verify log completeness and accuracy for sample transactions",
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
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO framework (process_name, process_id, version, effective_date, business_context, process_map, risk_register, mitigating_controls, compliance_requirements)
                VALUES (%(process_name)s, %(process_id)s, %(version)s, %(effective_date)s, %(business_context)s, %(process_map)s, %(risk_register)s, %(mitigating_controls)s, %(compliance_requirements)s)
                ON CONFLICT DO NOTHING
            """, framework_data)
            
            conn.commit()
            print("✅ Framework seeded successfully")
            return True
            
    except Exception as e:
        print(f"❌ Error seeding framework: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def seed_all_data():
    """Seed all demo data"""
    print("🌱 Starting database seeding...")
    
    success = True
    
    # Create tables
    if not create_tables():
        success = False
    
    # Seed data
    if success and not seed_baselines():
        success = False
    
    if success and not seed_tools():
        success = False
    
    if success and not seed_regions():
        success = False
    
    if success and not seed_framework():
        success = False
    
    if success:
        print("✅ All demo data seeded successfully!")
    else:
        print("❌ Seeding failed - check logs above")
    
    return success


if __name__ == "__main__":
    seed_all_data()
