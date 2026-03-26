#!/usr/bin/env python3
"""
Debug script to check database state
"""
import os
import sys

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.database import get_db_connection

def debug_database():
    """Debug database state"""
    print("🔍 Debugging database state...")
    
    # Test connection
    conn = get_db_connection()
    if not conn:
        print("❌ Database connection failed")
        return
    
    print("✅ Database connection successful")
    
    try:
        import sqlite3
        is_sqlite = isinstance(conn, sqlite3.Connection)
        
        if is_sqlite:
            cur = conn.cursor()
            
            # Check if tables exist
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cur.fetchall()
            print(f"📋 Tables found: {[table[0] for table in tables]}")
            
            # Check baselines count
            cur.execute("SELECT COUNT(*) FROM baselines")
            baselines_count = cur.fetchone()[0]
            print(f"📊 Baselines count: {baselines_count}")
            
            # Show sample baseline data
            if baselines_count > 0:
                cur.execute("SELECT baseline_id, baseline_name FROM baselines LIMIT 3")
                sample_baselines = cur.fetchall()
                print(f"📝 Sample baselines: {sample_baselines}")
            
            conn.close()
        else:
            print("🔄 PostgreSQL detected")
            conn.close()
            
    except Exception as e:
        print(f"❌ Error debugging database: {e}")
        conn.close()

if __name__ == "__main__":
    debug_database()
