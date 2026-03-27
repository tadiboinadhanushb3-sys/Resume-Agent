from __future__ import annotations

from resume_screening.agents.types import CandidateProfile, MatchResult, ScoreBreakdown


def build_explanation(
    *,
    candidate_name: str,
    profile: CandidateProfile,
    match: MatchResult,
    score: ScoreBreakdown,
) -> tuple[str, str]:
    matched = match.matched_skills
    missing = match.missing_skills

    positives: list[str] = []
    if matched:
        positives.append(f"Matched key skills: {', '.join(matched[:8])}{'…' if len(matched) > 8 else ''}.")
    if profile.years_experience:
        positives.append(f"Estimated experience: {profile.years_experience} years.")

    risks: list[str] = []
    if missing:
        risks.append(f"Missing skills: {', '.join(missing[:8])}{'…' if len(missing) > 8 else ''}.")
    if not profile.skills:
        risks.append("No recognizable skills were extracted (resume may be image-based or poorly formatted).")

    explanation = (
        f"{candidate_name} scored {score.overall_score:.2f}/100 "
        f"(skill match {score.match_score:.2f}, experience {score.experience_score:.2f}; "
        f"weights match={score.weights['match']:.2f}, experience={score.weights['experience']:.2f}).\n\n"
        + ("Strengths:\n- " + "\n- ".join(positives) + "\n\n" if positives else "")
        + ("Concerns:\n- " + "\n- ".join(risks) if risks else "")
    ).strip()

    gap = (
        f"Top gaps to close: {', '.join(missing[:10])}."
        if missing
        else "No major skill gaps detected for this job."
    )
    return explanation, gap

