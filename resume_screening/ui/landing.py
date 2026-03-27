from __future__ import annotations

import time

import streamlit as st


def render_landing_page() -> bool:
    st.markdown(
        """
<div class="hero-wrap">
  <div class="hero-glow"></div>
  <h1 class="hero-title">AI Resume Intelligence Platform</h1>
  <p class="hero-subtitle">Automated hiring powered by intelligent AI agents</p>
</div>
""",
        unsafe_allow_html=True,
    )

    launch = st.button("Launch Dashboard", type="primary", use_container_width=False)

    st.markdown(
        """
<div class="workflow-wrap">
  <h3>Animated AI Workflow</h3>
  <div class="wf-line">
    <span class="wf-node">Resume Upload</span>
    <span class="wf-arrow">→</span>
    <span class="wf-node">Parsing</span>
    <span class="wf-arrow">→</span>
    <span class="wf-node">Skill Extraction</span>
    <span class="wf-arrow">→</span>
    <span class="wf-node">Job Matching</span>
    <span class="wf-arrow">→</span>
    <span class="wf-node">Candidate Ranking</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("### Features")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown('<div class="feature-card">Agentic AI Processing</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="feature-card">Resume Understanding</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="feature-card">Skill Intelligence</div>', unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="feature-card">Candidate Ranking</div>', unsafe_allow_html=True)
    with c5:
        st.markdown('<div class="feature-card">Hiring Insights</div>', unsafe_allow_html=True)

    st.markdown("### How It Works")
    steps = st.columns(4)
    labels = [
        "Step 1: Upload Resume",
        "Step 2: AI Analysis",
        "Step 3: Candidate Score",
        "Step 4: Hiring Recommendation",
    ]
    for col, label in zip(steps, labels):
        with col:
            st.markdown(f'<div class="step-card">{label}</div>', unsafe_allow_html=True)

    if launch:
        _cinematic_loader()
        return True
    return False


def _cinematic_loader() -> None:
    st.markdown("### Initializing Platform")
    text = st.empty()
    prog = st.progress(0)
    messages = [
        "Initializing AI Agents",
        "Loading Resume Parser",
        "Analyzing Candidate Skills",
        "Generating Hiring Insights",
    ]
    for i, msg in enumerate(messages, start=1):
        text.markdown(f"#### {msg}")
        prog.progress(int((i / len(messages)) * 100))
        time.sleep(0.6)
    st.success("AI Recruitment Platform Ready")

