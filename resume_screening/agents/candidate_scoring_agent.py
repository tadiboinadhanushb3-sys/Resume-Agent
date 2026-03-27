from __future__ import annotations

from resume_screening.agents.types import CandidateProfile, MatchResult, ScoreBreakdown


class CandidateScoringAgent:
    name = "Candidate Scoring Agent"

    def __init__(self, *, w_match: float = 0.75, w_experience: float = 0.25):
        self.w_match = float(w_match)
        self.w_experience = float(w_experience)

    def run(self, profile: CandidateProfile, match: MatchResult) -> ScoreBreakdown:
        # Experience score saturates at 10 years.
        experience_score = round(min(10, max(0, profile.years_experience)) / 10 * 100.0, 2)
        overall = round((match.match_score * self.w_match) + (experience_score * self.w_experience), 2)
        return ScoreBreakdown(
            match_score=match.match_score,
            experience_score=experience_score,
            overall_score=overall,
            weights={"match": self.w_match, "experience": self.w_experience},
        )

