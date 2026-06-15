import io
import logging

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.config import settings
from app.dependencies.auth_dependency import CurrentUserIdDep
from app.dependencies.db_dependency import AppSessionDep
from app.models.schemas import AnalysisOut, AnalysisRequest, ResumeListItem, ResumeUploadResponse
from app.services.resume_service import ResumeService
from app.base.base import ApiResponse

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
    filename = file.filename or ""

    if filename.lower().endswith(".pdf"):
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

    try:
        return content.decode("utf-8")
    except Exception:
        try:
            return content.decode("latin-1")
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file encoding. Please upload a PDF or plain text file.",
            )


@router.post("/upload", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_resume(
    app_session: AppSessionDep,
    user_id: CurrentUserIdDep,
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    allowed_types = {"application/pdf", "text/plain"}
    if file.content_type not in allowed_types and not file.filename.endswith((".pdf", ".txt")):
        raise HTTPException(status_code=400, detail="Only PDF and plain text files are supported.")

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
    return ApiResponse(message="Resume deleted successfully.")


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
