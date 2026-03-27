from __future__ import annotations

from resume_screening.agents.types import CandidateProfile, MatchResult
from resume_screening.services.nlp import extract_job_required_skills
from resume_screening.services.skill_taxonomy import DEFAULT_SKILLS


class JobMatchingAgent:
    name = "Job Matching Agent"

    def __init__(self, taxonomy: list[str] | None = None):
        self.taxonomy = taxonomy or DEFAULT_SKILLS

    def run(self, profile: CandidateProfile, job_description: str) -> MatchResult:
        required = extract_job_required_skills(job_description, self.taxonomy)
        candidate_skills = set([s.lower() for s in profile.skills])
        matched = [s for s in required if s.lower() in candidate_skills]
        missing = [s for s in required if s.lower() not in candidate_skills]

        denom = max(1, len(required))
        match_score = round((len(matched) / denom) * 100.0, 2)
        return MatchResult(
            required_skills=required,
            matched_skills=matched,
            missing_skills=missing,
            match_score=match_score,
        )

