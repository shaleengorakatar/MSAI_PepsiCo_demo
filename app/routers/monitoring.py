"""Router for Predictive Risk monitoring and AI activity tracking."""
from __future__ import annotations

import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException

from app.data.store import store
from app.models.schemas import MonitoringReport, PerformanceDataPoint
from app.services.llm_service import generate_ai_summary
from app.services.risk_monitor import generate_mock_performance_data, run_predictive_risk_analysis

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Predictive Risk Monitoring"])

# AI Activity tracking for the monitoring dashboard
AI_AGENTS = [
    "Marketing_Copilot", "Sales_Analytics_Bot", "Finance_Operator", 
    "Quality_Control_AI", "Supply_Chain_AI", "Customer_Insight_AI",
    "Regulatory_Compliance_Agent", "Inventory_Optimizer", "Pricing_AI"
]

ACTIONS = [
    "API Call", "SQL Query", "Data Export", "User Authentication", 
    "File Access", "Report Generation", "Model Training", "Data Processing"
]

# Store for AI activity logs
ai_activity_logs = []


# ---------------------------------------------------------------------------
# AI Activity Monitoring Endpoints (for frontend compatibility)
# ---------------------------------------------------------------------------

@router.get("/logs")
async def get_ai_logs(limit: int = 50) -> Dict[str, Any]:
    """Get AI activity logs for monitoring dashboard."""
    global ai_activity_logs
    
    # Generate new logs if we don't have enough
    while len(ai_activity_logs) < limit:
        log_entry = {
            "id": len(ai_activity_logs) + 1,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "agent": random.choice(AI_AGENTS),
            "action": random.choice(ACTIONS),
            "risk_score": round(random.uniform(0.1, 0.8), 2),
            "status": "success" if random.random() > 0.1 else "warning",
            "details": f"AI agent performed {random.choice(ACTIONS).lower()} operation"
        }
        ai_activity_logs.append(log_entry)
    
    # Keep only the most recent logs
    ai_activity_logs = ai_activity_logs[-(limit * 2):]
    
    # Return the most recent logs
    recent_logs = ai_activity_logs[-limit:]
    
    print(f"📊 Returning {len(recent_logs)} logs")
    for log in recent_logs[-5:]:  # Print last 5 for debugging
        print(f"🔄 Generated normal log: {log['agent']} - {log['action']} (Risk: {log['risk_score']})")
    
    return {
        "logs": recent_logs,
        "total": len(ai_activity_logs),
        "generated_at": datetime.utcnow().isoformat() + "Z"
    }


@router.post("/classify")
async def classify_activity(activity: Dict[str, Any]) -> Dict[str, Any]:
    """Classify AI activity for risk assessment."""
    # Simulate classification logic
    risk_level = "low"
    risk_score = activity.get("risk_score", 0.3)
    
    if risk_score > 0.7:
        risk_level = "high"
    elif risk_score > 0.4:
        risk_level = "medium"
    
    return {
        "classification": risk_level,
        "confidence": round(random.uniform(0.8, 0.95), 2),
        "risk_factors": [
            "Unusual data access pattern",
            "Elevated privilege usage"
        ] if risk_score > 0.5 else ["Normal operation"],
        "recommendations": [
            "Monitor for continued activity",
            "Review access permissions"
        ] if risk_score > 0.4 else ["No action needed"],
        "analyzed_at": datetime.utcnow().isoformat() + "Z"
    }


@router.get("/stats")
async def get_monitoring_stats() -> Dict[str, Any]:
    """Get monitoring statistics for dashboard."""
    try:
        # Calculate stats from logs
        total_logs = len(ai_activity_logs)
        recent_logs = []
        
        for log in ai_activity_logs:
            try:
                # Safe datetime parsing
                timestamp_str = log["timestamp"].replace("Z", "+00:00")
                log_time = datetime.fromisoformat(timestamp_str)
                if log_time > datetime.utcnow() - timedelta(hours=24):
                    recent_logs.append(log)
            except Exception as e:
                logger.warning(f"Skipping invalid timestamp in log: {e}")
                continue
        
        high_risk_count = len([log for log in recent_logs if log["risk_score"] > 0.7])
        medium_risk_count = len([log for log in recent_logs if 0.4 < log["risk_score"] <= 0.7])
        low_risk_count = len(recent_logs) - high_risk_count - medium_risk_count
        
        # Agent activity breakdown
        agent_activity = {}
        for log in recent_logs:
            agent = log["agent"]
            agent_activity[agent] = agent_activity.get(agent, 0) + 1
        
        avg_risk_score = round(sum(log["risk_score"] for log in recent_logs) / len(recent_logs), 2) if recent_logs else 0
        
        return {
            "total_activities": total_logs,
            "recent_24h": len(recent_logs),
            "risk_distribution": {
                "high": high_risk_count,
                "medium": medium_risk_count, 
                "low": low_risk_count
            },
            "agent_activity": agent_activity,
            "avg_risk_score": avg_risk_score,
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error in get_monitoring_stats: {e}")
        # Return safe default values
        return {
            "total_activities": 0,
            "recent_24h": 0,
            "risk_distribution": {"high": 0, "medium": 0, "low": 0},
            "agent_activity": {},
            "avg_risk_score": 0.0,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "error": str(e)
        }


@router.get("/stats/history")
async def get_stats_history(hours: int = 24) -> Dict[str, Any]:
    """Get historical monitoring statistics."""
    try:
        # Generate hourly stats for the past N hours
        history = []
        current_time = datetime.utcnow()
        
        for i in range(hours):
            hour_time = current_time - timedelta(hours=i)
            hour_start = hour_time.replace(minute=0, second=0, microsecond=0)
            hour_end = hour_start + timedelta(hours=1)
            
            # Count logs in this hour with safe datetime parsing
            hour_logs = []
            for log in ai_activity_logs:
                try:
                    timestamp_str = log["timestamp"].replace("Z", "+00:00")
                    log_time = datetime.fromisoformat(timestamp_str)
                    if hour_start <= log_time < hour_end:
                        hour_logs.append(log)
                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping invalid timestamp in history log: {e}")
                    continue
            
            if hour_logs:
                avg_risk = sum(log["risk_score"] for log in hour_logs) / len(hour_logs)
                high_risk = len([log for log in hour_logs if log["risk_score"] > 0.7])
            else:
                avg_risk = 0
                high_risk = 0
            
            history.append({
                "timestamp": hour_start.isoformat() + "Z",
                "activity_count": len(hour_logs),
                "avg_risk_score": round(avg_risk, 2),
                "high_risk_count": high_risk
            })
        
        return {
            "history": list(reversed(history)),  # Most recent first
            "period_hours": hours,
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error in get_stats_history: {e}")
        # Return safe default values
        return {
            "history": [],
            "period_hours": hours,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "error": str(e)
        }


@router.post(
    "/monitoring/ingest",
    summary="Ingest performance data points",
    description="Submit performance data points (effectiveness scores, timing, etc.) for controls.",
)
async def ingest_performance_data(data_points: List[PerformanceDataPoint]):
    count = store.add_performance_data(data_points)
    return {"ingested": count, "total_stored": len(store.performance_data)}


@router.post(
    "/monitoring/generate-mock/{baseline_id}",
    summary="Generate mock performance data for a baseline",
    description="Creates synthetic performance data for demonstration and testing purposes.",
)
async def generate_mock_data(baseline_id: str):
    baseline = store.get_baseline(baseline_id)
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline not found")

    mock_data = generate_mock_performance_data(baseline)
    count = store.add_performance_data(mock_data)
    return {"generated": count, "baseline_id": baseline_id}


@router.get(
    "/monitoring/report/{baseline_id}",
    response_model=MonitoringReport,
    summary="Generate predictive risk report",
    description=(
        "Analyzes stored performance data for a baseline's controls and produces "
        "a predictive risk report with failure probabilities, trends, and recommendations. "
        "If no performance data exists, automatically generates mock data for demonstration."
    ),
)
async def get_risk_report(baseline_id: str, generate_mock: bool = True):
    baseline = store.get_baseline(baseline_id)
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline not found")

    perf_data = store.get_performance_data()
    # Filter to data relevant to this baseline
    relevant_data = [
        p for p in perf_data if p.control_id.startswith(baseline_id)
    ]

    # Auto-generate mock data if none exists and generate_mock is True
    if not relevant_data and generate_mock:
        logger.info(f"No performance data found for baseline {baseline_id}. Generating mock data...")
        mock_data = generate_mock_performance_data(baseline)
        store.add_performance_data(mock_data)
        relevant_data = mock_data
        logger.info(f"Generated {len(mock_data)} mock performance data points")

    if not relevant_data:
        raise HTTPException(
            status_code=404, 
            detail=f"No monitoring data has been ingested for baseline {baseline_id}. "
                   f"Use POST /monitoring/generate-mock/{baseline_id} to generate sample data."
        )

    report = run_predictive_risk_analysis(baseline, relevant_data)

    # Add data source information
    report.ai_summary = report.ai_summary or f"Risk report generated for baseline {baseline.name.default} "
    if not relevant_data:
        report.ai_summary += "using simulated performance data."
    else:
        report.ai_summary += f"based on {len(relevant_data)} performance data points."

    # Generate AI summary with source references
    try:
        summary_data = await generate_ai_summary(
            report.model_dump(),
            context_label=f"Predictive Risk report for baseline: {baseline.name.default}",
        )
        report.ai_summary = summary_data.get("ai_summary")
        report.ai_sources = summary_data.get("ai_sources", [])
    except Exception as e:
        logger.warning("AI summary generation failed for monitoring: %s", e)

    return report


@router.get(
    "/monitoring/status/{baseline_id}",
    summary="Check monitoring data status for baseline",
    description="Returns information about available performance data for a baseline.",
)
async def get_monitoring_status(baseline_id: str):
    baseline = store.get_baseline(baseline_id)
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline not found")

    perf_data = store.get_performance_data()
    relevant_data = [
        p for p in perf_data if p.control_id.startswith(baseline_id)
    ]

    return {
        "baseline_id": baseline_id,
        "baseline_name": baseline.name.default,
        "has_data": len(relevant_data) > 0,
        "data_points_count": len(relevant_data),
        "latest_timestamp": max([p.timestamp for p in relevant_data]) if relevant_data else None,
        "can_generate_report": True,
        "recommendation": "Use GET /monitoring/report/{baseline_id} to generate risk report" if len(relevant_data) > 0 
                           else "Use POST /monitoring/generate-mock/{baseline_id} to generate sample data first"
    }
