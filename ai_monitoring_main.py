"""
Enterprise AI Monitoring Backend
FastAPI application for monitoring AI agent behavior with live feed and anomaly detection
"""
import asyncio
import random
import time
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

# In-memory storage
logs_storage: List[AIAgentLog] = []
max_logs = 100

# FastAPI App
app = FastAPI(
    title="Enterprise AI Monitoring API",
    description="Backend for monitoring AI agent behavior with anomaly detection",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

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
            
            # Add to storage (keep only last max_logs)
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
        # Create high-risk anomaly log
        anomaly_log = AIAgentLog(
            timestamp=datetime.now(),
            agent_name=random.choice(AGENT_NAMES),
            action="Data Exfiltration Attempt",
            status="Blocked",
            risk_score=random.uniform(0.9, 1.0),  # High risk score
            raw_prompt=anomaly_request.raw_prompt
        )
        
        # Add to storage
        logs_storage.append(anomaly_log)
        if len(logs_storage) > max_logs:
            logs_storage.pop(0)
        
        print(f"🚨 ANOMALY INJECTED: {anomaly_log.agent_name} - {anomaly_log.action} (Risk: {anomaly_log.risk_score:.2f})")
        print(f"   Prompt: {anomaly_log.raw_prompt[:100]}...")
        
        return anomaly_log
        
    except Exception as e:
        print(f"❌ Error injecting anomaly: {e}")
        raise HTTPException(status_code=500, detail="Failed to inject anomaly")

@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get aggregate statistics for the UI"""
    try:
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Filter logs from today
        today_logs = [log for log in logs_storage if log.timestamp >= today_start]
        
        # Calculate basic stats
        total_requests_today = len(today_logs)
        blocked_requests = len([log for log in today_logs if log.status == "Blocked"])
        
        # Top active agents
        agent_counts = {}
        for log in today_logs:
            agent_counts[log.agent_name] = agent_counts.get(log.agent_name, 0) + 1
        
        top_active_agents = [
            {"agent_name": agent, "request_count": count}
            for agent, count in sorted(agent_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Average risk score
        avg_risk_score = sum(log.risk_score for log in today_logs) / len(today_logs) if today_logs else 0.0
        
        # Requests per hour (last 24 hours)
        requests_per_hour = {}
        last_24_hours = now - timedelta(hours=24)
        recent_logs = [log for log in logs_storage if log.timestamp >= last_24_hours]
        
        for log in recent_logs:
            hour_key = log.timestamp.strftime("%H:00")
            requests_per_hour[hour_key] = requests_per_hour.get(hour_key, 0) + 1
        
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
    """Start the background log generation task"""
    print("🚀 Starting Enterprise AI Monitoring Backend...")
    print("📊 Background log generation started (every 2 seconds)")
    print("🔴 Ready to inject anomalies via POST /api/trigger-anomaly")
    
    # Start the background task
    asyncio.create_task(generate_normal_logs())

if __name__ == "__main__":
    print("🚀 Starting Enterprise AI Monitoring Backend...")
    print("📊 Available endpoints:")
    print("   GET  /api/logs - Get latest logs")
    print("   POST /api/trigger-anomaly - Inject anomaly")
    print("   GET  /api/stats - Get statistics")
    print("   GET  /health - Health check")
    print("   GET  / - API info")
    print("🌐 CORS enabled for frontend development")
    print("🔄 Background log generation: every 2 seconds")
    print("📝 In-memory storage: last 100 logs")
    
    uvicorn.run(
        "ai_monitoring_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
