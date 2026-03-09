from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class RiskSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GapStatus(str, Enum):
    ALIGNED = "aligned"
    PARTIAL_GAP = "partial_gap"
    FULL_GAP = "full_gap"


class ControlEffectiveness(str, Enum):
    EFFECTIVE = "effective"
    PARTIALLY_EFFECTIVE = "partially_effective"
    INEFFECTIVE = "ineffective"


# ---------------------------------------------------------------------------
# Shared – AI Source References (clickable provenance)
# ---------------------------------------------------------------------------

class SourceReference(BaseModel):
    """Links an AI-generated item back to the source text that informed it."""
    excerpt: str = Field(..., description="Exact excerpt from the source text used as evidence")
    reasoning: str = Field(..., description="AI explanation of why this excerpt led to the conclusion")
    confidence: float = Field(default=0.0, ge=0, le=1, description="Confidence score 0-1")
    char_offset_start: Optional[int] = Field(default=None, description="Start character offset in source text")
    char_offset_end: Optional[int] = Field(default=None, description="End character offset in source text")


# ---------------------------------------------------------------------------
# AI Analysis – Request / Response
# ---------------------------------------------------------------------------

class AnalyzeSourceRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Raw text from interviews, SOPs, or process documents")
    language: str = Field(default="en", description="ISO-639-1 language code of the source text")
    context: Optional[str] = Field(default=None, description="Optional context about the process domain")


class ProcessStep(BaseModel):
    step_number: int
    title: str
    description: str
    responsible_role: Optional[str] = None
    estimated_duration: Optional[str] = None
    source_references: List[SourceReference] = Field(
        default_factory=list,
        description="Source excerpts and reasoning that led to this step being identified"
    )


class Risk(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    severity: RiskSeverity
    mitigating_controls: List[str] = Field(default_factory=list)
    source_references: List[SourceReference] = Field(
        default_factory=list,
        description="Source excerpts and reasoning for this risk identification"
    )


class Inefficiency(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    category: str  # e.g. "bottleneck", "redundancy", "manual_overhead"
    suggested_improvement: Optional[str] = None
    source_references: List[SourceReference] = Field(
        default_factory=list,
        description="Source excerpts and reasoning for this inefficiency"
    )


class ChangeImpact(BaseModel):
    """Key change impact to facilitate implementation by market."""
    area: str = Field(..., description="Area affected (e.g. 'Technology', 'People', 'Process')")
    description: str
    severity: RiskSeverity = RiskSeverity.MEDIUM
    affected_steps: List[int] = Field(default_factory=list, description="Step numbers impacted")
    source_references: List[SourceReference] = Field(default_factory=list)


class FutureCurrentStateEntry(BaseModel):
    """Side-by-side mapping of current vs. future/recommended state."""
    step_number: int
    current_state: str
    future_state: str
    gap_description: str
    priority: RiskSeverity = RiskSeverity.MEDIUM
    source_references: List[SourceReference] = Field(default_factory=list)


class AnalyzeSourceResponse(BaseModel):
    process_steps: List[ProcessStep]
    risks: List[Risk]
    inefficiencies: List[Inefficiency]
    change_impacts: List[ChangeImpact] = Field(default_factory=list)
    future_current_state_map: List[FutureCurrentStateEntry] = Field(default_factory=list)
    summary: str
    source_language: str
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


class CreateBaselineFromAnalysisRequest(BaseModel):
    """Convert AI analysis results into a Global Baseline Control."""
    analysis: AnalyzeSourceResponse = Field(..., description="The AI analysis output to convert")
    baseline_name: str = Field(..., min_length=1, description="Name for the new baseline")
    baseline_description: str = Field(default="", description="Optional description")
    version: str = Field(default="1.0", description="Baseline version")


# ---------------------------------------------------------------------------
# Global Baseline Control & Local Market Variation
# ---------------------------------------------------------------------------

class MultiLangText(BaseModel):
    """Text with multi-language support."""
    default: str = Field(..., description="Default (English) text")
    translations: Dict[str, str] = Field(
        default_factory=dict,
        description="ISO-639-1 code → translated text, e.g. {'fr': '...', 'de': '...'}"
    )

    def get(self, lang: str = "en") -> str:
        if lang == "en":
            return self.default
        return self.translations.get(lang, self.default)


class ControlStep(BaseModel):
    step_number: int
    title: MultiLangText
    description: MultiLangText
    responsible_role: Optional[str] = None
    is_mandatory: bool = True


class GlobalBaselineControl(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: MultiLangText
    description: MultiLangText
    process_steps: List[ControlStep] = Field(default_factory=list)
    risks: List[Risk] = Field(default_factory=list)
    version: str = "1.0"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class LocalOverride(BaseModel):
    step_number: int
    field: str  # "title", "description", "responsible_role"
    value: Any
    reason: Optional[str] = None


class LocalMarketVariation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    market_code: str = Field(..., description="ISO-3166-1 alpha-2 country code")
    market_name: str
    baseline_id: str = Field(..., description="ID of the parent GlobalBaselineControl")
    language: str = Field(default="en", description="Primary language for this market")
    overrides: List[LocalOverride] = Field(default_factory=list)
    additional_steps: List[ControlStep] = Field(default_factory=list)
    removed_step_numbers: List[int] = Field(
        default_factory=list,
        description="Step numbers from global baseline removed for this market"
    )
    additional_risks: List[Risk] = Field(default_factory=list)
    notes: Optional[MultiLangText] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Fit-Gap Engine
# ---------------------------------------------------------------------------

class StepComparison(BaseModel):
    step_number: int
    global_title: str
    local_title: Optional[str] = None
    status: GapStatus
    details: str
    ai_reasoning: Optional[str] = Field(
        default=None,
        description="AI-generated explanation of why this gap exists and its impact"
    )
    source_references: List[SourceReference] = Field(default_factory=list)


class FitGapRequest(BaseModel):
    baseline_id: str
    market_id: str


class FitGapResult(BaseModel):
    baseline_id: str
    market_id: str
    market_code: str
    overall_score: float = Field(..., ge=0, le=100, description="Fit percentage 0-100")
    step_comparisons: List[StepComparison] = Field(default_factory=list)
    missing_controls: List[str] = Field(default_factory=list)
    extra_controls: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    ai_summary: Optional[str] = Field(
        default=None,
        description="AI-generated narrative summary of the fit-gap analysis"
    )
    ai_sources: List[SourceReference] = Field(
        default_factory=list,
        description="Source references supporting the AI summary"
    )
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Predictive Risk / Monitoring
# ---------------------------------------------------------------------------

class PerformanceDataPoint(BaseModel):
    control_id: str
    metric_name: str
    value: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RiskPrediction(BaseModel):
    control_id: str
    control_name: str
    current_effectiveness: ControlEffectiveness
    failure_probability: float = Field(..., ge=0, le=1)
    trend: str  # "improving", "stable", "degrading"
    risk_factors: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    ai_reasoning: Optional[str] = Field(
        default=None,
        description="AI-generated explanation of prediction rationale"
    )
    source_references: List[SourceReference] = Field(default_factory=list)


class MonitoringReport(BaseModel):
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    predictions: List[RiskPrediction] = Field(default_factory=list)
    high_risk_count: int = 0
    overall_health: str = "healthy"  # "healthy", "at_risk", "critical"
    ai_summary: Optional[str] = Field(
        default=None,
        description="AI-generated narrative summary of the monitoring report"
    )
    ai_sources: List[SourceReference] = Field(
        default_factory=list,
        description="Source references supporting the AI summary"
    )
