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
# Prompt for AI-powered form prefill
# ---------------------------------------------------------------------------
PREFILL_SYSTEM_PROMPT = """You are a GRC (Governance, Risk & Compliance) expert assistant. 
Extract structured form fields from an analysis result. For baselines: provide a concise name, 
description, and version. For variations: focus on what makes this specific market different 
from a global standard — identify additional steps, market-specific risks, and suggested 
overrides to baseline steps. Be specific and actionable using the actual process details 
from the analysis.

Return JSON based on the mode:

If mode is "baseline":
{
  "baseline_name": "string - concise professional name",
  "baseline_description": "string - 1-2 sentence summary",
  "version": "1.0"
}

If mode is "variation":
{
  "notes": "string - summary of market-specific deviations",
  "additional_steps": [
    {
      "title": "string",
      "description": "string", 
      "responsible_role": "string",
      "is_mandatory": boolean
    }
  ],
  "additional_risks": [
    {
      "description": "string",
      "severity": "low|medium|high|critical",
      "mitigating_controls": "string"
    }
  ],
  "suggested_overrides": [
    {
      "step_keyword": "string",
      "field": "title|description|responsible_role",
      "value": "string",
      "reason": "string"
    }
  ]
}

Rules:
- Use actual process details from the analysis
- Be specific and actionable
- For variations, focus on market-specific differences
- Return ONLY valid JSON.
"""

# ---------------------------------------------------------------------------
# Prompt for AI-powered security triage
# ---------------------------------------------------------------------------
TRIAGE_SYSTEM_PROMPT = """You are a cybersecurity analyst specializing in GRC threat 
assessment. Analyze the provided anomaly data and produce a structured triage report. 
Classify the threat, assess risk, identify indicators of compromise, and recommend 
specific remediation actions. Consider regulatory implications (SOX, GDPR, ISO 27001).

Return JSON:
{
  "classification": "string - threat category",
  "confidence": number (0-1),
  "risk_score": number (0-100),
  "summary": "string - brief analysis summary",
  "recommended_actions": ["string"],
  "affected_systems": ["string"],
  "ioc_indicators": ["string - indicators of compromise"],
  "regulatory_impact": "string - potential compliance implications"
}

Rules:
- Assess risk based on severity and potential impact
- Identify specific indicators of compromise
- Recommend actionable remediation steps
- Consider regulatory compliance implications
- Return ONLY valid JSON.
"""

# ---------------------------------------------------------------------------
# Enhanced prompt for source analysis
# ---------------------------------------------------------------------------
ENHANCED_ANALYSIS_PROMPT = """You are a GRC expert analyzing interview transcripts and 
documents for process mapping. Extract structured process steps, identify risks and controls, 
flag inefficiencies, and note compliance observations. Strip noise like timestamps and 
[inaudible] markers. Reconstruct processes described out of sequence. Identify risks from 
conversational cues like hedging ('I think') or complaints ('we struggle with'). Flag 
inconsistencies when multiple perspectives describe the same process differently.

Return JSON:
{
  "process_steps": [
    {
      "step_number": number,
      "title": "string",
      "description": "string",
      "responsible_role": "string",
      "is_mandatory": boolean
    }
  ],
  "risks": [
    {
      "description": "string",
      "severity": "low|medium|high|critical",
      "mitigating_controls": ["string"],
      "related_step_numbers": [number]
    }
  ],
  "controls": [
    {
      "name": "string",
      "description": "string",
      "control_type": "preventive|detective|corrective",
      "frequency": "string",
      "risk_ids": ["string"]
    }
  ],
  "inefficiencies": ["string - process gaps or improvement opportunities"],
  "compliance_observations": ["string - regulatory alignment notes"],
  "metadata": {
    "interviewee_role": "string",
    "department": "string", 
    "region": "string",
    "confidence_score": number
  }
}

Rules:
- Standardize step names into clear, action-oriented titles
- Identify ALL risks, even implicit ones
- Flag bottlenecks, redundancies, and manual overhead
- Capture speaker/role information from transcripts
- Reconstruct logical process sequence
- Return ONLY valid JSON.
"""

# ---------------------------------------------------------------------------
# Prompt for /analyze-source (existing)
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a Control Design Assessment expert. Analyze the provided text 
and extract the following in JSON.

The source text may be:
- **Interview transcripts** (one or more speakers, Q&A format, conversational language)
- **Document-based transcripts** (pasted from Word, PDF, or text files — may include 
  headers, timestamps, page numbers, formatting artifacts, or meeting minutes)
- SOPs, process documents, or policy manuals
- A mix of the above

When processing INTERVIEW TRANSCRIPTS (live or from documents), apply these rules:
- Recognize speaker labels in any format: "Interviewer:", "John:", "Q:", "A:", 
  "Speaker 1:", "[John Smith]:", timestamps like "[00:12:34]", or document headings 
  like "Interview with John Smith, Operations Manager".
- Ignore document artifacts such as page numbers, headers/footers, timestamps, 
  "[inaudible]", "[crosstalk]", and formatting noise — focus on the substance.
- Conversational language often contains hedging ("I think", "usually", "sometimes", 
  "it depends"), complaints ("the problem is", "we struggle with"), and workarounds 
  ("what we actually do is"). Treat these as strong signals for risks and inefficiencies.
- Interviewees often describe processes out of order. Reconstruct the logical sequence of 
  steps from the full transcript, not just the order mentioned.
- Look for implicit risks hidden in casual remarks (e.g. "we just copy-paste it" → 
  manual error risk, data integrity risk).
- When multiple interviewees describe the same process differently, flag this as a 
  process inconsistency / standardization gap.
- Capture the speaker/role in responsible_role when identifiable from the transcript.
- For multi-interview documents (e.g. several interviews in one file), treat each 
  interview as a separate source but unify the extracted process into one coherent flow.

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
# Prompt for analysis-to-variation (compare local analysis vs global baseline)
# ---------------------------------------------------------------------------
VARIATION_COMPARISON_PROMPT = """You are a Control Design Assessment expert. You are given:
1. A Global Baseline Control (the corporate standard) with its process steps and risks.
2. An AI analysis of a local market's actual processes (from interviews/documents).

Compare the local analysis against the global baseline and determine:
- Which baseline steps are adopted as-is locally
- Which baseline steps are modified locally (and how)
- Which baseline steps are missing/removed locally
- What additional steps the local market has beyond the baseline
- What additional risks exist in the local market

Return JSON:
{
  "overrides": [
    {
      "step_number": 1,
      "field": "description",
      "value": "how the local market actually does this step",
      "reason": "why it differs from the global standard"
    }
  ],
  "removed_step_numbers": [3, 5],
  "removed_reasons": {"3": "reason step 3 doesn't apply", "5": "reason step 5 doesn't apply"},
  "additional_steps": [
    {
      "step_number": 100,
      "title": "Extra local step title",
      "description": "What this step does",
      "responsible_role": "role or null",
      "is_mandatory": true
    }
  ],
  "additional_risks": [
    {
      "description": "Local risk not in the global baseline",
      "severity": "low" | "medium" | "high" | "critical",
      "mitigating_controls": ["control 1"]
    }
  ],
  "notes": "Summary of key differences between local market and global baseline"
}

Rules:
- Match local analysis steps to baseline steps by semantic similarity, not just titles.
- If a local step partially matches a baseline step, create an override.
- If a baseline step has no corresponding local step, add it to removed_step_numbers.
- If a local step has no corresponding baseline step, add it to additional_steps.
- Be thorough — capture every deviation.
- Return ONLY valid JSON.
"""

# ---------------------------------------------------------------------------
# Prompt for implementation plan generation
# ---------------------------------------------------------------------------
IMPLEMENTATION_PLAN_PROMPT = """You are a Control Design Assessment expert specializing in 
market-specific implementation strategies. Given:
1. A Global Baseline Control (the standard)
2. A Local Market Variation (current state)
3. A Fit-Gap analysis result (gaps identified)

Generate a prioritized implementation plan to close the gaps. The plan should be 
practical and tailored to the local market's operational realities.

Return JSON:
{
  "executive_summary": "2-3 sentence overview of the implementation strategy",
  "steps": [
    {
      "priority": 1,
      "title": "Clear action title",
      "description": "Detailed description of what needs to be done",
      "category": "close_gap" | "adopt_control" | "alternative_mitigation" | "change_management" | "training",
      "affected_steps": [1, 2],
      "effort": "low" | "medium" | "high",
      "timeline": "e.g. 2 weeks, 1 month",
      "dependencies": ["step title that must be done first"]
    }
  ],
  "alternative_mitigations": [
    {
      "baseline_step_number": 3,
      "baseline_step_title": "step that can't be applied",
      "reason_cannot_apply": "why the standard control doesn't work here",
      "alternative_control": "what to do instead",
      "residual_risk": "remaining risk after the alternative",
      "effectiveness": "low" | "medium" | "high"
    }
  ],
  "estimated_total_effort": "e.g. 3-6 months"
}

Rules:
- Prioritize closing critical and high-severity gaps first.
- For removed baseline steps, ALWAYS provide an alternative mitigation approach.
- Be specific to the market — don't give generic advice.
- Group related actions where possible.
- Include change management and training steps.
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


async def compare_analysis_to_baseline(
    analysis_data: Dict[str, Any],
    baseline_data: Dict[str, Any],
    market_code: str,
) -> Dict[str, Any]:
    """Use LLM to compare a local market's AI analysis against a global baseline."""
    logger.info("Comparing local analysis to baseline for market: %s", market_code)

    user_content = (
        f"Market: {market_code}\n\n"
        f"--- GLOBAL BASELINE ---\n{json.dumps(baseline_data, default=str)}\n\n"
        f"--- LOCAL MARKET ANALYSIS ---\n{json.dumps(analysis_data, default=str)}"
    )

    return await _call_llm(VARIATION_COMPARISON_PROMPT, user_content)


async def generate_implementation_plan(
    baseline_data: Dict[str, Any],
    variation_data: Dict[str, Any],
    fit_gap_data: Dict[str, Any],
    market_code: str,
) -> Dict[str, Any]:
    """Use LLM to generate a market-specific implementation plan from fit-gap results."""
    logger.info("Generating implementation plan for market: %s", market_code)

    user_content = (
        f"Market: {market_code}\n\n"
        f"--- GLOBAL BASELINE ---\n{json.dumps(baseline_data, default=str)}\n\n"
        f"--- LOCAL MARKET VARIATION ---\n{json.dumps(variation_data, default=str)}\n\n"
        f"--- FIT-GAP ANALYSIS ---\n{json.dumps(fit_gap_data, default=str)}"
    )

    return await _call_llm(IMPLEMENTATION_PLAN_PROMPT, user_content)


# ---------------------------------------------------------------------------
# New AI-powered functions
# ---------------------------------------------------------------------------

async def generate_form_prefill(mode: str, analysis: Dict[str, Any], context: str = None) -> Dict[str, Any]:
    """Generate pre-filled form fields for baseline or variation creation."""
    logger.info("Generating form prefill for mode: %s", mode)
    
    user_content = f"Mode: {mode}\n"
    if context:
        user_content += f"Context: {context}\n"
    user_content += f"\n--- ANALYSIS DATA ---\n{json.dumps(analysis, default=str)}"
    
    return await _call_llm(PREFILL_SYSTEM_PROMPT, user_content)


async def perform_security_triage(anomaly: Dict[str, Any], context: str = None) -> Dict[str, Any]:
    """Perform AI-powered security triage analysis on detected anomaly."""
    logger.info("Performing security triage on anomaly: %s", anomaly.get('type', 'unknown'))
    
    user_content = f"Anomaly: {json.dumps(anomaly, default=str)}\n"
    if context:
        user_content += f"Context: {context}\n"
    
    return await _call_llm(TRIAGE_SYSTEM_PROMPT, user_content)


async def analyze_source_enhanced(text: str, language: str = "en", context: str = None) -> Dict[str, Any]:
    """Enhanced source analysis using the new structured prompt."""
    logger.info("Performing enhanced source analysis in language: %s", language)
    
    user_content = f"Source language: {language}\n"
    if context:
        user_content += f"Context: {context}\n"
    user_content += f"\n--- SOURCE TEXT ---\n{text}"
    
    return await _call_llm(ENHANCED_ANALYSIS_PROMPT, user_content)


# ---------------------------------------------------------------------------
# Prompt for AI baseline generation
# ---------------------------------------------------------------------------
BASELINE_GENERATION_PROMPT = """You are a senior GRC (Governance, Risk & Compliance) architect specializing in internal controls frameworks for Fortune 500 companies. Given a baseline name and optional description, generate a complete Global Baseline with:

1. A refined professional description (1-2 sentences)
2. 5-8 sequential process steps, each with: title, description, responsible_role, is_mandatory (boolean)
3. 3-5 risks associated with these steps, each with: description, severity (low/medium/high/critical), likelihood (low/medium/high), related_step_numbers (array of step indices 1-based)
4. 3-5 controls to mitigate the risks, each with: title, description, type (preventive/detective/corrective), frequency (daily/weekly/monthly/quarterly/annually), related_risk_numbers (array of risk indices 1-based)

Rules:
- Steps should follow a logical process flow (initiation → execution → review → closure)
- Each risk must reference at least one step
- Each control must reference at least one risk
- Use industry-standard GRC terminology
- Be specific and actionable, not generic

Return the structured JSON directly as the response body."""


async def generate_complete_baseline(name: str, description: str = None, industry: str = "FMCG") -> Dict[str, Any]:
    """Generate a complete GRC baseline using AI with structured output."""
    logger.info(f"Generating complete baseline for: {name}")
    
    user_content = f"Baseline Name: {name}\n"
    user_content += f"Industry: {industry}\n"
    if description:
        user_content += f"Description: {description}\n"
    
    # Use OpenAI with function calling for structured output
    try:
        from app.config import settings
        
        if settings.llm_provider.lower() == "anthropic":
            # For Anthropic, use regular JSON mode
            return await _call_llm(BASELINE_GENERATION_PROMPT, user_content)
        else:
            # For OpenAI, use function calling
            return await _call_openai_function_calling(name, description, industry)
            
    except Exception as e:
        logger.error(f"Error generating baseline: {e}")
        raise


async def _call_openai_function_calling(name: str, description: str = None, industry: str = "FMCG") -> Dict[str, Any]:
    """Use OpenAI function calling for structured baseline generation."""
    from openai import AsyncOpenAI
    from app.config import settings
    
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    # Define the function schema
    functions = [
        {
            "name": "generate_baseline",
            "description": "Generate a complete GRC baseline with process steps, risks, and controls",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "process_steps": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "responsible_role": {"type": "string"},
                                "is_mandatory": {"type": "boolean"}
                            },
                            "required": ["title", "description", "responsible_role", "is_mandatory"]
                        }
                    },
                    "risks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string"},
                                "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                                "likelihood": {"type": "string", "enum": ["low", "medium", "high"]},
                                "related_step_numbers": {"type": "array", "items": {"type": "integer"}}
                            },
                            "required": ["description", "severity", "likelihood", "related_step_numbers"]
                        }
                    },
                    "controls": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "type": {"type": "string", "enum": ["preventive", "detective", "corrective"]},
                                "frequency": {"type": "string", "enum": ["daily", "weekly", "monthly", "quarterly", "annually"]},
                                "related_risk_numbers": {"type": "array", "items": {"type": "integer"}}
                            },
                            "required": ["title", "description", "type", "frequency", "related_risk_numbers"]
                        }
                    }
                },
                "required": ["description", "process_steps", "risks", "controls"]
            }
        }
    ]
    
    user_content = f"Generate a complete GRC baseline for: {name}\n"
    user_content += f"Industry: {industry}\n"
    if description:
        user_content += f"Context: {description}\n"
    
    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": BASELINE_GENERATION_PROMPT},
            {"role": "user", "content": user_content}
        ],
        functions=functions,
        function_call={"name": "generate_baseline"},
        temperature=0.2
    )
    
    # Extract the function call result
    message = response.choices[0].message
    if message.function_call:
        function_args = json.loads(message.function_call.arguments)
        return function_args
    else:
        raise ValueError("No function call in response")
