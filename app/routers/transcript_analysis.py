"""
Transcript Analysis Router - Context Stuffing Approach
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services.transcript_analyzer import analyze_transcript, get_available_transcripts

router = APIRouter(prefix="/transcript-analysis", tags=["Transcript Analysis"])


@router.get("/transcripts")
async def get_transcripts():
    """Get list of available interview transcripts."""
    return get_available_transcripts()


@router.get("/analyze/{transcript_id}")
async def analyze_transcript_endpoint(transcript_id: str):
    """
    Analyze a specific transcript using context stuffing.
    
    Args:
        transcript_id: ID of the transcript to analyze (A, B, or C)
    
    Returns:
        Analysis result with mega-prompt and metadata
    """
    result = analyze_transcript(transcript_id)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.post("/analyze/{transcript_id}")
async def analyze_and_send_to_llm(transcript_id: str):
    """
    Analyze transcript and prepare for LLM processing.
    This endpoint would typically send the mega-prompt to an LLM service.
    
    For now, it returns the prepared mega-prompt ready for LLM input.
    """
    result = analyze_transcript(transcript_id)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    # In a real implementation, you would send this to your LLM service here
    # For now, return the prepared prompt
    
    return {
        "status": "ready_for_llm",
        "transcript_id": transcript_id,
        "context_size": result["context_size"],
        "mega_prompt": result["mega_prompt"],
        "metadata": {
            "region": result["region"],
            "interviewee": result["interviewee"],
            "position": result["position"]
        },
        "note": "Send this mega_prompt to your LLM service for analysis"
    }
