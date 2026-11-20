"""
Pydantic v2 schemas for CogniFlow Incident Triage & Impact Analysis.
"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class SeverityLevel(str, Enum):
    SEV1 = "SEV-1"  # Critical business outage / widespread customer impact
    SEV2 = "SEV-2"  # Major degradation / enterprise customer impact
    SEV3 = "SEV-3"  # Minor degradation / localized impact
    INFO = "INFO"   # Non-incident / routine telemetry

class TriageResult(BaseModel):
    incident_id: str
    service: str
    severity: SeverityLevel
    root_cause_summary: str = Field(min_length=10)
    sla_response_minutes: int
    recommended_action: str
    internal_engineering_brief: str
    external_customer_update: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    processing_time_ms: float

class BatchImpactReport(BaseModel):
    total_incidents_processed: int
    sev1_count: int
    sev2_count: int
    sev3_count: int
    info_count: int
    average_processing_time_ms: float
    manual_hours_baseline: float
    ai_hours_spent: float
    hours_saved: float
    annual_roi_projected_usd: float
    results: List[TriageResult]
