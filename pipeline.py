from __future__ import annotations

"""
Legacy wrapper kept for compatibility.

The production pipeline lives in `resume_screening/services/orchestrator.py`.
"""

from resume_screening.services.orchestrator import MultiAgentOrchestrator, UploadedResume
from resume_screening.database.session import get_session, init_db


def process_resume(file, job_description: str):
    init_db()
    data = file.read()
    orchestrator = MultiAgentOrchestrator()
    with get_session() as session:
        out = orchestrator.screen(
            session=session,
            job_title="Legacy run",
            job_description=job_description,
            resumes=[UploadedResume(filename=getattr(file, "name", "resume.pdf"), data=data)],
            max_workers=1,
        )
    c = out.ranked[0]
    return {
        "skills": c.skills,
        "experience": c.experience_score,
        "matched": c.matched_skills,
        "missing": c.missing_skills,
        "score": c.overall_score,
        "explanation": c.explanation,
    }