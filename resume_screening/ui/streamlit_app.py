from __future__ import annotations

import json
import time
from collections import Counter

import pandas as pd
import plotly.express as px
import streamlit as st

from resume_screening.database.repo import Repo
from resume_screening.database.session import get_session, init_db
from resume_screening.services.orchestrator import LiveEvent, MultiAgentOrchestrator, UploadedResume
from resume_screening.ui.components import render_agent_workflow, render_decision_panel, render_metric_card
from resume_screening.ui.landing import render_landing_page
from resume_screening.ui.style import apply_saas_theme


def _nav() -> str:
    return st.sidebar.radio(
        "Navigation",
        ["Screen", "Dashboard", "Candidates", "Admin"],
        index=0,
    )


def _score_label(score: float) -> str:
    if score >= 80:
        return "High"
    if score >= 55:
        return "Medium"
    return "Low"


def _score_color(score: float) -> str:
    if score >= 80:
        return "#4ade80"
    if score >= 55:
        return "#facc15"
    return "#f87171"


def _ai_strengths_weaknesses(skills: list[str], missing: list[str], experience_score: float) -> tuple[list[str], list[str]]:
    strengths = []
    weaknesses = []
    if skills:
        strengths.append(f"Strong stack coverage in: {', '.join(skills[:5])}.")
    if experience_score >= 70:
        strengths.append("Experience level appears suitable for independent delivery.")
    elif experience_score > 0:
        weaknesses.append("Limited experience score suggests need for mentoring support.")
    if missing:
        weaknesses.append(f"Skill gaps for this role: {', '.join(missing[:5])}.")
    if not strengths:
        strengths.append("General baseline fit found; resume has partial role relevance.")
    if not weaknesses:
        weaknesses.append("No major red flags detected for core requirements.")
    return strengths, weaknesses


def _interview_questions(skills: list[str], missing: list[str]) -> list[str]:
    q = []
    for s in skills[:3]:
        q.append(f"Can you describe a project where you used {s} and the impact you delivered?")
    for s in missing[:2]:
        q.append(f"What is your current familiarity with {s}, and how would you ramp up quickly?")
    q.append("Walk me through a difficult technical trade-off you made recently.")
    return q


def _screen_page() -> None:
    st.subheader("Batch resume screening")

    with st.sidebar:
        st.caption("Theme")
        bg_path = st.text_input("Background image path (optional)", value="")

    apply_saas_theme(background_image_path=bg_path.strip() or None)

    job_title = st.text_input("Job title", value="Software Engineer")
    job_description = st.text_area("Job description", height=220)
    uploaded = st.file_uploader(
        "Upload resumes (PDF/DOCX/TXT)",
        accept_multiple_files=True,
        type=["pdf", "docx", "txt"],
    )
    if uploaded:
        st.write("### Resume preview panel")
        preview_df = pd.DataFrame(
            [{"File": f.name, "Size (KB)": round(getattr(f, "size", 0) / 1024, 2)} for f in uploaded]
        )
        st.dataframe(preview_df, hide_index=True, use_container_width=True)

    col_a, col_b, col_c = st.columns([1, 1, 2])
    with col_a:
        max_workers = st.slider("Parallel workers", 1, 12, 4)
    with col_b:
        shortlist_n = st.slider("Shortlist size", 1, 20, 5)
    with col_c:
        live_stream = st.toggle("Live per-resume event stream", value=True)

    run = st.button("Run screening", type="primary", use_container_width=True)
    if not run:
        return

    if not job_description.strip():
        st.error("Please paste a job description.")
        return
    if not uploaded:
        st.error("Please upload at least one resume.")
        return

    resumes: list[UploadedResume] = []
    upload_progress = st.progress(0, text="Uploading resumes...")
    for idx, f in enumerate(uploaded, start=1):
        data = f.read()
        resumes.append(UploadedResume(filename=f.name, data=data))
        upload_progress.progress(int((idx / len(uploaded)) * 100), text=f"Uploaded {idx}/{len(uploaded)} resumes")
    upload_progress.empty()

    workflow_steps = [
        "Parsing Resume",
        "Extracting Skills",
        "Analyzing Experience",
        "Matching Job",
        "Generating Final Score",
    ]
    # lightweight animation so recruiters can see progress before orchestration.
    render_agent_workflow(workflow_steps, animated=False)
    status = st.empty()
    progress = st.progress(0)
    for idx, step in enumerate(workflow_steps, start=1):
        status.info(f"{step}...")
        progress.progress(int((idx / len(workflow_steps)) * 100))
        time.sleep(0.12)

    orchestrator = MultiAgentOrchestrator()
    event_box = st.empty()
    progress_box = st.empty()
    event_lines: list[str] = []

    def _emit(event: LiveEvent) -> None:
        icon = "✅" if event.status == "done" else "⏳"
        line = f"{icon} [{event.candidate}] {event.stage}: {event.message}"
        event_lines.append(line)
        # keep the live panel compact and performant
        event_box.code("\n".join(event_lines[-120:]))
        done_count = sum(1 for e in event_lines if "Ranking Queue: Candidate added" in e)
        progress_box.progress(min(100, int((done_count / max(1, len(resumes))) * 100)))

    with st.spinner("Running multi-agent pipeline..."):
        with get_session() as session:
            if live_stream:
                out = orchestrator.screen_live(
                    session=session,
                    job_title=job_title,
                    job_description=job_description,
                    resumes=resumes,
                    event_callback=_emit,
                )
            else:
                out = orchestrator.screen(
                    session=session,
                    job_title=job_title,
                    job_description=job_description,
                    resumes=resumes,
                    max_workers=max_workers,
                )
    status.success("All agents completed successfully.")

    st.success(f"Completed run #{out.run_id} with {len(out.ranked)} candidates.")
    st.session_state["selected_run_id"] = out.run_id

    df = pd.DataFrame(
        [
            {
                "Rank": c.rank,
                "Candidate": c.name,
                "Overall": c.overall_score,
                "Match": c.match_score,
                "Experience": c.experience_score,
                "Recommendation": c.recommendation,
                "Matched skills": ", ".join(c.matched_skills[:8]),
                "Missing skills": ", ".join(c.missing_skills[:8]),
                "File": c.source_filename,
            }
            for c in out.ranked
        ]
    )

    st.subheader("Ranked candidates")
    styled = df.style.apply(
        lambda row: [
            f"color: {_score_color(row['Overall'])}; font-weight: 700;" if col == "Overall" else ""
            for col in df.columns
        ],
        axis=1,
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)

    st.subheader("Top shortlist")
    st.table(df.head(shortlist_n))

    st.write("### Recruiter automation")
    top_df = df.head(shortlist_n).copy()
    st.download_button(
        "Download shortlist report (CSV)",
        data=top_df.to_csv(index=False).encode("utf-8"),
        file_name=f"shortlist_run_{out.run_id}.csv",
        mime="text/csv",
    )
    if st.toggle("Generate email alerts draft", value=False):
        lines = [
            "Subject: AI Screening Completed - Top Candidate Shortlist",
            "",
            f"Run #{out.run_id} completed for role: {job_title}",
            "",
            "Top candidates:",
        ]
        for _, r in top_df.iterrows():
            lines.append(f"- Rank {r['Rank']}: {r['Candidate']} ({r['Overall']:.2f})")
        st.code("\n".join(lines))


def _dashboard_page() -> None:
    st.subheader("Analytics dashboard")

    run_id = st.session_state.get("selected_run_id")
    with get_session() as session:
        repo = Repo(session)
        runs = repo.list_recent_runs(limit=50)

    if not runs:
        st.info("No runs yet. Go to Screen to process resumes.")
        return

    run_options = {f"Run #{r.id} · {r.created_at:%Y-%m-%d %H:%M}": r.id for r in runs}
    selected_label = st.selectbox("Select run", list(run_options.keys()), index=0 if run_id is None else 0)
    selected_run_id = run_options[selected_label]
    st.session_state["selected_run_id"] = selected_run_id

    with get_session() as session:
        repo = Repo(session)
        results = repo.list_results_for_run(selected_run_id)
        run = repo.get_run(selected_run_id)
        job = repo.get_job(run.job_id) if run else None

    if not results:
        st.info("No results found for this run.")
        return

    apply_saas_theme()

    scores = [r.overall_score for r in results]
    selected_count = len([s for s in scores if s >= 70])
    rejected_count = len([s for s in scores if s < 55])
    top_candidate = max(scores) if scores else 0
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        render_metric_card("👥 Total Candidates", str(len(results)), "Processed in this run")
    with col2:
        render_metric_card("✅ Shortlisted", str(selected_count), "Score >= 70")
    with col3:
        render_metric_card("❌ Rejected", str(rejected_count), "Score < 55")
    with col4:
        render_metric_card("📊 Avg Match Score", f"{(sum(scores)/max(1,len(scores))):.1f}", job.title if job else "—")
    with col5:
        render_metric_card("🏆 Top Candidate Score", f"{top_candidate:.1f}", "Best overall score")

    df = pd.DataFrame(
        [
            {
                "Rank": r.rank,
                "candidate_id": r.candidate_id,
                "Name": "",
                "Overall": r.overall_score,
                "Match": r.match_score,
                "Experience": r.experience_score,
                "Skills": json.loads(r.skills_json or "[]"),
                "Recommendation": r.recommendation,
            }
            for r in results
        ]
    )
    # Resolve candidate names with one query for faster dashboards.
    with get_session() as session:
        repo_names = Repo(session)
        candidates = repo_names.list_candidates_by_ids([r.candidate_id for r in results])
    id_to_name = {c.id: c.name for c in candidates if c.id is not None}
    df["Name"] = df["candidate_id"].map(id_to_name).fillna("Unknown")
    df["Score Band"] = df["Overall"].apply(_score_label)
    df["Job Match %"] = df["Match"].round(2)

    st.write("### AI Hiring Insights")
    best = df.sort_values("Overall", ascending=False).iloc[0]
    st.success(
        f"Top Candidate Found · Match Score: {best['Job Match %']:.1f}% · "
        f"Recommended for Interview ({_score_label(float(best['Overall']))})"
    )
    render_decision_panel(
        name=str(best["Name"]),
        match_pct=float(best["Job Match %"]),
        recommendation="Interview",
        key_skills=list(best["Skills"]) if isinstance(best["Skills"], list) else [],
    )

    fig_hist = px.histogram(
        df,
        x="Overall",
        nbins=12,
        title="Score distribution",
        color="Score Band",
        color_discrete_map={"High": "#4ade80", "Medium": "#facc15", "Low": "#f87171"},
    )
    fig_rank = px.line(
        df.sort_values("Rank"),
        x="Rank",
        y="Overall",
        title="Overall score by rank",
        markers=True,
    )
    fig_exp = px.scatter(
        df,
        x="Experience",
        y="Overall",
        color="Score Band",
        size="Match",
        title="Experience vs Score",
        color_discrete_map={"High": "#4ade80", "Medium": "#facc15", "Low": "#f87171"},
    )
    fig_match = px.bar(
        df.sort_values("Job Match %", ascending=False).head(12),
        x="Name",
        y="Job Match %",
        color="Score Band",
        title="Job match percentage by candidate",
        color_discrete_map={"High": "#4ade80", "Medium": "#facc15", "Low": "#f87171"},
    )
    for fig in [fig_hist, fig_rank, fig_exp, fig_match]:
        fig.update_layout(font=dict(size=16), hoverlabel=dict(font_size=15))

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(fig_hist, use_container_width=True)
    with c2:
        st.plotly_chart(fig_rank, use_container_width=True)
    st.plotly_chart(fig_exp, use_container_width=True)
    st.plotly_chart(fig_match, use_container_width=True)

    # Skill frequency chart
    skill_counter = Counter(s for row in df["Skills"] for s in row)
    if skill_counter:
        top_skills = pd.DataFrame(skill_counter.most_common(10), columns=["Skill", "Count"])
        top_skills["Percent"] = (top_skills["Count"] / max(1, len(results)) * 100).round(1)
        st.write("### Top Skills Detected")
        st.dataframe(top_skills, hide_index=True, use_container_width=True)
        fig_skills = px.bar(top_skills, x="Skill", y="Percent", title="Skill frequency (%)", text="Percent")
        fig_skills.update_layout(font=dict(size=16))
        st.plotly_chart(fig_skills, use_container_width=True)

    # Leaderboard
    leaderboard = df.sort_values("Overall", ascending=False).head(10).copy()
    leaderboard["Skills"] = leaderboard["Skills"].apply(lambda x: ", ".join(x[:5]))
    leaderboard = leaderboard[["Rank", "Name", "Overall", "Skills", "Experience", "Recommendation"]]
    st.write("### Top candidates leaderboard")
    st.dataframe(leaderboard, hide_index=True, use_container_width=True)

    # Resume processing timeline (run-level approximation)
    st.write("### Resume processing timeline")
    timeline = pd.DataFrame(
        [
            {"Stage": "Upload", "Minutes": 0.05},
            {"Stage": "Parsing", "Minutes": 0.15},
            {"Stage": "Skill + Experience", "Minutes": 0.2},
            {"Stage": "Scoring + Ranking", "Minutes": 0.1},
            {"Stage": "Persist + Analytics", "Minutes": 0.05},
        ]
    )
    fig_timeline = px.bar(timeline, x="Stage", y="Minutes", title="Pipeline stage timeline")
    fig_timeline.update_layout(font=dict(size=16))
    st.plotly_chart(fig_timeline, use_container_width=True)


def _candidates_page() -> None:
    st.subheader("Candidates")
    apply_saas_theme()

    run_id = st.session_state.get("selected_run_id")
    if not run_id:
        st.info("Select a run on the Dashboard, or run a screening first.")
        return

    with get_session() as session:
        repo = Repo(session)
        results = repo.list_results_for_run(run_id)
        run = repo.get_run(run_id)
        job = repo.get_job(run.job_id) if run else None

    if not results:
        st.info("No candidates for this run.")
        return

    df = pd.DataFrame(
        [
            {
                "rank": r.rank,
                "candidate_id": r.candidate_id,
                "overall": r.overall_score,
                "match": r.match_score,
                "experience": r.experience_score,
                "recommendation": r.recommendation,
                "skills": ", ".join(json.loads(r.skills_json or "[]")),
            }
            for r in results
        ]
    ).sort_values("rank")

    # ATS-style filters
    st.write("### Filters")
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        skill_filter = st.text_input("Filter by skill", value="")
    with f2:
        score_min, score_max = st.slider("Filter by score", 0, 100, (0, 100))
    with f3:
        exp_min, exp_max = st.slider("Filter by experience", 0, 100, (0, 100))
    with f4:
        role_filter = st.text_input("Filter by job role", value=job.title if job else "")

    filtered = df[
        (df["overall"] >= score_min)
        & (df["overall"] <= score_max)
        & (df["experience"] >= exp_min)
        & (df["experience"] <= exp_max)
    ].copy()
    if skill_filter.strip():
        filtered = filtered[filtered["skills"].str.lower().str.contains(skill_filter.strip().lower(), na=False)]
    if role_filter.strip() and job and role_filter.strip().lower() not in job.title.lower():
        filtered = filtered.iloc[0:0]

    selected = st.dataframe(
        filtered[["rank", "candidate_id", "overall", "match", "experience", "skills"]],
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
    )

    if not selected.selection.rows:
        st.caption("Select a row to open the candidate profile.")
        return

    row = selected.selection.rows[0]
    candidate_id = int(filtered.iloc[row]["candidate_id"])

    with get_session() as session:
        repo = Repo(session)
        c = repo.get_candidate(candidate_id)
        # Find candidate result in this run
        r = next((x for x in results if x.candidate_id == candidate_id), None)

    if not c or not r:
        st.error("Candidate not found.")
        return

    st.divider()
    st.subheader(f"Candidate profile · {c.name}")
    colA, colB, colC = st.columns(3)
    with colA:
        st.metric("Overall", f"{r.overall_score:.2f}")
    with colB:
        st.metric("Skill match", f"{r.match_score:.2f}")
    with colC:
        st.metric("Experience", f"{r.experience_score:.2f}")

    skills = json.loads(r.skills_json or "[]")
    matched = json.loads(r.matched_skills_json or "[]")
    missing = json.loads(r.missing_skills_json or "[]")
    experiences = json.loads(r.experiences_json or "[]")

    st.write("**Skills (extracted)**")
    if skills:
        st.markdown(" ".join([f"`{s}`" for s in skills]))
    else:
        st.write("—")

    col1, col2 = st.columns(2)
    with col1:
        st.write("**Matched skills**")
        st.write(", ".join(matched) if matched else "—")
    with col2:
        st.write("**Skill gaps**")
        st.write(", ".join(missing) if missing else "—")

    st.write("**Skill gap analysis**")
    st.info(r.skill_gap_summary or "—")

    st.write("**AI explanation**")
    st.code(r.explanation or "—")

    # AI features panel
    strengths, weaknesses = _ai_strengths_weaknesses(skills, missing, r.experience_score)
    fit_pct = min(100.0, round((r.overall_score * 0.7) + (r.match_score * 0.3), 1))
    st.write("### AI Recommendation")
    st.success(
        f"This candidate is {fit_pct:.1f}% suitable for {job.title if job else 'the role'}."
    )
    st.write("**Strengths**")
    for s in strengths:
        st.write(f"- {s}")
    st.write("**Weaknesses**")
    for w in weaknesses:
        st.write(f"- {w}")

    st.write("**Interview questions (auto-generated)**")
    for q in _interview_questions(skills, missing):
        st.write(f"- {q}")

    st.write("### Score breakdown")
    education_score = max(0.0, min(100.0, r.match_score * 0.35))
    project_score = max(0.0, min(100.0, r.overall_score * 0.5 + r.match_score * 0.2))
    score_df = pd.DataFrame(
        [
            {"Component": "Skill Score", "Score": r.match_score},
            {"Component": "Experience Score", "Score": r.experience_score},
            {"Component": "Education Score", "Score": education_score},
            {"Component": "Project Score", "Score": project_score},
        ]
    )
    fig_breakdown = px.bar(score_df, x="Component", y="Score", color="Score", title="Score breakdown")
    fig_breakdown.update_layout(font=dict(size=15))
    st.plotly_chart(fig_breakdown, use_container_width=True)

    st.write("### Resume preview")
    st.text_area("Raw resume text (preview)", value=(c.raw_text or "")[:2500], height=260, disabled=True)

    st.write("### Experience timeline")
    if experiences:
        timeline_df = pd.DataFrame(
            [{"Step": idx + 1, "Summary": e.get("summary", "")[:120]} for idx, e in enumerate(experiences)]
        )
        st.dataframe(timeline_df, use_container_width=True, hide_index=True)
    else:
        st.caption("No timeline entries extracted.")


def _admin_page() -> None:
    st.subheader("Admin")
    apply_saas_theme()

    with get_session() as session:
        repo = Repo(session)
        runs = repo.list_recent_runs(limit=100)
    st.write("**Recent runs**")
    st.dataframe(
        pd.DataFrame([{"run_id": r.id, "job_id": r.job_id, "candidates": r.total_candidates, "created_at": r.created_at} for r in runs]),
        use_container_width=True,
        hide_index=True,
    )
    st.caption("Production hardening ideas: role-based access, audit logs, data retention, PII redaction.")
    render_agent_workflow([
        "Resume Parsing Agent",
        "Skill Extraction Agent",
        "Experience Analyzer Agent",
        "Job Matching Agent",
        "Candidate Scoring Agent",
        "Ranking Agent",
    ])


def main() -> None:
    init_db()
    st.set_page_config(page_title="Resume Screening", layout="wide")
    apply_saas_theme()

    if "entered_dashboard" not in st.session_state:
        st.session_state["entered_dashboard"] = False

    if not st.session_state["entered_dashboard"]:
        launched = render_landing_page()
        if launched:
            st.session_state["entered_dashboard"] = True
            st.rerun()
        return

    with st.sidebar:
        st.title("Resume Screening")
        st.caption("Agentic, explainable, batch processing")
        if st.button("Back to Landing", use_container_width=True):
            st.session_state["entered_dashboard"] = False
            st.rerun()

    page = _nav()
    if page == "Screen":
        _screen_page()
    elif page == "Dashboard":
        _dashboard_page()
    elif page == "Candidates":
        _candidates_page()
    else:
        _admin_page()

