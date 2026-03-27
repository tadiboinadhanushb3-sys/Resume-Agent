from __future__ import annotations

from resume_screening.agents.types import RankedCandidate


class RankingAgent:
    name = "Ranking Agent"

    def run(self, candidates: list[RankedCandidate]) -> list[RankedCandidate]:
        ranked = sorted(candidates, key=lambda c: c.overall_score, reverse=True)
        for i, c in enumerate(ranked, start=1):
            c.rank = i
        return ranked

