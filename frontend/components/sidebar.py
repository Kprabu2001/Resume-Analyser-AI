import streamlit as st
from utils.session import do_logout, reset_chat
from utils.api_client import list_resumes, delete_resume


def render_sidebar():
    with st.sidebar:
        st.markdown('<p class="sb-title">Resume Analyser</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="sb-email">{st.session_state.user_email}</p>', unsafe_allow_html=True)
        st.markdown('<div class="sb-line"></div>', unsafe_allow_html=True)

        if st.button("+ New Chat", use_container_width=True, key="new_chat_btn"):
            reset_chat()
            st.rerun()

        st.markdown('<div class="sb-line"></div>', unsafe_allow_html=True)

        nav = [("Chat", "chat"), ("Upload", "upload"), ("Analyse", "analyse")]
        current = st.session_state.get("active_page", "chat")

        for label, page in nav:
            active = current == page
            kind = "primary" if active else "secondary"
            if st.button(label, key=f"nav_{page}", use_container_width=True, type=kind):
                st.session_state.active_page = page
                st.rerun()

        st.markdown('<div class="sb-line"></div>', unsafe_allow_html=True)

        st.markdown('<p class="sb-label">Select Resume</p>', unsafe_allow_html=True)
        resumes = list_resumes(st.session_state.access_token)

        if resumes:
            name_to_id = {resume["filename"]: resume["id"] for resume in resumes}
            filenames = list(name_to_id.keys())

            selected_index = 0
            active_id = st.session_state.get("active_resume_id")
            if active_id:
                for index, file_id in enumerate(name_to_id.values()):
                    if file_id == active_id:
                        selected_index = index
                        break

            selected_filename = st.selectbox(
                "Choose",
                options=filenames,
                index=selected_index,
                label_visibility="collapsed",
                key="resume_selector",
            )

            if selected_filename:
                st.session_state.active_resume_id = name_to_id[selected_filename]
                st.session_state.active_resume_name = selected_filename

            st.markdown('<p class="sb-label" style="margin-top:8px">Recently Uploaded</p>', unsafe_allow_html=True)

            name_col, delete_col = st.columns([5, 1])

            with name_col:
                for resume in reversed(resumes[:5]):
                    resume_id = resume["id"]
                    is_selected = st.session_state.get("active_resume_id") == resume_id
                    button_type = "primary" if is_selected else "secondary"
                    if st.button(
                        resume["filename"],
                        key=f"sel_{resume_id}",
                        use_container_width=True,
                        type=button_type,
                    ):
                        st.session_state.active_resume_id = resume_id
                        st.session_state.active_resume_name = resume["filename"]
                        st.rerun()

            with delete_col:
                for resume in reversed(resumes[:5]):
                    resume_id = resume["id"]
                    if st.button("✕", key=f"del_{resume_id}"):
                        delete_resume(resume_id, st.session_state.access_token)
                        if st.session_state.get("active_resume_id") == resume_id:
                            st.session_state.active_resume_id = None
                            st.session_state.active_resume_name = None
                        st.rerun()

        else:
            st.caption("No resumes uploaded yet.")
            st.session_state.active_resume_id = None

        st.markdown('<div class="sb-spacer"></div>', unsafe_allow_html=True)

        st.markdown('<div class="sb-line"></div>', unsafe_allow_html=True)

        if st.button("Log out", key="logout_btn", use_container_width=True):
            do_logout()
            st.rerun()
