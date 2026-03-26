#!/usr/bin/env python3
"""
Test script to verify database setup and CSV seeding
"""
import os
import sys

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.database import seed_all_data, get_db_connection

def test_database():
    """Test database connection and seeding"""
    print("🧪 Testing database setup...")
    
    # Test connection
    conn = get_db_connection()
    if not conn:
        print("❌ Database connection failed")
        return False
    
    print("✅ Database connection successful")
    conn.close()
    
    # Test seeding
    print("🌱 Testing database seeding...")
    success = seed_all_data()
    
    if success:
        print("✅ Database seeding successful!")
        
        # Verify data was seeded
        conn = get_db_connection()
        if conn:
            try:
                import sqlite3
                is_sqlite = isinstance(conn, sqlite3.Connection)
                
                if is_sqlite:
                    cur = conn.cursor()
                    # Check baselines
                    cur.execute("SELECT COUNT(*) FROM baselines")
                    baselines_count = cur.fetchone()[0]
                    print(f"📊 Baselines seeded: {baselines_count}")
                    
                    # Check tools
                    cur.execute("SELECT COUNT(*) FROM tools")
                    tools_count = cur.fetchone()[0]
                    print(f"🔧 Tools seeded: {tools_count}")
                    
                    # Check regions
                    cur.execute("SELECT COUNT(*) FROM regions")
                    regions_count = cur.fetchone()[0]
                    print(f"🌍 Regions seeded: {regions_count}")
                    
                    # Check framework
                    cur.execute("SELECT COUNT(*) FROM framework")
                    framework_count = cur.fetchone()[0]
                    print(f"🏗️ Framework seeded: {framework_count}")
                else:
                    # PostgreSQL with context manager
                    with conn.cursor() as cur:
                        # Check baselines
                        cur.execute("SELECT COUNT(*) FROM baselines")
                        baselines_count = cur.fetchone()[0]
                        print(f"📊 Baselines seeded: {baselines_count}")
                        
                        # Check tools
                        cur.execute("SELECT COUNT(*) FROM tools")
                        tools_count = cur.fetchone()[0]
                        print(f"🔧 Tools seeded: {tools_count}")
                        
                        # Check regions
                        cur.execute("SELECT COUNT(*) FROM regions")
                        regions_count = cur.fetchone()[0]
                        print(f"🌍 Regions seeded: {regions_count}")
                        
                        # Check framework
                        cur.execute("SELECT COUNT(*) FROM framework")
                        framework_count = cur.fetchone()[0]
                        print(f"🏗️ Framework seeded: {framework_count}")
                
                conn.close()
                return True
                    
            except Exception as e:
                print(f"❌ Error verifying seeded data: {e}")
                conn.close()
                return False
    else:
        print("❌ Database seeding failed")
        return False

if __name__ == "__main__":
    test_database()
