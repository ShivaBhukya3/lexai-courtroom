"""Argument Studio — AI-powered prosecution and defense argument generation."""

import streamlit as st


def render():
    """Render the Argument Studio page — the showpiece feature."""
    st.markdown("""
    <div class="lex-hero" style="margin-bottom:1.5rem;">
      <div class="lex-page-title">⚔ Argument <span class="gold">Studio</span></div>
      <div class="lex-page-subtitle">AI-generated prosecution and defense arguments with cross-examination</div>
    </div>
    """, unsafe_allow_html=True)

    active_case = st.session_state.get("active_case")
    if not active_case:
        st.warning("👈 Please select a case from the sidebar.")
        return

    # ── Control Bar ─────────────────────────────────────────────────────
    ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([2, 1, 1, 1])
    with ctrl1:
        style = st.selectbox(
            "Argument Style",
            ["balanced", "aggressive", "conservative"],
            format_func=lambda x: {"balanced": "⚖ Balanced", "aggressive": "🔥 Aggressive", "conservative": "🧊 Conservative"}[x],
        )
    with ctrl2:
        gen_prosecution = st.button("🔴 Generate Prosecution", use_container_width=True)
    with ctrl3:
        gen_defense = st.button("🟢 Generate Defense", use_container_width=True)
    with ctrl4:
        compare_both = st.button("🏆 Compare Both", use_container_width=True)

    # ── Generate arguments ──────────────────────────────────────────────
    if gen_prosecution or (compare_both and not st.session_state.get("prosecution_args")):
        _generate_prosecution(active_case, style)

    if gen_defense or (compare_both and not st.session_state.get("defense_args")):
        _generate_defense(active_case, style)

    # ── Display split view ──────────────────────────────────────────────
    prosecution_args = st.session_state.get("prosecution_args", {})
    defense_args = st.session_state.get("defense_args", {})

    if prosecution_args or defense_args:
        left_col, right_col = st.columns(2)

        with left_col:
            _render_prosecution_panel(prosecution_args)

        with right_col:
            _render_defense_panel(defense_args)

        # ── Argument comparison ─────────────────────────────────────────
        if prosecution_args and defense_args:
            st.markdown("---")
            _render_strength_comparison(prosecution_args, defense_args)

        # ── Cross-examination ───────────────────────────────────────────
        st.markdown("---")
        st.markdown("### ❓ Cross-Examination Generator")
        witness_stmt = st.text_area(
            "Enter witness statement to generate cross-examination questions:",
            height=120,
            placeholder="Paste the witness testimony or statement here...",
        )
        cx_side = st.radio("Examining side:", ["defense", "prosecution"], horizontal=True)
        if st.button("Generate Cross-Examination Questions") and witness_stmt:
            _generate_cross_exam(active_case, witness_stmt, cx_side)

    else:
        st.markdown("""
        <div style="background:rgba(255,255,255,0.02);border:2px dashed rgba(201,168,76,0.2);
             border-radius:12px;padding:3rem;text-align:center;">
          <div style="font-size:3rem;margin-bottom:1rem;">⚔</div>
          <div style="font-size:16px;font-weight:600;color:#f3f4f6;margin-bottom:8px;">Ready to Generate Arguments</div>
          <div style="font-size:13px;color:#9ca3af;">
            Click <strong>Generate Prosecution</strong> or <strong>Generate Defense</strong> above.
          </div>
        </div>
        """, unsafe_allow_html=True)


def _generate_prosecution(case_id: str, style: str):
    """Generate prosecution arguments via AI."""
    with st.spinner("⚖ Generating prosecution case..."):
        try:
            from src.argument_generator import LegalArgumentGenerator
            from rag.legal_retriever import LegalRAGRetriever

            case_data = st.session_state.cases.get(case_id, {})
            evidence = st.session_state.get("evidence_analyses", [])
            charges = case_data.get("metadata", {}).get("charges", [])

            retriever = LegalRAGRetriever()
            legal_ctx = retriever.get_legal_context(" ".join(charges))
            precedents = retriever.get_prosecution_precedents(charges)

            gen = LegalArgumentGenerator()
            args = gen.generate_prosecution_argument(case_data, evidence, legal_ctx, precedents, style)
            st.session_state.prosecution_args = args
            st.success("✅ Prosecution arguments generated!")
        except Exception as e:
            st.error(f"Generation failed: {e}")
            # Use demo data
            st.session_state.prosecution_args = _demo_prosecution_args()


def _generate_defense(case_id: str, style: str):
    """Generate defense arguments via AI."""
    with st.spinner("🛡 Building defense strategy..."):
        try:
            from src.argument_generator import LegalArgumentGenerator
            from rag.legal_retriever import LegalRAGRetriever

            case_data = st.session_state.cases.get(case_id, {})
            evidence = st.session_state.get("evidence_analyses", [])
            charges = case_data.get("metadata", {}).get("charges", [])

            retriever = LegalRAGRetriever()
            legal_ctx = retriever.get_legal_context(" ".join(charges))
            precedents = retriever.get_defense_precedents(charges)

            gen = LegalArgumentGenerator()
            args = gen.generate_defense_argument(case_data, evidence, legal_ctx, precedents, style)
            st.session_state.defense_args = args
            st.success("✅ Defense arguments generated!")
        except Exception as e:
            st.error(f"Generation failed: {e}")
            st.session_state.defense_args = _demo_defense_args()


def _generate_cross_exam(case_id: str, witness_stmt: str, side: str):
    """Generate cross-examination questions."""
    with st.spinner("Generating questions..."):
        try:
            from src.argument_generator import LegalArgumentGenerator
            case_data = st.session_state.cases.get(case_id, {})
            meta = case_data.get("metadata", {})
            ctx = f"Case: {meta.get('case_type','')} — {', '.join(meta.get('charges',[]))}"

            gen = LegalArgumentGenerator()
            questions = gen.generate_cross_examination(witness_stmt, ctx, side)
            st.session_state["cross_exam_questions"] = questions
        except Exception as e:
            st.error(f"Generation failed: {e}")
            st.session_state["cross_exam_questions"] = _demo_questions()

    questions = st.session_state.get("cross_exam_questions", [])
    if questions:
        st.markdown(f"**{len(questions)} Cross-Examination Questions ({side.title()} examining):**")
        for i, q in enumerate(questions, 1):
            if isinstance(q, dict):
                with st.expander(f"Q{i}: {str(q.get('question', q))[:80]}..."):
                    st.markdown(f"**Question:** {q.get('question', '')}")
                    st.markdown(f"**Purpose:** {q.get('purpose', '')}")
                    if q.get("expected_answer"):
                        st.markdown(f"**Expected Answer:** {q.get('expected_answer', '')}")
            else:
                st.markdown(f"**Q{i}:** {q}")


def _render_prosecution_panel(args: dict):
    """Render prosecution argument panel."""
    strength = args.get("argument_strength_score", 6.5)

    st.markdown(f"""
    <div class="arg-panel arg-prosecution">
      <div class="arg-title">🔴 Prosecution Case — Strength: {strength:.1f}/10</div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📜 Opening Statement", expanded=True):
        st.markdown(f"""<div class="arg-text">{args.get('opening_statement', 'Not generated yet.')}</div>""",
                    unsafe_allow_html=True)

    charge_args = args.get("charge_arguments", [])
    if charge_args:
        with st.expander(f"⚖ Charge Arguments ({len(charge_args)})"):
            for ca in charge_args:
                if isinstance(ca, dict):
                    st.markdown(f"**{ca.get('charge', 'Charge')}**")
                    for key in ["elements", "evidence", "precedents"]:
                        items = ca.get(key, [])
                        if items:
                            st.markdown(f"*{key.title()}:* " + " | ".join(str(i) for i in items[:3]))
                    st.markdown("---")

    precedents = args.get("cited_precedents", [])
    if precedents:
        with st.expander(f"📚 Precedents Cited ({len(precedents)})"):
            for p in precedents[:5]:
                name = p if isinstance(p, str) else p.get("case_name", str(p))
                st.markdown(f"""
                <div class="legal-cite">
                  <span class="cite-icon">§</span>
                  <div><div class="cite-case">{name}</div></div>
                </div>
                """, unsafe_allow_html=True)

    with st.expander("🎤 Closing Statement"):
        st.markdown(args.get("closing_statement", ""), unsafe_allow_html=False)


def _render_defense_panel(args: dict):
    """Render defense argument panel."""
    strength = args.get("argument_strength_score", 5.5)

    st.markdown(f"""
    <div class="arg-panel arg-defense">
      <div class="arg-title">🟢 Defense Case — Strength: {strength:.1f}/10</div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📜 Opening Statement", expanded=True):
        st.markdown(args.get("opening_statement", "Not generated yet."))

    counter_args = args.get("charge_counter_arguments", [])
    if counter_args:
        with st.expander(f"🛡 Counter-Arguments ({len(counter_args)})"):
            for ca in counter_args:
                if isinstance(ca, dict):
                    st.markdown(f"**{ca.get('charge', 'Charge')}**")
                    gaps = ca.get("prosecution_gaps", ca.get("alternative_explanation", ""))
                    if gaps:
                        st.markdown(f"*Gaps:* {str(gaps)[:200]}")
                    st.markdown("---")

    grounds = args.get("acquittal_grounds", [])
    if grounds:
        with st.expander(f"🏛 Acquittal Grounds ({len(grounds)})"):
            for g in grounds:
                st.markdown(f"• {g}")

    with st.expander("🎤 Closing Statement"):
        st.markdown(args.get("closing_statement", ""))


def _render_strength_comparison(prosecution: dict, defense: dict):
    """Render radar chart comparing prosecution and defense strength."""
    import plotly.graph_objects as go

    st.markdown("### 📊 Argument Strength Comparison")

    try:
        from src.argument_generator import LegalArgumentGenerator
        gen = LegalArgumentGenerator()
        comparison = gen.compare_argument_strength(prosecution, defense)
    except Exception:
        comparison = {
            "prosecution_scores": {"evidence_strength": 7, "precedent_support": 6, "logical_coherence": 7, "witness_strength": 6, "legal_accuracy": 8},
            "defense_scores": {"evidence_strength": 5, "precedent_support": 6, "logical_coherence": 6, "witness_strength": 5, "legal_accuracy": 7},
            "winner_prediction": "Prosecution",
            "overall_prosecution_score": 6.8,
            "overall_defense_score": 5.8,
        }

    categories = ["Evidence\nStrength", "Precedent\nSupport", "Logical\nCoherence", "Witness\nStrength", "Legal\nAccuracy"]
    pro_scores = list(comparison["prosecution_scores"].values())[:5]
    def_scores = list(comparison["defense_scores"].values())[:5]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=pro_scores + [pro_scores[0]],
        theta=categories + [categories[0]],
        fill="toself", name="Prosecution",
        line_color="#e02424", fillcolor="rgba(224,36,36,0.15)",
    ))
    fig.add_trace(go.Scatterpolar(
        r=def_scores + [def_scores[0]],
        theta=categories + [categories[0]],
        fill="toself", name="Defense",
        line_color="#057a55", fillcolor="rgba(5,122,85,0.15)",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 10], color="#4b5563"),
            bgcolor="#0c1221",
            angularaxis=dict(color="#9ca3af"),
        ),
        showlegend=True,
        paper_bgcolor="#04080f",
        plot_bgcolor="#04080f",
        font=dict(color="#f3f4f6", size=11),
        height=350,
        margin=dict(l=40, r=40, t=40, b=40),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#f3f4f6")),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Prediction summary
    winner = comparison.get("winner_prediction", "Prosecution")
    winner_color = "#e02424" if winner == "Prosecution" else "#057a55"
    st.markdown(f"""
    <div style="text-align:center;padding:1rem;background:var(--bg-surface);border-radius:10px;border:1px solid var(--border);">
      <span style="font-size:11px;color:#4b5563;text-transform:uppercase;letter-spacing:1px;">AI Prediction</span>
      <div style="font-size:22px;font-weight:800;color:{winner_color};margin-top:4px;">{winner} Advantage</div>
      <div style="font-size:12px;color:#9ca3af;margin-top:4px;">
        Prosecution: {comparison.get('overall_prosecution_score',0):.1f}/10 |
        Defense: {comparison.get('overall_defense_score',0):.1f}/10
      </div>
    </div>
    """, unsafe_allow_html=True)


def _demo_prosecution_args() -> dict:
    return {
        "side": "prosecution", "style": "balanced",
        "opening_statement": "Your Honour, the prosecution will demonstrate beyond reasonable doubt that the accused deliberately and with full knowledge committed the offences charged. The evidence before this court — documentary, testimonial, and forensic — paints an unambiguous picture of guilt. We shall present this evidence methodically and invite the court to draw the only logical conclusion: conviction.",
        "charge_arguments": [{"charge": "Primary Charge", "elements": ["Intent established", "Act proven", "Victim identified"], "evidence": ["Bank statements", "Witness testimony"], "precedents": ["Bachan Singh v. State of Punjab"]}],
        "closing_statement": "Your Honour, we have placed before this court overwhelming evidence of guilt. The prosecution respectfully prays for conviction and appropriate sentencing under the applicable provisions.",
        "cited_precedents": ["Lalita Kumari v. Government of UP (2014)", "Arnesh Kumar v. State of Bihar (2014)"],
        "argument_strength_score": 7.2,
    }


def _demo_defense_args() -> dict:
    return {
        "side": "defense", "style": "balanced",
        "opening_statement": "Your Honour, the defence will demonstrate that the prosecution has singularly failed to discharge its burden of proving guilt beyond reasonable doubt. The evidence is circumstantial, contradictory, and insufficient to sustain conviction. The accused is entitled to the benefit of every reasonable doubt.",
        "charge_counter_arguments": [{"charge": "Primary Charge", "prosecution_gaps": "No direct evidence links accused to the alleged act.", "alternative_explanation": "The accused was elsewhere at the material time."}],
        "closing_statement": "Your Honour, the prosecution's case is riddled with doubt. We pray for complete acquittal of the accused on all charges.",
        "acquittal_grounds": ["Insufficient evidence", "No forensic evidence", "Witness credibility questionable", "Benefit of reasonable doubt"],
        "argument_strength_score": 6.1,
    }


def _demo_questions() -> list:
    return [
        {"question": "You stated you saw the accused at the location at 6 PM — were you wearing your prescription glasses at that time?", "purpose": "Challenge identification reliability"},
        {"question": "How far away were you standing when you allegedly observed the accused?", "purpose": "Test observation conditions"},
        {"question": "Is it not true that you had a prior dispute with the accused?", "purpose": "Establish motive to lie"},
        {"question": "Did you give this same statement to the police on the day of the incident?", "purpose": "Check consistency with prior statement"},
        {"question": "You said the incident occurred at dusk — what was the lighting condition exactly?", "purpose": "Challenge visibility conditions"},
    ]
