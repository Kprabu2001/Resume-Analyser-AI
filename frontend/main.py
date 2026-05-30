import streamlit as st

from config.settings import APP_TITLE, APP_ICON
from config.styles import load_css
from utils.session import init_session, flush_pending_cookies, is_logged_in
from pages.auth_page import show_auth_page
from pages.main_page import show_main_page

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
)

load_css()
init_session()
flush_pending_cookies()

if is_logged_in():
    show_main_page()
else:
    show_auth_page()
