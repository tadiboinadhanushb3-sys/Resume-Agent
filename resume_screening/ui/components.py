from __future__ import annotations

import streamlit as st


def render_metric_card(title: str, metric: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
<div class="card">
  <h3>{title}</h3>
  <p class="metric">{metric}</p>
  <p class="muted">{subtitle}</p>
</div>
""",
        unsafe_allow_html=True,
    )


def render_agent_workflow(steps: list[str], *, animated: bool = False) -> None:
    st.write("### Agent Workflow")
    st.caption("Resume Parsing -> Skill Extraction -> Experience Analysis -> Job Matching -> Candidate Scoring -> Ranking")
    if not animated:
        for step in steps:
            st.progress(100, text=step)
        return
    status = st.empty()
    progress = st.progress(0)
    total = max(1, len(steps))
    for idx, step in enumerate(steps, start=1):
        status.info(f"{step}...")
        progress.progress(int((idx / total) * 100))
    status.success("All agents completed successfully.")


def render_decision_panel(*, name: str, match_pct: float, recommendation: str, key_skills: list[str]) -> None:
    st.write("### AI Decision Panel")
    st.success(
        f"Top Candidate Found: {name} | Match Score: {match_pct:.1f}% | "
        f"Recommended: {recommendation} | Key Skills: {', '.join(key_skills[:5]) or 'N/A'}"
    )

