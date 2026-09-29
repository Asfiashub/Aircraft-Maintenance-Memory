from datetime import date

import pytest
from pydantic import ValidationError

from app.models import DiagnosisResult, MaintenanceEvent


def test_maintenance_event_validates():
    event = MaintenanceEvent(
        event_id="VTABC-001",
        tail_number="VT-ABC",
        date=date(2025, 1, 1),
        ata_chapter="29",
        symptom="Hydraulic pressure warning",
        diagnostic_action="Pressure test",
        action_taken="Inspected system",
        component="Hydraulic system",
        outcome="No change",
        outcome_status="failed",
        source_type="SYNTHETIC",
        source_reference="test",
    )
    assert event.tail_number == "VT-ABC"


def test_diagnosis_requires_recommended_step():
    with pytest.raises(ValidationError):
        DiagnosisResult(
            tail_number="VT-ABC",
            fault_summary="summary",
            likely_fault_categories=["hydraulic"],
            recommended_next_steps=[],
            confidence="low",
            safety_note="Qualified review required.",
        )
