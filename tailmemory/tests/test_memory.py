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
