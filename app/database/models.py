from sqlalchemy import Column, String, Float, Text, ForeignKey, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship, foreign
from datetime import datetime, timezone
import uuid

from app.base.base import Base, AppBase
from app.base.id_gen import generate_id


class User(AppBase):
    __tablename__ = "users"
    __pk_prefix__ = "USR"

    id = Column(String, primary_key=True, default=lambda: generate_id("USR"))
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
    __pk_prefix__ = "USES"

    id = Column(String, primary_key=True, default=lambda: generate_id("USES"))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    refresh_token = Column(String, nullable=False, index=True)
    status = Column(String, default="active", nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True, default=None)
    user_agent = Column(String, nullable=False)
    ip_address = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

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
    __pk_prefix__ = "CHS"

    id = Column(String, primary_key=True, default=lambda: generate_id("CHS"))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="chat_session",
        primaryjoin="ChatSession.id == foreign(ChatMessage.session_id)",
        cascade="all, delete-orphan")


class Resume(AppBase):
    __tablename__ = "resumes"
    __pk_prefix__ = "RES"

    id = Column(String, primary_key=True, default=lambda: generate_id("RES"))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    raw_text = Column(Text, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.now(timezone.utc))

    candidate_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    location = Column(String, nullable=True)
    years_of_experience = Column(Float, nullable=True)
    education_level = Column(String, nullable=True)
    current_role = Column(String, nullable=True)

    skills = Column(JSON, nullable=True)
    work_experience = Column(JSON, nullable=True)
    education = Column(JSON, nullable=True)
    certifications = Column(JSON, nullable=True)
    languages = Column(JSON, nullable=True)

    analyses = relationship("ResumeAnalysis", back_populates="resume", cascade="all, delete-orphan")
    user = relationship("User", back_populates="resumes")


class ResumeAnalysis(AppBase):
    __tablename__ = "resume_analyses"
    __pk_prefix__ = "RAN"

    id = Column(String, primary_key=True, default=lambda: generate_id("RAN"))
    resume_id = Column(String, ForeignKey("resumes.id"), nullable=False)
    job_description = Column(Text, nullable=True)
    analysis_type = Column(String, nullable=False)

    overall_score = Column(Float, nullable=True)
    ats_score = Column(Float, nullable=True)
    skills_score = Column(Float, nullable=True)
    experience_score = Column(Float, nullable=True)
    education_score = Column(Float, nullable=True)
    formatting_score = Column(Float, nullable=True)

    strengths = Column(JSON, nullable=True)
    weaknesses = Column(JSON, nullable=True)
    suggestions = Column(JSON, nullable=True)
    missing_keywords = Column(JSON, nullable=True)
    matched_keywords = Column(JSON, nullable=True)
    summary = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    resume = relationship("Resume", back_populates="analyses")


class ChatMessage(AppBase):
    __tablename__ = "chat_messages"
    __pk_prefix__ = "CHM"

    id = Column(String, primary_key=True, default=lambda: generate_id("CHM"))
    session_id = Column(String, nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    resume_id = Column(String, ForeignKey("resumes.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    user = relationship("User", back_populates="chat_messages")
    chat_session = relationship("ChatSession", back_populates="messages",
        primaryjoin="foreign(ChatMessage.session_id) == ChatSession.id")
