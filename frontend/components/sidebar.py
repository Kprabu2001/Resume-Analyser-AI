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
            options = {r["filename"]: r["id"] for r in resumes}

            idx = 0
            active_id = st.session_state.get("active_resume_id")
            if active_id:
                for i, rid in enumerate(options.values()):
                    if rid == active_id:
                        idx = i
                        break

            selected = st.selectbox(
                "Choose",
                options=list(options.keys()),
                index=idx,
                label_visibility="collapsed",
                key="resume_selector",
            )

            if selected:
                st.session_state.active_resume_id = options[selected]
                st.session_state.active_resume_name = selected

            st.markdown('<p class="sb-label" style="margin-top:8px">Recently Uploaded</p>', unsafe_allow_html=True)
            st.markdown('<div class="sb-recent-list">', unsafe_allow_html=True)

            for r in reversed(resumes[:5]):
                name = r["filename"]
                rid = r["id"]
                is_sel = st.session_state.get("active_resume_id") == rid
                del_btn_key = f"del_recent_{rid}"
                sel_btn_key = f"sel_recent_{rid}"

                col_a, col_b = st.columns([5, 1])
                with col_a:
                    name_cls = "sb-recent-name active" if is_sel else "sb-recent-name"
                    st.markdown(f'<div class="{name_cls}">', unsafe_allow_html=True)
                    if st.button(name, key=sel_btn_key, use_container_width=True):
                        st.session_state.active_resume_id = rid
                        st.session_state.active_resume_name = name
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                with col_b:
                    st.markdown('<div class="sb-recent-del">', unsafe_allow_html=True)
                    if st.button("x", key=del_btn_key):
                        delete_resume(rid, st.session_state.access_token)
                        if st.session_state.get("active_resume_id") == rid:
                            st.session_state.active_resume_id = None
                            st.session_state.active_resume_name = None
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

        else:
            st.caption("No resumes uploaded yet.")
            st.session_state.active_resume_id = None

        st.markdown('<div class="sb-spacer"></div>', unsafe_allow_html=True)

        st.markdown('<div class="sb-line"></div>', unsafe_allow_html=True)

        if st.button("Log out", key="logout_btn", use_container_width=True):
            do_logout()
            st.rerun()
