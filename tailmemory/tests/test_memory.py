from app.config import Settings
from app.models import MaintenanceEvent
from backend.memory.hindsight_client import HindsightClient, HindsightConfigurationError


def test_missing_hindsight_configuration_is_explicit():
    settings = Settings(
        groq_api_key=None,
        hindsight_api_key=None,
        hindsight_base_url="https://api.hindsight.vectorize.io",
        hindsight_bank_id=None,
    )
    client = HindsightClient(settings)
    try:
        client.recall_maintenance_events("VT-ABC", "hydraulic warning")
    except HindsightConfigurationError as error:
        assert "HINDSIGHT_API_KEY" in str(error)
    else:
        raise AssertionError("Expected explicit configuration error")


def test_recall_parser_isolates_requested_tail():
    payload = {
        "results": [
            {
                "content": "Event ID: ABC-001. Tail number: VT-ABC. Date: 2025-01-01. "
                "ATA chapter: 29. Symptom: Hydraulic warning. Diagnostic action: Test. "
                "Action taken: Replaced pump. Component: Pump. Outcome: Failed. "
                "Outcome status: failed.",
                "metadata": {"tail_number": "VT-ABC"},
            },
            {
                "content": "Event ID: XYZ-001. Tail number: VT-XYZ. Date: 2025-01-01. "
                "ATA chapter: 24. Symptom: Generator caution.",
                "metadata": {"tail_number": "VT-XYZ"},
            },
        ]
    }
    memories = HindsightClient._parse_recall(payload, "VT-ABC")
    assert len(memories) == 1
    assert memories[0].tail_number == "VT-ABC"
    assert memories[0].outcome_status == "failed"


def test_recall_parser_reads_original_records_from_chunks():
    """Shape observed from the real Hindsight Cloud API: a synthesized observation
    under results, and the original retained records under chunks."""
    payload = {
        "results": [
            {
                "text": "Aircraft VT-ABC experienced recurring hydraulic pressure warnings; "
                "pump replacements failed but the return line fix worked.",
                "type": "observation",
                "metadata": {},
                "tags": ["tail:VT-ABC"],
            }
        ],
        "chunks": {
            "doc:VT-ABC:VTABC-P001_0": {
                "text": "Aircraft maintenance event. Event ID: VTABC-P001. Tail number: VT-ABC. "
                "Date: 2025-03-14. ATA chapter: 29. Symptom: Hydraulic pressure warning. "
                "Diagnostic action: Pressure test. Action taken: Replaced hydraulic pump. "
                "Component: Hydraulic pump. Outcome: Warning recurred after takeoff. "
                "Outcome status: failed. Source type: SYNTHETIC. Source reference: demo."
            },
            "doc:VT-XYZ:VTXYZ-P001_0": {
                "text": "Aircraft maintenance event. Event ID: VTXYZ-P001. Tail number: VT-XYZ. "
                "Symptom: Generator voltage fluctuation. Outcome status: worked."
            },
        },
    }
    memories = HindsightClient._parse_recall(payload, "VT-ABC")
    ids = [m.event_id for m in memories]
    assert ids == ["VTABC-P001", None]
    assert memories[0].outcome_status == "failed"
    assert memories[0].action_taken == "Replaced hydraulic pump"
    assert memories[0].source_type == "Hindsight chunk (original record)"
    assert memories[1].source_type == "Hindsight observation (synthesized)"
    assert all(m.tail_number == "VT-ABC" for m in memories)
