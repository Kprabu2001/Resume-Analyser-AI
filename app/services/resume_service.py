import json
import logging
import re
from typing import Optional

from groq import Groq

from app.base.base_repository import BaseRepository
from app.base.base_service import BaseService
from app.core.config import settings
from app.repositories.resume_repository import ResumeRepository

logger = logging.getLogger(__name__)

client = Groq(api_key=settings.groq_api_key)

PARSE_SYSTEM = """You are an expert resume parser. Extract structured information from the resume text provided.
Return ONLY a valid JSON object with these exact keys (use null for missing fields):
{
  "candidate_name": string or null,
  "email": string or null,
  "phone": string or null,
  "location": string or null,
  "years_of_experience": number or null,
  "education_level": string or null,
  "current_role": string or null,
  "skills": [list of skill strings],
  "work_experience": [{"company": string, "role": string, "duration": string, "description": string}],
  "education": [{"degree": string, "institution": string, "year": string}],
  "certifications": [list of certification strings],
  "languages": [list of language strings]
}
No markdown, no explanations — only the JSON object."""

ANALYSIS_SYSTEM = """You are an expert resume analyst and career coach. Analyse the given resume (and optionally a job description) and return ONLY a valid JSON object with:
{
  "overall_score": number 0-100,
  "ats_score": number 0-100,
  "skills_score": number 0-100,
  "experience_score": number 0-100,
  "education_score": number 0-100,
  "formatting_score": number 0-100,
  "strengths": [list of strength strings],
  "weaknesses": [list of weakness strings],
  "suggestions": [list of actionable improvement suggestions],
  "missing_keywords": [keywords missing vs JD, empty list if no JD],
  "matched_keywords": [keywords matched vs JD, empty list if no JD],
  "summary": "A 2-3 sentence overall assessment paragraph"
}
No markdown, no extra text — only the JSON object."""


def _parse_resume_text(raw_text: str) -> dict:
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=2000,
            messages=[
                {"role": "system", "content": PARSE_SYSTEM},
                {"role": "user", "content": f"Parse this resume:\n\n{raw_text[:8000]}"},
            ],
        )
        text = response.choices[0].message.content.strip()
        text = re.sub(r"^```json\s*|^```\s*|```$", "", text, flags=re.MULTILINE).strip()
        return json.loads(text)
    except Exception as e:
        logger.error(f"Resume parse error: {e}")
        return {}


class ResumeService(BaseService):

    def _get_repository(self) -> BaseRepository:
        return ResumeRepository(self.session)

    def create_and_parse(self, user_id: str, filename: str, raw_text: str):
        with self.get_db_session():
            resume = self.repository.create_resume(
                user_id=user_id,
                filename=filename,
                raw_text=raw_text,
            )

        parsed = _parse_resume_text(raw_text)

        if parsed:
            with self.get_db_session():
                resume = self.repository.update_resume_fields(resume, parsed)

        return resume

    def get_user_resumes(self, user_id: str):
        return self.repository.get_user_resumes(user_id)

    def get_by_id(self, resume_id: str, user_id: str):
        return self.repository.get_resume_by_id(resume_id, user_id)

    def delete(self, resume_id: str, user_id: str):
        resume = self.repository.get_resume_by_id(resume_id, user_id)
        if not resume:
            return None
        with self.get_db_session():
            self.repository.delete_resume(resume)
        return resume

    def analyse(self, resume, job_description: Optional[str] = None, analysis_type: str = "general"):
        resume_context = f"""
Candidate: {resume.candidate_name or 'Unknown'}
Current Role: {resume.current_role or 'N/A'}
Years of Experience: {resume.years_of_experience or 'N/A'}
Education Level: {resume.education_level or 'N/A'}
Skills: {', '.join(resume.skills or [])}
Work Experience: {json.dumps(resume.work_experience or [], indent=2)}
Education: {json.dumps(resume.education or [], indent=2)}
Certifications: {', '.join(resume.certifications or [])}
Languages: {', '.join(resume.languages or [])}

--- RAW RESUME TEXT (first 4000 chars) ---
{resume.raw_text[:4000]}
        """

        user_msg = f"Analyse this resume:\n{resume_context}"
        if job_description:
            user_msg += f"\n\n--- JOB DESCRIPTION ---\n{job_description[:2000]}"
            user_msg += "\n\nFocus on how well this resume matches the job description."

        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                max_tokens=2000,
                messages=[
                    {"role": "system", "content": ANALYSIS_SYSTEM},
                    {"role": "user", "content": user_msg},
                ],
            )
            text = response.choices[0].message.content.strip()
            text = re.sub(r"^```json\s*|^```\s*|```$", "", text, flags=re.MULTILINE).strip()
            data = json.loads(text)
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            data = {
                "overall_score": 0, "ats_score": 0, "skills_score": 0,
                "experience_score": 0, "education_score": 0, "formatting_score": 0,
                "strengths": [], "weaknesses": ["Analysis failed — please retry."],
                "suggestions": [], "missing_keywords": [], "matched_keywords": [],
                "summary": "Analysis could not be completed.",
            }

        with self.get_db_session():
            analysis = self.repository.create_analysis(
                resume_id=resume.id,
                job_description=job_description,
                analysis_type=analysis_type,
                data=data,
            )

        return analysis

    def get_analyses(self, resume_id: str):
        return self.repository.get_analyses_for_resume(resume_id)

    def generate_cover_letter(
        self,
        resume,
        job_description: Optional[str] = None,
        tone: str = "professional",
        company_name: Optional[str] = None,
        hiring_manager: Optional[str] = None,
    ) -> dict:
        resume_context = f"""
Candidate: {resume.candidate_name or 'Unknown'}
Current Role: {resume.current_role or 'N/A'}
Years of Experience: {resume.years_of_experience or 'N/A'}
Skills: {', '.join(resume.skills or [])}
Work Experience: {json.dumps(resume.work_experience or [], indent=2)}
Education: {json.dumps(resume.education or [], indent=2)}
Raw Text: {resume.raw_text[:2000]}
        """

        system = f"""You are an expert cover letter writer. Write a {tone} cover letter for the candidate based on their resume.
The letter should be well-structured, compelling, and tailored to the role and company.
Use the candidate's actual experience, skills, and achievements from the resume.

Return ONLY a valid JSON object:
{{
  "subject": "A compelling email subject line",
  "cover_letter": "The full cover letter with proper salutation, body paragraphs, and closing"
}}

The cover_letter should be 3-4 paragraphs, written in a {tone} tone, ready to copy-paste.
No markdown, no explanations — only the JSON object."""

        user_msg = f"Write a cover letter for this candidate:\n{resume_context}"
        if job_description:
            user_msg += f"\n\n--- JOB DESCRIPTION ---\n{job_description[:3000]}"
        if company_name:
            user_msg += f"\nCompany: {company_name}"
        if hiring_manager:
            user_msg += f"\nHiring Manager: {hiring_manager}"

        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                max_tokens=2000,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_msg},
                ],
            )
            text = response.choices[0].message.content.strip()
            text = re.sub(r"^```json\s*|^```\s*|```$", "", text, flags=re.MULTILINE).strip()
            return json.loads(text)
        except Exception as e:
            logger.error(f"Cover letter generation error: {e}")
            return {
                "subject": "Cover Letter",
                "cover_letter": "Could not generate cover letter. Please try again.",
            }
