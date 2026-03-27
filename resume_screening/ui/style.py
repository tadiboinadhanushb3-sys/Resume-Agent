from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st


def _encode_file(path: str) -> str:
    data = Path(path).read_bytes()
    return base64.b64encode(data).decode("utf-8")


def apply_saas_theme(*, background_image_path: str | None = None) -> None:
    bg_css = ""
    if background_image_path:
        try:
            b64 = _encode_file(background_image_path)
            bg_css = f"""
            .stApp {{
              background-image: linear-gradient(rgba(10,10,15,0.72), rgba(10,10,15,0.72)), url("data:image/png;base64,{b64}");
              background-size: cover;
              background-attachment: fixed;
              background-position: center;
            }}
            """
        except Exception:
            bg_css = ""
    else:
        bg_css = """
        .stApp {
          background: radial-gradient(circle at top right, #1d2a56 0%, #0b1020 45%, #070a14 100%);
        }
        """

    st.markdown(
        f"""
<style>
{bg_css}
section[data-testid="stSidebar"] {{
  border-right: 1px solid rgba(255,255,255,0.08);
  background: linear-gradient(180deg, rgba(90,74,255,0.35) 0%, rgba(20,30,60,0.35) 52%, rgba(8,12,24,0.40) 100%);
}}
.card {{
  padding: 16px 18px;
  border-radius: 14px;
  border: 1px solid rgba(255,255,255,0.10);
  background: linear-gradient(135deg, rgba(124,58,237,0.20) 0%, rgba(35,120,255,0.12) 45%, rgba(22,24,30,0.72) 100%);
  backdrop-filter: blur(8px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.28);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}}
.card:hover {{
  transform: translateY(-4px);
  box-shadow: 0 14px 38px rgba(80, 70, 220, 0.35);
}}
.card h3 {{
  margin: 0 0 6px 0;
  font-size: 16px;
  opacity: 0.86;
}}
.card .metric {{
  font-size: 34px;
  font-weight: 700;
  margin: 0;
  animation: pulseGlow 2.8s ease-in-out infinite;
}}
.muted {{
  opacity: 0.72;
}}
div[data-testid="stMetricValue"] {{
  font-size: 1.35rem;
}}
button[kind="primary"], .stDownloadButton button {{
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}}
button[kind="primary"]:hover, .stDownloadButton button:hover {{
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(124,58,237,0.4);
}}
.score-high {{ color: #4ade80; font-weight: 700; }}
.score-mid {{ color: #facc15; font-weight: 700; }}
.score-low {{ color: #f87171; font-weight: 700; }}
@keyframes pulseGlow {{
  0%, 100% {{ opacity: 1; text-shadow: 0 0 0 rgba(124,58,237,0.0); }}
  50% {{ opacity: 0.92; text-shadow: 0 0 18px rgba(124,58,237,0.45); }}
}}
.hero-wrap {{
  text-align: center;
  padding: 60px 20px 32px 20px;
  position: relative;
}}
.hero-glow {{
  width: 340px;
  height: 340px;
  border-radius: 50%;
  margin: 0 auto;
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  top: 0;
  background: radial-gradient(circle, rgba(124,58,237,0.35) 0%, rgba(124,58,237,0.05) 45%, rgba(124,58,237,0) 70%);
  filter: blur(18px);
  animation: floatGlow 4.5s ease-in-out infinite;
}}
.hero-title {{
  font-size: 3rem;
  line-height: 1.12;
  margin-bottom: 10px;
  letter-spacing: 0.3px;
  position: relative;
}}
.hero-subtitle {{
  font-size: 1.2rem;
  opacity: 0.86;
  position: relative;
}}
.workflow-wrap {{
  margin: 22px 0 26px 0;
  padding: 16px;
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.10);
  background: rgba(17, 20, 30, 0.58);
}}
.wf-line {{
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  justify-content: center;
  padding-top: 8px;
}}
.wf-node {{
  border: 1px solid rgba(124,58,237,0.55);
  border-radius: 999px;
  padding: 8px 14px;
  background: rgba(124,58,237,0.14);
  box-shadow: 0 0 20px rgba(124,58,237,0.25);
  animation: nodePulse 2.2s ease-in-out infinite;
}}
.wf-arrow {{
  font-size: 1.2rem;
  opacity: 0.8;
  animation: arrowFlow 1.6s linear infinite;
}}
.feature-card {{
  border-radius: 14px;
  border: 1px solid rgba(255,255,255,0.12);
  background: rgba(20,22,28,0.6);
  padding: 14px 10px;
  text-align: center;
  min-height: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}}
.feature-card:hover {{
  transform: translateY(-3px);
  box-shadow: 0 10px 24px rgba(40,60,160,0.35);
}}
.step-card {{
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.12);
  background: linear-gradient(135deg, rgba(20,28,60,0.45) 0%, rgba(22,24,30,0.65) 100%);
  padding: 14px 12px;
  min-height: 68px;
}}
@keyframes floatGlow {{
  0%, 100% {{ transform: translateX(-50%) translateY(0px); }}
  50% {{ transform: translateX(-50%) translateY(8px); }}
}}
@keyframes nodePulse {{
  0%, 100% {{ box-shadow: 0 0 10px rgba(124,58,237,0.22); }}
  50% {{ box-shadow: 0 0 24px rgba(124,58,237,0.42); }}
}}
@keyframes arrowFlow {{
  0% {{ opacity: 0.35; }}
  50% {{ opacity: 1; }}
  100% {{ opacity: 0.35; }}
}}
</style>
""",
        unsafe_allow_html=True,
    )

