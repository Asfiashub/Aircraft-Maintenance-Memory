from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
SYNTHETIC_DIR = DATA_DIR / "synthetic"
EVALUATION_DIR = PROJECT_ROOT / "evaluation" / "results"

load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    groq_api_key: str | None
    hindsight_api_key: str | None
    hindsight_base_url: str
    hindsight_bank_id: str | None
    groq_primary_model: str = "openai/gpt-oss-120b"

    @property
    def hindsight_configured(self) -> bool:
        return bool(self.hindsight_api_key and self.hindsight_bank_id)

    @property
    def groq_configured(self) -> bool:
        return bool(self.groq_api_key)

    @property
    def fully_configured(self) -> bool:
        return self.hindsight_configured and self.groq_configured


def get_settings() -> Settings:
    return Settings(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        hindsight_api_key=os.getenv("HINDSIGHT_API_KEY"),
        hindsight_base_url=os.getenv(
            "HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io"
        ).rstrip("/"),
        hindsight_bank_id=os.getenv("HINDSIGHT_BANK_ID"),
    )
