"""
Database setup and seeding for PepsiCo Control Design Assessment
"""
from __future__ import annotations

import csv
import json
import os
from datetime import datetime
from typing import Dict, Any, List

import psycopg2
from psycopg2.extras import RealDictCursor
import sqlite3

from app.config import settings
from app.golden_thread_templates import (
    get_process_steps_template,
    get_risks_template,
    get_controls_template,
    get_compliance_template
)


# Simple database path like Glencore
DB_PATH = settings.database_url.replace("sqlite:///", "")

def get_db_connection():
    """Get database connection - SQLite only for now"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Like Glencore
        print(f"✅ SQLite database connection successful: {DB_PATH}")
        return conn
    except Exception as e:
        print(f"❌ SQLite connection failed: {e}")
        return None


def create_tables():
    """Create database tables - simplified like Glencore"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS baselines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                baseline_id TEXT UNIQUE NOT NULL,
                baseline_name TEXT NOT NULL,
                description TEXT,
                maturity_level TEXT,
                control_coverage TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_id TEXT UNIQUE NOT NULL,
                tool_name TEXT NOT NULL,
                tool_type TEXT,
                description TEXT,
                vendor TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS regions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                region_id TEXT UNIQUE NOT NULL,
                region_name TEXT NOT NULL,
                country TEXT,
                compliance_score INTEGER,
                risk_level TEXT,
                interviewee TEXT,
                position TEXT,
                interview_date DATE,
                language TEXT,
                transcript_content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS framework (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                process_name TEXT,
                process_id TEXT,
                version TEXT,
                effective_date DATE,
                business_context TEXT,
                process_map TEXT,
                risk_register TEXT,
                mitigating_controls TEXT,
                compliance_requirements TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Golden Thread Tables
            CREATE TABLE IF NOT EXISTS baseline_process_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                baseline_id TEXT NOT NULL,
                step_number INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                responsible_role TEXT,
                objective TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (baseline_id) REFERENCES baselines(baseline_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS baseline_risks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                baseline_id TEXT NOT NULL,
                risk_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT,
                severity TEXT,
                related_step_numbers TEXT,  -- JSON array of step numbers
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (baseline_id) REFERENCES baselines(baseline_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS baseline_controls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                baseline_id TEXT NOT NULL,
                control_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                control_type TEXT,  -- Manual/Automated/ITGC
                risk_ids TEXT,     -- JSON array of risk IDs
                frequency TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (baseline_id) REFERENCES baselines(baseline_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS baseline_compliance_requirements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                baseline_id TEXT NOT NULL,
                regulation TEXT NOT NULL,
                requirement_text TEXT,
                applicable_regions TEXT,  -- JSON array of regions
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (baseline_id) REFERENCES baselines(baseline_id) ON DELETE CASCADE
            );
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
    """Seed baselines data from CSV file"""
    conn = get_db_connection()
    if not conn:
        return False
    
    baselines_data = []
    csv_file_path = os.path.join(os.path.dirname(__file__), '..', 'demo_data', 'baselines.csv')
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                baselines_data.append({
                    "baseline_id": row["baseline_id"],
                    "baseline_name": row["baseline_name"],
                    "description": row["description"],
                    "maturity_level": row["maturity_level"],
                    "control_coverage": row["control_coverage"]
                })
        print(f"✅ Loaded {len(baselines_data)} baselines from CSV")
    except FileNotFoundError:
        print(f"❌ CSV file not found: {csv_file_path}")
        return False
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        return False
    
    try:
        cur = conn.cursor()
        for baseline in baselines_data:
            # Simple INSERT OR REPLACE like Glencore approach
            cur.execute("""
                INSERT OR REPLACE INTO baselines (baseline_id, baseline_name, description, maturity_level, control_coverage)
                VALUES (?, ?, ?, ?, ?)
            """, (baseline["baseline_id"], baseline["baseline_name"], baseline["description"], 
                  baseline["maturity_level"], baseline["control_coverage"]))
        
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
    """Seed tools data from CSV file"""
    conn = get_db_connection()
    if not conn:
        return False
    
    tools_data = []
    csv_file_path = os.path.join(os.path.dirname(__file__), '..', 'demo_data', 'tools.csv')
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                tools_data.append({
                    "tool_id": row["tool_id"],
                    "tool_name": row["tool_name"],
                    "tool_type": row["tool_type"],
                    "description": row["description"],
                    "vendor": row["vendor"]
                })
        print(f"✅ Loaded {len(tools_data)} tools from CSV")
    except FileNotFoundError:
        print(f"❌ CSV file not found: {csv_file_path}")
        return False
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        return False
    
    try:
        cur = conn.cursor()
        for tool in tools_data:
            # Simple INSERT OR REPLACE like Glencore approach
            cur.execute("""
                INSERT OR REPLACE INTO tools (tool_id, tool_name, tool_type, description, vendor)
                VALUES (?, ?, ?, ?, ?)
            """, (tool["tool_id"], tool["tool_name"], tool["tool_type"], 
                  tool["description"], tool["vendor"]))
        
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
    """Seed regions data from CSV file"""
    conn = get_db_connection()
    if not conn:
        return False
    
    regions_data = []
    csv_file_path = os.path.join(os.path.dirname(__file__), '..', 'demo_data', 'regions.csv')
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                regions_data.append({
                    "region_id": row["region_id"],
                    "region_name": row["region_name"],
                    "country": row["country"],
                    "compliance_score": int(row["compliance_score"]),
                    "risk_level": row["risk_level"],
                    "interviewee": row["interviewee"],
                    "position": row["position"],
                    "interview_date": "2024-03-15",
                    "language": row.get("language", "English"),
                    "transcript_content": f"Interview with {row['interviewee']}, {row['position']} at {row['region_name']}. Compliance score: {row['compliance_score']}, Risk level: {row['risk_level']}."
                })
        print(f"✅ Loaded {len(regions_data)} regions from CSV")
    except FileNotFoundError:
        print(f"❌ CSV file not found: {csv_file_path}")
        return False
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        return False
    
    try:
        cur = conn.cursor()
        for region in regions_data:
            # Simple INSERT OR REPLACE like Glencore approach
            cur.execute("""
                INSERT OR REPLACE INTO regions (region_id, region_name, country, compliance_score, risk_level, interviewee, position, interview_date, language, transcript_content)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (region["region_id"], region["region_name"], region["country"], region["compliance_score"], 
                  region["risk_level"], region["interviewee"], region["position"], region["interview_date"], 
                  region["language"], region["transcript_content"]))
        
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
        cur = conn.cursor()
        # Convert JSON data to strings for SQLite
        framework_data_sqlite = framework_data.copy()
        framework_data_sqlite['process_map'] = json.dumps(framework_data_sqlite['process_map'])
        framework_data_sqlite['risk_register'] = json.dumps(framework_data_sqlite['risk_register'])
        framework_data_sqlite['mitigating_controls'] = json.dumps(framework_data_sqlite['mitigating_controls'])
        framework_data_sqlite['compliance_requirements'] = json.dumps(framework_data_sqlite['compliance_requirements'])
        
        # Simple INSERT OR IGNORE like Glencore approach
        cur.execute("""
            INSERT OR IGNORE INTO framework (process_name, process_id, version, effective_date, business_context, process_map, risk_register, mitigating_controls, compliance_requirements)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (framework_data_sqlite['process_name'], framework_data_sqlite['process_id'], 
              framework_data_sqlite['version'], framework_data_sqlite['effective_date'], 
              framework_data_sqlite['business_context'], framework_data_sqlite['process_map'],
              framework_data_sqlite['risk_register'], framework_data_sqlite['mitigating_controls'],
              framework_data_sqlite['compliance_requirements']))
        
        conn.commit()
        print("✅ Framework seeded successfully")
        return True
            
    except Exception as e:
        print(f"❌ Error seeding framework: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def seed_golden_thread_data():
    """Seed Golden Thread data for all baselines"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # Get all existing baselines
        cur.execute("SELECT baseline_id, baseline_name FROM baselines")
        baselines = cur.fetchall()
        
        print(f"🔄 Starting Golden Thread seeding for {len(baselines)} baselines...")
        
        for baseline in baselines:
            baseline_id = baseline[0]
            baseline_name = baseline[1]
            print(f"📝 Seeding Golden Thread for {baseline_id}: {baseline_name}")
            
            # Seed process steps
            seed_process_steps_for_baseline(cur, baseline_id)
            
            # Seed risks
            seed_risks_for_baseline(cur, baseline_id)
            
            # Seed controls
            seed_controls_for_baseline(cur, baseline_id)
            
            # Seed compliance requirements
            seed_compliance_for_baseline(cur, baseline_id)
        
        conn.commit()
        print("✅ Golden Thread data seeded successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error seeding Golden Thread data: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def seed_process_steps_for_baseline(cur, baseline_id):
    """Seed process steps for a specific baseline"""
    process_steps_data = get_process_steps_template(baseline_id)
    
    for step in process_steps_data:
        cur.execute("""
            INSERT OR REPLACE INTO baseline_process_steps 
            (baseline_id, step_number, title, description, responsible_role, objective)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (baseline_id, step["step_number"], step["title"], step["description"], 
              step["responsible_role"], step["objective"]))


def seed_risks_for_baseline(cur, baseline_id):
    """Seed risks for a specific baseline"""
    risks_data = get_risks_template(baseline_id)
    
    for risk in risks_data:
        cur.execute("""
            INSERT OR REPLACE INTO baseline_risks 
            (baseline_id, risk_id, name, description, category, severity, related_step_numbers)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (baseline_id, risk["risk_id"], risk["name"], risk["description"], 
              risk["category"], risk["severity"], json.dumps(risk["related_step_numbers"])))


def seed_controls_for_baseline(cur, baseline_id):
    """Seed controls for a specific baseline"""
    controls_data = get_controls_template(baseline_id)
    
    for control in controls_data:
        cur.execute("""
            INSERT OR REPLACE INTO baseline_controls 
            (baseline_id, control_id, name, description, control_type, risk_ids, frequency)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (baseline_id, control["control_id"], control["name"], control["description"], 
              control["control_type"], json.dumps(control["risk_ids"]), control["frequency"]))


def seed_compliance_for_baseline(cur, baseline_id):
    """Seed compliance requirements for a specific baseline"""
    compliance_data = get_compliance_template(baseline_id)
    
    for requirement in compliance_data:
        cur.execute("""
            INSERT OR REPLACE INTO baseline_compliance_requirements 
            (baseline_id, regulation, requirement_text, applicable_regions)
            VALUES (?, ?, ?, ?)
        """, (baseline_id, requirement["regulation"], requirement["requirement_text"], 
              json.dumps(requirement["applicable_regions"])))


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
    
    # Seed Golden Thread data after baselines are created
    if success and not seed_golden_thread_data():
        success = False
    
    if success:
        print("✅ All demo data seeded successfully!")
    else:
        print("❌ Seeding failed - check logs above")
    
    return success


if __name__ == "__main__":
    seed_all_data()
