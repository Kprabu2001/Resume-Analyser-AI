import os

APP_TITLE = "Resume Analyser AI"
APP_ICON = "📄"
APP_VERSION = "1.0.0"

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

INTENT_LABELS = {
    "analysis_query": "📊 Analysis Query",
    "improvement": "🔧 Improvement Tips",
    "skills_advice": "💡 Skills Advice",
    "job_advice": "💼 Job Advice",
    "salary_info": "💰 Salary Info",
    "interview_prep": "🎯 Interview Prep",
    "cover_letter": "✉️ Cover Letter",
    "general": "💬 General",
}

SCORE_COLORS = {
    "excellent": "#22c55e",   # green
    "good": "#84cc16",        # lime
    "average": "#f59e0b",     # amber
    "poor": "#ef4444",        # red
}

QUICK_SUGGESTIONS = [
    "What are my key strengths?",
    "How can I improve my ATS score?",
    "What skills am I missing?",
    "How does my experience compare to industry standards?",
    "Write a professional summary for my resume",
    "What roles am I a good fit for?",
    "How can I tailor my resume for a data science role?",
    "What interview questions should I prepare for?",
]
