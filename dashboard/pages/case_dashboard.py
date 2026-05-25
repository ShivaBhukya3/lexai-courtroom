"""Case Dashboard page — overview, KPIs, file upload."""

import json
import time
from pathlib import Path
import streamlit as st


def render():
    """Render the Case Dashboard page."""

    # ── KPI Row ────────────────────────────────────────────────────────
    cases = st.session_state.get("cases", {})
    evidence = st.session_state.get("evidence_analyses", [])
    verdict = st.session_state.get("verdict_prediction", {})

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div class="lex-kpi">
          <div class="lex-kpi-val">{}</div>
          <div class="lex-kpi-label">Active Cases</div>
        </div>
        """.format(len(cases)), unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="lex-kpi">
          <div class="lex-kpi-val">{}</div>
          <div class="lex-kpi-label">Evidence Items</div>
        </div>
        """.format(len(evidence) if evidence else "—"), unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="lex-kpi">
          <div class="lex-kpi-val">28</div>
          <div class="lex-kpi-label">Precedents Found</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        conf = verdict.get("conviction_probability", 0)
        conf_str = f"{conf*100:.0f}%" if conf else "—"
        st.markdown("""
        <div class="lex-kpi">
          <div class="lex-kpi-val">{}</div>
          <div class="lex-kpi-label">Verdict Confidence</div>
        </div>
        """.format(conf_str), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Case selector / overview ────────────────────────────────────────
    left, right = st.columns([1, 1])

    with left:
        st.markdown("### 📁 Case File Upload")
        uploaded = st.file_uploader(
            "Drop PDFs, images, or audio files",
            accept_multiple_files=True,
            type=["pdf", "docx", "txt", "jpg", "jpeg", "png", "mp3", "wav", "mp4"],
            help="Supports: PDF, DOCX, JPG, PNG, MP3, WAV",
        )

        if uploaded:
            active_case = st.session_state.get("active_case")
            if not active_case:
                st.warning("⚠ Please select an active case from the sidebar first.")
            else:
                process_btn = st.button("🚀 Process All Files", use_container_width=True)
                if process_btn:
                    _process_uploads(uploaded, active_case)

    with right:
        st.markdown("### 📋 Case Overview")
        active_case = st.session_state.get("active_case")
        if not active_case:
            st.info("👈 Select a case from the sidebar to view details.")
        else:
            case_data = st.session_state.cases.get(active_case, {})
            meta = case_data.get("metadata", {})
            _render_case_overview(meta)

    st.markdown("---")

    # ── Documents processed ─────────────────────────────────────────────
    st.markdown("### 📄 Processed Documents")
    if evidence:
        _render_documents_table(evidence)
    else:
        st.markdown("""
        <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);
             border-radius:10px;padding:2rem;text-align:center;color:#4b5563;">
          <div style="font-size:2rem;margin-bottom:0.5rem;">📂</div>
          <div style="font-size:13px;">No documents processed yet.</div>
          <div style="font-size:11px;margin-top:4px;">Upload files above to begin analysis.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Quick actions ───────────────────────────────────────────────────
    st.markdown("### ⚡ Quick Actions")
    qa1, qa2, qa3, qa4 = st.columns(4)
    with qa1:
        if st.button("⚔ Generate Arguments", use_container_width=True):
            st.session_state["_tab_switch"] = "arguments"
            st.info("Navigate to **Argument Studio** tab.")
    with qa2:
        if st.button("🎯 Predict Verdict", use_container_width=True):
            st.info("Navigate to **Verdict Predictor** tab.")
    with qa3:
        if st.button("📚 Find Precedents", use_container_width=True):
            st.info("Navigate to **Legal Research** tab.")
    with qa4:
        if st.button("📊 Download Report", use_container_width=True):
            _generate_report()


def _process_uploads(uploaded_files, case_id: str):
    """Process uploaded files with progress tracking."""
    ROOT = Path(__file__).parent.parent.parent
    upload_dir = ROOT / "data" / "cases" / "uploaded" / case_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    progress = st.progress(0, text="Initializing...")
    analyses = []

    try:
        from src.document_processor import MultimodalDocumentProcessor
        processor = MultimodalDocumentProcessor()
    except Exception as e:
        st.error(f"Processor initialization failed: {e}")
        return

    for i, file in enumerate(uploaded_files):
        pct = int((i / len(uploaded_files)) * 100)
        progress.progress(pct, text=f"Processing: {file.name}")

        file_path = upload_dir / file.name
        with open(file_path, "wb") as f:
            f.write(file.read())

        try:
            result = processor.process_document(str(file_path))
            analyses.append(result)
            st.success(f"✓ {file.name} — {result.get('doc_type', 'processed').upper()}")
        except Exception as e:
            st.error(f"✗ {file.name}: {e}")

    progress.progress(100, text="Complete!")
    st.session_state.evidence_analyses = analyses
    st.balloons()
    st.success(f"✅ Processed {len(analyses)} documents successfully!")


def _render_case_overview(meta: dict):
    """Render structured case overview card."""
    charges = meta.get("charges", [])
    status = meta.get("status", "Active")

    status_color = {"Active": "#6ee7b7", "Closed": "#9ca3af", "Pending": "#fcd34d"}.get(status, "#9ca3af")
    status_bg = {"Active": "rgba(5,122,85,0.2)", "Closed": "rgba(107,114,128,0.2)", "Pending": "rgba(245,158,11,0.2)"}.get(status, "rgba(107,114,128,0.2)")

    plaintiff = meta.get("plaintiff", meta.get("complainant", {}))
    if isinstance(plaintiff, dict):
        plaintiff = plaintiff.get("name", "N/A")
    defendant = meta.get("defendant", meta.get("accused", {}))
    if isinstance(defendant, dict):
        defendant = defendant.get("name", "N/A")

    st.markdown(f"""
    <div class="lex-card">
      <div class="lex-card-body">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;">
          <div>
            <div style="font-size:15px;font-weight:700;color:#f3f4f6;">{meta.get('case_id','N/A')}</div>
            <div style="font-size:11px;color:#9ca3af;margin-top:2px;">{meta.get('court','')}</div>
          </div>
          <span style="background:{status_bg};color:{status_color};font-size:10px;font-weight:700;
               padding:4px 10px;border-radius:100px;text-transform:uppercase;letter-spacing:1px;">
            {status}
          </span>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:12px;margin-bottom:12px;">
          <div><span style="color:#4b5563;">Plaintiff:</span> <span style="color:#f3f4f6;">{plaintiff}</span></div>
          <div><span style="color:#4b5563;">Defendant:</span> <span style="color:#f3f4f6;">{defendant}</span></div>
          <div><span style="color:#4b5563;">Filing Date:</span> <span style="color:#f3f4f6;">{meta.get('filing_date','N/A')}</span></div>
          <div><span style="color:#4b5563;">Next Hearing:</span> <span style="color:#f3f4f6;">{meta.get('next_hearing','N/A')}</span></div>
        </div>
        <div style="font-size:11px;color:#4b5563;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">Charges</div>
        {"".join(f'<div style="font-size:12px;color:#c9a84c;margin-bottom:3px;">• {c}</div>' for c in charges)}
      </div>
    </div>
    """, unsafe_allow_html=True)


def _render_documents_table(analyses: list):
    """Render a table of processed documents."""
    import pandas as pd

    rows = []
    for a in analyses:
        strength = a.get("evidence_strength", 5)
        entities = a.get("entities", {})
        persons = ", ".join(entities.get("persons", [])[:2]) if entities else ""
        rows.append({
            "File": a.get("file_name", "Unknown"),
            "Type": a.get("doc_type", "").upper(),
            "Strength": f"{strength}/10",
            "Words": a.get("word_count", 0),
            "Key Persons": persons or "—",
            "Summary": str(a.get("summary", ""))[:80] + "...",
        })

    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)


def _generate_report():
    """Generate and offer HTML report download."""
    active_case = st.session_state.get("active_case")
    if not active_case:
        st.warning("Select a case first.")
        return

    try:
        from src.report_generator import LegalReportGenerator
        from src.timeline_builder import TimelineBuilder

        case_data = st.session_state.cases.get(active_case, {})
        gen = LegalReportGenerator()
        builder = TimelineBuilder()
        timeline = builder.build_from_case_data(case_data, st.session_state.evidence_analyses or [])

        html = gen.generate_full_case_report(
            case_data=case_data,
            prosecution_args=st.session_state.get("prosecution_args", {}),
            defense_args=st.session_state.get("defense_args", {}),
            verdict_prediction=st.session_state.get("verdict_prediction", {}),
            timeline=timeline,
            evidence_list=st.session_state.get("evidence_analyses", []),
        )
        st.download_button(
            "⬇ Download Full Case Report (HTML)",
            html,
            file_name=f"LexAI_Report_{active_case}.html",
            mime="text/html",
        )
    except Exception as e:
        st.error(f"Report generation failed: {e}")
