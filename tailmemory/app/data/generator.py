from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from app.config import SYNTHETIC_DIR


TAILS = ["VT-ABC", "VT-DEF", "VT-GHI", "VT-JKL", "VT-MNO", "VT-PQR", "VT-STU", "VT-XYZ"]


def _event(
    event_id: str,
    tail: str,
    when: date,
    ata: str,
    symptom: str,
    diagnostic: str,
    action: str,
    component: str,
    outcome: str,
    status: str,
) -> dict:
    return {
        "event_id": event_id,
        "tail_number": tail,
        "date": when.isoformat(),
        "ata_chapter": ata,
        "symptom": symptom,
        "diagnostic_action": diagnostic,
        "action_taken": action,
        "component": component,
        "outcome": outcome,
        "outcome_status": status,
        "source_type": "SYNTHETIC",
        "source_reference": "TailMemory demonstration dataset",
    }


def generate_events() -> list[dict]:
    records: list[dict] = []
    base_date = date(2025, 1, 12)
    for tail_index, tail in enumerate(TAILS):
        offset = tail_index * 3
        for index in range(20):
            when = base_date + timedelta(days=offset + index * 11)
            records.append(
                _event(
                    f"{tail.replace('-', '')}-{index + 1:03d}",
                    tail,
                    when,
                    "25" if index % 3 == 0 else "32",
                    "Routine inspection finding",
                    "Visual inspection and log review",
                    "Recorded and monitored",
                    "General system",
                    "No recurrence observed",
                    "worked" if index % 4 else "not_verified",
                )
            )

    planted = {
        "VT-ABC": [
            ("29", "Hydraulic pressure warning", "Pressure test", "Replaced hydraulic pump", "Hydraulic pump", "Warning recurred after takeoff", "failed"),
            ("29", "Hydraulic pressure warning", "Component substitution", "Replaced hydraulic pump again", "Hydraulic pump", "Warning recurred on next sector", "failed"),
            ("29", "Hydraulic pressure warning", "Line and reservoir inspection", "Inspected return line and found restriction", "Hydraulic return line", "Pressure stabilized after corrective action", "worked"),
            ("29", "Hydraulic pressure warning", "Post-maintenance operational check", "Monitored pressure trend", "Hydraulic system", "No further warning observed", "worked"),
        ],
        "VT-DEF": [
            ("24", "Intermittent electrical bus caution", "Load test", "Reset generator control unit", "Generator control unit", "Caution returned", "failed"),
            ("24", "Intermittent electrical bus caution", "Wiring continuity check", "Inspected and repaired harness connection", "Electrical harness", "Bus remained stable", "worked"),
            ("24", "Generator voltage fluctuation", "Voltage trend review", "Replaced generator control unit", "Generator control unit", "Fluctuation returned", "failed"),
            ("24", "Generator voltage fluctuation", "Connector inspection", "Secured loose connector", "Generator connector", "Voltage stable", "worked"),
        ],
        "VT-GHI": [
            ("31", "Primary display blank during power-up", "LRU self-test", "Replaced display unit", "Display LRU", "Blank display returned", "failed"),
            ("31", "Primary display blank during power-up", "LRU swap", "Replaced display unit again", "Display LRU", "Blank display returned", "failed"),
            ("31", "Primary display blank during power-up", "Connector and pin inspection", "Reseated display connector", "Display connector", "Display restored", "worked"),
            ("31", "Primary display blank during power-up", "Operational check", "Verified display through multiple power cycles", "Display system", "No recurrence observed", "worked"),
        ],
        "VT-JKL": [
            ("73", "Low fuel flow indication", "Fuel pressure test", "Replaced fuel filter", "Fuel filter", "Low flow indication returned", "failed"),
            ("73", "Low fuel flow indication", "Filter inspection", "Replaced fuel filter again", "Fuel filter", "Low flow indication returned", "failed"),
            ("73", "Low fuel flow indication", "Sensor harness continuity check", "Repaired fuel flow sensor harness", "Fuel flow sensor harness", "Flow indication normalized", "worked"),
            ("73", "Low fuel flow indication", "Post-maintenance trend review", "Monitored fuel flow trend", "Fuel system", "No recurrence observed", "worked"),
        ],
        "VT-MNO": [
            ("32", "Brake temperature warning after taxi", "Brake unit inspection", "Replaced brake control unit", "Brake control unit", "Warning returned", "failed"),
            ("32", "Brake temperature warning after taxi", "Brake unit substitution", "Replaced brake control unit again", "Brake control unit", "Warning returned", "failed"),
            ("32", "Brake temperature warning after taxi", "Temperature circuit inspection", "Repaired temperature probe wiring", "Brake temperature probe wiring", "Temperature readings normalized", "worked"),
            ("32", "Brake temperature warning after taxi", "Operational brake check", "Monitored brake temperatures", "Brake system", "No recurrence observed", "worked"),
        ],
    }

    for tail, events in planted.items():
        start = date(2025, 3, 1) + timedelta(days=TAILS.index(tail) * 4)
        for index, values in enumerate(events, start=1):
            ata, symptom, diagnostic, action, component, outcome, status = values
            records.append(
                _event(
                    f"{tail.replace('-', '')}-P{index:03d}",
                    tail,
                    start + timedelta(days=index * 13),
                    ata,
                    symptom,
                    diagnostic,
                    action,
                    component,
                    outcome,
                    status,
                )
            )

    extra_events = {
        "VT-PQR": [
            ("21", "Cabin temperature high", "Cabin temperature check", "Adjusted temperature controller", "Temperature controller", "Cabin temperature normalized", "worked"),
            ("21", "Cabin temperature high", "Operational check", "Monitored cabin temperature", "Cabin system", "No recurrence observed", "worked"),
            ("27", "Flight control trim indication", "Control surface inspection", "Adjusted trim actuator linkage", "Trim actuator linkage", "Indication cleared", "worked"),
            ("27", "Flight control trim indication", "Operational check", "Completed control check", "Flight controls", "No recurrence observed", "worked"),
        ],
        "VT-STU": [
            ("72", "Engine vibration above expected trend", "Vibration survey", "Performed fan trim", "Fan assembly", "Vibration reduced", "worked"),
            ("72", "Engine vibration above expected trend", "Trend monitoring", "Monitored vibration after trim", "Engine vibration system", "No recurrence observed", "worked"),
            ("79", "Oil pressure indication fluctuating", "Pressure transducer test", "Replaced pressure transducer", "Oil pressure transducer", "Indication stable", "worked"),
            ("79", "Oil pressure indication fluctuating", "Operational check", "Verified oil pressure trend", "Oil system", "No recurrence observed", "worked"),
        ],
        "VT-XYZ": [
            ("24", "Generator voltage fluctuation", "Voltage trend review", "Monitored generator output", "Generator system", "No recurrence observed", "worked"),
            ("24", "Generator voltage fluctuation", "Operational check", "Verified generator output", "Generator system", "No recurrence observed", "worked"),
            ("30", "Rain repellent low flow", "Reservoir inspection", "Refilled rain repellent reservoir", "Rain repellent reservoir", "Flow restored", "worked"),
            ("30", "Rain repellent low flow", "Operational check", "Verified windshield spray", "Rain repellent system", "No recurrence observed", "worked"),
        ],
    }
    for tail, events in extra_events.items():
        start = date(2025, 4, 5) + timedelta(days=TAILS.index(tail) * 5)
        for index, values in enumerate(events, start=1):
            ata, symptom, diagnostic, action, component, outcome, status = values
            records.append(
                _event(
                    f"{tail.replace('-', '')}-P{index:03d}",
                    tail,
                    start + timedelta(days=index * 15),
                    ata,
                    symptom,
                    diagnostic,
                    action,
                    component,
                    outcome,
                    status,
                )
            )
    return sorted(records, key=lambda row: (row["tail_number"], row["date"], row["event_id"]))


def generate_truth() -> dict:
    return {
        "dataset": "TailMemory synthetic maintenance histories",
        "disclosure": "All aircraft records are synthetic and are not real aircraft records.",
        "held_out_faults": [
            {
                "tail_number": "VT-ABC",
                "fault": "Hydraulic pressure warning after takeoff",
                "root_cause_category": "hydraulic return-line restriction",
                "failed_actions": ["Replaced hydraulic pump", "Replaced hydraulic pump again"],
            },
            {
                "tail_number": "VT-DEF",
                "fault": "Intermittent electrical bus caution",
                "root_cause_category": "electrical harness or connector",
                "failed_actions": ["Reset generator control unit", "Replaced generator control unit"],
            },
            {
                "tail_number": "VT-GHI",
                "fault": "Primary display blank during power-up",
                "root_cause_category": "display connector",
                "failed_actions": ["Replaced display unit", "Replaced display unit again"],
            },
            {
                "tail_number": "VT-JKL",
                "fault": "Low fuel flow indication",
                "root_cause_category": "fuel flow sensor harness",
                "failed_actions": ["Replaced fuel filter", "Replaced fuel filter again"],
            },
            {
                "tail_number": "VT-MNO",
                "fault": "Brake temperature warning after taxi",
                "root_cause_category": "brake temperature probe wiring",
                "failed_actions": ["Replaced brake control unit", "Replaced brake control unit again"],
            },
            {
                "tail_number": "VT-XYZ",
                "fault": "Hydraulic pressure warning after takeoff",
                "root_cause_category": "unknown aircraft-specific cause",
                "failed_actions": [],
            },
        ],
    }


def write_dataset(output_dir: Path = SYNTHETIC_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(generate_events()).to_csv(
        output_dir / "maintenance_events.csv", index=False
    )
    (output_dir / "truth.json").write_text(
        json.dumps(generate_truth(), indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    write_dataset()
