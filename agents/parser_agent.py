import re

SKILLS = [
    "python","java","sql","machine learning",
    "data science","deep learning","nlp",
    "c","c++","javascript","react"
]

def parse_resume(text):
    text_lower = text.lower()

    skills_found = []
    for skill in SKILLS:
        if skill in text_lower:
            skills_found.append(skill)

    experience = 0
    exp_match = re.findall(r'(\d+)\+?\s*years', text_lower)
    if exp_match:
        experience = int(exp_match[0])

    return {
        "skills": skills_found,
        "experience": experience,
        "raw_text": text
    }