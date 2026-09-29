from __future__ import annotations

import json
from typing import Any

import requests
from pydantic import ValidationError

from app.config import Settings, get_settings
from app.models import DiagnosisResult, RecalledMemory
from backend.agent.prompts import (
    DIAGNOSIS_SCHEMA,
    correction_prompt,
    diagnosis_system_prompt,
    diagnosis_user_prompt,
)


class GroqConfigurationError(RuntimeError):
    pass


class GroqAPIError(RuntimeError):
    pass


class DiagnosisAgent:
    def __init__(self, settings: Settings | None = None, timeout: int = 45):
        self.settings = settings or get_settings()
        self.timeout = timeout

    def _ensure_configured(self) -> None:
        if not self.settings.groq_configured:
            raise GroqConfigurationError(
                "Groq is not configured. Set GROQ_API_KEY in the project secrets/environment."
            )

    def diagnose(
        self, tail_number: str, current_fault: str, memories: list[RecalledMemory]
    ) -> DiagnosisResult:
        self._ensure_configured()
        user_prompt = diagnosis_user_prompt(tail_number, current_fault, memories)
        first_error: Exception | None = None
        for model in (
            self.settings.groq_primary_model,
            self.settings.groq_fallback_model,
        ):
            try:
                raw = self._complete(model, user_prompt)
                try:
                    return self._validate(raw)
                except (json.JSONDecodeError, ValidationError) as error:
                    corrected = self._complete(
                        model,
                        diagnosis_user_prompt(tail_number, current_fault, memories)
                        + "\n\n"
                        + correction_prompt(raw),
                    )
                    return self._validate(corrected)
            except Exception as error:
                first_error = error
        raise GroqAPIError(f"Groq diagnosis failed after fallback: {first_error}")

    def _complete(self, model: str, user_prompt: str) -> str:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.settings.groq_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "temperature": 0,
                "max_completion_tokens": 1200,
                "messages": [
                    {"role": "system", "content": diagnosis_system_prompt()},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "tailmemory_diagnosis",
                        "strict": True,
                        "schema": DIAGNOSIS_SCHEMA,
                    },
                },
            },
            timeout=self.timeout,
        )
        if not response.ok:
            raise GroqAPIError(f"Groq {response.status_code}: {response.text[:600]}")
        data: dict[str, Any] = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise GroqAPIError("Groq response did not contain message content.") from error

    @staticmethod
    def _validate(raw: str) -> DiagnosisResult:
        parsed = json.loads(raw)
        return DiagnosisResult.model_validate(parsed)
