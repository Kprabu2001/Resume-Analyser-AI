import streamlit as st
from utils.api_client import (
    upload_resume, run_analysis, list_analyses, get_resume,
    send_chat_message, clear_chat_session,
    generate_cover_letter, export_analysis_pdf,
)
from utils.session import do_logout, reset_chat
from components.score_card import render_score_dashboard, render_feedback_sections
from components.sidebar import render_sidebar
from config.settings import INTENT_LABELS, QUICK_SUGGESTIONS


def show_main_page():
    if "active_page" not in st.session_state:
        st.session_state.active_page = "chat"

    render_sidebar()

    active_page = st.session_state.active_page

    if active_page == "upload":
        _render_upload_page()
    elif active_page == "analyse":
        _render_analyse_page()
    else:
        _render_chat_page()


# ──────────────────────────────────────────────────────────────────────────────
# Upload Page
# ──────────────────────────────────────────────────────────────────────────────

MAX_UPLOAD_MB = 5

def _render_upload_page():
    st.markdown("## Upload Your Resume")
    st.markdown(f"Upload a PDF or plain text resume (max {MAX_UPLOAD_MB}MB). AI will parse and extract all key information.")

    uploaded_file = st.file_uploader(
        "Choose a resume file",
        type=["pdf", "docx", "txt"],
        help=f"Supported: PDF, DOCX, TXT — Max file size: {MAX_UPLOAD_MB}MB",
    )

    if uploaded_file and uploaded_file.size > MAX_UPLOAD_MB * 1024 * 1024:
        st.error(f"File too large. Maximum size is {MAX_UPLOAD_MB}MB.")
        return

    if uploaded_file:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**File:** `{uploaded_file.name}` ({uploaded_file.size // 1024} KB)")
        with col2:
            if st.button("Upload & Parse", use_container_width=True):
                with st.spinner("Uploading and parsing resume with AI..."):
                    result = upload_resume(
                        uploaded_file.getvalue(),
                        uploaded_file.name,
                        st.session_state.access_token,
                    )
                st.session_state.upload_result = result
                st.rerun()

    # Render upload result full-width below the upload section
    if "upload_result" in st.session_state:
        result = st.session_state.upload_result
        if result["success"]:
            data = result["data"]
            st.success("Resume uploaded and parsed successfully!")
            _render_parsed_resume(data)
        elif result["error"] == "auth_error":
            st.warning("Session expired. Please login again.")
            do_logout()
        else:
            st.error(f"Upload failed: {result['error']}")
        del st.session_state.upload_result


def _render_parsed_resume(data: dict):
    candidate = data.get("candidate_name") or "Unknown Candidate"
    role = data.get("current_role") or "Role not specified"
    email = data.get("email")
    phone = data.get("phone")
    location = data.get("location")
    experience = data.get("years_of_experience")
    education_level = data.get("education_level")

    st.markdown(f"""
    <div class="resume-detail-card">
        <h2>{candidate}</h2>
        <p class="role-sub">{role}</p>
        <div class="resume-contact-bar">
            {f"<span class='detail-badge'>📧 {email}</span>" if email else ""}
            {f"<span class='detail-badge'>📱 {phone}</span>" if phone else ""}
            {f"<span class='detail-badge'>📍 {location}</span>" if location else ""}
        </div>
    </div>
    """, unsafe_allow_html=True)

    exp_val = experience if experience is not None else 0
    exp_display = int(exp_val) if float(exp_val) == int(float(exp_val)) else float(exp_val)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"""
        <div class="resume-detail-card">
            <p class="detail-key">Years of Experience</p>
            <p class="detail-value">{exp_display} years</p>
        </div>
        """, unsafe_allow_html=True)
    with col_b:
        st.markdown(f"""
        <div class="resume-detail-card">
            <p class="detail-key">Education Level</p>
            <p class="detail-value">{education_level or "N/A"}</p>
        </div>
        """, unsafe_allow_html=True)

    skills = data.get("skills") or []
    if skills:
        skills_html = " ".join(f"<span class='skill-tag'>{s}</span>" for s in skills)
        st.markdown(f"""
        <div class="resume-detail-card">
            <p class="resume-section-title">🛠 Skills</p>
            <div>{skills_html}</div>
        </div>
        """, unsafe_allow_html=True)

    work_exp = data.get("work_experience") or []
    if work_exp:
        exp_items = []
        for exp in work_exp:
            role_text = exp.get("role", "Role unknown")
            company_text = exp.get("company", "Company unknown")
            duration_text = exp.get("duration", "")
            if duration_text:
                exp_items.append(f"<div class='exp-item'><strong>{role_text}</strong> — {company_text} <span class='exp-dur'>{duration_text}</span></div>")
            else:
                exp_items.append(f"<div class='exp-item'><strong>{role_text}</strong> — {company_text}</div>")
        exp_block = "<br>".join(exp_items)
        st.markdown(f"""
        <div class="resume-detail-card">
            <p class="resume-section-title">💼 Work Experience</p>
            {exp_block}
        </div>
        """, unsafe_allow_html=True)

    education = data.get("education") or []
    if education:
        edu_items = []
        for edu in education:
            degree_text = edu.get("degree", "Degree unknown")
            inst_text = edu.get("institution", "Institution unknown")
            year_text = edu.get("year", "")
            if year_text:
                edu_items.append(f"<div class='edu-item'><strong>{degree_text}</strong> — {inst_text} <span class='edu-yr'>{year_text}</span></div>")
            else:
                edu_items.append(f"<div class='edu-item'><strong>{degree_text}</strong> — {inst_text}</div>")
        edu_block = "<br>".join(edu_items)
        st.markdown(f"""
        <div class="resume-detail-card">
            <p class="resume-section-title">🎓 Education</p>
            {edu_block}
        </div>
        """, unsafe_allow_html=True)

    certs = data.get("certifications") or []
    if certs:
        certs_html = " ".join(f"<span class='cert-pill'>{c}</span>" for c in certs)
        st.markdown(f"""
        <div class="resume-detail-card">
            <p class="resume-section-title">📜 Certifications</p>
            <div>{certs_html}</div>
        </div>
        """, unsafe_allow_html=True)

    languages = data.get("languages") or []
    if languages:
        lang_html = " ".join(f"<span class='lang-pill'>{lang}</span>" for lang in languages)
        st.markdown(f"""
        <div class="resume-detail-card">
            <p class="resume-section-title">🌐 Languages</p>
            <div>{lang_html}</div>
        </div>
        """, unsafe_allow_html=True)

    filename = data.get("filename", "Unknown file")
    uploaded_at = data.get("uploaded_at", "")
    if uploaded_at:
        uploaded_at = uploaded_at[:16].replace("T", " ").replace("Z", "")
    st.markdown(f"""
    <p class="resume-meta-footer">📎 {filename} · Uploaded: {uploaded_at or "N/A"}</p>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# Analyse Page
# ──────────────────────────────────────────────────────────────────────────────

def _render_analyse_page():
    st.markdown("## Resume Analysis")

    resume_id = st.session_state.get("active_resume_id")
    if not resume_id:
        st.info("Select a resume from the sidebar to begin analysis.")
        return

    resume_data = get_resume(resume_id, st.session_state.access_token)
    if resume_data:
        st.markdown(f"**Analysing:** `{resume_data.get('filename')}` — {resume_data.get('candidate_name') or 'Unknown'}")

    st.markdown("---")

    col1, col2 = st.columns([1, 1])
    with col1:
        analysis_type = st.selectbox(
            "Analysis Type",
            options=["general", "job_match", "improvement"],
            format_func=lambda x: {"general": "🔍 General Analysis", "job_match": "🎯 Job Match", "improvement": "🔧 Improvement Plan"}[x],
        )
    with col2:
        st.markdown("&nbsp;", unsafe_allow_html=True)

    job_description = None
    if analysis_type == "job_match":
        job_description = st.text_area(
            "Paste Job Description",
            placeholder="Paste the full job description here for keyword matching and fit analysis...",
            height=150,
        )

    if st.button("Run Analysis", use_container_width=True, type="primary"):
        if analysis_type == "job_match" and not job_description:
            st.warning("Please paste a job description for job match analysis.")
            return
        with st.spinner("Running AI analysis... this may take a moment."):
            result = run_analysis(
                resume_id=resume_id,
                access_token=st.session_state.access_token,
                job_description=job_description,
                analysis_type=analysis_type,
            )
        if result["success"]:
            st.success("Analysis complete!")
            _show_analysis(result["data"])
        else:
            st.error(f"Analysis failed: {result['error']}")

    # Show past analyses
    st.markdown("---")
    st.markdown("### Previous Analyses")
    analyses = list_analyses(resume_id, st.session_state.access_token)
    if analyses:
        for i, a in enumerate(analyses):
            with st.expander(f"{a.get('analysis_type', '').replace('_', ' ').title()} — Score: {a.get('overall_score') or 0:.0f}/100 | {a.get('created_at', '')[:16]}"):
                _show_analysis(a, key_prefix=f"prev_{i}")
    else:
        st.caption("No analyses yet. Run your first analysis above.")

    # Cover letter generator
    _render_cover_letter_section()


def _show_analysis(analysis: dict, key_prefix: str = ""):
    render_score_dashboard(analysis)
    render_feedback_sections(analysis)

    resume_id = st.session_state.get("active_resume_id")
    analysis_id = analysis.get("id")
    if resume_id and analysis_id:
        pdf_bytes = export_analysis_pdf(resume_id, analysis_id, st.session_state.access_token)
        if pdf_bytes:
            unique_key = f"{key_prefix}_pdf_{analysis_id}" if key_prefix else f"pdf_{analysis_id}"
            st.download_button(
                "Download PDF Report",
                data=pdf_bytes,
                file_name=f"analysis_{analysis_id[:8]}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key=unique_key,
            )



# Cover Letter Section

def _render_cover_letter_section():
    st.markdown("---")
    st.markdown("### Cover Letter Generator")

    resume_id = st.session_state.get("active_resume_id")
    if not resume_id:
        st.info("Select a resume from the sidebar to generate a cover letter.")
        return

    with st.expander("Generate a tailored cover letter", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            tone = st.selectbox(
                "Tone",
                options=["professional", "enthusiastic", "concise", "formal", "conversational"],
                index=0,
            )
            company_name = st.text_input("Company Name (optional)", placeholder="e.g. Acme Corp")
        with col2:
            hiring_manager = st.text_input("Hiring Manager (optional)", placeholder="e.g. Jane Smith")
            job_description = st.text_area(
                "Job Description (optional)",
                placeholder="Paste job description to tailor the letter...",
                height=100,
            )

        if st.button("Generate Cover Letter", use_container_width=True, type="primary"):
            with st.spinner("Writing your cover letter..."):
                result = generate_cover_letter(
                    resume_id=resume_id,
                    access_token=st.session_state.access_token,
                    job_description=job_description or None,
                    tone=tone,
                    company_name=company_name or None,
                    hiring_manager=hiring_manager or None,
                )
            if result["success"]:
                data = result["data"]
                st.success("Cover letter generated!")
                subject = data.get("subject")
                letter = data.get("cover_letter", "")
                if subject:
                    st.markdown(f"**Subject:** {subject}")
                st.markdown("**Preview:**")
                st.markdown(letter.replace("\n", "  \n"))
                st.markdown("**Copy-paste version:**")
                st.text_area("Cover Letter", letter, height=400, label_visibility="collapsed")
                st.download_button(
                    "Download as Text",
                    data=f"Subject: {subject or 'Cover Letter'}\n\n{letter}",
                    file_name="cover_letter.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
            else:
                st.error(f"Generation failed: {result['error']}")


# Chat Page


def _render_chat_page():
    st.markdown('<p class="app-title">AI Career Coach</p>', unsafe_allow_html=True)

    resume_id = st.session_state.get("active_resume_id")
    if resume_id:
        st.caption(f"📎 {st.session_state.get('active_resume_name', '')}")

    _render_welcome_message()
    _render_chat_history()
    _handle_pending_message()

    # Quick suggestions
    if not st.session_state.messages:
        st.markdown("**Quick questions:**")
        cols = st.columns(2)
        for i, suggestion in enumerate(QUICK_SUGGESTIONS[:4]):
            with cols[i % 2]:
                if st.button(suggestion, key=f"quick_{i}", use_container_width=True):
                    st.session_state.pending_msg = suggestion
                    st.rerun()

    _handle_chat_input()


def _render_welcome_message():
    if not st.session_state.messages:
        with st.chat_message("assistant"):
            st.markdown("""
            Hi! I'm your **AI Career Coach**.

            I can help you with:
            - Understanding your resume analysis scores
            - Specific improvement suggestions
            - Tailoring your resume for a role
            - Interview preparation tips
            - Salary expectations for your profile
            - Writing cover letters

            Select a resume from the sidebar and start chatting!
            """)


def _render_chat_history():
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])


def _handle_pending_message():
    if st.session_state.pending_msg:
        msg = st.session_state.pending_msg
        st.session_state.pending_msg = None
        _process_message(msg)


def _handle_chat_input():
    user_input = st.chat_input("Ask about your resume, career, or job search...")
    if user_input:
        _process_message(user_input)


def _process_message(user_message: str):
    st.session_state.messages.append({"role": "user", "content": user_message})
    with st.chat_message("user"):
        st.markdown(user_message)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = send_chat_message(
                st.session_state.session_id,
                user_message,
                st.session_state.access_token,
                resume_id=st.session_state.get("active_resume_id"),
            )

            if result.get("session_id"):
                st.session_state.session_id = result["session_id"]

            if result.get("intent") == "auth_error":
                st.warning("Session expired. Please login again.")
                do_logout()
                st.rerun()
                return

        reply = result.get("reply", "Sorry, something went wrong.")
        intent = result.get("intent", "general")

        st.markdown(reply)
        if intent and intent not in ("error", "auth_error"):
            st.caption(f"Intent: {INTENT_LABELS.get(intent, intent)}")

    st.session_state.messages.append({"role": "assistant", "content": reply})
