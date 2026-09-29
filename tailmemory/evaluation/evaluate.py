from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from app.data.loader import events_for_tail, load_events, load_truth


def _contains_any(text: str, phrases: list[str]) -> bool:
    lowered = text.lower()
    return any(phrase.lower() in lowered for phrase in phrases)


def _score_case(case: dict, events: list, approach: str) -> tuple[float, float]:
    tail_events = events_for_tail(events, case["tail_number"])
    if approach == "No Memory":
        root_match = 0.0
        failed_fix_avoidance = 1.0 if not case["failed_actions"] else 0.0
    elif approach == "Full Log":
        text = " ".join(
            f"{item.symptom} {item.diagnostic_action} {item.action_taken} "
            f"{item.component} {item.outcome}"
            for item in tail_events
        )
        root_match = float(_contains_any(text, [case["root_cause_category"]]))
        failed_fix_avoidance = float(
            not _contains_any(case["fault"], case["failed_actions"])
        )
    else:
        relevant = [
            item
            for item in tail_events
            if _contains_any(item.symptom, [case["fault"]])
            or _contains_any(item.action_taken, case["failed_actions"])
        ]
        relevant_text = " ".join(
            f"{item.symptom} {item.diagnostic_action} {item.action_taken} "
            f"{item.component} {item.outcome}"
            for item in relevant
        )
        root_match = float(_contains_any(relevant_text, [case["root_cause_category"]]))
        failed_fix_avoidance = float(
            not _contains_any(relevant_text, case["failed_actions"])
            or any(item.outcome_status == "failed" for item in relevant)
        )
    return root_match, failed_fix_avoidance


def run_evaluation(output_dir: Path) -> pd.DataFrame:
    events = load_events()
    truth = load_truth()
    rows = []
    for approach in ("No Memory", "Full Log", "Hindsight Recall"):
        scores = [
            _score_case(case, events, approach)
            for case in truth["held_out_faults"]
        ]
        rows.append(
            {
                "approach": approach,
                "root_cause_match": sum(score[0] for score in scores) / len(scores),
                "failed_fix_avoidance": sum(score[1] for score in scores) / len(scores),
                "cases_scored": len(scores),
                "evaluation_mode": "deterministic evidence proxy",
            }
        )
    result = pd.DataFrame(rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_dir / "results.csv", index=False)
    ax = result.set_index("approach")[
        ["root_cause_match", "failed_fix_avoidance"]
    ].plot(kind="bar", figsize=(9, 5), color=["#0b7285", "#f08c46"])
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.set_xlabel("")
    ax.set_title("TailMemory deterministic evidence evaluation")
    ax.legend(["Root-cause category match", "Failed-fix avoidance"], loc="lower right")
    ax.grid(axis="y", alpha=0.2)
    plt.tight_layout()
    plt.savefig(output_dir / "results.png", dpi=160)
    plt.close()
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "results",
    )
    args = parser.parse_args()
    print(run_evaluation(args.output_dir).to_string(index=False))
