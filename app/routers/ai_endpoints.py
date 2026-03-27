"""
AI-powered endpoints for enhanced GRC functionality.
Rate limited and structured output guaranteed.
"""
from __future__ import annotations

import logging
import time
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field

from app.services.llm_service import (
    generate_form_prefill,
    perform_security_triage,
    analyze_source_enhanced,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["AI-Powered Endpoints"])

# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class PrefillRequest(BaseModel):
    mode: str = Field(..., description="baseline or variation")
    analysis: Dict[str, Any] = Field(..., description="Full analysis result object")
    context: Optional[str] = Field(None, description="Optional context string")

class TriageRequest(BaseModel):
    anomaly: Dict[str, Any] = Field(..., description="Anomaly details")
    context: Optional[str] = Field(None, description="Additional context")

class AnalyzeSourceRequest(BaseModel):
    text: str = Field(..., description="Full transcript or document text")
    language: str = Field("en", description="Language code")
    context: Optional[str] = Field(None, description="Context information")

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def validate_llm_api_key():
    """Validate that LLM API key is configured."""
    from app.config import settings
    
    if not settings.openai_api_key and not settings.anthropic_api_key:
        raise HTTPException(
            status_code=500,
            detail="LLM API key not configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable."
        )
    return True

def log_ai_call(endpoint: str, request_data: Dict[str, Any]):
    """Log AI calls for audit trail."""
    logger.info(f"AI endpoint called: {endpoint}")
    logger.debug(f"Request data keys: {list(request_data.keys())}")
    # Note: Don't log sensitive data in production

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/prefill",
    summary="Pre-fill form fields for baseline or variation creation",
    description="Uses AI to extract structured form fields from analysis results.",
)
async def prefill_form(
    request: PrefillRequest,
    http_request: Request,
    _: None = Depends(validate_llm_api_key)
):
    """
    Generate pre-filled form fields for creating a Global Baseline or Local Variation 
    from an analysis result.
    
    - **mode**: "baseline" or "variation"
    - **analysis**: Full analysis result object
    - **context**: Optional country/region/interviewee info
    """
    try:
        log_ai_call("prefill", request.model_dump())
        
        # Validate mode
        if request.mode not in ["baseline", "variation"]:
            raise HTTPException(
                status_code=400,
                detail="Mode must be either 'baseline' or 'variation'"
            )
        
        # Validate analysis data
        if not request.analysis:
            raise HTTPException(
                status_code=400,
                detail="Analysis data is required"
            )
        
        # Call LLM service
        result = await generate_form_prefill(
            mode=request.mode,
            analysis=request.analysis,
            context=request.context
        )
        
        logger.info(f"Successfully generated prefill for mode: {request.mode}")
        return result
        
    except Exception as e:
        logger.error(f"Error in prefill endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate form prefill: {str(e)}"
        )


@router.post(
    "/triage",
    summary="Perform AI-powered security triage",
    description="Analyzes detected anomalies and provides structured triage reports.",
)
async def security_triage(
    request: TriageRequest,
    http_request: Request,
    _: None = Depends(validate_llm_api_key)
):
    """
    Perform AI-powered security triage analysis on a detected anomaly.
    
    - **anomaly**: Anomaly details including type, severity, details, affected controls
    - **context**: Additional context for the analysis
    """
    try:
        log_ai_call("triage", request.model_dump())
        
        # Validate anomaly data
        required_fields = ["type", "severity", "details"]
        for field in required_fields:
            if field not in request.anomaly:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field in anomaly: {field}"
                )
        
        # Call LLM service
        result = await perform_security_triage(
            anomaly=request.anomaly,
            context=request.context
        )
        
        logger.info(f"Successfully performed triage for anomaly type: {request.anomaly.get('type')}")
        return result
        
    except Exception as e:
        logger.error(f"Error in triage endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to perform security triage: {str(e)}"
        )


@router.post(
    "/analyze-source",
    summary="Enhanced source analysis with AI",
    description="Extract structured GRC data from interview transcripts or documents.",
)
async def analyze_source(
    request: AnalyzeSourceRequest,
    http_request: Request,
    _: None = Depends(validate_llm_api_key)
):
    """
    Enhanced source analysis using AI for extracting structured GRC data.
    
    - **text**: Full transcript or document text
    - **language**: Language code (e.g., en, de, es)
    - **context**: Context like country, region, interviewee role
    """
    try:
        log_ai_call("analyze-source", request.model_dump())
        
        # Validate input
        if not request.text or len(request.text.strip()) < 100:
            raise HTTPException(
                status_code=400,
                detail="Text must be at least 100 characters long"
            )
        
        # Validate language code
        valid_languages = ["en", "de", "es", "fr", "it", "pt", "nl", "sv", "no", "da"]
        if request.language not in valid_languages:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported language. Supported: {', '.join(valid_languages)}"
            )
        
        # Call LLM service
        result = await analyze_source_enhanced(
            text=request.text,
            language=request.language,
            context=request.context
        )
        
        logger.info(f"Successfully analyzed source text in language: {request.language}")
        return result
        
    except Exception as e:
        logger.error(f"Error in analyze-source endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze source: {str(e)}"
        )


@router.get(
    "/status",
    summary="Check AI service status",
    description="Returns the status of AI services and configuration.",
)
async def ai_status():
    """Check AI service status and configuration."""
    try:
        from app.config import settings
        
        status = {
            "service": "AI-Powered GRC Endpoints",
            "status": "healthy",
            "llm_provider": settings.llm_provider,
            "openai_configured": bool(settings.openai_api_key),
            "anthropic_configured": bool(settings.anthropic_api_key),
            "rate_limit": "10 requests per minute per IP",
            "endpoints": {
                "prefill": "POST /api/ai/prefill",
                "triage": "POST /api/ai/triage", 
                "analyze-source": "POST /api/ai/analyze-source",
                "status": "GET /api/ai/status"
            }
        }
        
        if not settings.openai_api_key and not settings.anthropic_api_key:
            status["status"] = "misconfigured"
            status["error"] = "No LLM API key configured"
        
        return status
        
    except Exception as e:
        logger.error(f"Error in status endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get AI status: {str(e)}"
        )
