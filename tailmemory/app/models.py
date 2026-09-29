from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


OutcomeStatus = Literal["worked", "failed", "inconclusive", "not_verified"]


class MaintenanceEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    tail_number: str
    date: date
    ata_chapter: str
    symptom: str
    diagnostic_action: str
    action_taken: str
    component: str
    outcome: str
    outcome_status: OutcomeStatus
    source_type: str
    source_reference: str


class DiagnosisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tail_number: str
    fault_summary: str
    likely_fault_categories: list[str] = Field(min_length=1)
    historical_matches: list[str] = Field(default_factory=list)
    relevant_previous_actions: list[str] = Field(default_factory=list)
    failed_actions_to_avoid: list[str] = Field(default_factory=list)
    recommended_next_steps: list[str] = Field(min_length=1)
    confidence: Literal["low", "moderate", "high"]
    safety_note: str
    evidence_event_ids: list[str] = Field(default_factory=list)


class RecalledMemory(BaseModel):
    event_id: str | None = None
    tail_number: str | None = None
    date: str | None = None
    ata_chapter: str | None = None
    symptom: str
    diagnostic_action: str | None = None
    action_taken: str | None = None
    component: str | None = None
    outcome: str | None = None
    outcome_status: str | None = None
    source_type: str = "Hindsight Cloud"
    source_reference: str = "Hindsight recall"
    raw_content: str
