from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
from datetime import datetime


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
    refresh_token:Optional[str]=None
    token_type: str = "bearer"
    user_id: int
    email: str


class UserOut(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Resume ──────────────────────────────────────────────────────────────────

class ResumeUploadResponse(BaseModel):
    id: int
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

    class Config:
        from_attributes = True


class ResumeListItem(BaseModel):
    id: int
    filename: str
    candidate_name: Optional[str]
    current_role: Optional[str]
    years_of_experience: Optional[float]
    uploaded_at: datetime

    class Config:
        from_attributes = True


# ─── Analysis ────────────────────────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    resume_id: int
    job_description: Optional[str] = None
    analysis_type: str = "general"   # "general" | "job_match" | "improvement"


class AnalysisOut(BaseModel):
    id: int
    resume_id: int
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

    class Config:
        from_attributes = True


# ─── Chat ────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    resume_id: Optional[int] = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    intent: Optional[str] = None


# ─── Health ─────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str



#─── user session ─────────────────────────────────────────────────────────────────
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum

class USER_SESSION_STATUS (str, Enum):
    active = "active"
    revoked ="revoked"
    expired ="expired"
    

class UserSessionCreate(BaseModel):
    user_id: int
    refresh_token: str
    expires_at: datetime
    status: USER_SESSION_STATUS= USER_SESSION_STATUS.active
    revoked_at: Optional[datetime] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


class UserSessionSchema(BaseModel):
    id: int
    user_id: int
    expires_at: datetime
    status:  USER_SESSION_STATUS  # active | revoked | expired
    revoked_at: Optional[datetime] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)



class UserSessionResponse(BaseModel):
    id: Optional[str]=None
    user_id: Optional[str]=None
    expires_at: Optional[datetime]=None
    status:  Optional[USER_SESSION_STATUS]=None  # active | revoked | expired
    revoked_at: Optional[datetime] =None
    user_agent: Optional[str] =None
    ip_address: Optional[str] =None