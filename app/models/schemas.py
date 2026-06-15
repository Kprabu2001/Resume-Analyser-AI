from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


# ─── Auth ────────────────────────────────────────────────────────────────────

class UserSignUp(BaseModel):
    full_name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserTokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user_id: str
    email: str


class UserOut(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─── Resume ──────────────────────────────────────────────────────────────────

class ResumeUploadResponse(BaseModel):
    id: str
    filename: str
    candidate_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    location: Optional[str]
    years_of_experience: Optional[float]
    education_level: Optional[str]
    current_role: Optional[str]
    skills: Optional[List[str]]
    work_experience: Optional[List[Any]]
    education: Optional[List[Any]]
    certifications: Optional[List[str]]
    languages: Optional[List[str]]
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeListItem(BaseModel):
    id: str
    filename: str
    candidate_name: Optional[str]
    current_role: Optional[str]
    years_of_experience: Optional[float]
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─── Analysis ────────────────────────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    resume_id: str
    job_description: Optional[str] = None
    analysis_type: str = "general"


class AnalysisOut(BaseModel):
    id: str
    resume_id: str
    analysis_type: str
    job_description: Optional[str]
    overall_score: Optional[float]
    ats_score: Optional[float]
    skills_score: Optional[float]
    experience_score: Optional[float]
    education_score: Optional[float]
    formatting_score: Optional[float]
    strengths: Optional[List[str]]
    weaknesses: Optional[List[str]]
    suggestions: Optional[List[str]]
    missing_keywords: Optional[List[str]]
    matched_keywords: Optional[List[str]]
    summary: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─── Cover Letter ────────────────────────────────────────────────────────────

class CoverLetterRequest(BaseModel):
    resume_id: str
    job_description: Optional[str] = None
    tone: str = "professional"
    company_name: Optional[str] = None
    hiring_manager: Optional[str] = None


class CoverLetterResponse(BaseModel):
    cover_letter: str
    subject: Optional[str] = None


# ─── Chat ────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    resume_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    intent: Optional[str] = None


# ─── Health ─────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


# ─── User Session ───────────────────────────────────────────────────────────

class USER_SESSION_STATUS(str, Enum):
    active = "active"
    revoked = "revoked"
    expired = "expired"


class UserSessionCreate(BaseModel):
    user_id: str
    refresh_token: str
    expires_at: datetime
    status: USER_SESSION_STATUS = USER_SESSION_STATUS.active
    revoked_at: Optional[datetime] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


class UserSessionSchema(BaseModel):
    id: str
    user_id: str
    expires_at: datetime
    status: USER_SESSION_STATUS
    revoked_at: Optional[datetime] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserSessionResponse(BaseModel):
    id: Optional[str] = None
    user_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    status: Optional[USER_SESSION_STATUS] = None
    revoked_at: Optional[datetime] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None