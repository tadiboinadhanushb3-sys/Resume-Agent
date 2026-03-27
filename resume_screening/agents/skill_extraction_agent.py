from __future__ import annotations

from resume_screening.agents.types import CandidateProfile, ParsedResume
from resume_screening.services.nlp import extract_skills
from resume_screening.services.skill_taxonomy import DEFAULT_SKILLS


class SkillExtractionAgent:
    name = "Skill Extraction Agent"

    def __init__(self, taxonomy: list[str] | None = None):
        self.taxonomy = taxonomy or DEFAULT_SKILLS

    def run(self, parsed: ParsedResume, profile: CandidateProfile) -> CandidateProfile:
        extraction = extract_skills(parsed.cleaned_text, self.taxonomy)
        profile.skills = extraction.skills
        profile.skill_evidence = extraction.evidence
        return profile

