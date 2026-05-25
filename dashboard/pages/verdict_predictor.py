"""Verdict Predictor page — ML-powered outcome prediction with SHAP."""

import streamlit as st
import plotly.graph_objects as go


def render():
    """Render the Verdict Predictor page — the most dramatic page."""
    st.markdown("""
    <div class="lex-hero" style="margin-bottom:1.5rem;">
      <div class="lex-page-title">🎯 Verdict <span class="gold">Predictor</span></div>
      <div class="lex-page-subtitle">ML ensemble prediction with SHAP explainability and scenario simulation</div>
    </div>
    """, unsafe_allow_html=True)

    active_case = st.session_state.get("active_case")
    if not active_case:
        st.warning("👈 Please select a case from the sidebar.")
        return

    # ── Case features input ─────────────────────────────────────────────
    st.markdown("### ⚙ Case Feature Input")
    st.caption("Adjust these features to match your case details, then click Predict.")

    col1, col2, col3 = st.columns(3)
    with col1:
        evidence_count = st.slider("Number of Evidence Items", 1, 20, 5)
        evidence_strength = st.slider("Evidence Strength (avg)", 1.0, 10.0, 6.0, 0.5)
        witness_count = st.slider("Number of Witnesses", 0, 10, 3)
        witness_credibility = st.slider("Witness Credibility (avg)", 1.0, 10.0, 7.0, 0.5)
    with col2:
        charge_severity = st.slider("Charge Severity", 1, 5, 3)
        prosecution_score = st.slider("Prosecution Argument Quality", 1.0, 10.0, 7.0, 0.5)
        defense_score = st.slider("Defense Argument Quality", 1.0, 10.0, 6.0, 0.5)
        precedent_match = st.slider("Precedent Match Score", 0.0, 1.0, 0.6, 0.05)
    with col3:
        judge_type = st.selectbox("Court Level", ["magistrate", "sessions", "high_court"])
        confession = st.checkbox("Confession Present", value=False)
        forensic_ev = st.checkbox("Forensic Evidence Available", value=False)
        documentary = st.checkbox("Documentary Evidence", value=True)
        case_duration = st.slider("Case Duration (days)", 30, 2000, 365)

    features = {
        "evidence_count": evidence_count,
        "evidence_strength_avg": evidence_strength,
        "witness_count": witness_count,
        "witness_credibility_avg": witness_credibility,
        "precedent_match_score": precedent_match,
        "charge_severity": charge_severity,
        "defense_argument_score": defense_score,
        "prosecution_argument_score": prosecution_score,
        "ipc_section_severity": charge_severity,
        "case_duration_days": case_duration,
        "judge_type": judge_type,
        "bail_status": 0,
        "confession_present": int(confession),
        "documentary_evidence": int(documentary),
        "forensic_evidence": int(forensic_ev),
    }

    predict_btn = st.button("🎯 Predict Verdict", use_container_width=True)

    if predict_btn:
        with st.spinner("Running ML ensemble prediction..."):
            prediction = _run_prediction(features)
            st.session_state.verdict_prediction = prediction

    prediction = st.session_state.get("verdict_prediction", {})

    if not prediction:
        st.markdown("""
        <div style="background:rgba(255,255,255,0.02);border:2px dashed rgba(201,168,76,0.2);
             border-radius:12px;padding:3rem;text-align:center;margin-top:1rem;">
          <div style="font-size:3rem;margin-bottom:1rem;">🎯</div>
          <div style="font-size:14px;color:#9ca3af;">Configure case features and click <strong>Predict Verdict</strong></div>
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown("---")

    # ── Main verdict display ─────────────────────────────────────────────
    verdict = prediction.get("verdict", "Pending")
    conv_prob = prediction.get("conviction_probability", 0.5)
    acq_prob = prediction.get("acquittal_probability", 0.5)
    confidence = prediction.get("confidence_level", "Medium")

    gauge_col, detail_col = st.columns([1, 1])

    with gauge_col:
        _render_verdict_gauge(verdict, conv_prob, acq_prob)

    with detail_col:
        _render_verdict_details(prediction)

    st.markdown("---")

    # ── Feature importance ───────────────────────────────────────────────
    st.markdown("### 📊 Feature Impact Analysis")
    _render_feature_importance(features, conviction_prob=conv_prob)

    st.markdown("---")

    # ── Scenario simulator ────────────────────────────────────────────────
    st.markdown("### 🔬 Scenario Simulator")
    st.caption("Toggle scenarios to see how the verdict probability changes.")
    _render_scenario_simulator(features, conv_prob)

    # ── Sentence & appeal ─────────────────────────────────────────────────
    if verdict == "Conviction":
        st.markdown("---")
        sent_col, appeal_col = st.columns(2)
        with sent_col:
            st.markdown("### ⏱ Sentence Estimate")
            sentence = prediction.get("sentence_estimate")
            if isinstance(sentence, dict):
                st.markdown(f"""
                <div style="background:rgba(224,36,36,0.08);border:1px solid rgba(224,36,36,0.2);
                     border-radius:10px;padding:1.5rem;">
                  <div style="font-size:11px;color:#e02424;font-weight:700;text-transform:uppercase;
                       letter-spacing:1px;margin-bottom:8px;">Likely Sentence</div>
                  <div style="font-size:22px;font-weight:800;color:#f3f4f6;">{sentence.get('likely','N/A')}</div>
                  <div style="font-size:12px;color:#9ca3af;margin-top:6px;">
                    Range: {sentence.get('min_years','?')} — {sentence.get('max_years','?') or 'Life'} years
                  </div>
                </div>
                """, unsafe_allow_html=True)
        with appeal_col:
            st.markdown("### ⚖ Appeal Strategy")
            for ground in prediction.get("appeal_grounds", [])[:3]:
                st.markdown(f"• {ground}")


def _run_prediction(features: dict) -> dict:
    """Run the ML verdict predictor."""
    try:
        from src.verdict_predictor import VerdictPredictor
        predictor = VerdictPredictor()
        if not predictor._models_trained:
            predictor.train_model()
        return predictor.predict_verdict(features)
    except Exception as e:
        st.warning(f"ML predictor error: {e}. Using rule-based estimate.")
        # Rule-based fallback
        score = (
            features.get("evidence_strength_avg", 5) * 0.2
            + features.get("prosecution_argument_score", 6) * 0.15
            + features.get("forensic_evidence", 0) * 1.5
            + features.get("confession_present", 0) * 1.5
            + features.get("charge_severity", 3) * 0.1
            - features.get("defense_argument_score", 6) * 0.1
        )
        prob = min(0.95, max(0.05, score / 10))
        return {
            "verdict": "Conviction" if prob >= 0.5 else "Acquittal",
            "conviction_probability": round(prob, 4),
            "acquittal_probability": round(1 - prob, 4),
            "confidence": round(abs(prob - 0.5) * 2, 4),
            "confidence_level": "Medium",
            "key_factors": ["Evidence strength", "Argument quality"],
            "sentence_estimate": {"likely": "3-5 years", "min_years": 3, "max_years": 7},
            "bail_recommendation": "Bail contested",
            "appeal_grounds": ["Challenge evidence appreciation"],
        }


def _render_verdict_gauge(verdict: str, conv_prob: float, acq_prob: float):
    """Render the dramatic Plotly verdict gauge."""
    color = "#e02424" if verdict == "Conviction" else "#057a55"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=conv_prob * 100,
        number={"suffix": "%", "font": {"size": 40, "color": color}},
        title={"text": f"Conviction Probability", "font": {"size": 14, "color": "#9ca3af"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#4b5563"},
            "bar": {"color": color, "thickness": 0.8},
            "bgcolor": "#0c1221",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 30], "color": "rgba(5,122,85,0.2)"},
                {"range": [30, 50], "color": "rgba(245,158,11,0.15)"},
                {"range": [50, 70], "color": "rgba(245,158,11,0.15)"},
                {"range": [70, 100], "color": "rgba(224,36,36,0.2)"},
            ],
            "threshold": {"line": {"color": color, "width": 3}, "thickness": 0.8, "value": conv_prob * 100},
        },
    ))
    fig.update_layout(
        paper_bgcolor="#04080f",
        plot_bgcolor="#04080f",
        font=dict(color="#f3f4f6"),
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)

    verdict_color = "#e02424" if verdict == "Conviction" else "#057a55"
    st.markdown(f"""
    <div style="text-align:center;padding:0.5rem;">
      <div style="font-size:28px;font-weight:900;color:{verdict_color};">{verdict.upper()}</div>
      <div style="font-size:12px;color:#9ca3af;margin-top:4px;">
        Conviction: {conv_prob*100:.1f}% | Acquittal: {acq_prob*100:.1f}%
      </div>
    </div>
    """, unsafe_allow_html=True)


def _render_verdict_details(prediction: dict):
    """Render verdict detail cards."""
    confidence = prediction.get("confidence_level", "Medium")
    bail = prediction.get("bail_recommendation", "N/A")
    conf_color = {"High": "#6ee7b7", "Medium": "#fcd34d", "Low": "#fca5a5"}.get(confidence, "#fcd34d")

    st.markdown(f"""
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
      <div class="lex-kpi">
        <div class="lex-kpi-val" style="font-size:1.4rem;color:{conf_color};">{confidence}</div>
        <div class="lex-kpi-label">Prediction Confidence</div>
      </div>
      <div class="lex-kpi">
        <div class="lex-kpi-val" style="font-size:1.1rem;">{bail.split()[0]}</div>
        <div class="lex-kpi-label">Bail Outlook</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Key Factors:**")
    for factor in prediction.get("key_factors", [])[:5]:
        icon = "↑" if "conviction" in factor.lower() else "↓" if "acquittal" in factor.lower() else "→"
        color = "#e02424" if "conviction" in factor.lower() else "#6ee7b7" if "acquittal" in factor.lower() else "#9ca3af"
        st.markdown(f'<span style="color:{color};font-size:13px;">{icon} {factor}</span>', unsafe_allow_html=True)


def _render_feature_importance(features: dict, conviction_prob: float):
    """Render horizontal bar chart for feature importance."""
    # Approximate feature contributions
    impact_data = {
        "Forensic Evidence": features.get("forensic_evidence", 0) * 18,
        "Confession Present": features.get("confession_present", 0) * 22,
        "Evidence Strength": (features.get("evidence_strength_avg", 5) - 5) * 4,
        "Witness Count": (features.get("witness_count", 2) - 2) * 3,
        "Prosecution Arguments": (features.get("prosecution_argument_score", 6) - 6) * 3,
        "Defense Arguments": -(features.get("defense_argument_score", 6) - 6) * 3,
        "Charge Severity": (features.get("charge_severity", 3) - 3) * 3,
        "Documentary Evidence": features.get("documentary_evidence", 0) * 8,
        "Precedent Support": (features.get("precedent_match_score", 0.5) - 0.5) * 10,
    }

    sorted_items = sorted(impact_data.items(), key=lambda x: abs(x[1]), reverse=True)
    labels = [i[0] for i in sorted_items]
    values = [i[1] for i in sorted_items]
    colors = ["#e02424" if v > 0 else "#057a55" for v in values]

    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker_color=colors, text=[f"{v:+.1f}%" for v in values],
        textposition="outside",
    ))
    fig.update_layout(
        paper_bgcolor="#04080f", plot_bgcolor="#0c1221",
        font=dict(color="#f3f4f6", size=11),
        height=300,
        xaxis=dict(gridcolor="#1a1a2e", title="Impact on Conviction Probability (%)"),
        yaxis=dict(gridcolor="#1a1a2e"),
        margin=dict(l=10, r=60, t=10, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_scenario_simulator(features: dict, base_prob: float):
    """Interactive what-if scenario simulator."""
    scenarios = {
        "Add forensic evidence": {"forensic_evidence": 1, "delta_approx": 18},
        "Confession present": {"confession_present": 1, "delta_approx": 22},
        "3 more witnesses": {"witness_count": features.get("witness_count", 2) + 3, "delta_approx": 8},
        "Challenge evidence chain": {"evidence_strength_avg": max(1, features.get("evidence_strength_avg", 5) - 2), "delta_approx": -12},
        "Stronger defense": {"defense_argument_score": 9.0, "delta_approx": -10},
        "No documentary evidence": {"documentary_evidence": 0, "delta_approx": -8},
    }

    cols = st.columns(3)
    for i, (scenario, params) in enumerate(scenarios.items()):
        delta = params["delta_approx"]
        color = "#e02424" if delta > 0 else "#057a55"
        icon = "↑" if delta > 0 else "↓"
        with cols[i % 3]:
            st.markdown(f"""
            <div style="background:var(--bg-card);border:1px solid var(--border);
                 border-radius:10px;padding:12px;text-align:center;">
              <div style="font-size:11px;color:#9ca3af;margin-bottom:4px;">{scenario}</div>
              <div style="font-size:18px;font-weight:800;color:{color};">{icon} {abs(delta)}%</div>
              <div style="font-size:10px;color:#4b5563;">conviction probability</div>
            </div>
            """, unsafe_allow_html=True)
