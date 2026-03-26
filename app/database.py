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


def get_db_connection():
    """Get database connection - PostgreSQL or SQLite"""
    if not settings.database_url:
        print("❌ DATABASE_URL not configured")
        return None
    
    # Check if it's a SQLite URL
    if settings.database_url.startswith("sqlite:///"):
        try:
            # Extract database path from SQLite URL
            db_path = settings.database_url.replace("sqlite:///", "")
            if not os.path.isabs(db_path):
                # Make relative path absolute
                db_path = os.path.join(os.path.dirname(__file__), '..', db_path)
            
            conn = sqlite3.connect(db_path)
            print(f"✅ SQLite database connection successful: {db_path}")
            return conn
        except Exception as e:
            print(f"❌ SQLite connection failed: {e}")
            return None
    
    # Try PostgreSQL
    try:
        conn = psycopg2.connect(settings.database_url)
        print("✅ PostgreSQL database connection successful")
        return conn
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return None


def create_tables():
    """Create database tables"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        # Check if using SQLite or PostgreSQL
        is_sqlite = isinstance(conn, sqlite3.Connection)
        
        if is_sqlite:
            cur = conn.cursor()
            
            # Create baselines table (SQLite)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS baselines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    baseline_id TEXT UNIQUE NOT NULL,
                    baseline_name TEXT NOT NULL,
                    description TEXT,
                    maturity_level TEXT,
                    control_coverage TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create tools table (SQLite)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tools (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_id TEXT UNIQUE NOT NULL,
                    tool_name TEXT NOT NULL,
                    tool_type TEXT,
                    description TEXT,
                    vendor TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create regions table (SQLite)
            cur.execute("""
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
                )
            """)
            
            # Create framework table (SQLite)
            cur.execute("""
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
                )
            """)
            
        else:
            # PostgreSQL with context manager
            with conn.cursor() as cur:
                # Create baselines table (PostgreSQL)
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
                
                # Create tools table (PostgreSQL)
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
                
                # Create regions table (PostgreSQL)
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
                
                # Create framework table (PostgreSQL)
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
        # Check if using SQLite or PostgreSQL
        is_sqlite = isinstance(conn, sqlite3.Connection)
        
        if is_sqlite:
            cur = conn.cursor()
            for baseline in baselines_data:
                # SQLite uses INSERT OR REPLACE
                cur.execute("""
                    INSERT OR REPLACE INTO baselines (baseline_id, baseline_name, description, maturity_level, control_coverage)
                    VALUES (?, ?, ?, ?, ?)
                """, (baseline["baseline_id"], baseline["baseline_name"], baseline["description"], 
                      baseline["maturity_level"], baseline["control_coverage"]))
        else:
            # PostgreSQL with context manager
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
        # Check if using SQLite or PostgreSQL
        is_sqlite = isinstance(conn, sqlite3.Connection)
        
        if is_sqlite:
            cur = conn.cursor()
            for tool in tools_data:
                # SQLite uses INSERT OR REPLACE
                cur.execute("""
                    INSERT OR REPLACE INTO tools (tool_id, tool_name, tool_type, description, vendor)
                    VALUES (?, ?, ?, ?, ?)
                """, (tool["tool_id"], tool["tool_name"], tool["tool_type"], 
                      tool["description"], tool["vendor"]))
        else:
            # PostgreSQL with context manager
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
        # Check if using SQLite or PostgreSQL
        is_sqlite = isinstance(conn, sqlite3.Connection)
        
        if is_sqlite:
            cur = conn.cursor()
            for region in regions_data:
                # SQLite uses INSERT OR REPLACE
                cur.execute("""
                    INSERT OR REPLACE INTO regions (region_id, region_name, country, compliance_score, risk_level, interviewee, position, interview_date, language, transcript_content)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (region["region_id"], region["region_name"], region["country"], region["compliance_score"], 
                      region["risk_level"], region["interviewee"], region["position"], region["interview_date"], 
                      region["language"], region["transcript_content"]))
        else:
            # PostgreSQL with context manager
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
        # Check if using SQLite or PostgreSQL
        is_sqlite = isinstance(conn, sqlite3.Connection)
        
        if is_sqlite:
            cur = conn.cursor()
            # Convert JSON data to strings for SQLite
            framework_data_sqlite = framework_data.copy()
            framework_data_sqlite['process_map'] = json.dumps(framework_data_sqlite['process_map'])
            framework_data_sqlite['risk_register'] = json.dumps(framework_data_sqlite['risk_register'])
            framework_data_sqlite['mitigating_controls'] = json.dumps(framework_data_sqlite['mitigating_controls'])
            framework_data_sqlite['compliance_requirements'] = json.dumps(framework_data_sqlite['compliance_requirements'])
            
            cur.execute("""
                INSERT OR IGNORE INTO framework (process_name, process_id, version, effective_date, business_context, process_map, risk_register, mitigating_controls, compliance_requirements)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (framework_data_sqlite['process_name'], framework_data_sqlite['process_id'], 
                  framework_data_sqlite['version'], framework_data_sqlite['effective_date'], 
                  framework_data_sqlite['business_context'], framework_data_sqlite['process_map'],
                  framework_data_sqlite['risk_register'], framework_data_sqlite['mitigating_controls'],
                  framework_data_sqlite['compliance_requirements']))
        else:
            # PostgreSQL with context manager
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
