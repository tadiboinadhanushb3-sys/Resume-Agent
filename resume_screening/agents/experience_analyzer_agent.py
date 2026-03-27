from __future__ import annotations

import re

from resume_screening.agents.types import CandidateProfile, ParsedResume
from resume_screening.services.nlp import extract_years_experience


class ExperienceAnalyzerAgent:
    name = "Experience Analyzer Agent"

    def run(self, parsed: ParsedResume, profile: CandidateProfile) -> CandidateProfile:
        profile.years_experience = extract_years_experience(parsed.cleaned_text)

        # Lightweight experience bullet extraction: capture lines with verbs/company-like tokens.
        experiences: list[dict] = []
        for line in (parsed.raw_text or "").splitlines():
            l = line.strip()
            if len(l) < 20:
                continue
            if re.search(r"\b(intern|engineer|developer|analyst|manager|lead)\b", l.lower()):
                experiences.append({"summary": l[:220]})
        profile.experiences = experiences[:10]
        return profile

