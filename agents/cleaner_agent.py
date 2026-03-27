def clean_data(data):
    skills = list(set([s.title() for s in data["skills"]]))
    data["skills"] = skills
    return data