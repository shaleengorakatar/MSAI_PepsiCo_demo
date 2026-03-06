"""
LLM integration service – supports OpenAI and Anthropic.
Parses source text into structured process steps, risks, and inefficiencies.
Each AI-generated item includes source_references for provenance/clickability.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt for /analyze-source
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a Control Design Assessment expert. Analyze the provided text 
(which may come from interviews, SOPs, or process documents) and extract the following in JSON.

CRITICAL: For EVERY item you extract (each process step, risk, inefficiency, change impact, 
and future/current state entry), you MUST include a "source_references" array. Each reference 
contains the exact excerpt from the source text you used plus your reasoning. This allows 
users to click on the AI output and see exactly what evidence backed it.

{
  "process_steps": [
    {
      "step_number": 1,
      "title": "...",
      "description": "...",
      "responsible_role": "..." or null,
      "estimated_duration": "..." or null,
      "source_references": [
        {
          "excerpt": "exact quote from the source text",
          "reasoning": "why this excerpt indicates this process step",
          "confidence": 0.95
        }
      ]
    }
  ],
  "risks": [
    {
      "description": "...",
      "severity": "low" | "medium" | "high" | "critical",
      "mitigating_controls": ["..."],
      "source_references": [
        {
          "excerpt": "exact quote from the source text",
          "reasoning": "why this excerpt indicates this risk",
          "confidence": 0.9
        }
      ]
    }
  ],
  "inefficiencies": [
    {
      "description": "...",
      "category": "bottleneck" | "redundancy" | "manual_overhead" | "delay" | "communication_gap",
      "suggested_improvement": "..." or null,
      "source_references": [
        {
          "excerpt": "exact quote from the source text",
          "reasoning": "why this excerpt indicates this inefficiency",
          "confidence": 0.85
        }
      ]
    }
  ],
  "change_impacts": [
    {
      "area": "Technology" | "People" | "Process" | "Policy" | "Regulatory",
      "description": "...",
      "severity": "low" | "medium" | "high" | "critical",
      "affected_steps": [1, 2],
      "source_references": [
        {
          "excerpt": "exact quote from the source text",
          "reasoning": "why this change impact was identified",
          "confidence": 0.8
        }
      ]
    }
  ],
  "future_current_state_map": [
    {
      "step_number": 1,
      "current_state": "description of current state",
      "future_state": "description of recommended future state",
      "gap_description": "what needs to change",
      "priority": "low" | "medium" | "high" | "critical",
      "source_references": [
        {
          "excerpt": "exact quote from the source text",
          "reasoning": "why this current/future state mapping was identified",
          "confidence": 0.85
        }
      ]
    }
  ],
  "summary": "A concise 2-3 sentence summary of the process."
}

Rules:
- Standardize step names into clear, action-oriented titles.
- Identify ALL risks, even implicit ones, and suggest mitigating controls.
- Flag bottlenecks, redundancies, and manual overhead as inefficiencies.
- For change_impacts, identify technology, people, process, and policy changes needed.
- For future_current_state_map, produce a side-by-side current vs. future state for each step.
- source_references excerpts MUST be exact substrings from the source text.
- Return ONLY valid JSON, no markdown fences or extra text.
"""

# ---------------------------------------------------------------------------
# Prompt for AI summaries (fit-gap, monitoring)
# ---------------------------------------------------------------------------
SUMMARY_SYSTEM_PROMPT = """You are a Control Design Assessment expert. Given structured 
analysis data, produce a concise AI summary with source references.

Return JSON:
{
  "ai_summary": "A clear 3-5 sentence narrative summary of the analysis findings, key risks, and recommended actions.",
  "ai_sources": [
    {
      "excerpt": "specific data point or finding from the input that supports this summary",
      "reasoning": "why this data point is significant and how it influenced the summary",
      "confidence": 0.9
    }
  ]
}

Rules:
- The summary should be actionable and highlight the most critical findings.
- Each ai_sources entry should reference a specific data point from the input.
- Return ONLY valid JSON.
"""


# ---------------------------------------------------------------------------
# LLM call helpers
# ---------------------------------------------------------------------------

async def _call_openai(system: str, user_content: str) -> Dict[str, Any]:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content
    return json.loads(raw)


async def _call_anthropic(system: str, user_content: str) -> Dict[str, Any]:
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    response = await client.messages.create(
        model=settings.anthropic_model,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user_content}],
        temperature=0.2,
    )
    raw = response.content[0].text
    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        if raw.endswith("```"):
            raw = raw[:-3]
    return json.loads(raw)


async def _call_llm(system: str, user_content: str) -> Dict[str, Any]:
    """Route to the configured LLM provider."""
    provider = settings.llm_provider.lower()
    if provider == "anthropic":
        return await _call_anthropic(system, user_content)
    return await _call_openai(system, user_content)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def analyze_source_text(text: str, context: str | None = None, language: str = "en") -> Dict[str, Any]:
    """Analyze source text and extract structured process data with source references."""
    logger.info("Using LLM provider: %s", settings.llm_provider)

    user_content = f"Source language: {language}\n"
    if context:
        user_content += f"Context: {context}\n"
    user_content += f"\n--- SOURCE TEXT ---\n{text}"

    return await _call_llm(SYSTEM_PROMPT, user_content)


async def generate_ai_summary(analysis_data: Dict[str, Any], context_label: str = "analysis") -> Dict[str, Any]:
    """Generate an AI narrative summary with source references for any structured analysis data."""
    logger.info("Generating AI summary for: %s", context_label)

    user_content = f"Context: {context_label}\n\n--- ANALYSIS DATA ---\n{json.dumps(analysis_data, default=str)}"

    try:
        result = await _call_llm(SUMMARY_SYSTEM_PROMPT, user_content)
        return {
            "ai_summary": result.get("ai_summary", ""),
            "ai_sources": result.get("ai_sources", []),
        }
    except Exception as e:
        logger.warning("AI summary generation failed: %s", e)
        return {"ai_summary": None, "ai_sources": []}
