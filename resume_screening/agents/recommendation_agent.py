from __future__ import annotations

from resume_screening.agents.types import RankedCandidate


class RecommendationAgent:
    name = "Recommendation Agent"

    def run(self, candidate: RankedCandidate) -> RankedCandidate:
        s = candidate.overall_score
        if s >= 85:
            candidate.recommendation = "Strong Hire"
        elif s >= 70:
            candidate.recommendation = "Hire"
        elif s >= 55:
            candidate.recommendation = "Maybe"
        else:
            candidate.recommendation = "No"
        return candidate

