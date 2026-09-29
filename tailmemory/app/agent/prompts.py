"""Public prompt module kept at the application boundary."""

from backend.agent.prompts import (
    DIAGNOSIS_SCHEMA,
    correction_prompt,
    diagnosis_system_prompt,
    diagnosis_user_prompt,
)

__all__ = [
    "DIAGNOSIS_SCHEMA",
    "correction_prompt",
    "diagnosis_system_prompt",
    "diagnosis_user_prompt",
]