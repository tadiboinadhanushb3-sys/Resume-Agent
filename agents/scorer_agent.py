def score_candidate(candidate, match_result):
    skill_score = match_result["match_score"]
    exp_score = candidate["experience"] * 5

    total_score = skill_score + exp_score

    if total_score > 100:
        total_score = 100

    return round(total_score, 2)