import streamlit as st

from utils.api_client import login, signup
from utils.session import do_login


def show_auth_page() -> None:
    st.markdown('<div style="text-align: center; padding: 1rem 0;">', unsafe_allow_html=True)
    st.markdown('<p class="auth-title">Resume Analyser AI</p>', unsafe_allow_html=True)
    st.markdown('<p class="auth-sub">AI-powered resume analysis & career coaching</p>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.2, 1])

    with col:
        tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

        with tab_login:
            _render_login_tab()

        with tab_signup:
            _render_signup_tab()

    st.markdown("---")
    _, status_col, _ = st.columns([1, 2, 1])
    with status_col:
        if st.session_state.backend_ok:
            st.markdown(
                '<p class="online" style="text-align:center;">Backend Connected</p>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<p class="offline" style="text-align:center;">'
                "Backend Offline \u2014 run: uvicorn app.main:app --reload"
                "</p>",
                unsafe_allow_html=True,
            )


def _render_login_tab() -> None:
    st.markdown("")
    email = st.text_input("Email", placeholder="you@example.com", key="login_email")
    password = st.text_input(
        "Password", placeholder="Your password", key="login_password", type="password"
    )
    st.markdown("")

    if st.button("Login", key="login_btn", use_container_width=True, type="primary"):
        if not email or not password:
            st.error("Please fill in all fields.")
            return

        with st.spinner("Logging in\u2026"):
            result = login(email, password)

        if result["success"]:
            do_login(
                access_token=result["access_token"],
                refresh_token=result.get("refresh_token"),
                email=result["email"],
                user_id=result.get("user_id"),
            )
            st.success(f"Welcome back, {result['email']}!")
            st.rerun()
        else:
            st.error(f"Login failed: {result['error']}")


def _render_signup_tab() -> None:
    st.markdown("")
    full_name = st.text_input("Full Name", placeholder="Your name", key="signup_name")
    email = st.text_input("Email", placeholder="you@example.com", key="signup_email")
    password = st.text_input(
        "Password", placeholder="Min 6 characters", key="signup_password", type="password"
    )
    confirm = st.text_input(
        "Confirm Password", placeholder="Repeat password", key="signup_confirm", type="password"
    )
    st.markdown("")

    if st.button("Create Account", key="signup_btn", use_container_width=True, type="primary"):
        if not all([full_name, email, password, confirm]):
            st.error("Please fill in all fields.")
            return
        if password != confirm:
            st.error("Passwords do not match.")
            return
        if len(password) < 6:
            st.error("Password must be at least 6 characters.")
            return

        with st.spinner("Creating account\u2026"):
            result = signup(full_name, email, password)

        if result["success"]:
            st.success("Account created! Please login.")
        else:
            st.error(f"Signup failed: {result['error']}")
