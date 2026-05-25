"""Evidence Room page — view and analyze all evidence."""

import streamlit as st


def render():
    """Render the Evidence Room page."""
    st.markdown("""
    <div class="lex-hero" style="margin-bottom:1.5rem;">
      <div class="lex-page-title">🔍 Evidence <span class="gold">Room</span></div>
      <div class="lex-page-subtitle">Analyze documents, images, and audio testimony</div>
    </div>
    """, unsafe_allow_html=True)

    analyses = st.session_state.get("evidence_analyses", [])

    if not analyses:
        st.markdown("""
        <div style="background:rgba(255,255,255,0.02);border:2px dashed rgba(201,168,76,0.2);
             border-radius:12px;padding:3rem;text-align:center;">
          <div style="font-size:3rem;margin-bottom:1rem;">🔍</div>
          <div style="font-size:16px;font-weight:600;color:#f3f4f6;margin-bottom:8px;">No Evidence Loaded</div>
          <div style="font-size:13px;color:#9ca3af;">
            Go to <strong>Case Dashboard</strong> and upload documents to analyze them here.
          </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Filter controls ─────────────────────────────────────────────────
    col_filter1, col_filter2, col_filter3 = st.columns([2, 1, 1])
    with col_filter1:
        filter_type = st.selectbox("Filter by type", ["All", "PDF", "IMAGE", "AUDIO", "DOCX", "TEXT"])
    with col_filter2:
        sort_by = st.selectbox("Sort by", ["Evidence Strength ↓", "Name A-Z", "Type"])
    with col_filter3:
        st.markdown("<br>", unsafe_allow_html=True)
        show_matrix = st.checkbox("Show Evidence Matrix")

    # Filter
    filtered = analyses
    if filter_type != "All":
        filtered = [a for a in analyses if a.get("doc_type", "").upper() == filter_type]

    # Sort
    if sort_by == "Evidence Strength ↓":
        filtered.sort(key=lambda x: x.get("evidence_strength", 5), reverse=True)
    elif sort_by == "Name A-Z":
        filtered.sort(key=lambda x: x.get("file_name", ""))
    elif sort_by == "Type":
        filtered.sort(key=lambda x: x.get("doc_type", ""))

    st.markdown(f"**{len(filtered)} evidence items** {f'(filtered from {len(analyses)})' if len(filtered) < len(analyses) else ''}")
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Evidence list + viewer ──────────────────────────────────────────
    left_col, right_col = st.columns([1, 2])

    with left_col:
        st.markdown("#### Evidence List")
        selected_idx = None
        for i, ev in enumerate(filtered):
            strength = ev.get("evidence_strength", 5)
            doc_type = ev.get("doc_type", "unknown")
            badge_cls = {"pdf": "badge-doc", "docx": "badge-doc", "image": "badge-image",
                         "audio": "badge-audio"}.get(doc_type, "badge-doc")
            strength_cls = "strength-high" if strength >= 7 else "strength-med" if strength >= 4 else "strength-low"

            clicked = st.button(
                f"{'📄' if doc_type in ('pdf','docx','text') else '🖼' if doc_type == 'image' else '🎵'} "
                f"{ev.get('file_name', 'Unknown')[:30]}",
                key=f"ev_{i}",
                use_container_width=True,
            )
            if clicked:
                st.session_state["selected_evidence_idx"] = i

            st.markdown(f"""
            <div style="display:flex;gap:6px;margin:-8px 0 6px 0;padding-left:4px;">
              <span class="evidence-type-badge {badge_cls}">{doc_type.upper()}</span>
              <span class="evidence-strength {strength_cls}">{strength}/10</span>
            </div>
            """, unsafe_allow_html=True)

    with right_col:
        sel_idx = st.session_state.get("selected_evidence_idx", 0)
        if filtered and sel_idx < len(filtered):
            _render_evidence_detail(filtered[sel_idx])
        elif filtered:
            _render_evidence_detail(filtered[0])

    # ── Evidence Matrix ─────────────────────────────────────────────────
    if show_matrix:
        st.markdown("---")
        st.markdown("#### Evidence × Charges Matrix")
        _render_evidence_matrix(analyses)


def _render_evidence_detail(ev: dict):
    """Render detailed analysis for a selected evidence item."""
    doc_type = ev.get("doc_type", "unknown")
    strength = ev.get("evidence_strength", 5)

    st.markdown(f"""
    <div class="lex-card">
      <div class="lex-card-header">
        <span style="font-size:16px;">
          {'📄' if doc_type in ('pdf','docx','text') else '🖼' if doc_type == 'image' else '🎵'}
        </span>
        <span class="lex-card-title">{ev.get('file_name', 'Unknown')}</span>
        <span class="evidence-strength {'strength-high' if strength >= 7 else 'strength-med' if strength >= 4 else 'strength-low'}" style="margin-left:auto;">
          Strength: {strength}/10
        </span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📝 Content", "🔍 Entities", "⚖ Legal Analysis"])

    with tab1:
        if doc_type == "image":
            vision = ev.get("vision_analysis", {})
            if vision.get("description"):
                st.markdown("**AI Vision Analysis:**")
                st.info(vision.get("description", ""))
            ocr = ev.get("ocr_text", "")
            if ocr:
                st.markdown("**OCR Text:**")
                st.text_area("", ocr[:1000], height=150, label_visibility="collapsed")
        elif doc_type == "audio":
            transcript = ev.get("transcript", ev.get("text", ""))
            if transcript:
                st.markdown("**Transcript:**")
                st.text_area("", transcript[:2000], height=200, label_visibility="collapsed")
        else:
            text = ev.get("text", "")
            if text:
                st.text_area("Extracted Text", text[:3000], height=250)

    with tab2:
        entities = ev.get("entities", {})
        if entities:
            cols = st.columns(2)
            entity_items = [
                ("👤 Persons", entities.get("persons", [])),
                ("🏢 Organizations", entities.get("organizations", [])),
                ("📍 Locations", entities.get("locations", [])),
                ("📅 Dates", entities.get("dates", [])),
                ("💰 Amounts", entities.get("money", [])),
                ("📋 IPC Sections", entities.get("ipc_sections", [])),
            ]
            for i, (label, items) in enumerate(entity_items):
                with cols[i % 2]:
                    if items:
                        st.markdown(f"**{label}**")
                        for item in items[:5]:
                            st.markdown(f"• {item}")
        else:
            st.info("No entities extracted. Upload a document with text content.")

    with tab3:
        charges = ev.get("legal_charges", [])
        summary = ev.get("summary", "")

        if summary:
            st.markdown("**Document Summary:**")
            st.info(summary)

        if charges:
            st.markdown("**Identified Legal Sections:**")
            for c in charges:
                st.markdown(f"""
                <div class="legal-cite">
                  <span class="cite-icon">§</span>
                  <div>
                    <div class="cite-case">{c.get('section', '')}</div>
                    <div class="cite-principle">{c.get('context', '')[:100]}</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

        vision = ev.get("vision_analysis", {})
        if vision.get("legal_relevance"):
            st.markdown("**Legal Relevance:**")
            st.markdown(vision["legal_relevance"])


def _render_evidence_matrix(analyses: list):
    """Render color-coded evidence vs charges matrix."""
    import pandas as pd

    active_case = st.session_state.get("active_case")
    cases = st.session_state.get("cases", {})
    case_data = cases.get(active_case, {})
    charges = case_data.get("metadata", {}).get("charges", ["Primary Charge"])

    matrix_data = {}
    for ev in analyses:
        name = ev.get("file_name", "Unknown")
        strength = ev.get("evidence_strength", 5)
        matrix_data[name] = {}
        for charge in charges:
            status = "✅ Supports" if strength >= 6 else "⚪ Neutral" if strength >= 4 else "❌ Contradicts"
            matrix_data[name][charge[:25]] = status

    if matrix_data:
        df = pd.DataFrame(matrix_data).T
        st.dataframe(df, use_container_width=True)
