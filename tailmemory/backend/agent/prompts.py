from __future__ import annotations

import json

from app.models import RecalledMemory


DIAGNOSIS_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "tail_number": {"type": "string"},
        "fault_summary": {"type": "string"},
        "likely_fault_categories": {"type": "array", "items": {"type": "string"}},
        "historical_matches": {"type": "array", "items": {"type": "string"}},
        "relevant_previous_actions": {"type": "array", "items": {"type": "string"}},
        "failed_actions_to_avoid": {"type": "array", "items": {"type": "string"}},
        "recommended_next_steps": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "string", "enum": ["low", "moderate", "high"]},
        "safety_note": {"type": "string"},
        "evidence_event_ids": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "tail_number",
        "fault_summary",
        "likely_fault_categories",
        "historical_matches",
        "relevant_previous_actions",
        "failed_actions_to_avoid",
        "recommended_next_steps",
        "confidence",
        "safety_note",
        "evidence_event_ids",
    ],
}


def diagnosis_system_prompt() -> str:
    return """You are TailMemory, an aircraft maintenance memory assistant.
This is advisory decision support only. Never certify airworthiness, authorize
maintenance, claim a certain diagnosis, provide dangerous procedural instructions,
or replace a licensed or qualified aircraft maintenance engineer.

Use only the provided recalled Hindsight evidence. Never invent maintenance history.
Clearly distinguish aircraft-specific evidence from inference. Identify interventions
whose recorded outcome_status is failed. Do not present a previously failed
intervention as the primary next recommendation when the evidence indicates it failed.
Keep next steps at a high-level verification and review level. Always recommend
qualified human verification. Return only valid JSON matching the supplied schema."""


def diagnosis_user_prompt(
    tail_number: str, current_fault: str, memories: list[RecalledMemory]
) -> str:
    evidence = [
        {
            "event_id": memory.event_id,
            "tail_number": memory.tail_number,
            "date": memory.date,
            "ata_chapter": memory.ata_chapter,
            "symptom": memory.symptom,
            "diagnostic_action": memory.diagnostic_action,
            "action_taken": memory.action_taken,
            "component": memory.component,
            "outcome": memory.outcome,
            "outcome_status": memory.outcome_status,
            "source_type": memory.source_type,
            "source_reference": memory.source_reference,
        }
        for memory in memories
    ]
    return (
        f"TAIL NUMBER\n{tail_number}\n\n"
        f"CURRENT FAULT\n{current_fault}\n\n"
        f"RECALLED HINDSIGHT MEMORIES\n{json.dumps(evidence, indent=2)}\n\n"
        "If the recalled evidence is empty, say so explicitly and keep "
        "aircraft-specific claims empty. Do not use a full local aircraft log."
    )


def correction_prompt(raw_response: str) -> str:
    return (
        "The prior response was not valid for the required schema. Return only a "
        "single JSON object matching the schema exactly. Preserve only evidence "
        "supported by the input. Prior response:\n" + raw_response
    )
