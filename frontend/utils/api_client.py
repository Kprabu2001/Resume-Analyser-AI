import requests
from typing import Optional
from config.settings import BACKEND_URL

_session = requests.Session()


def signup(full_name: str, email: str, password: str) -> dict:
    try:
        r = _session.post(
            f"{BACKEND_URL}/auth/signup",
            json={"full_name": full_name, "email": email, "password": password},
            timeout=10,
        )
        if r.status_code == 201:
            return {"success": True, "data": r.json()}
        return {"success": False, "error": r.json().get("detail", "Signup failed")}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def login(email: str, password: str) -> dict:
    try:
        r = _session.post(
            f"{BACKEND_URL}/auth/login",
            json={"email": email, "password": password},
            timeout=10,
        )
        if r.status_code == 200:
            body = r.json()
            data = body.get("data") or body
            at = data.get("access_token")
            rt = data.get("refresh_token")
            return {
                "success": True,
                "access_token": at,
                "refresh_token": rt,
                "email": data.get("email"),
                "user_id": data.get("user_id"),
            }
        return {"success": False, "error": r.json().get("detail", "Login failed")}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Cannot connect to backend"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def refresh_access_token(refresh_token: str) -> Optional[dict]:
    try:
        r = _session.post(
            f"{BACKEND_URL}/auth/refresh",
            cookies={"res_ref_token": refresh_token},
            timeout=10,
        )
        if r.status_code == 200:
            body = r.json()
            data = body.get("data") or body
            at = data.get("access_token")
            rt = data.get("refresh_token")
            return {
                "success": True,
                "access_token": at,
                "refresh_token": rt,
                "email": data.get("email"),
                "user_id": data.get("user_id"),
            }
        return None
    except Exception:
        return None


def logout() -> bool:
    try:
        r = _session.post(f"{BACKEND_URL}/auth/logout", timeout=10)
        _session.cookies.clear()
        return r.status_code == 200
    except Exception:
        _session.cookies.clear()
        return False


def check_health() -> bool:
    try:
        r = _session.get(f"{BACKEND_URL}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def _make_request(method: str, url: str, access_token: str, **kwargs) -> requests.Response:
    import streamlit as st

    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {access_token}"

    r = _session.request(method, url, headers=headers, **kwargs)

    if r.status_code == 401:
        try:
            refresh_token = st.session_state.get("refresh_token")
            if refresh_token:
                result = refresh_access_token(refresh_token)
                new_token = result.get("access_token") if result else None
                if new_token:
                    st.session_state.access_token = new_token
                    new_refresh = result.get("refresh_token")
                    if new_refresh:
                        st.session_state.refresh_token = new_refresh
                    st.session_state._pending_cookies = (new_token, new_refresh or st.session_state.get("refresh_token"))
                    headers["Authorization"] = f"Bearer {new_token}"
                    r = _session.request(method, url, headers=headers, **kwargs)
                else:
                    st.session_state.logged_in = False
                    st.session_state.access_token = None
                    st.session_state.refresh_token = None
        except Exception:
            pass

    return r


def upload_resume(file_bytes: bytes, filename: str, access_token: str) -> dict:
    try:
        r = _make_request(
            "POST",
            f"{BACKEND_URL}/resumes/upload",
            access_token,
            files={"file": (filename, file_bytes, "application/pdf")},
            timeout=60,
        )
        if r.status_code == 201:
            return {"success": True, "data": r.json()}
        if r.status_code == 401:
            return {"success": False, "error": "auth_error"}
        return {"success": False, "error": r.json().get("detail", "Upload failed")}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timed out"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def list_resumes(access_token: str) -> list:
    try:
        r = _make_request("GET", f"{BACKEND_URL}/resumes/", access_token, timeout=15)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


def get_resume(resume_id: str, access_token: str) -> Optional[dict]:
    try:
        r = _make_request("GET", f"{BACKEND_URL}/resumes/{resume_id}", access_token, timeout=15)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def delete_resume(resume_id: str, access_token: str) -> bool:
    try:
        r = _make_request("DELETE", f"{BACKEND_URL}/resumes/{resume_id}", access_token, timeout=10)
        return r.status_code == 204
    except Exception:
        return False


def run_analysis(
    resume_id: str,
    access_token: str,
    job_description: Optional[str] = None,
    analysis_type: str = "general",
) -> dict:
    try:
        r = _make_request(
            "POST",
            f"{BACKEND_URL}/resumes/analyse",
            access_token,
            json={
                "resume_id": resume_id,
                "job_description": job_description,
                "analysis_type": analysis_type,
            },
            timeout=60,
        )
        if r.status_code == 201:
            return {"success": True, "data": r.json()}
        return {"success": False, "error": r.json().get("detail", "Analysis failed")}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def list_analyses(resume_id: str, access_token: str) -> list:
    try:
        r = _make_request(
            "GET", f"{BACKEND_URL}/resumes/{resume_id}/analyses", access_token, timeout=15
        )
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


def send_chat_message(
    session_id: str, message: str, access_token: str, resume_id: Optional[str] = None
) -> dict:
    try:
        payload = {"session_id": session_id, "message": message}
        if resume_id:
            payload["resume_id"] = resume_id
        r = _make_request(
            "POST",
            f"{BACKEND_URL}/chat/",
            access_token,
            json=payload,
            timeout=30,
        )
        if r.status_code == 401:
            return {"reply": "\u26a0\ufe0f Session expired. Please login again.", "intent": "auth_error"}
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        return {"reply": "\u274c Cannot connect to backend.", "intent": "error"}
    except requests.exceptions.Timeout:
        return {"reply": "\u23f3 Request timed out. Please try again.", "intent": "error"}
    except Exception as exc:
        return {"reply": f"\u274c Error: {str(exc)}", "intent": "error"}


def export_analysis_pdf(resume_id: str, analysis_id: str, access_token: str) -> Optional[bytes]:
    try:
        r = _make_request(
            "GET", f"{BACKEND_URL}/resumes/{resume_id}/analyses/{analysis_id}/export",
            access_token, timeout=30,
        )
        return r.content if r.status_code == 200 else None
    except Exception:
        return None


def generate_cover_letter(
    resume_id: str, access_token: str, job_description: Optional[str] = None,
    tone: str = "professional", company_name: Optional[str] = None,
    hiring_manager: Optional[str] = None,
) -> dict:
    try:
        payload = {"resume_id": resume_id, "tone": tone}
        if job_description:
            payload["job_description"] = job_description
        if company_name:
            payload["company_name"] = company_name
        if hiring_manager:
            payload["hiring_manager"] = hiring_manager
        r = _make_request("POST", f"{BACKEND_URL}/resumes/cover-letter", access_token, json=payload, timeout=30)
        if r.status_code == 200:
            return {"success": True, "data": r.json()}
        return {"success": False, "error": r.json().get("detail", "Generation failed")}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def clear_chat_session(session_id: str, access_token: str) -> bool:
    try:
        r = _make_request(
            "DELETE", f"{BACKEND_URL}/chat/session/{session_id}", access_token, timeout=10
        )
        return r.status_code == 200
    except Exception:
        return False
