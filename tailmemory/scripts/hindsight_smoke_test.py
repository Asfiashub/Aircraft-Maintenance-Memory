from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.data.loader import load_events
from backend.memory.hindsight_client import HindsightClient


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run one real Hindsight Cloud retain and recall operation."
    )
    parser.add_argument("--tail", default="VT-ABC")
    args = parser.parse_args()

    event = next(
        item for item in load_events() if item.tail_number == args.tail
    )
    client = HindsightClient()
    retained = client.retain_maintenance_event(event)
    recalled = client.recall_maintenance_events(
        args.tail, "Hydraulic pressure warning after takeoff"
    )
    print(
        {
            "retain_success": retained.get("success"),
            "recalled_count": len(recalled),
            "recalled_event_ids": [item.event_id for item in recalled],
        }
    )


if __name__ == "__main__":
    main()