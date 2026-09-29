"""Retain the 4 planted VT-ABC events, then print the RAW Hindsight recall response.

Purpose: see exactly what Hindsight returns so the recall parser can be verified.
Run from the tailmemory folder:  python scripts/hindsight_debug.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.data.loader import events_for_tail, load_events
from backend.memory.hindsight_client import (
    HindsightAPIError,
    HindsightClient,
    HindsightConfigurationError,
)

TAIL = "VT-ABC"
FAULT = "Hydraulic pressure warning after takeoff"


def main() -> None:
    client = HindsightClient()
    events = [
        e for e in events_for_tail(load_events(), TAIL)
        if e.event_id.startswith("VTABC-P")
    ]

    try:
        print(f"Retaining {len(events)} events to the bank...")
        for e in events:
            result = client.retain_maintenance_event(e)
            print(f"  {e.event_id} -> success={result.get('success')}")

        raw = client._post(
            "/memories/recall",
            {
                "query": (
                    f"Aircraft-specific maintenance history for tail {TAIL}. "
                    f"Current fault: {FAULT}"
                ),
                "types": ["experience", "observation"],
                "budget": "mid",
                "max_tokens": 3000,
                "tags": [f"tail:{TAIL}"],
                "tags_match": "exact",
                "include": {"chunks": {}},
            },
        )
    except (HindsightConfigurationError, HindsightAPIError) as error:
        print(f"\nFAILED: {error}")
        return

    print("\n=== RAW RECALL (first 3500 chars) ===")
    print(json.dumps(raw, indent=2)[:3500])

    print("\n=== WHAT OUR PARSER EXTRACTED ===")
    parsed = HindsightClient._parse_recall(raw, TAIL)
    print(f"{len(parsed)} memories parsed")
    for m in parsed:
        print(f"  event_id={m.event_id} | status={m.outcome_status} | {m.symptom[:80]}")


if __name__ == "__main__":
    main()
