from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "Agentic AI Resume Screening"
    database_url: str = os.getenv(
        "RESUME_DB_URL",
        "sqlite:///./resume_screening.db",
    )
    # Optional: set to a real LLM endpoint/key in production.
    llm_provider: str = os.getenv("RESUME_LLM_PROVIDER", "disabled")


settings = Settings()

