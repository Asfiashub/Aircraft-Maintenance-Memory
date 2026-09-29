from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from app.config import DATA_DIR, SYNTHETIC_DIR
from app.models import MaintenanceEvent


def load_events(path: Path | None = None) -> list[MaintenanceEvent]:
    csv_path = path or SYNTHETIC_DIR / "maintenance_events.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Synthetic event data is missing: {csv_path}")
    frame = pd.read_csv(csv_path)
    events = []
    for _, row in frame.iterrows():
        record = row.to_dict()
        record["ata_chapter"] = str(record["ata_chapter"])
        events.append(MaintenanceEvent.model_validate(record))
    return events


def load_truth(path: Path | None = None) -> dict:
    truth_path = path or SYNTHETIC_DIR / "truth.json"
    if not truth_path.exists():
        raise FileNotFoundError(f"Truth data is missing: {truth_path}")
    return json.loads(truth_path.read_text(encoding="utf-8"))


def load_faa_sample(path: Path | None = None) -> pd.DataFrame:
    csv_path = path or DATA_DIR / "faa_sdr_sample.csv"
    if not csv_path.exists():
        return pd.DataFrame()
    return pd.read_csv(csv_path)


def events_for_tail(events: list[MaintenanceEvent], tail_number: str) -> list[MaintenanceEvent]:
    return sorted(
        [event for event in events if event.tail_number == tail_number],
        key=lambda event: event.date,
    )


def known_tails(events: list[MaintenanceEvent]) -> list[str]:
    return sorted({event.tail_number for event in events})
