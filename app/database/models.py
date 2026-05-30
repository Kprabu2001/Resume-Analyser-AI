from sqlalchemy import Column, String, Float, Integer, Text, ForeignKey, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship, foreign
from datetime import datetime,timezone
import uuid

from app.base.base import Base, AppBase


class User(AppBase):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, nullable=False, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")

class UserSession(AppBase):
    __tablename__ = "user_sessions"
 
    id = Column(Integer, primary_key=True,  autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    refresh_token = Column(String, nullable=False, index=True)
    status = Column(String, default="active", nullable=False)  # active | revoked | expired
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True, default=None)
    user_agent = Column(String, nullable=False)
    ip_address = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
 
    # user = relationship("User", back_populates="user_sessions")
    user = relationship("User")
    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return True
        now = datetime.now(timezone.utc)
        exp = (
            self.expires_at.replace(tzinfo=timezone.utc)
            if self.expires_at.tzinfo is None
            else self.expires_at
        )
        return now >= exp
 
    @property
    def is_revoked(self) -> bool:
        return self.status == "revoked" or self.revoked_at is not None
 
    @property
    def is_active(self) -> bool:
        return self.status == "active" and not self.is_expired and not self.is_revoked
 

 


class ChatSession(AppBase):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="chat_session",
        primaryjoin="ChatSession.id == foreign(ChatMessage.session_id)",
        cascade="all, delete-orphan")


class Resume(AppBase):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    raw_text = Column(Text, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.now(timezone.utc))

    # Parsed fields
    candidate_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    location = Column(String, nullable=True)
    years_of_experience = Column(Float, nullable=True)
    education_level = Column(String, nullable=True)   # e.g. "Bachelor's", "Master's", "PhD"
    current_role = Column(String, nullable=True)

    # JSON arrays stored as JSON
    skills = Column(JSON, nullable=True)           # list of skill strings
    work_experience = Column(JSON, nullable=True)  # list of {company, role, duration}
    education = Column(JSON, nullable=True)        # list of {degree, institution, year}
    certifications = Column(JSON, nullable=True)   # list of cert strings
    languages = Column(JSON, nullable=True)        # list of language strings

    analyses = relationship("ResumeAnalysis", back_populates="resume", cascade="all, delete-orphan")

    user = relationship("User", back_populates="resumes")


class ResumeAnalysis(AppBase):
    __tablename__ = "resume_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    job_description = Column(Text, nullable=True)   # optional JD to match against
    analysis_type = Column(String, nullable=False)   # "general" | "job_match" | "improvement"

    # Scores (0-100)
    overall_score = Column(Float, nullable=True)
    ats_score = Column(Float, nullable=True)
    skills_score = Column(Float, nullable=True)
    experience_score = Column(Float, nullable=True)
    education_score = Column(Float, nullable=True)
    formatting_score = Column(Float, nullable=True)

    # Textual feedback
    strengths = Column(JSON, nullable=True)          # list of strength strings
    weaknesses = Column(JSON, nullable=True)         # list of weakness strings
    suggestions = Column(JSON, nullable=True)        # list of improvement suggestions
    missing_keywords = Column(JSON, nullable=True)   # list of missing keywords vs JD
    matched_keywords = Column(JSON, nullable=True)   # list of matched keywords vs JD
    summary = Column(Text, nullable=True)            # paragraph summary

    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    resume = relationship("Resume", back_populates="analyses")


class ChatMessage(AppBase):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String, nullable=False)   # "user" or "assistant"
    content = Column(Text, nullable=False)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)  # context resume
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    user = relationship("User", back_populates="chat_messages")
    chat_session = relationship("ChatSession", back_populates="messages",
        primaryjoin="foreign(ChatMessage.session_id) == ChatSession.id")
