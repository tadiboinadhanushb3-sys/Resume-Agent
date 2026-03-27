from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ParsedResume:
    raw_text: str
    cleaned_text: str
    name_hint: str = ""


@dataclass
class CandidateProfile:
    name: str
    skills: list[str] = field(default_factory=list)
    skill_evidence: dict[str, str] = field(default_factory=dict)
    years_experience: int = 0
    experiences: list[dict] = field(default_factory=list)


@dataclass
class MatchResult:
    required_skills: list[str]
    matched_skills: list[str]
    missing_skills: list[str]
    match_score: float


@dataclass
class ScoreBreakdown:
    match_score: float
    experience_score: float
    overall_score: float
    weights: dict[str, float]


@dataclass
class RankedCandidate:
    name: str
    source_filename: str
    skills: list[str]
    experiences: list[dict]
    matched_skills: list[str]
    missing_skills: list[str]
    match_score: float
    experience_score: float
    overall_score: float
    rank: int = 0
    recommendation: str = ""
    explanation: str = ""
    skill_gap_summary: str = ""

