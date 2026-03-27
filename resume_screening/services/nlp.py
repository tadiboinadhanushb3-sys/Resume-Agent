from __future__ import annotations

import re
from dataclasses import dataclass

from rapidfuzz import fuzz


_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9\.\+#/ -]{1,50}")


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def tokenize_lower(text: str) -> list[str]:
    return re.findall(r"[a-z0-9\+#\.]+", (text or "").lower())


def extract_years_experience(text: str) -> int:
    t = (text or "").lower()
    patterns = [
        r"(\d+)\s*\+?\s*years",
        r"(\d+)\s*\+?\s*yrs",
        r"(\d+)\s*\+?\s*year",
    ]
    for p in patterns:
        m = re.search(p, t)
        if m:
            try:
                return max(0, int(m.group(1)))
            except ValueError:
                continue
    return 0


def fuzzy_contains(haystack: str, needle: str, *, threshold: int = 90) -> bool:
    h = (haystack or "").lower()
    n = (needle or "").lower()
    if not n:
        return False
    if n in h:
        return True
    # Token-set ratio helps for skills like "machine learning"
    return fuzz.token_set_ratio(h, n) >= threshold


@dataclass(frozen=True)
class SkillExtraction:
    skills: list[str]
    evidence: dict[str, str]


def extract_skills(text: str, taxonomy: list[str]) -> SkillExtraction:
    t = (text or "").lower()
    skills: list[str] = []
    evidence: dict[str, str] = {}
    for skill in taxonomy:
        if fuzzy_contains(t, skill, threshold=92 if len(skill) <= 4 else 88):
            skills.append(skill)
            # best-effort evidence snippet
            m = re.search(re.escape(skill.split()[0]), t)
            if m:
                start = max(0, m.start() - 40)
                end = min(len(t), m.end() + 60)
                evidence[skill] = t[start:end].strip()
            else:
                evidence[skill] = "mentioned"
    # de-dupe, stable order by first appearance in taxonomy
    uniq = []
    seen = set()
    for s in skills:
        if s not in seen:
            uniq.append(s)
            seen.add(s)
    return SkillExtraction(skills=uniq, evidence=evidence)


def extract_job_required_skills(job_description: str, taxonomy: list[str]) -> list[str]:
    return extract_skills(job_description, taxonomy).skills

