"""Case Timeline page — visual chronological event display."""

import streamlit as st


def render():
    """Render the Case Timeline page."""
    st.markdown("""
    <div class="lex-hero" style="margin-bottom:1.5rem;">
      <div class="lex-page-title">📅 Case <span class="gold">Timeline</span></div>
      <div class="lex-page-subtitle">Chronological reconstruction of all case events from documents</div>
    </div>
    """, unsafe_allow_html=True)

    active_case = st.session_state.get("active_case")
    if not active_case:
        st.warning("👈 Please select a case from the sidebar.")
        return

    case_data = st.session_state.get("cases", {}).get(active_case, {})
    evidence = st.session_state.get("evidence_analyses", [])

    # ── Build timeline ──────────────────────────────────────────────────
    with st.spinner("Building chronological timeline..."):
        try:
            from src.timeline_builder import TimelineBuilder
            builder = TimelineBuilder()
            timeline = builder.build_from_case_data(case_data, evidence)
        except Exception as e:
            st.warning(f"Timeline builder error: {e}. Using metadata events only.")
            timeline = _build_fallback_timeline(case_data)

    if not timeline:
        st.info("No timeline events found. Add case metadata or upload documents.")
        return

    # ── Filter controls ─────────────────────────────────────────────────
    ctrl1, ctrl2 = st.columns([2, 1])
    with ctrl1:
        sig_filter = st.multiselect(
            "Filter by significance",
            ["High", "Medium", "Low"],
            default=["High", "Medium", "Low"],
        )
    with ctrl2:
        show_extracted = st.checkbox("Include document-extracted events", value=False)

    filtered = [
        e for e in timeline
        if e.get("significance", "Medium") in sig_filter
        and (show_extracted or not e.get("extracted", False))
    ]

    # ── Summary stats ───────────────────────────────────────────────────
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total Events", len(filtered))
    with m2:
        high_events = sum(1 for e in filtered if e.get("significance") == "High")
        st.metric("Critical Events", high_events)
    with m3:
        if filtered:
            date_range = f"{filtered[0].get('date','')} → {filtered[-1].get('date','')}"
            st.metric("Date Range", date_range)

    st.markdown("---")

    # ── Timeline visualization ──────────────────────────────────────────
    _render_plotly_timeline(filtered)

    st.markdown("---")

    # ── Detailed event list ─────────────────────────────────────────────
    st.markdown("### 📋 Event Details")
    for i, event in enumerate(filtered, 1):
        sig = event.get("significance", "Medium")
        sig_color = {"High": "#e02424", "Medium": "#f59e0b", "Low": "#4b5563"}.get(sig, "#4b5563")
        sig_bg = {"High": "rgba(224,36,36,0.15)", "Medium": "rgba(245,158,11,0.1)", "Low": "rgba(75,85,99,0.1)"}.get(sig, "rgba(75,85,99,0.1)")

        st.markdown(f"""
        <div class="timeline-item">
          <div class="timeline-dot">{i}</div>
          <div style="flex:1;">
            <div class="timeline-date">{event.get('date','')}</div>
            <div style="display:flex;align-items:center;gap:8px;margin-top:2px;">
              <div class="timeline-event">{event.get('event','')}</div>
              <span style="background:{sig_bg};color:{sig_color};font-size:9px;font-weight:700;
                   padding:2px 6px;border-radius:100px;text-transform:uppercase;">{sig}</span>
            </div>
            <div class="timeline-desc">
              {event.get('legal_impact','')}
              {f" | Source: {event.get('document_source','')}" if event.get('document_source') else ''}
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)


def _render_plotly_timeline(events: list):
    """Render interactive Plotly timeline chart."""
    import plotly.graph_objects as go

    if not events:
        return

    dates = [e.get("date", "") for e in events]
    labels = [e.get("event", "")[:40] for e in events]
    sig_colors = {"High": "#e02424", "Medium": "#f59e0b", "Low": "#4b5563"}
    colors = [sig_colors.get(e.get("significance", "Medium"), "#4b5563") for e in events]

    fig = go.Figure()

    # Timeline line
    fig.add_trace(go.Scatter(
        x=list(range(len(events))), y=[0] * len(events),
        mode="lines",
        line=dict(color="rgba(201,168,76,0.3)", width=2),
        hoverinfo="none",
        showlegend=False,
    ))

    # Events
    for i, (event, color) in enumerate(zip(events, colors)):
        fig.add_trace(go.Scatter(
            x=[i], y=[0],
            mode="markers+text",
            marker=dict(size=14, color=color, line=dict(color="#c9a84c", width=2)),
            text=[event.get("date", "")],
            textposition="top center",
            textfont=dict(color="#c9a84c", size=9),
            name=event.get("event", ""),
            hovertext=(
                f"<b>{event.get('event','')}</b><br>"
                f"Date: {event.get('date','')}<br>"
                f"Impact: {event.get('legal_impact','')}"
            ),
            hoverinfo="text",
            showlegend=False,
        ))

    fig.update_layout(
        paper_bgcolor="#04080f",
        plot_bgcolor="#04080f",
        font=dict(color="#f3f4f6", size=11),
        height=200,
        yaxis=dict(visible=False, range=[-1, 1]),
        xaxis=dict(
            visible=True,
            ticktext=labels,
            tickvals=list(range(len(events))),
            tickangle=-45,
            color="#4b5563",
            gridcolor="#1a1a2e",
        ),
        margin=dict(l=20, r=20, t=30, b=80),
    )
    st.plotly_chart(fig, use_container_width=True)


def _build_fallback_timeline(case_data: dict) -> list:
    """Build basic timeline from metadata when TimelineBuilder unavailable."""
    events = []
    meta = case_data.get("metadata", case_data)

    field_map = {
        "filing_date": ("Case filed", "Legal proceedings initiated", "High"),
        "arrest_date": ("Accused arrested", "Custody begins", "High"),
        "chargesheet_date": ("Chargesheet filed", "Formal charges framed", "High"),
        "next_hearing": ("Next hearing scheduled", "Upcoming court date", "Medium"),
    }

    for field, (event, impact, sig) in field_map.items():
        date = meta.get(field, "")
        if date:
            events.append({"date": date, "event": event, "legal_impact": impact,
                           "significance": sig, "document_source": "Case Metadata"})

    for i, date in enumerate(meta.get("hearing_dates", []), 1):
        events.append({
            "date": date, "event": f"Court Hearing #{i}",
            "legal_impact": "Arguments heard", "significance": "Medium",
            "document_source": "Court Records",
        })

    events.sort(key=lambda x: x.get("date", "9999"))
    return events
