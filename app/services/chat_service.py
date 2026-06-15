import logging
from typing import Optional

from groq import Groq

from app.base.base_repository import BaseRepository
from app.base.base_service import BaseService
from app.core.config import settings
from app.database.models import Resume
from app.database.models import ChatSession
from app.repositories.resume_repository import ResumeRepository

logger = logging.getLogger(__name__)

client = Groq(api_key=settings.groq_api_key)

SYSTEM_PROMPT = """You are Resume Analyser AI, an expert career coach and resume consultant.

YOUR ONLY JOB is to help users with:
1. Understanding their resume analysis results (scores, strengths, weaknesses)
2. Answering questions about their resume content
3. Career advice — how to improve their resume for specific roles
4. Keyword optimisation and ATS tips
5. Interview preparation based on their profile
6. Salary expectations and job market insights for their skill set
7. Cover letter guidance

STRICT RULES:
- ONLY answer resume, career, job search, and professional development questions
- Do NOT write code, answer general knowledge, tell jokes, or engage in off-topic chat
- If asked anything outside career/resume topics: say "I'm Resume Analyser AI and I can only help with resume and career questions. How can I help you today? 📄"
- Be encouraging, specific, and actionable in your advice

When resume data is provided in [Context], use it to give personalised, specific answers.
Always reference the candidate's actual skills, experience, and scores when relevant."""


def _detect_intent(message: str) -> str:
    msg = message.lower()
    if any(w in msg for w in ["score", "rating", "ats", "analysis", "result", "feedback"]):
        return "analysis_query"
    if any(w in msg for w in ["improve", "better", "fix", "enhance", "suggestion", "tip", "how to"]):
        return "improvement"
    if any(w in msg for w in ["skill", "technology", "tool", "language", "framework"]):
        return "skills_advice"
    if any(w in msg for w in ["job", "role", "position", "apply", "company", "hiring"]):
        return "job_advice"
    if any(w in msg for w in ["salary", "pay", "compensation", "package", "ctc"]):
        return "salary_info"
    if any(w in msg for w in ["interview", "question", "prepare", "hr", "technical round"]):
        return "interview_prep"
    if any(w in msg for w in ["cover letter", "summary", "objective", "profile"]):
        return "cover_letter"
    return "general"


def _build_resume_context(resume: Resume) -> str:
    if not resume:
        return ""
    return f"""
[Context — Active Resume]
Candidate: {resume.candidate_name or 'Unknown'}
Current Role: {resume.current_role or 'N/A'}
Years of Experience: {resume.years_of_experience or 'N/A'}
Education: {resume.education_level or 'N/A'}
Skills: {', '.join(resume.skills or []) or 'N/A'}
Certifications: {', '.join(resume.certifications or []) or 'N/A'}
Languages: {', '.join(resume.languages or []) or 'N/A'}
"""


class ChatService(BaseService):

    def _get_repository(self) -> BaseRepository:
        return ResumeRepository(self.session)

    def create_session(self, user_id: str) -> ChatSession:
        return self.repository.create_chat_session(user_id)

    def get_history(self, session_id: str) -> list[dict]:
        return self.repository.get_chat_history(session_id)

    def clear_session(self, session_id: str) -> None:
        with self.get_db_session():
            self.repository.clear_chat_session(session_id)

    def save_message(
        self,
        session_id: str,
        user_id: str,
        role: str,
        content: str,
        resume_id: Optional[str] = None,
    ) -> None:
        with self.get_db_session():
            self.repository.create_chat_message(
                session_id=session_id,
                user_id=user_id,
                role=role,
                content=content,
                resume_id=resume_id,
            )

    def get_ai_response(
        self,
        session_id: str,
        user_message: str,
        user_id: str,
        resume: Optional[Resume] = None,
    ) -> dict:
        history = self.get_history(session_id)
        intent = _detect_intent(user_message)

        context = _build_resume_context(resume) if resume else ""
        final_message = f"{user_message}\n\n{context}" if context else user_message

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(history)
        messages.append({"role": "user", "content": final_message})

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=800,
            messages=messages,
        )

        reply = response.choices[0].message.content
        resume_id = resume.id if resume else None

        self.save_message(session_id, user_id, "user", user_message, resume_id=resume_id)
        self.save_message(session_id, user_id, "assistant", reply, resume_id=resume_id)

        return {"reply": reply, "intent": intent}
