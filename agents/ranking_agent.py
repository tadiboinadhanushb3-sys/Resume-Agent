def rank_candidates(candidates):
    sorted_list = sorted(
        candidates,
        key=lambda x: x["score"],
        reverse=True
    )

    for i, c in enumerate(sorted_list, start=1):
        c["rank"] = i

    return sorted_list