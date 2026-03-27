from __future__ import annotations

import re

from resume_screening.agents.types import ParsedResume
from resume_screening.services.nlp import normalize_text


class ResumeParsingAgent:
    name = "Resume Parsing Agent"

    def run(self, raw_text: str) -> ParsedResume:
        cleaned = normalize_text(raw_text)
        # naive name hint: first non-empty line with 2-4 words and no digits
        name_hint = ""
        for line in (raw_text or "").splitlines()[:15]:
            l = line.strip()
            if not l:
                continue
            if any(ch.isdigit() for ch in l):
                continue
            if len(l.split()) in (2, 3, 4) and len(l) <= 40 and not re.search(r"@|http|www\.", l.lower()):
                name_hint = l
                break
        return ParsedResume(raw_text=raw_text, cleaned_text=cleaned, name_hint=name_hint)

