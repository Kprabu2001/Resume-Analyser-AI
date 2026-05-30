import streamlit as st


def load_css():
    st.markdown("""
    <style>
    /* ── Global ── */
    [data-testid="stAppViewContainer"] { background: #ffffff; }
    [data-testid="stSidebar"] {
        background: #f9fafb !important;
        border-right: 1px solid #e5e7eb;
    }
    .stChatMessage { background: transparent !important; }

    /* ── Typography ── */
    .app-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #0f172a;
        margin: 0 0 1rem 0;
    }
    .app-sub {
        color: #64748b;
        font-size: 0.9rem;
        margin: 0.2rem 0 1rem 0;
    }
    .auth-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #0f172a;
        text-align: center;
    }
    .auth-sub {
        color: #64748b;
        text-align: center;
        margin-bottom: 1.5rem;
    }

    /* ── Score cards ── */
    .score-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.8rem;
        text-align: center;
        margin: 0.3rem;
    }
    .score-value { font-size: 1.8rem; font-weight: 700; margin: 0; }
    .score-label { color: #64748b; font-size: 0.7rem; margin: 0; }

    /* ── Feedback lists ── */
    .strength-item { color: #16a34a; margin: 0.15rem 0; font-size: 0.85rem; }
    .weakness-item { color: #dc2626; margin: 0.15rem 0; font-size: 0.85rem; }
    .suggestion-item { color: #d97706; margin: 0.15rem 0; font-size: 0.85rem; }

    /* ── Status indicators ── */
    .online  { color: #16a34a; font-size: 0.8rem; }
    .offline { color: #dc2626; font-size: 0.8rem; }

    /* ── Misc ── */
    div[data-testid="stHorizontalBlock"] { gap: 0.5rem; }

    /* ── Resume Detail Cards ── */
    .resume-detail-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.6rem 0;
    }
    .resume-detail-card h2 {
        color: #111827;
        margin: 0 0 0.15rem 0;
        font-size: 1.3rem;
        font-weight: 600;
    }
    .role-sub {
        color: #6b7280;
        margin: 0 0 0.6rem 0;
        font-size: 0.9rem;
    }
    .resume-section-title {
        font-size: 0.8rem;
        font-weight: 600;
        color: #374151;
        margin: 0 0 0.5rem 0;
        padding-bottom: 0.3rem;
        border-bottom: 1px solid #f3f4f6;
    }
    .resume-contact-bar {
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
        margin-top: 0.5rem;
    }
    .detail-badge {
        display: inline-block;
        background: #f3f4f6;
        color: #374151;
        border-radius: 6px;
        padding: 0.25rem 0.5rem;
        font-size: 0.78rem;
    }
    .detail-key {
        color: #9ca3af;
        font-size: 0.75rem;
        margin: 0;
    }
    .detail-value {
        color: #111827;
        font-size: 0.95rem;
        font-weight: 600;
        margin: 0.15rem 0 0 0;
    }
    .exp-item {
        padding: 0.4rem 0;
        border-bottom: 1px solid #f9fafb;
        font-size: 0.85rem;
        color: #374151;
    }
    .exp-item:last-child {
        border-bottom: none;
    }
    .exp-item strong {
        color: #111827;
    }
    .exp-dur {
        color: #6366f1;
        font-size: 0.75rem;
        font-weight: 500;
    }
    .edu-item {
        padding: 0.4rem 0;
        border-bottom: 1px solid #f9fafb;
        font-size: 0.85rem;
        color: #374151;
    }
    .edu-item:last-child {
        border-bottom: none;
    }
    .edu-item strong {
        color: #111827;
    }
    .edu-yr {
        color: #6366f1;
        font-size: 0.75rem;
        font-weight: 500;
    }
    .skill-tag {
        display: inline-block;
        background: #eef2ff;
        color: #4f46e5;
        border-radius: 999px;
        padding: 0.15rem 0.5rem;
        font-size: 0.75rem;
        margin: 0.1rem;
    }
    .cert-pill {
        display: inline-block;
        background: #ecfdf5;
        color: #059669;
        border-radius: 999px;
        padding: 0.15rem 0.5rem;
        font-size: 0.75rem;
        margin: 0.1rem;
    }
    .lang-pill {
        display: inline-block;
        background: #eef2ff;
        color: #4f46e5;
        border-radius: 999px;
        padding: 0.15rem 0.5rem;
        font-size: 0.75rem;
        margin: 0.1rem;
    }
    .resume-meta-footer {
        color: #9ca3af;
        font-size: 0.72rem;
        margin-top: 0.8rem;
        text-align: right;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        padding: 0.5rem 0.4rem !important;
    }
    .sb-title {
        font-size: 0.8rem;
        font-weight: 600;
        color: #111827;
        margin: 0;
        padding: 0;
        line-height: 1.1;
    }
    .sb-email {
        font-size: 0.65rem;
        color: #9ca3af;
        margin: 0;
        padding: 0;
        line-height: 1.1;
    }
    .sb-label {
        font-size: 0.6rem;
        font-weight: 600;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin: 0;
        padding: 0;
        line-height: 1.1;
    }
    .sb-line {
        border-top: 1px solid #e5e7eb;
        margin: 4px 0;
        padding: 0;
    }
    .sb-spacer {
        flex-grow: 1;
        height: 0;
    }

    /* ── Sidebar buttons ── */
    [data-testid="stSidebar"] .stButton {
        margin: 0 !important;
        padding: 0 !important;
    }
    [data-testid="stSidebar"] .stButton > button {
        padding: 3px 6px !important;
        margin: 0 !important;
        min-height: 0 !important;
    }
    [data-testid="stSidebar"] button[kind="primary"] {
        background: #f3f4f6;
        border: none;
        color: #111827;
        font-size: 0.68rem;
        font-weight: 500;
        border-radius: 4px;
        justify-content: flex-start;
    }
    [data-testid="stSidebar"] button[kind="primary"]:hover {
        background: #e5e7eb;
    }
    [data-testid="stSidebar"] button[kind="secondary"] {
        background: transparent;
        border: none;
        color: #4b5563;
        font-size: 0.68rem;
        font-weight: 400;
        border-radius: 4px;
        justify-content: flex-start;
    }
    [data-testid="stSidebar"] button[kind="secondary"]:hover {
        background: #f9fafb;
    }

    /* ── New Chat ── */
    [data-testid="stSidebar"] .stButton:first-child button {
        border: 1px solid #d1d5db;
        color: #374151;
        font-size: 0.7rem;
        font-weight: 500;
        padding: 4px 8px !important;
        border-radius: 4px;
        justify-content: center;
    }
    [data-testid="stSidebar"] .stButton:first-child button:hover {
        background: #f9fafb;
    }

    /* ── Recently Uploaded List ── */
    .sb-recent-list {
        margin-top: 4px;
    }
    [data-testid="stSidebar"] .sb-recent-name {
        padding: 0 !important;
        margin: 0 !important;
    }
    [data-testid="stSidebar"] .sb-recent-name button {
        background: transparent !important;
        border: none !important;
        color: #6b7280 !important;
        font-size: 0.68rem !important;
        padding: 2px 4px !important;
        justify-content: flex-start !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        white-space: nowrap !important;
        width: 100% !important;
        min-height: 0 !important;
        height: auto !important;
    }
    [data-testid="stSidebar"] .sb-recent-name button:hover {
        background: #f3f4f6 !important;
    }
    [data-testid="stSidebar"] .sb-recent-name.active button {
        background: #e5e7eb !important;
        color: #111827 !important;
        font-weight: 500 !important;
    }
    [data-testid="stSidebar"] .sb-recent-del {
        padding: 0 !important;
        margin: 0 !important;
    }
    [data-testid="stSidebar"] .sb-recent-del button {
        color: #d1d5db !important;
        font-size: 0.6rem !important;
        padding: 2px 4px !important;
        margin: 0 !important;
        justify-content: center !important;
        min-height: 0 !important;
        height: auto !important;
        width: 100% !important;
    }
    [data-testid="stSidebar"] .sb-recent-del button:hover {
        color: #ef4444 !important;
    }

    /* ── Delete ── */
    [data-testid="stSidebar"] button[kind="secondary"][data-testid*="del_"] {
        color: #9ca3af;
        font-size: 0.65rem;
        padding: 2px 4px !important;
        justify-content: center;
    }
    [data-testid="stSidebar"] button[kind="secondary"][data-testid*="del_"]:hover {
        color: #ef4444;
    }

    /* ── Logout ── */
    [data-testid="stSidebar"] button[kind="secondary"][aria-label*="Log"] {
        color: #9ca3af;
        font-size: 0.65rem;
        justify-content: center;
    }
    [data-testid="stSidebar"] button[kind="secondary"][aria-label*="Log"]:hover {
        color: #ef4444;
    }

    /* ── Sidebar columns ── */
    [data-testid="stSidebar"] .row-widget.stHorizontal {
        gap: 0 !important;
    }
    [data-testid="stSidebar"] .row-widget.stHorizontal > div {
        padding: 0 !important;
    }
    [data-testid="stSidebar"] .stColumn {
        padding: 0 !important;
    }

    /* ── Sidebar caption ── */
    [data-testid="stSidebar"] p {
        margin: 0 !important;
        padding: 0 !important;
    }

    /* ── Global text color ── */
    .main .stMarkdown p, .main .stMarkdown span, .main .stMarkdown div {
        color: #374151;
    }
    .main h1, .main h2, .main h3, .main h4 {
        color: #111827;
    }
    </style>
    """, unsafe_allow_html=True)
