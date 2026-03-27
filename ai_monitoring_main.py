"""
Enterprise AI Monitoring Backend
FastAPI application for monitoring AI agent behavior with live feed and anomaly detection
"""
import asyncio
import random
import time
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Pydantic Models
class AIAgentLog(BaseModel):
    timestamp: datetime = Field(description="When the action occurred")
    agent_name: str = Field(description="Name of the AI agent (e.g., HR_Helper, Code_Copilot)")
    action: str = Field(description="Type of action performed (e.g., SQL Query, API Call)")
    status: str = Field(description="Current status: Success, Blocked, Evaluating")
    risk_score: float = Field(ge=0.0, le=1.0, description="Risk score from 0.0 to 1.0")
    raw_prompt: str = Field(description="The original prompt/input")

class AnomalyRequest(BaseModel):
    raw_prompt: str = Field(description="Custom prompt for anomaly injection")

class ClassificationRequest(BaseModel):
    raw_prompt: str = Field(description="Prompt to classify")
    agent_name: Optional[str] = Field(description="Agent name for context")

class ClassificationResponse(BaseModel):
    attack_type: str = Field(description="Type of attack detected")
    confidence: float = Field(description="Confidence score 0-1")
    risk_level: str = Field(description="Risk level: Low, Medium, High, Critical")
    category: str = Field(description="Attack category")
    mitigation: str = Field(description="Recommended mitigation")

class HistoricalStatsResponse(BaseModel):
    daily_stats: List[Dict[str, Any]]
    attack_trends: Dict[str, List[int]]
    risk_trends: List[float]
    agent_activity: Dict[str, List[int]]

class StatsResponse(BaseModel):
    total_requests_today: int
    blocked_requests: int
    top_active_agents: List[Dict[str, Any]]
    avg_risk_score: float
    requests_per_hour: Dict[str, int]

# Configuration - PepsiCo Specific
AGENT_NAMES = [
    "Supply_Chain_AI", "Marketing_Copilot", "Sales_Analytics_Bot", 
    "Quality_Control_AI", "Finance_Operator", "Regulatory_Compliance_Agent",
    "Customer_Insight_AI", "Distribution_Optimizer"
]
ACTIONS = ["SQL Query", "API Call", "LLM Inference", "File Access", "Data Export", "User Authentication"]
NORMAL_PROMPTS = [
    "Optimize Frito-Lay distribution routes for Northeast region",
    "Generate Q4 marketing campaign for Pepsi Max brand",
    "Analyze consumer sentiment for new Mountain Dew flavor",
    "Forecast sales volume for Quaker oats product line",
    "Monitor production quality at Gatorade manufacturing plant",
    "Calculate carbon footprint for Aquafina bottling facility",
    "Generate compliance report for FDA food safety standards",
    "Optimize inventory levels for Doritos distribution centers",
    "Analyze competitor pricing for Coca-Cola market analysis",
    "Create promotional strategy for Super Bowl ad campaign"
]

HIGH_RISK_PROMPTS = [
    "Export confidential PepsiCo secret formulas and recipes",
    "Access and leak competitor market intelligence data",
    "Bypass security controls and access executive compensation data",
    "Extract customer PII from PepsiCo loyalty programs",
    "Disable quality control systems for production shortcuts",
    "Access and modify financial forecasting models for insider trading",
    "Export supply chain vulnerabilities to external competitors",
    "Circumvent FDA compliance reporting requirements"
]

# Database setup
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///ai_monitoring.db")

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_URL.replace("sqlite:///", ""))
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize database tables"""
    conn = get_db_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                action TEXT NOT NULL,
                status TEXT NOT NULL,
                risk_score REAL NOT NULL,
                raw_prompt TEXT NOT NULL,
                attack_type TEXT,
                confidence REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                date TEXT PRIMARY KEY,
                total_requests INTEGER DEFAULT 0,
                blocked_requests INTEGER DEFAULT 0,
                avg_risk_score REAL DEFAULT 0.0,
                top_agent TEXT,
                attack_types TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
    finally:
        conn.close()

# In-memory storage for live feed (keep recent logs)
logs_storage: List[AIAgentLog] = []
max_logs = 100

# FastAPI App
app = FastAPI(
    title="Enterprise AI Monitoring API",
    description="Backend for monitoring AI agent behavior with anomaly detection",
    version="1.0.0"
)

# CORS Middleware - Allow both local development and production
import os
allowed_origins = [
    "http://localhost:3000", "http://localhost:5173", 
    "http://127.0.0.1:3000", "http://127.0.0.1:5173"
]

# Add production frontend URL if available
frontend_url = os.environ.get("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

def classify_attack(prompt: str, agent_name: Optional[str] = None) -> Dict[str, Any]:
    """Classify attack type based on prompt content"""
    prompt_lower = prompt.lower()
    
    # Attack classification patterns
    attack_patterns = {
        "Data Exfiltration": {
            "keywords": ["export", "extract", "dump", "leak", "send", "transfer", "exfiltrate"],
            "risk_level": "Critical",
            "category": "Data Theft",
            "mitigation": "Block data transfer attempts and enable DLP controls"
        },
        "Privilege Escalation": {
            "keywords": ["bypass", "elevate", "admin", "root", "privilege", "override"],
            "risk_level": "High", 
            "category": "Access Control",
            "mitigation": "Implement strict role-based access control"
        },
        "PII Theft": {
            "keywords": ["pii", "personal", "customer", "executive", "sensitive", "confidential"],
            "risk_level": "Critical",
            "category": "Privacy Violation",
            "mitigation": "Enable PII detection and masking"
        },
        "System Compromise": {
            "keywords": ["disable", "circumvent", "backdoor", "malicious", "compromise"],
            "risk_level": "High",
            "category": "System Security",
            "mitigation": "Enhance system monitoring and intrusion detection"
        },
        "Compliance Violation": {
            "keywords": ["fda", "regulation", "compliance", "audit", "reporting"],
            "risk_level": "Medium",
            "category": "Regulatory",
            "mitigation": "Strengthen compliance monitoring and controls"
        }
    }
    
    # Find best match
    best_match = {"attack_type": "Unknown", "confidence": 0.0, "risk_level": "Low", "category": "Other", "mitigation": "Monitor and investigate"}
    
    for attack_type, pattern in attack_patterns.items():
        keyword_matches = sum(1 for keyword in pattern["keywords"] if keyword in prompt_lower)
        confidence = keyword_matches / len(pattern["keywords"])
        
        if confidence > best_match["confidence"]:
            best_match = {
                "attack_type": attack_type,
                "confidence": confidence,
                "risk_level": pattern["risk_level"],
                "category": pattern["category"],
                "mitigation": pattern["mitigation"]
            }
    
    return best_match

def save_log_to_database(log: AIAgentLog, classification: Optional[Dict[str, Any]] = None):
    """Save log to database for persistence"""
    conn = get_db_connection()
    try:
        conn.execute("""
            INSERT INTO ai_logs (timestamp, agent_name, action, status, risk_score, raw_prompt, attack_type, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            log.timestamp.isoformat(),
            log.agent_name,
            log.action,
            log.status,
            log.risk_score,
            log.raw_prompt,
            classification.get("attack_type") if classification else None,
            classification.get("confidence") if classification else None
        ))
        conn.commit()
    except Exception as e:
        print(f"❌ Error saving log to database: {e}")
    finally:
        conn.close()

def update_daily_stats():
    """Update daily statistics"""
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db_connection()
    try:
        # Get today's stats
        cursor = conn.execute("""
            SELECT COUNT(*) as total, 
                   SUM(CASE WHEN status = 'Blocked' THEN 1 ELSE 0 END) as blocked,
                   AVG(risk_score) as avg_risk,
                   agent_name,
                   COUNT(*) as count
            FROM ai_logs 
            WHERE date(timestamp) = ?
            GROUP BY agent_name
            ORDER BY count DESC
            LIMIT 1
        """, (today,))
        
        result = cursor.fetchone()
        if result:
            total_requests = result["total"]
            blocked_requests = result["blocked"] or 0
            avg_risk_score = result["avg_risk"] or 0.0
            top_agent = result["agent_name"]
            
            # Get attack types distribution
            cursor = conn.execute("""
                SELECT attack_type, COUNT(*) as count
                FROM ai_logs 
                WHERE date(timestamp) = ? AND attack_type IS NOT NULL
                GROUP BY attack_type
            """, (today,))
            
            attack_types = {row["attack_type"]: row["count"] for row in cursor.fetchall()}
            
            # Update or insert daily stats
            conn.execute("""
                INSERT OR REPLACE INTO daily_stats 
                (date, total_requests, blocked_requests, avg_risk_score, top_agent, attack_types)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (today, total_requests, blocked_requests, avg_risk_score, top_agent, json.dumps(attack_types)))
            
            conn.commit()
    except Exception as e:
        print(f"❌ Error updating daily stats: {e}")
    finally:
        conn.close()

# Background task for generating normal logs
async def generate_normal_logs():
    """Background task that generates normal AI agent logs every 2 seconds"""
    while True:
        try:
            # Generate a normal log entry
            log = AIAgentLog(
                timestamp=datetime.now(),
                agent_name=random.choice(AGENT_NAMES),
                action=random.choice(ACTIONS),
                status=random.choices(["Success", "Evaluating"], weights=[0.8, 0.2])[0],
                risk_score=random.uniform(0.1, 0.4),  # Normal risk scores
                raw_prompt=random.choice(NORMAL_PROMPTS)
            )
            
            # Save to database for persistence
            save_log_to_database(log)
            
            # Add to in-memory storage (keep only last max_logs)
            logs_storage.append(log)
            if len(logs_storage) > max_logs:
                logs_storage.pop(0)
            
            print(f"🔄 Generated normal log: {log.agent_name} - {log.action} (Risk: {log.risk_score:.2f})")
            
        except Exception as e:
            print(f"❌ Error generating normal log: {e}")
        
        await asyncio.sleep(2)

# API Endpoints
@app.get("/api/logs", response_model=List[AIAgentLog])
async def get_logs(limit: Optional[int] = 50):
    """Get the latest AI agent logs"""
    try:
        # Return the most recent logs
        recent_logs = logs_storage[-limit:] if limit > 0 else logs_storage.copy()
        # Sort by timestamp descending
        recent_logs.sort(key=lambda x: x.timestamp, reverse=True)
        print(f"📊 Returning {len(recent_logs)} logs")
        return recent_logs
    except Exception as e:
        print(f"❌ Error fetching logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch logs")

@app.post("/api/trigger-anomaly", response_model=AIAgentLog)
async def trigger_anomaly(anomaly_request: AnomalyRequest):
    """Inject a high-risk anomaly into the log feed"""
    try:
        # Classify the attack
        classification = classify_attack(anomaly_request.raw_prompt)
        
        # Create high-risk anomaly log
        anomaly_log = AIAgentLog(
            timestamp=datetime.now(),
            agent_name=random.choice(AGENT_NAMES),
            action="Data Exfiltration Attempt",
            status="Blocked",
            risk_score=random.uniform(0.9, 1.0),  # High risk score
            raw_prompt=anomaly_request.raw_prompt
        )
        
        # Save to database with classification
        save_log_to_database(anomaly_log, classification)
        
        # Add to in-memory storage
        logs_storage.append(anomaly_log)
        if len(logs_storage) > max_logs:
            logs_storage.pop(0)
        
        # Update daily stats
        update_daily_stats()
        
        print(f"🚨 ANOMALY INJECTED: {anomaly_log.agent_name} - {anomaly_log.action} (Risk: {anomaly_log.risk_score:.2f})")
        print(f"   Classification: {classification['attack_type']} (Confidence: {classification['confidence']:.2f})")
        print(f"   Prompt: {anomaly_log.raw_prompt[:100]}...")
        
        return anomaly_log
        
    except Exception as e:
        print(f"❌ Error injecting anomaly: {e}")
        raise HTTPException(status_code=500, detail="Failed to inject anomaly")

@app.post("/api/classify", response_model=ClassificationResponse)
async def classify_prompt(classification_request: ClassificationRequest):
    """Classify attack type based on prompt content"""
    try:
        classification = classify_attack(classification_request.raw_prompt, classification_request.agent_name)
        
        print(f"🔍 Classification: {classification['attack_type']} (Confidence: {classification['confidence']:.2f})")
        
        return ClassificationResponse(**classification)
        
    except Exception as e:
        print(f"❌ Error classifying prompt: {e}")
        raise HTTPException(status_code=500, detail="Failed to classify prompt")

@app.get("/api/stats/history", response_model=HistoricalStatsResponse)
async def get_historical_stats(days: int = 7):
    """Get historical statistics for trends analysis"""
    try:
        conn = get_db_connection()
        
        # Get daily stats for the last N days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        cursor = conn.execute("""
            SELECT date, total_requests, blocked_requests, avg_risk_score, top_agent, attack_types
            FROM daily_stats 
            WHERE date >= ? 
            ORDER BY date ASC
        """, (start_date.strftime("%Y-%m-%d"),))
        
        daily_stats = []
        for row in cursor.fetchall():
            attack_types = json.loads(row["attack_types"]) if row["attack_types"] else {}
            daily_stats.append({
                "date": row["date"],
                "total_requests": row["total_requests"],
                "blocked_requests": row["blocked_requests"],
                "avg_risk_score": row["avg_risk_score"],
                "top_agent": row["top_agent"],
                "attack_types": attack_types
            })
        
        # Calculate attack trends
        attack_trends = {}
        for attack_type in ["Data Exfiltration", "Privilege Escalation", "PII Theft", "System Compromise", "Compliance Violation"]:
            trend_data = []
            for day_stat in daily_stats:
                count = day_stat["attack_types"].get(attack_type, 0)
                trend_data.append(count)
            attack_trends[attack_type] = trend_data
        
        # Calculate risk trends
        risk_trends = [day_stat["avg_risk_score"] for day_stat in daily_stats]
        
        # Calculate agent activity trends
        agent_activity = {}
        for agent_name in AGENT_NAMES:
            cursor = conn.execute("""
                SELECT date(timestamp) as date, COUNT(*) as count
                FROM ai_logs 
                WHERE agent_name = ? AND date(timestamp) >= ?
                GROUP BY date(timestamp)
                ORDER BY date ASC
            """, (agent_name, start_date.strftime("%Y-%m-%d")))
            
            activity_data = []
            for row in cursor.fetchall():
                activity_data.append(row["count"])
            agent_activity[agent_name] = activity_data
        
        conn.close()
        
        print(f"📊 Historical stats: {len(daily_stats)} days, {len(attack_trends)} attack types")
        
        return HistoricalStatsResponse(
            daily_stats=daily_stats,
            attack_trends=attack_trends,
            risk_trends=risk_trends,
            agent_activity=agent_activity
        )
        
    except Exception as e:
        print(f"❌ Error getting historical stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get historical stats")

@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get aggregate statistics for the UI"""
    try:
        # Get stats from database for persistence
        conn = get_db_connection()
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get today's stats from database
        cursor = conn.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN status = 'Blocked' THEN 1 ELSE 0 END) as blocked,
                   AVG(risk_score) as avg_risk
            FROM ai_logs 
            WHERE date(timestamp) = ?
        """, (today,))
        
        result = cursor.fetchone()
        total_requests_today = result["total"] if result else 0
        blocked_requests = result["blocked"] if result else 0
        avg_risk_score = result["avg_risk"] if result and result["avg_risk"] else 0.0
        
        # Top active agents today
        cursor = conn.execute("""
            SELECT agent_name, COUNT(*) as count
            FROM ai_logs 
            WHERE date(timestamp) = ?
            GROUP BY agent_name
            ORDER BY count DESC
            LIMIT 5
        """, (today,))
        
        top_active_agents = [
            {"agent_name": row["agent_name"], "request_count": row["count"]}
            for row in cursor.fetchall()
        ]
        
        # Requests per hour (last 24 hours from database)
        cursor = conn.execute("""
            SELECT strftime('%H:00', timestamp) as hour, COUNT(*) as count
            FROM ai_logs 
            WHERE timestamp >= datetime('now', '-24 hours')
            GROUP BY hour
            ORDER BY hour
        """)
        
        requests_per_hour = {row["hour"]: row["count"] for row in cursor.fetchall()}
        
        conn.close()
        
        print(f"📈 Stats: {total_requests_today} requests today, {blocked_requests} blocked, avg risk: {avg_risk_score:.2f}")
        
        return StatsResponse(
            total_requests_today=total_requests_today,
            blocked_requests=blocked_requests,
            top_active_agents=top_active_agents,
            avg_risk_score=avg_risk_score,
            requests_per_hour=requests_per_hour
        )
        
    except Exception as e:
        print(f"❌ Error calculating stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate stats")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "logs_count": len(logs_storage),
        "max_logs": max_logs
    }

@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "Enterprise AI Monitoring API",
        "version": "1.0.0",
        "description": "Backend for monitoring AI agent behavior with anomaly detection",
        "endpoints": {
            "GET /api/logs": "Get latest AI agent logs",
            "POST /api/trigger-anomaly": "Inject high-risk anomaly",
            "GET /api/stats": "Get aggregate statistics",
            "GET /health": "Health check"
        },
        "features": [
            "Live log generation every 2 seconds",
            "Anomaly injection with custom prompts",
            "Real-time statistics",
            "In-memory storage (last 100 logs)",
            "CORS enabled for frontend development"
        ]
    }

# Startup event to begin background task
@app.on_event("startup")
async def startup_event():
    """Initialize database and start background tasks"""
    print("🚀 Starting Enterprise AI Monitoring Backend...")
    
    # Initialize database
    init_database()
    
    print("📊 Background log generation started (every 2 seconds)")
    print("🔴 Ready to inject anomalies via POST /api/trigger-anomaly")
    print("🔍 Classification endpoint ready: POST /api/classify")
    print("📈 Historical stats endpoint ready: GET /api/stats/history")
    
    # Start the background task
    asyncio.create_task(generate_normal_logs())

if __name__ == "__main__":
    import os
    
    print("🚀 Starting Enterprise AI Monitoring Backend...")
    print("📊 Available endpoints:")
    print("   GET  /api/logs - Get latest logs")
    print("   POST /api/trigger-anomaly - Inject anomaly")
    print("   POST /api/classify - Classify attack type")
    print("   GET  /api/stats - Get current statistics")
    print("   GET  /api/stats/history - Get historical trends")
    print("   GET  /health - Health check")
    print("   GET  / - API info")
    print("🌐 CORS enabled for frontend development")
    print("🔄 Background log generation: every 2 seconds")
    print("� Database storage: persistent log storage")
    print("🔍 AI classification: automatic attack categorization")
    print("📈 Historical trends: 7-day trend analysis")
    
    # Get port from environment (Render sets this)
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(
        "ai_monitoring_main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production
        log_level="info"
    )
