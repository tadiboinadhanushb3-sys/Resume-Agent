from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Job(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class Candidate(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    source_filename: str
    raw_text: str
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class ScreeningRun(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(index=True, foreign_key="job.id")
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    total_candidates: int = 0


class CandidateResult(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(index=True, foreign_key="screeningrun.id")
    candidate_id: int = Field(index=True, foreign_key="candidate.id")

    # Derived fields
    skills_json: str = "[]"
    experiences_json: str = "[]"
    matched_skills_json: str = "[]"
    missing_skills_json: str = "[]"

    # Scores
    match_score: float = 0.0
    experience_score: float = 0.0
    overall_score: float = 0.0
    rank: int = 0
    recommendation: str = ""

    # Explainability
    explanation: str = ""
    skill_gap_summary: str = ""

