"""Legal Research page — AI-powered precedent and section search."""

import streamlit as st


EXAMPLE_QUERIES = [
    "What are the elements of IPC Section 420 cheating?",
    "Landmark cases on bail for serious offences",
    "Death penalty in rarest of rare cases",
    "Evidence required to prove criminal conspiracy",
    "Rights of accused during police interrogation",
    "Anticipatory bail under Section 438 CrPC",
]


def render():
    """Render the Legal Research page."""
    st.markdown("""
    <div class="lex-hero" style="margin-bottom:1.5rem;">
      <div class="lex-page-title">📚 Legal <span class="gold">Research</span></div>
      <div class="lex-page-subtitle">AI-powered search across IPC sections, precedents, and judgments</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Search bar ─────────────────────────────────────────────────────
    st.markdown("#### 🔍 Search Indian Legal Database")
    query = st.text_input(
        "Ask anything about Indian law...",
        placeholder="e.g. 'rarest of rare doctrine for death penalty'",
        label_visibility="collapsed",
    )

    st.markdown("**Example queries:**")
    example_cols = st.columns(3)
    for i, example in enumerate(EXAMPLE_QUERIES):
        with example_cols[i % 3]:
            if st.button(example[:45], key=f"example_{i}", use_container_width=True):
                query = example
                st.session_state["research_query"] = example

    if "research_query" in st.session_state:
        query = st.session_state["research_query"]

    search_btn = st.button("🔍 Search", use_container_width=True)

    if (search_btn or query) and query:
        st.session_state["last_research_query"] = query
        _run_search(query)

    # ── Ask Legal AI Chat ───────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 💬 Ask Legal AI")
    st.caption("Get direct answers with citations from the Indian legal database")

    question = st.text_area(
        "Legal question:",
        placeholder="What is the punishment for IPC Section 302? Can bail be granted in murder cases?",
        height=80,
        label_visibility="collapsed",
    )
    active_case = st.session_state.get("active_case")

    if st.button("Ask Legal AI", use_container_width=True) and question:
        with st.spinner("Consulting Indian legal database..."):
            try:
                from rag.legal_retriever import LegalRAGRetriever
                retriever = LegalRAGRetriever()
                case_data = st.session_state.get("cases", {}).get(active_case, {}) if active_case else {}
                meta = case_data.get("metadata", {})
                case_ctx = f"Case: {meta.get('case_type','')} — {', '.join(meta.get('charges',[]))}" if meta else ""
                answer = retriever.ask_legal_question(question, case_ctx)
                st.markdown("**LexAI Legal Answer:**")
                st.info(answer)
            except Exception as e:
                st.error(f"Research failed: {e}")
                st.info(
                    "**Demo Answer:** Please configure your GROQ_API_KEY for live AI responses. "
                    "The legal database contains 30+ case precedents and 50+ IPC sections for retrieval."
                )


def _run_search(query: str):
    """Run legal database search and display results."""
    with st.spinner(f"Searching Indian legal database for: '{query}'..."):
        try:
            from rag.legal_retriever import LegalRAGRetriever
            retriever = LegalRAGRetriever()
            precedents = retriever.search_precedents(query, top_k=5)
            sections = retriever.search_legal_sections(query, top_k=4)
        except Exception as e:
            st.warning(f"Search error: {e}. Showing demo results.")
            precedents = _demo_precedents()
            sections = _demo_sections()

    tab1, tab2 = st.tabs([
        f"📜 Case Precedents ({len(precedents)})",
        f"§ IPC/CrPC Sections ({len(sections)})",
    ])

    with tab1:
        if not precedents:
            st.info("No precedents found. Build the legal index first.")
        for p in precedents:
            _render_precedent_card(p)

    with tab2:
        if not sections:
            st.info("No sections found.")
        for s in sections:
            _render_section_card(s)


def _render_precedent_card(p: dict):
    """Render a case precedent card."""
    score = p.get("relevance_score", 0)
    score_pct = f"{score*100:.0f}%" if score <= 1 else f"{score:.2f}"

    st.markdown(f"""
    <div class="lex-card" style="margin-bottom:12px;">
      <div class="lex-card-body">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
          <div>
            <div style="font-size:14px;font-weight:700;color:#c9a84c;">{p.get('case_name','Unknown')}</div>
            <div style="font-size:11px;color:#9ca3af;margin-top:2px;">
              {p.get('court','')} | {p.get('citation','')} | Year: {p.get('year','')}
            </div>
          </div>
          <span style="background:rgba(201,168,76,0.1);color:#c9a84c;font-size:10px;
               font-weight:700;padding:3px 8px;border-radius:4px;">
            Relevance: {score_pct}
          </span>
        </div>
        <div style="font-size:12px;color:#9ca3af;margin-bottom:6px;">
          <strong style="color:#f3f4f6;">Held:</strong> {str(p.get('held',''))[:250]}
        </div>
        <div style="font-size:12px;color:#9ca3af;">
          <strong style="color:#c9a84c;">Legal Principle:</strong> {str(p.get('legal_principle',''))[:200]}
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def _render_section_card(s: dict):
    """Render an IPC/CrPC section card."""
    bailable = s.get("bailable")
    bail_str = "✅ Bailable" if bailable is True else "❌ Non-Bailable" if bailable is False else "—"
    bail_color = "#6ee7b7" if bailable else "#fca5a5" if bailable is False else "#9ca3af"

    st.markdown(f"""
    <div class="lex-card" style="margin-bottom:12px;">
      <div class="lex-card-body">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
          <div>
            <div style="font-size:18px;font-weight:900;color:#c9a84c;">{s.get('section','')}</div>
            <div style="font-size:13px;font-weight:600;color:#f3f4f6;margin-top:2px;">{s.get('title','')}</div>
          </div>
          <span style="color:{bail_color};font-size:11px;font-weight:700;">{bail_str}</span>
        </div>
        <div style="font-size:12px;color:#9ca3af;margin-bottom:8px;line-height:1.6;">
          {str(s.get('description',''))[:350]}
        </div>
        <div style="font-size:11px;color:#c9a84c;font-weight:600;">
          Punishment: {s.get('punishment','N/A')}
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def _demo_precedents():
    return [
        {"case_name": "Bachan Singh v. State of Punjab", "citation": "AIR 1980 SC 898",
         "court": "Supreme Court of India", "year": 1980,
         "held": "Death penalty valid but only in rarest of rare cases.",
         "legal_principle": "Rarest of rare doctrine for capital punishment.",
         "relevance_score": 0.92},
        {"case_name": "Lalita Kumari v. Government of UP", "citation": "(2014) 2 SCC 1",
         "court": "Supreme Court of India", "year": 2014,
         "held": "FIR registration is mandatory for cognizable offences.",
         "legal_principle": "Police cannot refuse to register FIR for cognizable offence.",
         "relevance_score": 0.85},
    ]


def _demo_sections():
    return [
        {"section": "IPC 302", "title": "Punishment for murder",
         "description": "Whoever commits murder shall be punished with death, or imprisonment for life.",
         "punishment": "Death or life imprisonment + fine",
         "bailable": False, "cognizable": True, "relevance_score": 0.95},
        {"section": "IPC 420", "title": "Cheating and dishonestly inducing delivery of property",
         "description": "Whoever cheats and thereby dishonestly induces the person deceived to deliver property.",
         "punishment": "Up to 7 years + fine",
         "bailable": False, "cognizable": True, "relevance_score": 0.88},
    ]
