from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import requests

from app.config import Settings, get_settings
from app.models import MaintenanceEvent, RecalledMemory


class HindsightConfigurationError(RuntimeError):
    """Raised when Hindsight credentials or bank configuration are missing."""


class HindsightAPIError(RuntimeError):
    """Raised when Hindsight returns a non-success response."""


class HindsightClient:
    """Small, explicit wrapper around the verified Hindsight Cloud REST API."""

    def __init__(self, settings: Settings | None = None, timeout: int = 30):
        self.settings = settings or get_settings()
        self.timeout = timeout

    @property
    def configured(self) -> bool:
        return self.settings.hindsight_configured

    def _ensure_configured(self) -> None:
        if not self.configured:
            raise HindsightConfigurationError(
                "Hindsight Cloud is not configured. Set HINDSIGHT_API_KEY and "
                "HINDSIGHT_BANK_ID in the project secrets/environment."
            )

    def _url(self, suffix: str) -> str:
        return (
            f"{self.settings.hindsight_base_url}/v1/default/banks/"
            f"{self.settings.hindsight_bank_id}{suffix}"
        )

    def _post(self, suffix: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._ensure_configured()
        response = requests.post(
            self._url(suffix),
            headers={
                "Authorization": f"Bearer {self.settings.hindsight_api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.timeout,
        )
        if not response.ok:
            detail = response.text[:600]
            raise HindsightAPIError(
                f"Hindsight {response.status_code} at {suffix}: {detail}"
            )
        data = response.json()
        if not isinstance(data, dict):
            raise HindsightAPIError("Hindsight returned an unexpected response shape.")
        return data

    @staticmethod
    def _event_content(event: MaintenanceEvent) -> str:
        return (
            f"Aircraft maintenance event. Event ID: {event.event_id}. "
            f"Tail number: {event.tail_number}. Date: {event.date.isoformat()}. "
            f"ATA chapter: {event.ata_chapter}. Symptom: {event.symptom}. "
            f"Diagnostic action: {event.diagnostic_action}. "
            f"Action taken: {event.action_taken}. Component: {event.component}. "
            f"Outcome: {event.outcome}. Outcome status: {event.outcome_status}. "
            f"Source type: {event.source_type}. Source reference: {event.source_reference}."
        )

    def retain_maintenance_event(self, event: MaintenanceEvent) -> dict[str, Any]:
        return self._post(
            "/memories",
            {
                "async": False,
                "items": [
                    {
                        "content": self._event_content(event),
                        "timestamp": f"{event.date.isoformat()}T00:00:00Z",
                        "context": "Synthetic aircraft maintenance history for TailMemory.",
                        "document_id": f"maintenance:{event.tail_number}:{event.event_id}",
                        "tags": [f"tail:{event.tail_number}"],
                        "metadata": {
                            "event_id": event.event_id,
                            "tail_number": event.tail_number,
                            "source_type": event.source_type,
                        },
                    }
                ],
            },
        )

    def retain_feedback(
        self, tail_number: str, fault: str, outcome: str, advisory: str
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        return self._post(
            "/memories",
            {
                "async": False,
                "items": [
                    {
                        "content": (
                            f"TailMemory feedback for aircraft {tail_number}. "
                            f"Observed fault: {fault}. Advisory outcome: {outcome}. "
                            f"Advisory summary: {advisory}"
                        ),
                        "timestamp": now,
                        "context": "Maintenance outcome feedback recorded by TailMemory.",
                        "document_id": f"feedback:{tail_number}:{now}",
                        "tags": [f"tail:{tail_number}"],
                        "metadata": {
                            "tail_number": tail_number,
                            "feedback_outcome": outcome,
                            "source_type": "TAILMEMORY_FEEDBACK",
                        },
                    }
                ],
            },
        )

    def recall_maintenance_events(
        self, tail_number: str, current_fault: str, max_tokens: int = 5000
    ) -> list[RecalledMemory]:
        data = self._post(
            "/memories/recall",
            {
                "query": (
                    f"Aircraft-specific maintenance history for tail {tail_number}. "
                    f"Current fault: {current_fault}"
                ),
                "types": ["experience", "observation"],
                "budget": "mid",
                "max_tokens": max_tokens,
                "tags": [f"tail:{tail_number}"],
                "tags_match": "exact",
                "include": {"chunks": {}},
            },
        )
        return self._parse_recall(data, tail_number)

    @staticmethod
    def _parse_recall(data: dict[str, Any], requested_tail: str) -> list[RecalledMemory]:
        """Parse a Hindsight recall response.

        Hindsight returns synthesized facts/observations under ``results`` and the
        original retained records under ``chunks``. Chunks keep our exact
        "Event ID ... Outcome status" text, so they are parsed first and are the
        primary evidence. Observations are kept as clearly labeled summaries.
        """
        chunks = data.get("chunks")
        if isinstance(chunks, dict):
            chunk_items = list(chunks.values())
        elif isinstance(chunks, list):
            chunk_items = chunks
        else:
            chunk_items = []
        result_items = data.get("results") or data.get("memories") or data.get("items") or []
        if not isinstance(result_items, list):
            result_items = []

        memories: list[RecalledMemory] = []
        seen_events: set[str] = set()
        sources = [(item, "Hindsight chunk (original record)") for item in chunk_items] + [
            (item, "Hindsight observation (synthesized)") for item in result_items
        ]
        for item, source_type in sources:
            memory = HindsightClient._item_to_memory(item, requested_tail, source_type)
            if memory is None:
                continue
            if memory.event_id:
                if memory.event_id in seen_events:
                    continue
                seen_events.add(memory.event_id)
            memories.append(memory)
        return memories

    @staticmethod
    def _item_to_memory(
        item: Any, requested_tail: str, source_type: str
    ) -> RecalledMemory | None:
        if not isinstance(item, dict):
            return None
        content = (
            item.get("content")
            or item.get("text")
            or item.get("memory")
            or item.get("observation")
            or ""
        )
        if isinstance(content, dict):
            content = content.get("text") or content.get("content") or str(content)
        content = str(content)
        if not content.strip():
            return None
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        parsed_tail = (
            metadata.get("tail_number")
            or _match(content, r"Tail number:\s*([A-Z0-9-]+)")
            or _feedback_tail(content)
        )
        if parsed_tail and parsed_tail != requested_tail:
            return None
        return RecalledMemory(
            event_id=metadata.get("event_id") or _match(content, r"Event ID:\s*([A-Z0-9-]+)"),
            tail_number=parsed_tail or requested_tail,
            date=metadata.get("date") or _match(content, r"Date:\s*([0-9-]+)"),
            ata_chapter=metadata.get("ata_chapter") or _match(content, r"ATA chapter:\s*([0-9]+)"),
            symptom=_match(content, r"Symptom:\s*(.+?)(?:\. Diagnostic action:|$)") or content[:400],
            diagnostic_action=_match(content, r"Diagnostic action:\s*(.+?)(?:\. Action taken:|$)"),
            action_taken=_match(content, r"Action taken:\s*(.+?)(?:\. Component:|$)"),
            component=_match(content, r"Component:\s*(.+?)(?:\. Outcome:|$)"),
            outcome=_match(content, r"Outcome:\s*(.+?)(?:\. Outcome status:|$)"),
            outcome_status=_match(content, r"Outcome status:\s*(\w+)"),
            source_type=source_type,
            raw_content=content,
        )


def _feedback_tail(content: str) -> str | None:
    """Tail number from TailMemory feedback text ("... for aircraft VT-ABC.")."""
    found = re.search(r"feedback for aircraft\s+([A-Z]{1,2}-[A-Z0-9]+)", content)
    return found.group(1) if found else None


def _match(value: str, pattern: str) -> str | None:
    found = re.search(pattern, value, flags=re.IGNORECASE | re.DOTALL)
    return found.group(1).strip() if found else None


def retain_maintenance_event(event: MaintenanceEvent) -> dict[str, Any]:
    return HindsightClient().retain_maintenance_event(event)


def recall_maintenance_events(
    tail_number: str, current_fault: str
) -> list[RecalledMemory]:
    return HindsightClient().recall_maintenance_events(tail_number, current_fault)


def retain_feedback(
    tail_number: str, fault: str, outcome: str, advisory: str
) -> dict[str, Any]:
    return HindsightClient().retain_feedback(tail_number, fault, outcome, advisory)
