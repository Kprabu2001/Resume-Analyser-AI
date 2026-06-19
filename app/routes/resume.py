import io
import json
import logging

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import Response

from app.core.config import settings
from app.dependencies.auth_dependency import CurrentUserIdDep
from app.dependencies.db_dependency import AppSessionDep
from app.models.schemas import AnalysisOut, AnalysisRequest, CoverLetterRequest, CoverLetterResponse, ResumeListItem, ResumeUploadResponse
from app.services.resume_service import ResumeService
from app.base.base import ApiResponse
from app.utils.file_validator import validate_file, extract_text_from_docx
from app.utils.pdf_export import analysis_to_pdf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resumes", tags=["Resumes"])


def _extract_text_from_upload(file: UploadFile) -> str:
    content = file.file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_upload_size_mb}MB.",
        )

    valid, file_type = validate_file(content, file.filename or "")
    if not valid:
        raise HTTPException(status_code=400, detail=file_type)

    if file_type == "pdf":
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
        except Exception as e:
            logger.warning(f"pdfplumber failed: {e}, trying pypdf")
            try:
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(content))
                return "\n".join(p.extract_text() or "" for p in reader.pages)
            except Exception as e2:
                raise HTTPException(status_code=400, detail=f"Could not extract text from PDF: {e2}")

    if file_type == "docx":
        try:
            return extract_text_from_docx(content)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not extract text from DOCX: {e}")

    try:
        return content.decode("utf-8")
    except Exception:
        try:
            return content.decode("latin-1")
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file encoding. Please upload a PDF, DOCX, or plain text file.",
            )


@router.post("/upload", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_resume(
    app_session: AppSessionDep,
    user_id: CurrentUserIdDep,
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    allowed_types = {"application/pdf", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    if file.content_type not in allowed_types and not file.filename.endswith((".pdf", ".docx", ".txt")):
        raise HTTPException(status_code=400, detail="Only PDF, DOCX, and plain text files are supported.")

    raw_text = _extract_text_from_upload(file)
    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract any text from the file.")

    return ResumeService(app_session).create_and_parse(user_id, file.filename, raw_text)


@router.get("/", response_model=list[ResumeListItem])
def list_resumes(app_session: AppSessionDep, user_id: CurrentUserIdDep):
    return ResumeService(app_session).get_user_resumes(user_id)


@router.get("/{resume_id}", response_model=ResumeUploadResponse)
def get_resume(resume_id: str, app_session: AppSessionDep, user_id: CurrentUserIdDep):
    resume = ResumeService(app_session).get_by_id(resume_id, user_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")
    return resume


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(resume_id: str, app_session: AppSessionDep, user_id: CurrentUserIdDep):
    resume = ResumeService(app_session).delete(resume_id, user_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")


@router.post("/analyse", response_model=AnalysisOut, status_code=status.HTTP_201_CREATED)
def run_analysis(
    request: AnalysisRequest,
    app_session: AppSessionDep,
    user_id: CurrentUserIdDep,
):
    service = ResumeService(app_session)
    resume = service.get_by_id(request.resume_id, user_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")
    return service.analyse(
        resume,
        job_description=request.job_description,
        analysis_type=request.analysis_type,
    )


@router.get("/{resume_id}/analyses", response_model=list[AnalysisOut])
def list_analyses(resume_id: str, app_session: AppSessionDep, user_id: CurrentUserIdDep):
    service = ResumeService(app_session)
    resume = service.get_by_id(resume_id, user_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")
    return service.get_analyses(resume_id)


@router.get("/{resume_id}/analyses/{analysis_id}/export")
def export_analysis_pdf(
    resume_id: str, analysis_id: str,
    app_session: AppSessionDep, user_id: CurrentUserIdDep,
):
    service = ResumeService(app_session)
    resume = service.get_by_id(resume_id, user_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")
    analyses = service.get_analyses(resume_id)
    analysis = next((a for a in analyses if a.id == analysis_id), None)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    pdf_bytes = analysis_to_pdf(
        {
            "overall_score": analysis.overall_score,
            "ats_score": analysis.ats_score,
            "skills_score": analysis.skills_score,
            "experience_score": analysis.experience_score,
            "education_score": analysis.education_score,
            "formatting_score": analysis.formatting_score,
            "summary": analysis.summary,
            "strengths": analysis.strengths if isinstance(analysis.strengths, list) else json.loads(analysis.strengths or "[]"),
            "weaknesses": analysis.weaknesses if isinstance(analysis.weaknesses, list) else json.loads(analysis.weaknesses or "[]"),
            "suggestions": analysis.suggestions if isinstance(analysis.suggestions, list) else json.loads(analysis.suggestions or "[]"),
            "missing_keywords": analysis.missing_keywords if isinstance(analysis.missing_keywords, list) else json.loads(analysis.missing_keywords or "[]"),
            "matched_keywords": analysis.matched_keywords if isinstance(analysis.matched_keywords, list) else json.loads(analysis.matched_keywords or "[]"),
        },
        {
            "candidate_name": resume.candidate_name,
            "current_role": resume.current_role,
            "filename": resume.filename,
        },
    )
    return Response(
        content=bytes(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=analysis_{analysis_id}.pdf"},
    )


@router.post("/cover-letter", response_model=CoverLetterResponse, status_code=status.HTTP_200_OK)
def generate_cover_letter(
    request: CoverLetterRequest,
    app_session: AppSessionDep,
    user_id: CurrentUserIdDep,
):
    service = ResumeService(app_session)
    resume = service.get_by_id(request.resume_id, user_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")
    result = service.generate_cover_letter(
        resume,
        job_description=request.job_description,
        tone=request.tone,
        company_name=request.company_name,
        hiring_manager=request.hiring_manager,
    )
    return CoverLetterResponse(
        cover_letter=result.get("cover_letter", ""),
        subject=result.get("subject"),
    )
