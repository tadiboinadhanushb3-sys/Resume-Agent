from __future__ import annotations

from collections import Counter

from resume_screening.agents.types import RankedCandidate


class AnalyticsAgent:
    name = "Analytics Agent"

    def run(self, ranked: list[RankedCandidate]) -> dict:
        scores = [c.overall_score for c in ranked]
        skills = Counter(s for c in ranked for s in c.skills)
        recs = Counter(c.recommendation for c in ranked)
        return {
            "count": len(ranked),
            "avg_score": round(sum(scores) / max(1, len(scores)), 2),
            "top_skills": skills.most_common(20),
            "recommendation_counts": dict(recs),
        }

