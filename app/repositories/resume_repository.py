import logging
from typing import Optional

from app.base.app_session import AppSession
from app.base.base_repository import BaseRepository
from app.database.models import ChatMessage, ChatSession, Resume, ResumeAnalysis

logger = logging.getLogger(__name__)


class ResumeRepository(BaseRepository):
    """
    Handles all DB operations for Resume, ResumeAnalysis and ChatMessage.
    Receives an AppSession through BaseRepository.__init__.
    """

    def __init__(self, db: AppSession) -> None:
        super().__init__(db)

    # ── Resume ────────────────────────────────────────────────────────────────

    def create_resume(self, user_id: int, filename: str, raw_text: str) -> Resume:
        return self.create(
            Resume,
            user_id=user_id,
            filename=filename,
            raw_text=raw_text,
        )

    def get_resume_by_id(self, resume_id: int, user_id: int) -> Optional[Resume]:
        return self.get_one(Resume, id=resume_id, user_id=user_id)

    def get_user_resumes(self, user_id: int):
        return (
            self.db.query(Resume)
            .filter(Resume.user_id == user_id)
            .order_by(Resume.uploaded_at.desc())
            .all()
        )

    def delete_resume(self, resume: Resume) -> None:
        # Remove related chat messages first to avoid FK constraint errors
        self.db.query(ChatMessage).filter(ChatMessage.resume_id == resume.id).delete()
        self.delete(resume)

    def update_resume_fields(self, resume: Resume, parsed: dict) -> Resume:
        resume.candidate_name = parsed.get("candidate_name")
        resume.email = parsed.get("email")
        resume.phone = parsed.get("phone")
        resume.location = parsed.get("location")
        resume.years_of_experience = parsed.get("years_of_experience")
        resume.education_level = parsed.get("education_level")
        resume.current_role = parsed.get("current_role")
        resume.skills = parsed.get("skills") or []
        resume.work_experience = parsed.get("work_experience") or []
        resume.education = parsed.get("education") or []
        resume.certifications = parsed.get("certifications") or []
        resume.languages = parsed.get("languages") or []
        self.db.flush()
        self.db.refresh(resume)
        return resume

    # ── ResumeAnalysis ────────────────────────────────────────────────────────

    def create_analysis(
        self,
        resume_id: int,
        job_description: Optional[str],
        analysis_type: str,
        data: dict,
    ) -> ResumeAnalysis:
        return self.create(
            ResumeAnalysis,
            resume_id=resume_id,
            job_description=job_description,
            analysis_type=analysis_type,
            overall_score=data.get("overall_score"),
            ats_score=data.get("ats_score"),
            skills_score=data.get("skills_score"),
            experience_score=data.get("experience_score"),
            education_score=data.get("education_score"),
            formatting_score=data.get("formatting_score"),
            strengths=data.get("strengths"),
            weaknesses=data.get("weaknesses"),
            suggestions=data.get("suggestions"),
            missing_keywords=data.get("missing_keywords"),
            matched_keywords=data.get("matched_keywords"),
            summary=data.get("summary"),
        )

    def get_analyses_for_resume(self, resume_id: int):
        return (
            self.db.query(ResumeAnalysis)
            .filter(ResumeAnalysis.resume_id == resume_id)
            .order_by(ResumeAnalysis.created_at.desc())
            .all()
        )

    # ── ChatSession ──────────────────────────────────────────────────────────

    def create_chat_session(self, user_id: int) -> ChatSession:
        return self.create(ChatSession, user_id=user_id)

    # ── ChatMessage ───────────────────────────────────────────────────────────

    def create_chat_message(
        self,
        session_id: str,
        user_id: int,
        role: str,
        content: str,
        resume_id: Optional[int] = None,
    ) -> ChatMessage:
        return self.create(
            ChatMessage,
            session_id=session_id,
            user_id=user_id,
            role=role,
            content=content,
            resume_id=resume_id,
        )

    def get_chat_history(self, session_id: str) -> list[dict]:
        rows = (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.id.asc())
            .all()
        )
        return [{"role": row.role, "content": row.content} for row in rows[-20:]]

    def clear_chat_session(self, session_id: str) -> None:
        self.delete_by_query(ChatMessage, session_id=session_id)
