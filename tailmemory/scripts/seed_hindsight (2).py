"""Seed every TailMemory maintenance event into Hindsight Cloud, then verify recall.

Safe to re-run: each event has a stable document_id, so Hindsight updates the
existing record instead of creating a duplicate.

Run from the tailmemory folder:  python scripts/seed_hindsight.py
"""
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests

from app.data.loader import load_events
from backend.memory.hindsight_client import (
    HindsightAPIError,
    HindsightClient,
    HindsightConfigurationError,
)

MAX_ATTEMPTS = 3
SETTLE_SECONDS = 5


def retain_with_retry(client: HindsightClient, event) -> str | None:
    """Retain one event. Returns None on success, or an error message."""
    last_error = "unknown error"
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            result = client.retain_maintenance_event(event)
            if result.get("success") is False:
                raise HindsightAPIError(f"success=False: {result}")
            return None
        except (HindsightAPIError, requests.RequestException) as error:
            last_error = str(error)
            if attempt < MAX_ATTEMPTS:
                time.sleep(2 * attempt)
    return last_error


def seed(client: HindsightClient, events: list) -> list[tuple[str, str]]:
    failures: list[tuple[str, str]] = []
    total = len(events)
    print(f"Seeding {total} events into the Hindsight bank...")
    for index, event in enumerate(events, start=1):
        error = retain_with_retry(client, event)
        if error:
            failures.append((event.event_id, error))
            print(f"  [{index}/{total}] {event.event_id} FAILED: {error[:120]}")
        elif index % 10 == 0 or index == total:
            print(f"  [{index}/{total}] retained (last: {event.event_id})")
    return failures


def raw_recall(client: HindsightClient, tail: str, fault: str) -> dict:
    """Same request the app makes, but returns the unparsed response."""
    return client._post(
        "/memories/recall",
        {
            "query": (
                f"Aircraft-specific maintenance history for tail {tail}. "
                f"Current fault: {fault}"
            ),
            "types": ["experience", "observation"],
            "budget": "mid",
            "max_tokens": 5000,
            "tags": [f"tail:{tail}"],
            "tags_match": "exact",
            "include": {"chunks": {}},
        },
    )


def foreign_tails_in_chunks(raw: dict, tail: str) -> list[str]:
    """Tail numbers found in returned chunks that are NOT the requested tail.

    The app's parser silently drops other tails, so leaks must be checked on
    the raw response to mean anything.
    """
    chunks = raw.get("chunks") or {}
    items = chunks.values() if isinstance(chunks, dict) else chunks
    found = []
    for item in items:
        text = str(item.get("text", "")) if isinstance(item, dict) else ""
        match = re.search(r"Tail number:\s*([A-Z0-9-]+)", text)
        if match and match.group(1) != tail:
            found.append(match.group(1))
    return found


def verify(client: HindsightClient, events: list) -> bool:
    """For each tail, check recall returns every failed fix and nothing foreign."""
    print(f"\nWaiting {SETTLE_SECONDS}s for Hindsight to settle, then verifying recall...")
    time.sleep(SETTLE_SECONDS)

    by_tail: dict[str, list] = {}
    for event in events:
        by_tail.setdefault(event.tail_number, []).append(event)

    all_ok = True
    print("\n=== RECALL CHECK (per tail) ===")
    for tail, tail_events in sorted(by_tail.items()):
        expected_failed = {
            e.event_id
            for e in tail_events
            if str(e.outcome_status or "").lower() == "failed"
        }
        fault = next(
            (e.symptom for e in tail_events if e.event_id in expected_failed),
            "Routine inspection finding",
        )
        raw = raw_recall(client, tail, fault)
        memories = HindsightClient._parse_recall(raw, tail)
        recalled_failed = {
            m.event_id
            for m in memories
            if m.event_id and str(m.outcome_status or "").lower() == "failed"
        }
        foreign = foreign_tails_in_chunks(raw, tail)
        missing = sorted(expected_failed - recalled_failed)

        ok = not missing and not foreign
        all_ok = all_ok and ok
        status = "OK  " if ok else "FAIL"
        print(
            f"  {status} {tail}: expected {len(expected_failed)} failed fix(es), "
            f"recalled {len(recalled_failed & expected_failed)}, "
            f"total memories returned {len(memories)}"
        )
        if missing:
            print(f"        missing failed fixes: {', '.join(missing)}")
        if foreign:
            print(f"        WRONG-TAIL memories leaked: {len(foreign)}")
    return all_ok


def main() -> int:
    events = load_events()
    if not events:
        print("No events found. Check the data loader before seeding.")
        return 1

    client = HindsightClient()
    try:
        failures = seed(client, events)
    except HindsightConfigurationError as error:
        print(f"\nNOT CONFIGURED: {error}")
        return 1

    if failures:
        print(f"\n{len(failures)} event(s) failed to retain:")
        for event_id, message in failures:
            print(f"  {event_id}: {message[:200]}")
        print("Re-run this script; already-retained events are safe to repeat.")
        return 1

    print("\nAll events retained.")
    try:
        ok = verify(client, events)
    except (HindsightAPIError, HindsightConfigurationError, requests.RequestException) as error:
        print(f"\nVerification could not complete: {error}")
        return 1

    if ok:
        print("\nDONE: every planted failed fix is recallable and tails are isolated.")
        return 0
    print("\nSeeded, but recall check found problems (see FAIL lines above).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
