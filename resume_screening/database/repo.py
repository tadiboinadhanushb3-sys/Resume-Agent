from __future__ import annotations

import json
from dataclasses import dataclass

from sqlmodel import Session, select

from resume_screening.database.models import Candidate, CandidateResult, Job, ScreeningRun


@dataclass(frozen=True)
class PersistedResult:
    candidate: Candidate
    result: CandidateResult


class Repo:
    def __init__(self, session: Session):
        self.session = session

    def upsert_job(self, title: str, description: str) -> Job:
        job = Job(title=title.strip() or "Untitled role", description=description)
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job

    def create_run(self, job_id: int, total_candidates: int) -> ScreeningRun:
        run = ScreeningRun(job_id=job_id, total_candidates=total_candidates)
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def create_candidate(self, name: str, source_filename: str, raw_text: str) -> Candidate:
        c = Candidate(name=name, source_filename=source_filename, raw_text=raw_text)
        self.session.add(c)
        self.session.commit()
        self.session.refresh(c)
        return c

    def create_result(
        self,
        *,
        run_id: int,
        candidate_id: int,
        skills: list[str],
        experiences: list[dict],
        matched_skills: list[str],
        missing_skills: list[str],
        match_score: float,
        experience_score: float,
        overall_score: float,
        rank: int,
        recommendation: str,
        explanation: str,
        skill_gap_summary: str,
    ) -> CandidateResult:
        r = CandidateResult(
            run_id=run_id,
            candidate_id=candidate_id,
            skills_json=json.dumps(skills, ensure_ascii=False),
            experiences_json=json.dumps(experiences, ensure_ascii=False),
            matched_skills_json=json.dumps(matched_skills, ensure_ascii=False),
            missing_skills_json=json.dumps(missing_skills, ensure_ascii=False),
            match_score=match_score,
            experience_score=experience_score,
            overall_score=overall_score,
            rank=rank,
            recommendation=recommendation,
            explanation=explanation,
            skill_gap_summary=skill_gap_summary,
        )
        self.session.add(r)
        self.session.commit()
        self.session.refresh(r)
        return r

    def list_recent_runs(self, limit: int = 50) -> list[ScreeningRun]:
        stmt = select(ScreeningRun).order_by(ScreeningRun.created_at.desc()).limit(limit)
        return list(self.session.exec(stmt).all())

    def list_results_for_run(self, run_id: int) -> list[CandidateResult]:
        stmt = select(CandidateResult).where(CandidateResult.run_id == run_id).order_by(CandidateResult.rank.asc())
        return list(self.session.exec(stmt).all())

    def get_candidate(self, candidate_id: int) -> Candidate | None:
        return self.session.get(Candidate, candidate_id)

    def list_candidates_by_ids(self, candidate_ids: list[int]) -> list[Candidate]:
        if not candidate_ids:
            return []
        stmt = select(Candidate).where(Candidate.id.in_(candidate_ids))
        return list(self.session.exec(stmt).all())

    def get_job(self, job_id: int) -> Job | None:
        return self.session.get(Job, job_id)

    def get_run(self, run_id: int) -> ScreeningRun | None:
        return self.session.get(ScreeningRun, run_id)

