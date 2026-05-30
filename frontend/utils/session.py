import json
from datetime import datetime, timezone
from base64 import urlsafe_b64decode

import streamlit as st
import streamlit.components.v1 as components

from utils.api_client import (
    check_health, logout as api_logout, refresh_access_token, _session,
)

COOKIE_ACCESS = "res_acc_token"
COOKIE_REFRESH = "res_ref_token"


def _decode_jwt_payload(token: str) -> dict | None:
    try:
        parts = token.split(".")
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += "=" * padding
        return json.loads(urlsafe_b64decode(payload))
    except Exception:
        return None


def _is_token_expired(token: str) -> bool:
    payload = _decode_jwt_payload(token)
    if not payload:
        return True
    exp = payload.get("exp")
    if not exp:
        return True
    return datetime.fromtimestamp(exp, tz=timezone.utc) <= datetime.now(timezone.utc)


def _read_tokens() -> tuple:
    at = st.session_state.get("access_token")
    rt = st.session_state.get("refresh_token")
    if at:
        return at, rt

    try:
        cookies = _session.cookies.get_dict()
        at = cookies.get(COOKIE_ACCESS)
        rt = cookies.get(COOKIE_REFRESH)
        if at:
            return at, rt
    except Exception:
        pass

    try:
        at = st.context.cookies.get(COOKIE_ACCESS)
        rt = st.context.cookies.get(COOKIE_REFRESH)
    except Exception:
        pass

    return at, rt


def init_session() -> None:
    defaults: dict = {
        "logged_in": False,
        "access_token": None,
        "refresh_token": None,
        "user_email": None,
        "user_id": None,
        "session_id": None,
        "messages": [],
        "pending_msg": None,
        "backend_ok": check_health(),
        "active_resume_id": None,
        "active_resume_name": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if not st.session_state.logged_in:
        _try_restore_session()


def _try_restore_session() -> None:
    if st.session_state.pop("_skip_restore", False):
        return
    try:
        access_token, refresh_token = _read_tokens()
        if not access_token and not refresh_token:
            return

        if access_token and not _is_token_expired(access_token):
            st.session_state.logged_in = True
            st.session_state.access_token = access_token
            st.session_state.refresh_token = refresh_token
            payload = _decode_jwt_payload(access_token)
            st.session_state.user_email = (payload or {}).get("email")
            st.session_state.user_id = (payload or {}).get("user_id")
            st.session_state._pending_cookies = (access_token, refresh_token)
            return

        if refresh_token:
            result = refresh_access_token(refresh_token)
            if result and result.get("success"):
                st.session_state.logged_in = True
                st.session_state.access_token = result["access_token"]
                st.session_state.user_email = result.get("email")
                st.session_state.user_id = result.get("user_id")
                new_refresh = result.get("refresh_token")
                st.session_state.refresh_token = new_refresh or refresh_token
                st.session_state._pending_cookies = (result["access_token"], new_refresh or refresh_token)
    except Exception:
        pass


def do_login(access_token: str, email: str, user_id: str | None = None, refresh_token: str | None = None) -> None:
    st.session_state.logged_in = True
    st.session_state.access_token = access_token
    st.session_state.refresh_token = refresh_token
    st.session_state.user_email = email
    st.session_state.user_id = user_id

    if refresh_token:
        st.session_state._pending_cookies = (access_token, refresh_token)


def flush_pending_cookies() -> None:
    pending = st.session_state.pop("_pending_cookies", None)
    if pending:
        acc_payload = _decode_jwt_payload(pending[0])
        ref_payload = _decode_jwt_payload(pending[1])
        acc_exp = acc_payload.get("exp") if acc_payload else None
        ref_exp = ref_payload.get("exp") if ref_payload else None
        acc_max_age = max(1, int(acc_exp - datetime.now(timezone.utc).timestamp())) if acc_exp else 300
        ref_max_age = max(1, int(ref_exp - datetime.now(timezone.utc).timestamp())) if ref_exp else 604800
        components.html(
            "<script>"
            f"document.cookie='{COOKIE_ACCESS}={pending[0]};path=/;max-age={acc_max_age};SameSite=Lax';"
            f"document.cookie='{COOKIE_REFRESH}={pending[1]};path=/;max-age={ref_max_age};SameSite=Lax';"
            "</script>",
            height=0, width=0,
        )

    if st.session_state.pop("_pending_clear_cookies", False):
        components.html(
            "<script>"
            f"document.cookie='{COOKIE_ACCESS}=;path=/;max-age=0';"
            f"document.cookie='{COOKIE_REFRESH}=;path=/;max-age=0';"
            "</script>",
            height=0, width=0,
        )


def do_logout() -> None:
    st.session_state._skip_restore = True
    api_logout()
    st.session_state._pending_clear_cookies = True

    st.session_state.logged_in = False
    st.session_state.access_token = None
    st.session_state.refresh_token = None
    st.session_state.user_email = None
    st.session_state.user_id = None
    st.session_state.messages = []
    st.session_state.session_id = None
    st.session_state.active_resume_id = None
    st.session_state.active_resume_name = None


def reset_chat() -> None:
    st.session_state.messages = []
    st.session_state.session_id = None


def is_logged_in() -> bool:
    return (
        st.session_state.get("logged_in", False)
        and st.session_state.get("access_token") is not None
    )
