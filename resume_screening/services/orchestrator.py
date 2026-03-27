from __future__ import annotations

import concurrent.futures
from dataclasses import dataclass
from typing import Callable

from sqlmodel import Session

from resume_screening.agents.analytics_agent import AnalyticsAgent
from resume_screening.agents.candidate_scoring_agent import CandidateScoringAgent
from resume_screening.agents.experience_analyzer_agent import ExperienceAnalyzerAgent
from resume_screening.agents.job_matching_agent import JobMatchingAgent
from resume_screening.agents.ranking_agent import RankingAgent
from resume_screening.agents.recommendation_agent import RecommendationAgent
from resume_screening.agents.resume_parsing_agent import ResumeParsingAgent
from resume_screening.agents.skill_extraction_agent import SkillExtractionAgent
from resume_screening.agents.types import CandidateProfile, RankedCandidate
from resume_screening.database.repo import Repo
from resume_screening.services.explain import build_explanation
from resume_screening.utils.resume_reader import read_resume_bytes


@dataclass(frozen=True)
class UploadedResume:
    filename: str
    data: bytes


@dataclass(frozen=True)
class ScreeningOutput:
    run_id: int
    job_id: int
    ranked: list[RankedCandidate]
    analytics: dict


@dataclass(frozen=True)
class LiveEvent:
    filename: str
    candidate: str
    stage: str
    status: str
    message: str


class MultiAgentOrchestrator:
    def __init__(self):
        self.resume_parsing_agent = ResumeParsingAgent()
        self.skill_extraction_agent = SkillExtractionAgent()
        self.experience_analyzer_agent = ExperienceAnalyzerAgent()
        self.job_matching_agent = JobMatchingAgent()
        self.candidate_scoring_agent = CandidateScoringAgent()
        self.recommendation_agent = RecommendationAgent()
        self.ranking_agent = RankingAgent()
        self.analytics_agent = AnalyticsAgent()

    def _process_one(self, uploaded: UploadedResume, job_description: str) -> tuple[str, str, RankedCandidate]:
        rr = read_resume_bytes(uploaded.filename, uploaded.data)
        parsed = self.resume_parsing_agent.run(rr.text)

        candidate_name = parsed.name_hint or rr.filename.rsplit(".", 1)[0]
        profile = CandidateProfile(name=candidate_name)
        profile = self.skill_extraction_agent.run(parsed, profile)
        profile = self.experience_analyzer_agent.run(parsed, profile)

        match = self.job_matching_agent.run(profile, job_description)
        score = self.candidate_scoring_agent.run(profile, match)
        explanation, gap = build_explanation(
            candidate_name=candidate_name,
            profile=profile,
            match=match,
            score=score,
        )

        ranked = RankedCandidate(
            name=candidate_name,
            source_filename=rr.filename,
            skills=profile.skills,
            experiences=profile.experiences,
            matched_skills=match.matched_skills,
            missing_skills=match.missing_skills,
            match_score=score.match_score,
            experience_score=score.experience_score,
            overall_score=score.overall_score,
            recommendation="",
            explanation=explanation,
            skill_gap_summary=gap,
        )
        ranked = self.recommendation_agent.run(ranked)
        return candidate_name, parsed.raw_text, ranked

    def _process_one_live(
        self,
        uploaded: UploadedResume,
        job_description: str,
        emit: Callable[[LiveEvent], None],
    ) -> tuple[str, str, RankedCandidate]:
        emit(LiveEvent(uploaded.filename, uploaded.filename, "Resume Parsing", "running", "Reading file and extracting text"))
        rr = read_resume_bytes(uploaded.filename, uploaded.data)
        parsed = self.resume_parsing_agent.run(rr.text)
        candidate_name = parsed.name_hint or rr.filename.rsplit(".", 1)[0]
        emit(LiveEvent(uploaded.filename, candidate_name, "Resume Parsing", "done", "Parsed resume content"))

        profile = CandidateProfile(name=candidate_name)
        emit(LiveEvent(uploaded.filename, candidate_name, "Skill Extraction", "running", "Extracting skill signals"))
        profile = self.skill_extraction_agent.run(parsed, profile)
        emit(LiveEvent(uploaded.filename, candidate_name, "Skill Extraction", "done", f"Found {len(profile.skills)} skills"))

        emit(LiveEvent(uploaded.filename, candidate_name, "Experience Analysis", "running", "Estimating years and experience timeline"))
        profile = self.experience_analyzer_agent.run(parsed, profile)
        emit(
            LiveEvent(
                uploaded.filename,
                candidate_name,
                "Experience Analysis",
                "done",
                f"Estimated {profile.years_experience} years",
            )
        )

        emit(LiveEvent(uploaded.filename, candidate_name, "Job Matching", "running", "Comparing against job requirements"))
        match = self.job_matching_agent.run(profile, job_description)
        emit(
            LiveEvent(
                uploaded.filename,
                candidate_name,
                "Job Matching",
                "done",
                f"Match score {match.match_score:.1f}%",
            )
        )

        emit(LiveEvent(uploaded.filename, candidate_name, "Candidate Scoring", "running", "Computing weighted score"))
        score = self.candidate_scoring_agent.run(profile, match)
        explanation, gap = build_explanation(
            candidate_name=candidate_name,
            profile=profile,
            match=match,
            score=score,
        )
        ranked = RankedCandidate(
            name=candidate_name,
            source_filename=rr.filename,
            skills=profile.skills,
            experiences=profile.experiences,
            matched_skills=match.matched_skills,
            missing_skills=match.missing_skills,
            match_score=score.match_score,
            experience_score=score.experience_score,
            overall_score=score.overall_score,
            recommendation="",
            explanation=explanation,
            skill_gap_summary=gap,
        )
        ranked = self.recommendation_agent.run(ranked)
        emit(LiveEvent(uploaded.filename, candidate_name, "Candidate Scoring", "done", f"Overall {ranked.overall_score:.1f}"))
        return candidate_name, parsed.raw_text, ranked

    def _persist_ranked(
        self,
        *,
        repo: Repo,
        run_id: int,
        ranked_candidates: list[tuple[object, RankedCandidate]],
    ) -> list[RankedCandidate]:
        ranked_only = [r for (_, r) in ranked_candidates]
        ranked_only = self.ranking_agent.run(ranked_only)

        candidate_id_by_key: dict[tuple[str, str], int] = {
            (c.source_filename, c.name): c.id for (c, _) in ranked_candidates if c.id is not None
        }
        for r in ranked_only:
            candidate_id = candidate_id_by_key.get((r.source_filename, r.name))
            if candidate_id is None:
                continue
            repo.create_result(
                run_id=run_id,
                candidate_id=candidate_id,
                skills=r.skills,
                experiences=r.experiences,
                matched_skills=r.matched_skills,
                missing_skills=r.missing_skills,
                match_score=r.match_score,
                experience_score=r.experience_score,
                overall_score=r.overall_score,
                rank=r.rank,
                recommendation=r.recommendation,
                explanation=r.explanation,
                skill_gap_summary=r.skill_gap_summary,
            )
        return ranked_only

    def screen(
        self,
        *,
        session: Session,
        job_title: str,
        job_description: str,
        resumes: list[UploadedResume],
        max_workers: int = 4,
    ) -> ScreeningOutput:
        repo = Repo(session)
        job = repo.upsert_job(job_title, job_description)
        run = repo.create_run(job.id, total_candidates=len(resumes))

        ranked_candidates: list[tuple[object, RankedCandidate]] = []

        # Batch processing (parallel per-resume).
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = [ex.submit(self._process_one, r, job_description) for r in resumes]
            for f in concurrent.futures.as_completed(futures):
                candidate_name, raw_text, ranked = f.result()
                # Persist candidate + placeholder; rank is assigned later.
                candidate = repo.create_candidate(candidate_name, ranked.source_filename, raw_text=raw_text)
                ranked_candidates.append((candidate, ranked))

        ranked_only = self._persist_ranked(repo=repo, run_id=run.id, ranked_candidates=ranked_candidates)
        analytics = self.analytics_agent.run(ranked_only)
        return ScreeningOutput(run_id=run.id, job_id=job.id, ranked=ranked_only, analytics=analytics)

    def screen_live(
        self,
        *,
        session: Session,
        job_title: str,
        job_description: str,
        resumes: list[UploadedResume],
        event_callback: Callable[[LiveEvent], None],
    ) -> ScreeningOutput:
        repo = Repo(session)
        job = repo.upsert_job(job_title, job_description)
        run = repo.create_run(job.id, total_candidates=len(resumes))

        ranked_candidates: list[tuple[object, RankedCandidate]] = []
        for uploaded in resumes:
            event_callback(LiveEvent(uploaded.filename, uploaded.filename, "Resume", "running", "Starting candidate pipeline"))
            candidate_name, raw_text, ranked = self._process_one_live(uploaded, job_description, event_callback)
            candidate = repo.create_candidate(candidate_name, ranked.source_filename, raw_text=raw_text)
            ranked_candidates.append((candidate, ranked))
            event_callback(
                LiveEvent(
                    uploaded.filename,
                    candidate_name,
                    "Ranking Queue",
                    "done",
                    "Candidate added to global ranking",
                )
            )

        ranked_only = self._persist_ranked(repo=repo, run_id=run.id, ranked_candidates=ranked_candidates)
        analytics = self.analytics_agent.run(ranked_only)
        event_callback(LiveEvent("all", "all", "Complete", "done", f"Run #{run.id} finished with {len(ranked_only)} candidates"))
        return ScreeningOutput(run_id=run.id, job_id=job.id, ranked=ranked_only, analytics=analytics)

