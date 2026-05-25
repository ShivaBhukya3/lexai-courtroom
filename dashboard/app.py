"""LexAI Dashboard — Main Streamlit entry point."""

import sys
import json
from pathlib import Path

import streamlit as st

# Add project root to Python path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# ── Page config (must be first Streamlit call) ──────────────────────────
st.set_page_config(
    page_title="LexAI — Courtroom Intelligence",
    page_icon="⚖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject CSS ─────────────────────────────────────────────────────────
css_path = Path(__file__).parent / "assets" / "custom.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# ── Session state initialization ────────────────────────────────────────
if "active_case" not in st.session_state:
    st.session_state.active_case = None
if "cases" not in st.session_state:
    st.session_state.cases = _load_sample_cases()
if "evidence_analyses" not in st.session_state:
    st.session_state.evidence_analyses = []
if "prosecution_args" not in st.session_state:
    st.session_state.prosecution_args = {}
if "defense_args" not in st.session_state:
    st.session_state.defense_args = {}
if "verdict_prediction" not in st.session_state:
    st.session_state.verdict_prediction = {}


def _load_sample_cases() -> dict:
    """Load sample cases from disk."""
    cases = {}
    cases_dir = ROOT / "data" / "cases" / "sample_cases"
    if not cases_dir.exists():
        return cases
    for case_dir in cases_dir.iterdir():
        meta_path = case_dir / "case_metadata.json"
        if meta_path.exists():
            try:
                with open(meta_path, encoding="utf-8") as f:
                    meta = json.load(f)
                cases[meta["case_id"]] = {"metadata": meta, "dir": str(case_dir)}
            except Exception:
                pass
    return cases


# ── Sidebar ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding: 1.5rem 0 1rem;">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
        <div style="width:32px;height:32px;background:linear-gradient(135deg,#c9a84c,#f0d060);
             border-radius:6px;display:flex;align-items:center;justify-content:center;
             font-size:16px;color:#000;font-weight:900;">⚖</div>
        <div>
          <div style="font-size:18px;font-weight:700;color:#f3f4f6;letter-spacing:-0.02em;">
            Lex<span style="color:#c9a84c;">AI</span>
          </div>
          <div style="font-size:10px;color:#4b5563;text-transform:uppercase;letter-spacing:1px;">
            Courtroom Intelligence
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Active Case**")

    case_options = ["— Select a Case —"] + list(st.session_state.cases.keys())
    selected = st.selectbox("Case", case_options, label_visibility="collapsed")

    if selected and selected != "— Select a Case —":
        st.session_state.active_case = selected
        meta = st.session_state.cases[selected]["metadata"]
        st.markdown(f"""
        <div style="background:rgba(201,168,76,0.07);border:1px solid rgba(201,168,76,0.2);
             border-radius:8px;padding:10px 14px;margin-top:8px;">
          <div style="font-size:11px;color:#c9a84c;font-weight:700;text-transform:uppercase;
               letter-spacing:1px;margin-bottom:6px;">Active</div>
          <div style="font-size:13px;color:#f3f4f6;font-weight:600;">{meta.get('case_id','')}</div>
          <div style="font-size:11px;color:#9ca3af;margin-top:2px;">
            {meta.get('case_type','')} — {meta.get('court','')[:30]}
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="font-size:11px;color:#4b5563;text-align:center;padding:8px 0;">
      <div>LexAI v1.0.0</div>
      <div style="margin-top:4px;">Powered by RAG + GPT-4V + Whisper</div>
    </div>
    """, unsafe_allow_html=True)


# ── Main content ─────────────────────────────────────────────────────────
st.markdown("""
<div class="lex-hero">
  <div class="lex-page-title">⚖ Lex<span class="gold">AI</span> Courtroom Intelligence</div>
  <div class="lex-page-subtitle">
    Multimodal AI Platform — Document Analysis · Evidence Processing · Verdict Prediction · Argument Generation
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Navigation tabs ───────────────────────────────────────────────────────
tabs = st.tabs([
    "🏛 Case Dashboard",
    "🔍 Evidence Room",
    "⚔ Argument Studio",
    "🎯 Verdict Predictor",
    "📚 Legal Research",
    "📅 Case Timeline",
])

with tabs[0]:
    from dashboard.pages.case_dashboard import render
    render()

with tabs[1]:
    from dashboard.pages.evidence_room import render
    render()

with tabs[2]:
    from dashboard.pages.argument_studio import render
    render()

with tabs[3]:
    from dashboard.pages.verdict_predictor import render
    render()

with tabs[4]:
    from dashboard.pages.legal_research import render
    render()

with tabs[5]:
    from dashboard.pages.case_timeline import render
    render()
