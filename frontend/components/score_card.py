import streamlit as st


def _score_color(score: float) -> str:
    if score >= 80:
        return "#22c55e"
    if score >= 60:
        return "#84cc16"
    if score >= 40:
        return "#f59e0b"
    return "#ef4444"


def _score_emoji(score: float) -> str:
    if score >= 80:
        return "🟢"
    if score >= 60:
        return "🟡"
    if score >= 40:
        return "🟠"
    return "🔴"


def render_score_dashboard(analysis: dict):
    """Render the main score dashboard."""
    overall = analysis.get("overall_score") or 0

    st.markdown(f"""
    <div style="text-align:center; padding: 1.5rem; background: #ffffff; border-radius: 16px;
                border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 1rem;">
        <div style="font-size: 3.5rem; font-weight: 900; color: {_score_color(overall)};">{overall:.0f}</div>
        <div style="color: #64748b; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.1em;">Overall Score</div>
        <div style="color: #94a3b8; font-size: 0.75rem; margin-top: 0.25rem;">{_score_emoji(overall)} {analysis.get('analysis_type', 'general').replace('_', ' ').title()} Analysis</div>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(5)
    score_items = [
        ("ATS", analysis.get("ats_score") or 0),
        ("Skills", analysis.get("skills_score") or 0),
        ("Experience", analysis.get("experience_score") or 0),
        ("Education", analysis.get("education_score") or 0),
        ("Formatting", analysis.get("formatting_score") or 0),
    ]
    for col, (label, score) in zip(cols, score_items):
        with col:
            st.markdown(f"""
            <div class="score-card">
                <p class="score-value" style="color:{_score_color(score)};">{score:.0f}</p>
                <p class="score-label">{label}</p>
            </div>
            """, unsafe_allow_html=True)


def render_feedback_sections(analysis: dict):
    """Render strengths, weaknesses, and suggestions."""
    strengths = analysis.get("strengths") or []
    weaknesses = analysis.get("weaknesses") or []
    suggestions = analysis.get("suggestions") or []
    missing_kw = analysis.get("missing_keywords") or []
    matched_kw = analysis.get("matched_keywords") or []

    if analysis.get("summary"):
        st.info(f"📋 **Summary:** {analysis['summary']}")

    col1, col2 = st.columns(2)

    with col1:
        if strengths:
            st.markdown("#### ✅ Strengths")
            for s in strengths:
                st.markdown(f'<p class="strength-item">✓ {s}</p>', unsafe_allow_html=True)

    with col2:
        if weaknesses:
            st.markdown("#### ❌ Weaknesses")
            for w in weaknesses:
                st.markdown(f'<p class="weakness-item">✗ {w}</p>', unsafe_allow_html=True)

    if suggestions:
        st.markdown("#### 💡 Suggestions")
        for sug in suggestions:
            st.markdown(f'<p class="suggestion-item">→ {sug}</p>', unsafe_allow_html=True)

    if matched_kw or missing_kw:
        st.markdown("#### 🔑 Keyword Analysis")
        kw_col1, kw_col2 = st.columns(2)
        with kw_col1:
            if matched_kw:
                st.markdown("**Matched keywords:**")
                st.markdown(" ".join(f'<span class="skill-tag">✓ {k}</span>' for k in matched_kw), unsafe_allow_html=True)
        with kw_col2:
            if missing_kw:
                st.markdown("**Missing keywords:**")
                st.markdown(" ".join(f'<span style="display:inline-block;background:#450a0a;color:#fca5a5;border-radius:999px;padding:0.15rem 0.6rem;font-size:0.75rem;margin:0.15rem;border:1px solid #7f1d1d;">✗ {k}</span>' for k in missing_kw), unsafe_allow_html=True)
