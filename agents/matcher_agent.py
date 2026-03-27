def match_skills(candidate, job_description):
    jd = job_description.lower()

    matched = []
    missing = []

    for skill in candidate["skills"]:
        if skill.lower() in jd:
            matched.append(skill)
        else:
            missing.append(skill)

    score = (len(matched) / (len(candidate["skills"]) + 1)) * 100

    return {
        "matched": matched,
        "missing": missing,
        "match_score": round(score, 2)
    }