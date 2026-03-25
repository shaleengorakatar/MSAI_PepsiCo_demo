"""
Transcript Analysis Service for Context Stuffing Approach
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

from app.services.framework_loader import get_global_framework, is_framework_loaded


def load_mock_interviews() -> Dict[str, Any]:
    """Load mock interview transcripts from JSON file."""
    try:
        interviews_path = Path("mock_interviews.json")
        if interviews_path.exists():
            with open(interviews_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print("❌ Mock interviews file not found")
            return {}
    except Exception as e:
        print(f"❌ Error loading mock interviews: {e}")
        return {}


def analyze_transcript(transcript_id: str) -> Dict[str, Any]:
    """
    Analyze a transcript using context stuffing approach.
    
    Args:
        transcript_id: ID of the transcript to analyze (A, B, or C)
    
    Returns:
        Dictionary containing the mega-prompt and metadata
    """
    
    # Load the mock interviews
    interviews = load_mock_interviews()
    
    # Get the specific transcript
    transcript_data = interviews.get("transcripts", {}).get(transcript_id)
    
    if not transcript_data:
        return {
            "error": f"Transcript {transcript_id} not found",
            "available_transcripts": list(interviews.get("transcripts", {}).keys())
        }
    
    # Validate global framework is loaded
    if not is_framework_loaded():
        return {
            "error": "Global framework not loaded",
            "message": "Please ensure the application started correctly"
        }
    
    # Build the mega-prompt using context stuffing
    framework = get_global_framework()
    mega_prompt = build_mega_prompt(transcript_data, framework)
    
    return {
        "transcript_id": transcript_id,
        "region": transcript_data.get("region"),
        "interviewee": transcript_data.get("interviewee"),
        "position": transcript_data.get("position"),
        "mega_prompt": mega_prompt,
        "context_size": len(mega_prompt),
        "framework_loaded": is_framework_loaded(),
        "transcript_loaded": bool(transcript_data)
    }


def build_mega_prompt(transcript_data: Dict[str, Any], framework: Dict[str, Any]) -> str:
    """
    Build the mega-prompt by combining transcript and global framework.
    
    Args:
        transcript_data: The interview transcript data
        framework: The global framework data
    
    Returns:
        Complete mega-prompt string for LLM analysis
    """
    
    prompt_sections = []
    
    # 1. System Instructions
    prompt_sections.append("""
# CONTEXT STUFFING ANALYSIS INSTRUCTIONS

You are an expert internal auditor and process analyst specializing in financial services control environments. Your task is to analyze regional interview transcripts against a global framework to identify gaps, risks, and control deficiencies.

ANALYSIS APPROACH:
1. Compare regional process against global standard
2. Identify control gaps and deviations
3. Assess risk implications
4. Recommend remediation actions
5. Consider local regulatory requirements

OUTPUT FORMAT:
- Executive Summary
- Detailed Gap Analysis
- Risk Assessment
- Control Recommendations
- Compliance Status
""")
    
    # 2. Global Framework Context
    prompt_sections.append(f"""
# GLOBAL FRAMEWORK CONTEXT

Process Name: {framework.get('process_name')}
Version: {framework.get('version')}
Business Context: {framework.get('business_context')}

## Standard Process Steps:
""")
    
    for step in framework.get("process_map", {}).get("steps", []):
        prompt_sections.append(f"""
Step {step.get('step_id')}: {step.get('step_name')}
- Description: {step.get('description')}
- Responsible Role: {step.get('responsible_role')}
- System: {step.get('system')}
- Controls: {', '.join(step.get('controls', []))}
- SLA: {step.get('time_sla')}
""")
    
    # 3. Risk Register
    prompt_sections.append("""
## Global Risk Register:
""")
    
    for risk in framework.get("risk_register", {}).get("risks", []):
        prompt_sections.append(f"""
Risk {risk.get('risk_id')}: {risk.get('risk_name')}
- Description: {risk.get('description')}
- Impact: {risk.get('impact')}, Likelihood: {risk.get('likelihood')}
- Risk Score: {risk.get('risk_score')}
- Potential Loss: {risk.get('potential_loss')}
""")
    
    # 4. Mitigating Controls
    prompt_sections.append("""
## Mitigating Controls:

### Manual Controls:
""")
    
    for control in framework.get("mitigating_controls", {}).get("manual_controls", []):
        prompt_sections.append(f"""
- {control.get('control_id')}: {control.get('control_name')}
  {control.get('description')}
  Effectiveness: {control.get('effectiveness')}
""")
    
    prompt_sections.append("""
### Automated Controls:
""")
    
    for control in framework.get("mitigating_controls", {}).get("automated_controls", []):
        prompt_sections.append(f"""
- {control.get('control_id')}: {control.get('control_name')}
  {control.get('description')}
  Effectiveness: {control.get('effectiveness')}
""")
    
    prompt_sections.append("""
### IT General Controls:
""")
    
    for control in framework.get("mitigating_controls", {}).get("itgc_controls", []):
        prompt_sections.append(f"""
- {control.get('control_id')}: {control.get('control_name')}
  {control.get('description')}
  Effectiveness: {control.get('effectiveness')}
""")
    
    # 5. Compliance Requirements
    compliance = framework.get("compliance_requirements", {})
    prompt_sections.append(f"""
## Compliance Requirements:
- SOX 404: {compliance.get('sox_404', 'N/A')}
- PCI DSS: {compliance.get('pci_dss', 'N/A')}
- GDPR: {compliance.get('gdpr', 'N/A')}
- CCPA: {compliance.get('ccpa', 'N/A')}
- Local Regulations: {', '.join(compliance.get('local_regulations', []))}
""")
    
    # 6. Interview Transcript
    prompt_sections.append(f"""
# REGIONAL INTERVIEW TRANSCRIPT

Region: {transcript_data.get('region')}
Interviewee: {transcript_data.get('position')} - {transcript_data.get('interviewee')}
Date: {transcript_data.get('date')}
Language: {transcript_data.get('language')}

## Transcript Content:
{transcript_data.get('content')}
""")
    
    # 7. Analysis Instructions
    prompt_sections.append("""
# ANALYSIS TASKS

Please provide a comprehensive analysis covering:

1. **PROCESS COMPLIANCE ASSESSMENT**
   - How closely does the regional process follow the global framework?
   - Which steps are being followed, modified, or skipped?
   - Timeline comparisons (SLAs vs actual)

2. **CONTROL EFFECTIVENESS EVALUATION**
   - Are global controls implemented correctly?
   - Are there compensating controls for gaps?
   - Control effectiveness rating (High/Medium/Low)

3. **RISK IDENTIFICATION**
   - New risks introduced by local variations
   - Risk level assessment (Critical/High/Medium/Low)
   - Potential financial and operational impact

4. **GAP ANALYSIS**
   - Specific gaps between global and local processes
   - Root causes of deviations
   - Business justification for variations

5. **REGULATORY COMPLIANCE**
   - Local regulatory requirements impact
   - Conflicts between global and local requirements
   - Compliance risk assessment

6. **RECOMMENDATIONS**
   - Immediate actions required
   - Long-term improvement recommendations
   - Control enhancement suggestions
   - Monitoring and reporting improvements

7. **IMPLEMENTATION PLAN**
   - Priority ranking of recommendations
   - Resource requirements
   - Timeline for remediation
   - Success metrics

Please structure your response clearly with headings and bullet points. Be specific and actionable in your recommendations.
""")
    
    # Combine all sections
    return "\n".join(prompt_sections)


def get_available_transcripts() -> Dict[str, Any]:
    """Get list of available transcripts with metadata."""
    interviews = load_mock_interviews()
    transcripts = interviews.get("transcripts", {})
    
    return {
        "total_transcripts": len(transcripts),
        "available_transcripts": [
            {
                "id": transcript_id,
                "region": data.get("region"),
                "interviewee": data.get("interviewee"),
                "position": data.get("position"),
                "date": data.get("date")
            }
            for transcript_id, data in transcripts.items()
        ]
    }
